"""
Custom title bar v3.2 - abordagem A.
- overrideredirect(True) pra remover barra nativa SEM deixar artefatos
- WS_EX_APPWINDOW pra manter janela na taskbar e Alt+Tab
- 8 resize grips invisíveis nas bordas pra permitir redimensionar manualmente
"""
import logging
import sys
import tkinter as tk
from typing import Callable, Optional

from spacing import SPACING_SM, SPACING_MD, SPACING_LG

log = logging.getLogger(__name__)


# ============================================================================
# Win32 - força aparição na taskbar mesmo com overrideredirect
# ============================================================================

def _win32_minimize(window):
    """
    Minimiza janela com overrideredirect via Win32 nativo.
    O iconify() do Tk NÃO funciona bem em janelas overrideredirect no Windows
    (a janela some sem ir pra taskbar). ShowWindow(SW_MINIMIZE) resolve.
    """
    if sys.platform != 'win32':
        try:
            window.iconify()
        except Exception:
            pass
        return
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        SW_MINIMIZE = 6
        ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
    except Exception as e:
        log.error(f"Erro ao minimizar via Win32: {e}")
        try:
            window.iconify()
        except Exception:
            pass


def _force_taskbar_appearance(window):
    """
    Hack pra fazer janelas overrideredirect aparecerem na taskbar e Alt+Tab.
    Define WS_EX_APPWINDOW em vez de WS_EX_TOOLWINDOW.
    """
    if sys.platform != 'win32':
        return False

    try:
        import ctypes

        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            log.warning("Não consegui obter HWND.")
            return False

        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080

        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style = (ex_style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

        # Hide+show pra forçar refresh da taskbar
        window.withdraw()
        window.after(10, window.deiconify)
        return True
    except Exception as e:
        log.error(f"Erro no force_taskbar: {e}")
        return False


# ============================================================================
# Resize Grips - 8 frames invisíveis nas bordas pra permitir resize
# ============================================================================

class ResizeGrips:
    """
    Adiciona zonas invisíveis nas bordas da janela pra permitir resize.
    8 zonas: 4 cantos + 4 bordas.

    A cor de fundo dos grips fica igual à do bg_color, então ficam invisíveis
    contra o fundo.
    """

    EDGE_SIZE = 5
    CORNER_SIZE = 10

    def __init__(self, window, bg_color="#1a1a1a", min_width=300, min_height=200):
        self.window = window
        self.bg_color = bg_color
        self.min_width = min_width
        self.min_height = min_height

        self._action: Optional[str] = None
        self._start_mx = 0
        self._start_my = 0
        self._start_w = 0
        self._start_h = 0
        self._start_wx = 0
        self._start_wy = 0

        self._create_grips()

    def _create_grips(self):
        cfg = {
            'bg': self.bg_color,
            'highlightthickness': 0,
            'borderwidth': 0,
        }

        # Bordas (4)
        self.grip_n = tk.Frame(self.window, cursor='size_ns', **cfg)
        self.grip_s = tk.Frame(self.window, cursor='size_ns', **cfg)
        self.grip_w = tk.Frame(self.window, cursor='size_we', **cfg)
        self.grip_e = tk.Frame(self.window, cursor='size_we', **cfg)

        # Cantos (4)
        self.grip_nw = tk.Frame(self.window, cursor='size_nw_se', **cfg)
        self.grip_ne = tk.Frame(self.window, cursor='size_ne_sw', **cfg)
        self.grip_sw = tk.Frame(self.window, cursor='size_ne_sw', **cfg)
        self.grip_se = tk.Frame(self.window, cursor='size_nw_se', **cfg)

        # Place — bordas ficam entre os cantos
        E = self.EDGE_SIZE
        C = self.CORNER_SIZE

        self.grip_n.place(x=C, y=0, relwidth=1, width=-2*C, height=E)
        self.grip_s.place(x=C, rely=1, y=-E, relwidth=1, width=-2*C, height=E)
        self.grip_w.place(x=0, y=C, width=E, relheight=1, height=-2*C)
        self.grip_e.place(relx=1, x=-E, y=C, width=E, relheight=1, height=-2*C)

        self.grip_nw.place(x=0, y=0, width=C, height=C)
        self.grip_ne.place(relx=1, x=-C, y=0, width=C, height=C)
        self.grip_sw.place(x=0, rely=1, y=-C, width=C, height=C)
        self.grip_se.place(relx=1, x=-C, rely=1, y=-C, width=C, height=C)

        # Bind cada grip à sua direção
        directions = {
            self.grip_n: 'n', self.grip_s: 's',
            self.grip_w: 'w', self.grip_e: 'e',
            self.grip_nw: 'nw', self.grip_ne: 'ne',
            self.grip_sw: 'sw', self.grip_se: 'se',
        }
        for grip, direction in directions.items():
            grip.bind('<ButtonPress-1>', lambda e, d=direction: self._on_press(e, d))
            grip.bind('<B1-Motion>', self._on_drag)
            grip.bind('<ButtonRelease-1>', self._on_release)

    def lift_all(self):
        """Garante que grips fiquem acima do conteúdo."""
        for grip in [
            self.grip_n, self.grip_s, self.grip_e, self.grip_w,
            self.grip_nw, self.grip_ne, self.grip_sw, self.grip_se,
        ]:
            try:
                grip.lift()
            except Exception:
                pass

    def update_bg(self, bg_color: str):
        """Atualiza cor de fundo dos grips (pra trocar de tema)."""
        self.bg_color = bg_color
        for grip in [
            self.grip_n, self.grip_s, self.grip_e, self.grip_w,
            self.grip_nw, self.grip_ne, self.grip_sw, self.grip_se,
        ]:
            try:
                grip.configure(bg=bg_color)
            except Exception:
                pass

    def _on_press(self, event, direction: str):
        self._action = direction
        self._start_mx = event.x_root
        self._start_my = event.y_root
        self._start_w = self.window.winfo_width()
        self._start_h = self.window.winfo_height()
        self._start_wx = self.window.winfo_x()
        self._start_wy = self.window.winfo_y()

    def _on_drag(self, event):
        if not self._action:
            return

        dx = event.x_root - self._start_mx
        dy = event.y_root - self._start_my

        new_x = self._start_wx
        new_y = self._start_wy
        new_w = self._start_w
        new_h = self._start_h

        if 'e' in self._action:
            new_w = max(self.min_width, self._start_w + dx)
        if 'w' in self._action:
            shrink = dx
            new_w = max(self.min_width, self._start_w - shrink)
            if new_w > self.min_width:
                new_x = self._start_wx + shrink
            else:
                # Não deixa passar do limite mínimo
                new_x = self._start_wx + (self._start_w - self.min_width)
        if 's' in self._action:
            new_h = max(self.min_height, self._start_h + dy)
        if 'n' in self._action:
            shrink = dy
            new_h = max(self.min_height, self._start_h - shrink)
            if new_h > self.min_height:
                new_y = self._start_wy + shrink
            else:
                new_y = self._start_wy + (self._start_h - self.min_height)

        try:
            self.window.geometry(f"{int(new_w)}x{int(new_h)}+{int(new_x)}+{int(new_y)}")
        except Exception:
            pass

    def _on_release(self, event):
        self._action = None


# ============================================================================
# Custom Title Bar widget
# ============================================================================

class CustomTitleBar:
    """Barra de título customizada com botões min/close + drag."""

    HEIGHT = 32

    def __init__(
        self,
        parent_window,
        parent_frame,
        title: str,
        on_close: Optional[Callable] = None,
        on_minimize: Optional[Callable] = None,
        show_minimize: bool = True,
        # NOVO v1.0.21: customizar ícone do botão minimize (overlay usa "⊙" pra colapsar)
        minimize_icon: str = "─",
        bg_titlebar: str = "#0f0f0f",
        bg_button_hover: str = "#3a3a3a",
        fg: str = "#e0e0e0",
        accent: str = "#e8d4a2",
        close_hover_bg: str = "#c44",
    ):
        self.parent_window = parent_window
        self.title_text = title
        self.on_close_cb = on_close
        self.on_minimize_cb = on_minimize
        self.minimize_icon = minimize_icon

        self.bg_titlebar = bg_titlebar
        self.bg_button_hover = bg_button_hover
        self.fg = fg
        self.accent = accent
        self.close_hover_bg = close_hover_bg

        self._drag_offset_x = 0
        self._drag_offset_y = 0

        self.frame = tk.Frame(parent_frame, bg=self.bg_titlebar, height=self.HEIGHT)
        self.frame.pack(fill='x', side='top')
        self.frame.pack_propagate(False)

        # Ícone do app na esquerda da titlebar (antes do título)
        self._icon_photo = None  # mantém referência pra evitar GC
        try:
            from assets_helper import get_icon_path
            from PIL import Image, ImageTk
            icon_path = get_icon_path()
            if icon_path:
                img = Image.open(str(icon_path))
                # Redimensiona pra 18x18 (cabe na titlebar de 30px com padding)
                img = img.resize((18, 18), Image.LANCZOS)
                self._icon_photo = ImageTk.PhotoImage(img)
                icon_label = tk.Label(
                    self.frame, image=self._icon_photo,
                    bg=self.bg_titlebar, padx=SPACING_MD,  # v1.0.22: era 10
                )
                icon_label.pack(side='left', fill='y')
                # Drag também funciona clicando no ícone
                icon_label.bind('<ButtonPress-1>', self._on_drag_start)
                icon_label.bind('<B1-Motion>', self._on_drag)
        except Exception as e:
            log.debug(f"Não consegui carregar ícone na titlebar: {e}")

        self.title_label = tk.Label(
            self.frame, text=title, bg=self.bg_titlebar, fg=accent,
            font=('Segoe UI', 10, 'bold'),
            # v1.0.22: padding consistente: se tem ícone usa 0 (já fica colado),
            # se não tem usa SPACING_LG pra título não colar na borda
            padx=0 if self._icon_photo else SPACING_LG,
        )
        self.title_label.pack(side='left', fill='y')

        self.close_btn = self._make_button(
            "✕", self._on_close,
            hover_bg=close_hover_bg, hover_fg='white',
        )
        self.close_btn.pack(side='right', fill='y')

        if show_minimize:
            self.min_btn = self._make_button(self.minimize_icon, self._on_minimize)
            self.min_btn.pack(side='right', fill='y')

        # Drag (clica na barra ou no título)
        for w in [self.frame, self.title_label]:
            w.bind('<ButtonPress-1>', self._on_drag_start)
            w.bind('<B1-Motion>', self._on_drag)
            # Duplo clique pra maximizar/restaurar (futuro)

    def _make_button(self, text: str, command, hover_bg=None, hover_fg=None):
        bg = self.bg_titlebar
        fg = self.fg
        hover_bg = hover_bg or self.bg_button_hover
        hover_fg = hover_fg or self.fg

        btn = tk.Label(
            self.frame, text=text,
            bg=bg, fg=fg,
            font=('Segoe UI', 12),
            padx=SPACING_LG, cursor='hand2',  # v1.0.22: padding consistente
        )
        btn.bind('<Button-1>', lambda e: command())
        btn.bind('<Enter>', lambda e: btn.config(bg=hover_bg, fg=hover_fg))
        btn.bind('<Leave>', lambda e: btn.config(bg=bg, fg=fg))
        return btn

    def _on_close(self):
        if self.on_close_cb:
            try:
                self.on_close_cb()
            except Exception as e:
                log.error(f"Erro no on_close: {e}")
        else:
            self.parent_window.destroy()

    def _on_minimize(self):
        if self.on_minimize_cb:
            try:
                self.on_minimize_cb()
            except Exception as e:
                log.error(f"Erro no on_minimize: {e}")
        else:
            _win32_minimize(self.parent_window)

    def _on_drag_start(self, event):
        self._drag_offset_x = event.x_root - self.parent_window.winfo_x()
        self._drag_offset_y = event.y_root - self.parent_window.winfo_y()

    def _on_drag(self, event):
        try:
            x = event.x_root - self._drag_offset_x
            y = event.y_root - self._drag_offset_y
            self.parent_window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def set_title(self, title: str):
        self.title_text = title
        try:
            self.title_label.config(text=title)
        except Exception:
            pass

    def update_theme(self, bg_titlebar, fg, accent, bg_button_hover, close_hover_bg):
        """Atualiza cores da barra (pra trocar de tema)."""
        self.bg_titlebar = bg_titlebar
        self.fg = fg
        self.accent = accent
        self.bg_button_hover = bg_button_hover
        self.close_hover_bg = close_hover_bg
        try:
            self.frame.configure(bg=bg_titlebar)
            self.title_label.configure(bg=bg_titlebar, fg=accent)
            self.close_btn.configure(bg=bg_titlebar, fg=fg)
            if hasattr(self, 'min_btn'):
                self.min_btn.configure(bg=bg_titlebar, fg=fg)
        except Exception:
            pass


# ============================================================================
# Função principal - aplica titlebar custom + grips em uma janela
# ============================================================================

def apply_custom_titlebar(
    window,
    title: str,
    on_close: Optional[Callable] = None,
    on_minimize: Optional[Callable] = None,
    show_minimize: bool = True,
    minimize_icon: str = "─",
    keep_taskbar: bool = True,
    resizable: bool = True,
    bg_color: str = "#1a1a1a",
    bg_titlebar: str = "#0f0f0f",
    fg: str = "#e0e0e0",
    accent: str = "#e8d4a2",
    bg_button_hover: str = "#3a3a3a",
    close_hover_bg: str = "#c44",
    min_width: int = 300,
    min_height: int = 200,
) -> dict:
    """
    Esconde barra nativa e adiciona barra customizada com botões.
    Retorna dict {titlebar, grips} pra permitir update de tema depois.
    """
    # 1. Remove decoração nativa
    window.overrideredirect(True)

    # 2. Mantém na taskbar (Win32 hack)
    if keep_taskbar:
        _force_taskbar_appearance(window)

    # 3. Adiciona resize grips se redimensionável
    grips = None
    if resizable:
        grips = ResizeGrips(
            window, bg_color=bg_color,
            min_width=min_width, min_height=min_height,
        )

    # 4. Custom title bar no topo
    bar = CustomTitleBar(
        window, window, title,
        on_close=on_close, on_minimize=on_minimize,
        show_minimize=show_minimize,
        bg_titlebar=bg_titlebar,
        bg_button_hover=bg_button_hover,
        fg=fg, accent=accent,
        close_hover_bg=close_hover_bg,
    )

    # 5. Levanta grips por cima do conteúdo (mas não da titlebar)
    if grips:
        # Schedule lift depois do build do conteúdo
        window.after(100, grips.lift_all)

    return {'titlebar': bar, 'grips': grips}
