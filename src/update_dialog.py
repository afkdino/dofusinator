"""
UpdateDialog — modal de confirmação de atualização Velopack.

v1.0.34/Fase 4

Fluxo:
1. User clica no toast "Nova versão disponível"
2. Abre esse dialog modal centralizado
3. Mostra: versão atual, versão nova, botões "Atualizar agora" e "Mais tarde"
4. Se user clica "Atualizar agora":
   - Botões somem
   - Aparece progress bar indeterminada com texto "Baixando atualização..."
   - Quando download completa, app reinicia automaticamente via Velopack
5. Se user clica "Mais tarde":
   - Modal fecha
   - Próxima checagem ocorre na próxima abertura do app

Estilização: segue tema do app (bg, accent, text). Não usa cores hardcoded.

Uso:
    dialog = UpdateDialog(
        master=root,
        theme=theme,
        current_version="1.0.34",
        new_version="1.1.0",
        updater=dofus_updater,
        on_close=lambda: log.info("Update dialog fechado")
    )
    dialog.show()
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

import customtkinter as ctk

log = logging.getLogger(__name__)


class UpdateDialog:
    """Modal de confirmação de update Velopack."""

    DIALOG_WIDTH = 460
    DIALOG_HEIGHT = 240

    def __init__(
        self,
        master,
        theme: dict,
        current_version: str,
        new_version: str,
        updater,  # DofusUpdater
        on_close: Optional[Callable] = None,
    ):
        self.master = master
        self.theme = theme
        self.current_version = current_version
        self.new_version = new_version
        self.updater = updater
        self.on_close = on_close

        self.window: Optional[ctk.CTkToplevel] = None
        self._is_downloading = False

    def show(self):
        """Cria e exibe o modal."""
        try:
            self._build()
        except Exception as e:
            log.error(f"Erro ao mostrar UpdateDialog: {e}", exc_info=True)
            self._destroy()

    def _build(self):
        theme = self.theme

        self.window = ctk.CTkToplevel(self.master)
        self.window.title("Atualização disponível")
        self.window.geometry(f"{self.DIALOG_WIDTH}x{self.DIALOG_HEIGHT}")
        self.window.resizable(False, False)
        self.window.attributes('-topmost', True)
        self.window.configure(fg_color=theme.get('bg', '#2a1f1a'))

        # Centraliza na tela
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - self.DIALOG_WIDTH) // 2
        y = (self.window.winfo_screenheight() - self.DIALOG_HEIGHT) // 2
        self.window.geometry(f"{self.DIALOG_WIDTH}x{self.DIALOG_HEIGHT}+{x}+{y}")

        # Modal: bloqueia interação com main window enquanto aberto
        self.window.transient(self.master)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self._on_later)

        # === Conteúdo ===
        container = ctk.CTkFrame(self.window, fg_color="transparent")
        container.pack(fill='both', expand=True, padx=24, pady=20)

        # Título com emoji
        title_label = ctk.CTkLabel(
            container,
            text="🚀 Nova versão disponível!",
            font=('Segoe UI', 18, 'bold'),
            text_color=theme.get('accent', '#c5a572'),
        )
        title_label.pack(anchor='w', pady=(0, 8))

        # Texto descritivo
        desc_text = (
            f"A versão {self.new_version} do Dofusinator está disponível.\n"
            f"Você está usando a versão {self.current_version}."
        )
        desc_label = ctk.CTkLabel(
            container,
            text=desc_text,
            font=('Segoe UI', 11),
            text_color=theme.get('text', '#D5CFAA'),
            justify='left',
            anchor='w',
        )
        desc_label.pack(anchor='w', pady=(0, 16))

        # Container pra botões / progress (vai trocar conteúdo)
        self._action_container = ctk.CTkFrame(container, fg_color="transparent")
        self._action_container.pack(fill='x', side='bottom')

        self._show_buttons()

    def _show_buttons(self):
        """Exibe botões 'Atualizar agora' e 'Mais tarde'."""
        # Limpa container
        for w in self._action_container.winfo_children():
            w.destroy()

        # Botão "Mais tarde" (esquerda, secundário)
        btn_later = ctk.CTkButton(
            self._action_container,
            text="Mais tarde",
            font=('Segoe UI', 11),
            fg_color=self.theme.get('bg_pill', '#3a2a1f'),
            hover_color=self.theme.get('border', '#5a4a3f'),
            text_color=self.theme.get('text', '#D5CFAA'),
            width=140,
            height=36,
            command=self._on_later,
        )
        btn_later.pack(side='left')

        # Botão "Atualizar agora" (direita, primário)
        btn_update = ctk.CTkButton(
            self._action_container,
            text="Atualizar agora",
            font=('Segoe UI', 11, 'bold'),
            fg_color=self.theme.get('accent', '#c5a572'),
            hover_color=self.theme.get('accent_hover', '#d4b88a'),
            text_color=self.theme.get('bg', '#2a1f1a'),
            width=140,
            height=36,
            command=self._on_update_now,
        )
        btn_update.pack(side='right')

    def _show_progress(self):
        """Substitui botões por progress bar indeterminada + texto."""
        # Limpa container
        for w in self._action_container.winfo_children():
            w.destroy()

        # Texto de status
        self._status_label = ctk.CTkLabel(
            self._action_container,
            text="Baixando atualização...",
            font=('Segoe UI', 11),
            text_color=self.theme.get('text', '#D5CFAA'),
        )
        self._status_label.pack(anchor='w', pady=(0, 8))

        # Progress bar indeterminada
        self._progress = ctk.CTkProgressBar(
            self._action_container,
            mode='indeterminate',
            progress_color=self.theme.get('accent', '#c5a572'),
            fg_color=self.theme.get('bg_pill', '#3a2a1f'),
            height=10,
        )
        self._progress.pack(fill='x')
        self._progress.start()

    def _on_update_now(self):
        """User aceitou. Inicia download em background."""
        if self._is_downloading:
            return
        self._is_downloading = True

        log.info(f"User aceitou update {self.new_version}. Iniciando download...")
        self._show_progress()

        def on_done(success: bool):
            # Esse callback roda numa thread de background — marshallar pro main
            try:
                self.master.after(0, lambda: self._after_download(success))
            except Exception as e:
                log.error(f"Erro marshallando on_done: {e}", exc_info=True)

        def on_progress(pct: int):
            # Não usado por enquanto (velopack-py não dá granular).
            # Quando der, a gente troca progress mode='indeterminate' por 'determinate'.
            pass

        try:
            self.updater.download_async(on_done=on_done, on_progress=on_progress)
        except Exception as e:
            log.error(f"Falha ao iniciar download: {e}", exc_info=True)
            self._after_download(False)

    def _after_download(self, success: bool):
        """Callback no main thread após download terminar."""
        if success:
            try:
                self._status_label.configure(text="Reiniciando o app...")
            except Exception:
                pass
            log.info("Download OK. Aplicando update e reiniciando...")
            # Pequeno delay pra user ver "Reiniciando..." antes do app fechar
            self.master.after(800, self._apply_and_restart)
        else:
            log.error("Download falhou. Voltando pra estado de botões.")
            self._is_downloading = False
            try:
                self._show_buttons()
                # TODO: mostrar mensagem de erro discreta ali tipo "Falha. Tente mais tarde."
            except Exception:
                pass

    def _apply_and_restart(self):
        """Aplica o update e reinicia o app. NÃO RETORNA."""
        try:
            # IMPORTANT: Velopack mata o processo. Settings/cache devem estar
            # salvos antes daqui. (DofusUpdater já tem o release info em mãos
            # via download_async).
            self.updater.apply_and_restart()
        except Exception as e:
            log.error(f"apply_and_restart falhou: {e}", exc_info=True)
            self._destroy()

    def _on_later(self):
        """User postpôs. Fecha modal."""
        log.info(f"User postpos update {self.new_version}.")
        self._destroy()

    def _destroy(self):
        """Fecha o modal limpamente."""
        try:
            if self.window and self.window.winfo_exists():
                self.window.grab_release()
                self.window.destroy()
                self.window = None
        except Exception:
            pass
        if self.on_close:
            try:
                self.on_close()
            except Exception as e:
                log.error(f"on_close error: {e}", exc_info=True)
