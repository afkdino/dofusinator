"""
Welcome Screen - Tutorial de boas-vindas mostrado na primeira execução.

Modal de 5 passos:
  1. Bem-vindo (introdução)
  2. Idioma do app (dropdown - troca em runtime)
  3. Captura (instruções pra definir região do chat)
  4. Hotkey (mostra Ctrl+Shift+T)
  5. Pronto (dicas finais)

Botões:
  - "Pular tutorial": fecha imediatamente, marca first_run_completed=True
  - "Voltar / Próximo / Começar a usar": navegação

Persistência:
  - Marca settings.first_run_completed=True quando chegar no fim ou pular
  - Próxima execução não mostra mais

Modal:
  - grab_set() bloqueia interação com a main window
  - Centralizada em cima da main window
  - Custom titlebar (Dofusinator)

Bloco 3 / Sub-bloco 3.1 da v1.1
"""
import logging
import tkinter as tk
from typing import Optional, Callable

import customtkinter as ctk

from theme import get_theme
from custom_titlebar import apply_custom_titlebar
from assets_helper import apply_icon_via_win32, get_icon_path
from i18n import (
    t, set_language, get_supported_languages, get_language_label,
)

log = logging.getLogger(__name__)


class WelcomeScreen:
    """
    Modal de boas-vindas (tutorial de 5 passos).

    Uso:
        welcome = WelcomeScreen(
            parent=root,
            settings=settings,
            on_complete=lambda: print("done"),
        )
        welcome.show()
    """

    WINDOW_WIDTH = 560
    WINDOW_HEIGHT = 480
    TOTAL_STEPS = 5

    def __init__(
        self,
        parent: tk.Tk,
        settings,
        on_complete: Optional[Callable[[], None]] = None,
        on_language_changed: Optional[Callable[[str], None]] = None,
    ):
        self.parent = parent
        self.settings = settings
        self.on_complete = on_complete
        # Callback chamado se user trocar idioma na step 2 (pra app reagir em runtime)
        self.on_language_changed = on_language_changed

        self.window: Optional[ctk.CTkToplevel] = None
        self.current_step = 1

        # Refs pros widgets que precisam ser atualizados ao mudar de step
        self._heading_label: Optional[ctk.CTkLabel] = None
        self._body_label: Optional[ctk.CTkLabel] = None
        self._step_indicator_label: Optional[ctk.CTkLabel] = None
        self._next_btn: Optional[ctk.CTkButton] = None
        self._back_btn: Optional[ctk.CTkButton] = None
        self._skip_btn: Optional[ctk.CTkButton] = None
        self._lang_combo: Optional[ctk.CTkComboBox] = None
        self._lang_combo_frame: Optional[ctk.CTkFrame] = None

        # Cache do tema escolhido pra estilizar
        self._theme = get_theme(settings.get('main_window_theme', 'dofus_retro'))

        # Mapa label↔code do idioma
        supported = get_supported_languages()
        self._lang_labels_to_codes = {get_language_label(c): c for c in supported}
        self._lang_codes_to_labels = {c: get_language_label(c) for c in supported}

    def show(self):
        """Cria e mostra o modal."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self._build()
        self._render_step()

    # ========================================================================
    # Construção da UI
    # ========================================================================

    def _build(self):
        theme = self._theme

        self.window = ctk.CTkToplevel(self.parent)
        self.window.title(t("welcome.title"))
        self.window.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.window.configure(fg_color=theme['bg'])
        self.window.resizable(False, False)

        # Custom titlebar (sem botão de minimizar - é modal)
        apply_custom_titlebar(
            self.window,
            t("welcome.title"),
            on_close=self._on_skip,  # X = skip
            show_minimize=False,
            resizable=False,
            bg_color=theme['bg'],
            bg_titlebar=theme['titlebar_bg'],
            fg=theme['text'],
            accent=theme['accent'],
            bg_button_hover=theme['bg_hover'],
            close_hover_bg=theme['titlebar_close_hover'],
            min_width=self.WINDOW_WIDTH,
            min_height=self.WINDOW_HEIGHT,
        )
        # Ícone na barra (Win32) — delay igual nos outros toplevels
        self.window.after(300, lambda: apply_icon_via_win32(self.window))
        self.window.after(800, lambda: apply_icon_via_win32(self.window))

        # Conteúdo principal
        content = ctk.CTkFrame(self.window, fg_color="transparent")
        content.pack(fill='both', expand=True, padx=28, pady=20)

        # === HEADING ===
        self._heading_label = ctk.CTkLabel(
            content, text="",
            text_color=theme['accent'],
            font=('Segoe UI', 22, 'bold'),
            anchor='w', justify='left',
        )
        self._heading_label.pack(fill='x', pady=(0, 16))

        # === BODY (texto descritivo) ===
        self._body_label = ctk.CTkLabel(
            content, text="",
            text_color=theme['text'],
            font=('Segoe UI', 12),
            anchor='nw', justify='left',
            wraplength=self.WINDOW_WIDTH - 80,
        )
        self._body_label.pack(fill='x', pady=(0, 8))

        # === Combo de idioma (só aparece no step 2) ===
        self._lang_combo_frame = ctk.CTkFrame(content, fg_color="transparent")
        # NÃO pack ainda - só quando estiver no step 2

        current_lang = self.settings.get('ui_language', 'pt')
        self._lang_var = tk.StringVar(
            value=self._lang_codes_to_labels.get(current_lang, get_language_label('pt'))
        )
        self._lang_combo = ctk.CTkComboBox(
            self._lang_combo_frame,
            variable=self._lang_var,
            values=list(self._lang_labels_to_codes.keys()),
            width=260,
            fg_color=theme['bg_input'],
            border_color=theme['border'],
            button_color=theme['accent'],
            button_hover_color=theme['accent_hover'],
            text_color=theme['text'],
            dropdown_fg_color=theme['bg_input'],
            dropdown_text_color=theme['text'],
            dropdown_hover_color=theme['bg_hover'],
            command=self._on_language_picked,
            state='readonly',
        )
        self._lang_combo.pack(anchor='w', pady=(8, 0))

        # === Spacer pra empurrar rodapé pra baixo ===
        spacer = ctk.CTkFrame(content, fg_color="transparent", height=10)
        spacer.pack(fill='both', expand=True)

        # === RODAPÉ ===
        # Layout:
        #   [Pular tutorial]              [Passo X de Y]              [← Voltar] [Próximo →]
        #   ↑ esquerda                    ↑ centro                    ↑ direita (next na ponta)
        footer = ctk.CTkFrame(content, fg_color="transparent")
        footer.pack(fill='x', pady=(8, 0))

        # Skip button — ESQUERDA (rodapé)
        # Visual discreto mas LEGÍVEL no hover.
        # text_dim em hover_color cinza fica ilegível (cinza-em-cinza).
        # Solução: hover usa bg_pill (mais escuro) + bordinha accent + text_color via bind.
        self._skip_btn = ctk.CTkButton(
            footer, text=t("welcome.btn.skip"),
            command=self._on_skip,
            fg_color="transparent",
            hover_color=theme['bg_pill'],
            text_color=theme['text_dim'],
            border_width=1,
            border_color=theme['border'],
            font=('Segoe UI', 10),
            corner_radius=8, height=36, width=120,
        )
        # Aplica binds pra trocar text_color no hover (CTkButton não tem hover_text_color nativo)
        self._skip_btn.bind('<Enter>', lambda e: self._skip_btn.configure(text_color=theme['text']))
        self._skip_btn.bind('<Leave>', lambda e: self._skip_btn.configure(text_color=theme['text_dim']))
        self._skip_btn.pack(side='left')

        # Botão Próximo — DIREITA (na ponta direita do footer)
        self._next_btn = ctk.CTkButton(
            footer, text=t("welcome.btn.next"),
            command=self._on_next,
            fg_color=theme['accent'], hover_color=theme['accent_hover'],
            text_color=theme['text_on_accent'],
            font=('Segoe UI', 12, 'bold'),
            corner_radius=8, height=36, width=140,
        )
        self._next_btn.pack(side='right', padx=(8, 0))

        # Botão Voltar — DIREITA (à esquerda do Próximo)
        # NÃO faz pack inicial — _render_step decide quando mostrar (step >= 2)
        self._back_btn = ctk.CTkButton(
            footer, text=t("welcome.btn.back"),
            command=self._on_back,
            fg_color=theme['bg_pill'], hover_color=theme['bg_hover'],
            text_color=theme['text'],
            font=('Segoe UI', 11),
            corner_radius=8, height=36, width=100,
        )
        # NÃO chama .pack() aqui - deixa pro _render_step

        # Indicador "Passo X de Y" — CENTRO (entre skip e botões)
        # side='left' com expand=True pra ocupar o espaço sobrando após skip
        self._step_indicator_label = ctk.CTkLabel(
            footer, text="",
            text_color=theme['text_dim'],
            font=('Segoe UI', 10),
        )
        self._step_indicator_label.pack(side='left', expand=True)

        # === MODAL SETUP (no fim, com sequência segura) ===
        # ATENÇÃO: a ordem aqui é crítica. Bug anterior travava o app porque
        # o grab_set era aplicado antes da janela estar mapeada/visível.
        # Sequência correta:
        #   1. update_idletasks() → processa todos os eventos pendentes
        #   2. deiconify() → garante que está visível (não minimizada)
        #   3. lift() + focus_force() → traz pro topo
        #   4. update() → força um ciclo de render
        #   5. SÓ ENTÃO: grab_set (SEM transient, ver nota abaixo)
        #
        # IMPORTANTE: NÃO usar transient() aqui!
        # transient + overrideredirect(True) = bug fatal no Windows:
        # quando a janela perde foco (user click em outro app), o tk
        # desregistra ela do Alt+Tab e às vezes some completamente, mas
        # o grab_set continua ativo → app fantasma travado.
        #
        # Sem transient, a janela vira "top-level normal" — aparece no Alt+Tab
        # como qualquer aplicativo, e mesmo perdendo foco continua acessível.
        log.info("Welcome: configurando modal...")
        try:
            self.window.update_idletasks()
            self.window.deiconify()
            self._center_on_screen()  # ← centro da TELA, não do parent
            self.window.lift()
            self.window.focus_force()
            self.window.update()  # força ciclo de render

            # Agenda grab_set com delay generoso (300ms) - garantia extra de timing
            self.window.after(300, self._safe_grab_set)

            # === Defesas contra "fantasma ao perder foco" ===
            # Se a Welcome perder foco (user click em outra janela), força
            # voltar pro topo. Sem isso, o user pode "perder" a Welcome
            # atrás de outras janelas e o app parece travado (porque grab_set
            # ainda bloqueia interação com a main).
            self.window.bind('<FocusOut>', self._on_focus_out)

            # Atalho de emergência: Esc fecha a Welcome (igual ao Pular).
            # Se algo der errado e o user não conseguir clicar nos botões,
            # Esc resolve.
            self.window.bind('<Escape>', lambda e: self._on_skip())

            log.info("Welcome: modal configurado com sucesso")
        except Exception as e:
            # Se algo der errado, NÃO trava o app - apenas loga e segue.
            # User pode interagir normalmente (welcome fica como janela normal)
            log.error(f"Welcome: erro no modal setup (não-fatal): {e}", exc_info=True)
            # PARANOIA: força grab_release pra liberar input se algo deu errado
            try:
                self.window.grab_release()
            except Exception:
                pass

    def _on_focus_out(self, event):
        """
        Quando a Welcome perde foco, traz ela de volta pro topo.

        Sem isso (e sem transient), o user pode mover atenção pra outro app
        e a Welcome fica atrás. Como ela tem grab_set, a main fica bloqueada
        sem interação possível → impressão de app travado.

        Workaround: agenda um lift+focus em 100ms (delay pra não brigar com
        FocusOut events legítimos do tk durante diálogos internos).
        """
        try:
            if self.window and self.window.winfo_exists() and self.window.winfo_viewable():
                self.window.after(100, self._restore_focus)
        except Exception as e:
            log.debug(f"_on_focus_out falhou: {e}")

    def _restore_focus(self):
        """Restaura foco da Welcome (chamado após perder foco)."""
        try:
            if self.window and self.window.winfo_exists() and self.window.winfo_viewable():
                self.window.lift()
                self.window.focus_force()
        except Exception as e:
            log.debug(f"_restore_focus falhou: {e}")

    def _center_on_screen(self):
        """
        Centraliza no centro da tela primária.
        Substitui o _center_on_parent — agora a Welcome aparece no meio
        da tela independente de onde a janela principal estiver.
        """
        try:
            self.window.update_idletasks()
            screen_w = self.window.winfo_screenwidth()
            screen_h = self.window.winfo_screenheight()
            x = max(0, (screen_w - self.WINDOW_WIDTH) // 2)
            y = max(0, (screen_h - self.WINDOW_HEIGHT) // 2)
            self.window.geometry(f"+{x}+{y}")
        except Exception as e:
            log.debug(f"_center_on_screen falhou: {e}")

    def _safe_grab_set(self):
        """
        grab_set defensivo - NUNCA pode travar o app.

        Bugs históricos: grab_set em janela invisível trava o app inteiro
        sem possibilidade de fechar. Defensa em profundidade aqui:
          1. Verifica se janela existe
          2. Verifica se janela está mapeada (visível)
          3. Tenta grab_set
          4. Se qualquer coisa falhar, faz grab_release pra liberar input
        """
        try:
            if not self.window or not self.window.winfo_exists():
                log.warning("Welcome: window não existe pra grab_set")
                return

            # Verifica se a janela está REALMENTE mapeada (visível na tela).
            # winfo_viewable() retorna 1 se sim, 0 se não.
            if not self.window.winfo_viewable():
                log.warning("Welcome: window não viewable - pulando grab_set")
                return

            self.window.grab_set()
            self.window.focus_force()
            log.info("Welcome: grab_set aplicado")
        except Exception as e:
            log.error(f"Welcome: grab_set falhou ({e}) - liberando input")
            # Garantia: se grab_set deu erro parcial, força release
            try:
                self.window.grab_release()
            except Exception:
                pass

    # ========================================================================
    # Renderização dos passos
    # ========================================================================

    def _render_step(self):
        """Atualiza o conteúdo da janela conforme o step atual."""
        if not self.window or not self.window.winfo_exists():
            return

        step = self.current_step

        # Heading + body do step atual
        heading_key = f"welcome.step{step}.heading"
        body_key = f"welcome.step{step}.body"
        self._heading_label.configure(text=t(heading_key))
        self._body_label.configure(text=t(body_key))

        # Indicador de progresso
        self._step_indicator_label.configure(
            text=t("welcome.step_indicator", current=step, total=self.TOTAL_STEPS)
        )

        # Combo de idioma só aparece no step 2
        # Aparece logo abaixo do body_label (texto explicativo do idioma)
        # com pady decente pra dar respiro visual
        if step == 2:
            self._lang_combo_frame.pack(fill='x', pady=(8, 4))
        else:
            self._lang_combo_frame.pack_forget()

        # Botão "Voltar" só aparece a partir do step 2
        # IMPORTANTE: a ordem dos pack(side='right') já foi definida no _build:
        # - Primeiro packado: next  → fica MAIS à direita
        # - Depois packado: back    → fica à ESQUERDA do next
        # Aqui só fazemos hide/show do back, sem mexer na ordem.
        if step == 1:
            self._back_btn.pack_forget()
        else:
            # Re-mostra o back na posição correta (à esquerda do next)
            # Como o next já está mapeado, packar back com side='right' o coloca
            # à esquerda do next automaticamente.
            if not self._back_btn.winfo_ismapped():
                self._back_btn.pack(side='right', padx=(8, 0), before=self._next_btn)

        # Botão "Próximo" vira "Começar" no último step
        if step == self.TOTAL_STEPS:
            self._next_btn.configure(text=t("welcome.btn.finish"), width=160)
        else:
            self._next_btn.configure(text=t("welcome.btn.next"), width=140)

    # ========================================================================
    # Callbacks de navegação
    # ========================================================================

    def _on_next(self):
        if self.current_step < self.TOTAL_STEPS:
            self.current_step += 1
            self._render_step()
        else:
            # Último passo: finaliza
            self._finish(skipped=False)

    def _on_back(self):
        if self.current_step > 1:
            self.current_step -= 1
            self._render_step()

    def _on_skip(self):
        self._finish(skipped=True)

    def _on_language_picked(self, choice: str):
        """User trocou o idioma no combo (step 2)."""
        new_code = self._lang_labels_to_codes.get(choice, 'pt')
        log.info(f"Welcome: idioma escolhido = {new_code}")

        # Aplica em runtime — só pra UI da própria welcome screen
        set_language(new_code)
        # Salva no settings
        self.settings.set('ui_language', new_code)
        self.settings.save()

        # Atualiza labels do combo (recarrega com nomes no novo idioma)
        new_labels = {get_language_label(c): c for c in get_supported_languages()}
        self._lang_labels_to_codes = new_labels
        self._lang_codes_to_labels = {c: l for l, c in new_labels.items()}
        new_values = list(new_labels.keys())
        self._lang_combo.configure(values=new_values)
        self._lang_var.set(self._lang_codes_to_labels[new_code])

        # Re-renderiza o step atual com strings no novo idioma
        self._render_step()
        # Atualiza textos dos botões + título
        self._next_btn.configure(text=t("welcome.btn.next"))
        self._back_btn.configure(text=t("welcome.btn.back"))
        self._skip_btn.configure(text=t("welcome.btn.skip"))
        self.window.title(t("welcome.title"))

        # Notifica o app pra atualizar a main window se quiser
        if self.on_language_changed:
            try:
                self.on_language_changed(new_code)
            except Exception as e:
                log.error(f"on_language_changed callback falhou: {e}")

    # ========================================================================
    # Finalização
    # ========================================================================

    def _finish(self, skipped: bool):
        """Marca first_run_completed e fecha o modal."""
        try:
            self.settings.set('first_run_completed', True)
            self.settings.save()
            log.info(f"Welcome screen finalizada (skipped={skipped})")
        except Exception as e:
            log.error(f"Erro ao salvar first_run_completed: {e}")

        # Libera grab e destrói
        try:
            if self.window and self.window.winfo_exists():
                self.window.grab_release()
                self.window.destroy()
        except Exception as e:
            log.debug(f"Destroy welcome falhou: {e}")

        # Callback do app
        if self.on_complete:
            try:
                self.on_complete()
            except Exception as e:
                log.error(f"on_complete callback falhou: {e}")
