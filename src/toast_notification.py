"""
ToastNotification - Notificação flutuante estilizada (canto sup-direito).

Aparece com fade-in, mantém visível por X ms, some com fade-out.
Stackable: múltiplos toasts se empilham verticalmente.

Uso:
    toast_mgr = ToastManager(root, theme)
    toast_mgr.show("✓ Tema do overlay alterado", level='success')
    toast_mgr.show("⚠️ Reabra o app pra aplicar", level='warning')

Levels:
    'success' (verde/accent) — config salva normal
    'warning' (amarelo/laranja) — precisa restart
    'info' (azul/dim) — neutro

v1.0.30 / Auto-apply settings
"""
import logging
import tkinter as tk
from typing import Optional

import customtkinter as ctk

log = logging.getLogger(__name__)


class ToastManager:
    """
    Gerencia múltiplos toasts empilhados no canto superior-direito da janela.

    A posição é relativa ao root.
    Toast zero fica logo abaixo da titlebar/abas (offset configurável).
    Próximos empilham abaixo (com gap entre eles).
    """

    # Configuração visual
    DEFAULT_DURATION_MS = 2000
    FADE_IN_MS = 200
    FADE_OUT_MS = 300
    FADE_STEPS = 10  # quantos passos de fade
    TOAST_WIDTH = 260
    TOAST_HEIGHT = 44
    OFFSET_TOP = 90        # distância do topo da janela (abaixo das abas)
    OFFSET_RIGHT = 20      # distância da borda direita
    GAP_BETWEEN = 8        # espaço entre toasts empilhados

    def __init__(self, root, theme: dict):
        self.root = root
        self.theme = theme
        # Lista de toasts ativos (Toplevel widgets)
        self._active_toasts: list = []

    def update_theme(self, theme: dict):
        """Atualiza o tema usado nos novos toasts."""
        self.theme = theme

    def show(self, text: str, level: str = 'success', duration_ms: Optional[int] = None):
        """
        Mostra um toast. Se já tem outros visíveis, empilha abaixo.

        Args:
            text: texto a exibir
            level: 'success' / 'warning' / 'info'
            duration_ms: tempo visível antes do fade out (default 2000ms)
        """
        if duration_ms is None:
            duration_ms = self.DEFAULT_DURATION_MS

        try:
            toast = _Toast(self.root, self.theme, text, level, duration_ms,
                           on_destroy=self._on_toast_destroyed)
            self._active_toasts.append(toast)
            # IMPORTANTE: show() CRIA a window e chama geometry. Precisa rodar
            # ANTES do reposition pra ter window.winfo_exists() == True.
            toast.show()
            self._reposition_toasts()
        except Exception as e:
            log.error(f"Erro ao mostrar toast: {e}", exc_info=True)

    def _on_toast_destroyed(self, toast):
        """Callback quando um toast some (animação acabou ou foi clicado)."""
        if toast in self._active_toasts:
            self._active_toasts.remove(toast)
        self._reposition_toasts()

    def _reposition_toasts(self):
        """Reposiciona todos os toasts ativos pra ficarem empilhados."""
        try:
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            root_w = self.root.winfo_width()

            base_x = root_x + root_w - self.TOAST_WIDTH - self.OFFSET_RIGHT
            base_y = root_y + self.OFFSET_TOP

            for i, toast in enumerate(self._active_toasts):
                if toast.window and toast.window.winfo_exists():
                    y = base_y + i * (self.TOAST_HEIGHT + self.GAP_BETWEEN)
                    toast.window.geometry(f"{self.TOAST_WIDTH}x{self.TOAST_HEIGHT}+{base_x}+{y}")
        except Exception as e:
            log.debug(f"reposition_toasts: {e}")

    def clear_all(self):
        """Esconde todos os toasts (útil em close/destroy)."""
        for toast in list(self._active_toasts):
            try:
                toast.destroy()
            except Exception:
                pass
        self._active_toasts.clear()


class _Toast:
    """Toast individual. Use ToastManager pra criar."""

    def __init__(self, root, theme: dict, text: str, level: str,
                 duration_ms: int, on_destroy=None):
        self.root = root
        self.theme = theme
        self.text = text
        self.level = level
        self.duration_ms = duration_ms
        self.on_destroy = on_destroy

        self.window: Optional[tk.Toplevel] = None
        self._fade_alpha = 0.0
        self._fade_after_id: Optional[str] = None
        self._destroyed = False

    def show(self):
        """Cria o Toplevel e inicia animação de fade-in."""
        try:
            self.window = tk.Toplevel(self.root)
            self.window.overrideredirect(True)
            self.window.attributes('-topmost', True)
            self.window.attributes('-alpha', 0.0)  # começa invisível

            # Cores baseadas no level
            bg_color, fg_color, border_color = self._get_colors()
            self.window.configure(bg=bg_color)

            # Container com padding interno
            container = tk.Frame(self.window, bg=bg_color,
                                 highlightbackground=border_color,
                                 highlightthickness=1, bd=0)
            container.pack(fill='both', expand=True)

            # Texto
            label = tk.Label(
                container, text=self.text,
                bg=bg_color, fg=fg_color,
                font=('Segoe UI', 10, 'bold'),
                anchor='w', padx=12, pady=10,
                wraplength=ToastManager.TOAST_WIDTH - 24,
                justify='left',
            )
            label.pack(fill='both', expand=True)

            # Click no toast → fecha imediatamente
            def click_dismiss(event=None):
                if not self._destroyed:
                    self._fade_out()
            self.window.bind('<Button-1>', click_dismiss)
            container.bind('<Button-1>', click_dismiss)
            label.bind('<Button-1>', click_dismiss)

            # Inicia fade-in
            self._fade_in()

        except Exception as e:
            log.error(f"Erro ao criar toast window: {e}", exc_info=True)
            self._destroy_internal()

    def _get_colors(self):
        """Retorna (bg, fg, border) baseado no level."""
        theme = self.theme
        if self.level == 'success':
            return (
                theme.get('bg_pill', '#2a1f1a'),
                theme.get('accent', '#c5a572'),
                theme.get('accent', '#c5a572'),
            )
        elif self.level == 'warning':
            # Amarelo/laranja pra warning
            return (
                '#3a2a1a',  # marrom escuro
                '#f0b060',  # laranja claro
                '#d49050',  # borda laranja
            )
        else:  # info
            return (
                theme.get('bg_pill', '#2a1f1a'),
                theme.get('text', '#D5CFAA'),
                theme.get('border', '#444'),
            )

    def _fade_in(self):
        """Anima opacidade de 0 → 1 em FADE_STEPS."""
        if self._destroyed or not self.window or not self.window.winfo_exists():
            return

        self._fade_alpha += 1.0 / ToastManager.FADE_STEPS
        if self._fade_alpha >= 1.0:
            self._fade_alpha = 1.0
            try:
                self.window.attributes('-alpha', 0.95)
            except Exception:
                pass
            # Inicia timer pro fade-out
            interval = ToastManager.FADE_IN_MS // ToastManager.FADE_STEPS
            self._fade_after_id = self.window.after(self.duration_ms, self._fade_out)
            return

        try:
            self.window.attributes('-alpha', self._fade_alpha * 0.95)
        except Exception:
            pass

        interval = ToastManager.FADE_IN_MS // ToastManager.FADE_STEPS
        self._fade_after_id = self.window.after(interval, self._fade_in)

    def _fade_out(self):
        """Anima opacidade de 1 → 0, depois destroi."""
        if self._destroyed or not self.window or not self.window.winfo_exists():
            self._destroy_internal()
            return

        self._fade_alpha -= 1.0 / ToastManager.FADE_STEPS
        if self._fade_alpha <= 0.0:
            self._destroy_internal()
            return

        try:
            self.window.attributes('-alpha', self._fade_alpha * 0.95)
        except Exception:
            pass

        interval = ToastManager.FADE_OUT_MS // ToastManager.FADE_STEPS
        self._fade_after_id = self.window.after(interval, self._fade_out)

    def destroy(self):
        """API pública pra forçar destruição."""
        self._destroy_internal()

    def _destroy_internal(self):
        if self._destroyed:
            return
        self._destroyed = True

        if self._fade_after_id and self.window:
            try:
                self.window.after_cancel(self._fade_after_id)
            except Exception:
                pass

        if self.window:
            try:
                if self.window.winfo_exists():
                    self.window.destroy()
            except Exception:
                pass
            self.window = None

        if self.on_destroy:
            try:
                self.on_destroy(self)
            except Exception:
                pass
