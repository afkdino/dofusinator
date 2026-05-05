"""
Mini-Pill v2 - Botão flutuante circular tipo notificação.

Quando o usuário aciona o hotkey de overlay (Ctrl+Shift+O), o overlay completo
colapsa pra esse mini-pill flutuante:
  - Botão circular (~56px) com ícone do app
  - Badge vermelho no canto sup-direito mostrando "+N" linhas novas desde o colapso
  - Click → expande pro overlay (zera badge)
  - Drag → mover pelo desktop
  - Aparece onde o overlay estava antes (preserva contexto)

Background: a captura CONTINUA rodando silenciosamente. Cada nova linha
incrementa o contador do badge. User vê "+5" se 5 linhas chegaram desde
que colapsou.

Bloco 3 / Sub-bloco 3.2 (refinamento v1.0.20)
"""
import logging
import tkinter as tk
from typing import Optional, Callable

from theme import get_theme

log = logging.getLogger(__name__)


class MiniPill:
    """
    Mini overlay flutuante (botão circular) que substitui o overlay quando colapsado.

    Uso:
        pill = MiniPill(master, settings)
        pill.set_on_expand(callback)
        pill.show(x=100, y=100)
        # ... conforme novas linhas chegam:
        pill.increment_badge()
        # ... depois:
        pill.hide()
    """

    SIZE = 64               # diâmetro do botão circular
    BADGE_SIZE = 22         # diâmetro do badge
    BADGE_OFFSET_X = 4      # offset do badge (canto sup-dir)
    BADGE_OFFSET_Y = 4
    # v1.0.22: margem da janela > raio do badge pra evitar clipping
    # Badge tem raio 11, fica colada na borda direita do círculo. Margem
    # de 14px (11 + 3) garante que o badge inteiro fica dentro da Toplevel.
    WINDOW_MARGIN = 14

    def __init__(self, master, settings):
        self.master = master
        self.settings = settings
        self._theme = get_theme(settings.get('main_window_theme', 'dofus_retro'))

        self.window: Optional[tk.Toplevel] = None
        self._canvas: Optional[tk.Canvas] = None
        self._badge_count: int = 0
        self._on_expand: Optional[Callable[[], None]] = None
        self._icon_photo = None  # ref pra evitar GC

        # Estado de drag
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False
        self._drag_threshold = 5

        # Última posição (preserva entre show/hide)
        self._last_x = 100
        self._last_y = 100

    def set_on_expand(self, callback: Callable[[], None]):
        self._on_expand = callback

    def show(self, x: Optional[int] = None, y: Optional[int] = None):
        """Mostra o mini-pill. Se x/y omitidos, usa última posição."""
        if x is None:
            x = self._last_x
        if y is None:
            y = self._last_y

        # Se já existe, só atualiza posição
        if self.window and self.window.winfo_exists():
            self._move(x, y)
            return

        self._badge_count = 0  # zera contador ao abrir
        self._build(x, y)

    def increment_badge(self, delta: int = 1):
        """Incrementa contador de linhas novas e redesenha badge."""
        if not self.is_visible():
            return
        self._badge_count += delta
        self._redraw()

    def get_badge_count(self) -> int:
        return self._badge_count

    def hide(self):
        """Esconde, salvando última posição."""
        if self.window:
            try:
                if self.window.winfo_exists():
                    geom = self.window.geometry()
                    parts = geom.split('+')
                    if len(parts) >= 3:
                        self._last_x = int(parts[1])
                        self._last_y = int(parts[2])
                    self.window.destroy()
            except Exception as e:
                log.debug(f"Erro ao esconder mini-pill: {e}")
            self.window = None
        self._canvas = None
        self._icon_photo = None

    def is_visible(self) -> bool:
        return self.window is not None and self.window.winfo_exists()

    def get_position(self) -> tuple:
        if self.window and self.window.winfo_exists():
            try:
                return (self.window.winfo_rootx(), self.window.winfo_rooty())
            except Exception:
                pass
        return (self._last_x, self._last_y)

    # ========================================================================
    # Build / Redraw
    # ========================================================================

    def _build(self, x: int, y: int):
        try:
            self.window = tk.Toplevel(self.master)
            self.window.overrideredirect(True)
            self.window.attributes('-topmost', True)
            # v1.0.22: margem maior pra acomodar badge (bug fix de clipping)
            win_w = self.SIZE + 2 * self.WINDOW_MARGIN
            win_h = self.SIZE + 2 * self.WINDOW_MARGIN
            self.window.geometry(f"{win_w}x{win_h}+{x}+{y}")

            # Trick pra fundo transparente: usa cor sentinel + transparentcolor
            # A janela inteira fica transparente, só o círculo do botão aparece.
            transparent_key = '#FF00FF'  # magenta, improvável de aparecer no design
            self.window.configure(bg=transparent_key)
            try:
                self.window.attributes('-transparentcolor', transparent_key)
            except Exception:
                # Se não tiver -transparentcolor (não-Windows), usa fundo do tema
                self.window.configure(bg=self._theme['bg'])

            # Canvas que desenha o círculo + badge + ícone
            self._canvas = tk.Canvas(
                self.window,
                width=win_w, height=win_h,
                bg=transparent_key,
                highlightthickness=0,
                bd=0,
                cursor='hand2',
            )
            self._canvas.pack(fill='both', expand=True)

            # Carrega ícone do app
            self._load_icon()

            # Desenha o conteúdo
            self._redraw()

            # Binds (drag + click)
            self._canvas.bind('<ButtonPress-1>', self._on_press)
            self._canvas.bind('<B1-Motion>', self._on_drag)
            self._canvas.bind('<ButtonRelease-1>', self._on_release)

            log.info(f"Mini-pill v2 criado em ({x}, {y})")
        except Exception as e:
            log.error(f"Erro ao criar mini-pill v2: {e}", exc_info=True)
            self.hide()

    def _load_icon(self):
        """Carrega ícone do app pra desenhar dentro do círculo."""
        try:
            from PIL import Image, ImageTk
            from assets_helper import get_icon_path
            ico_path = get_icon_path()
            img = Image.open(ico_path)
            biggest = img
            try:
                for i in range(20):
                    img.seek(i)
                    if img.size[0] > biggest.size[0]:
                        biggest = img.copy()
            except EOFError:
                pass
            if biggest.mode != 'RGBA':
                biggest = biggest.convert('RGBA')
            # Tamanho do ícone = ~70% do diâmetro do círculo
            icon_size = int(self.SIZE * 0.7)
            biggest = biggest.resize((icon_size, icon_size), Image.LANCZOS)
            self._icon_photo = ImageTk.PhotoImage(biggest)
        except Exception as e:
            log.debug(f"Não foi possível carregar ícone do pill: {e}")
            self._icon_photo = None

    def _redraw(self):
        """Re-desenha tudo no canvas (círculo + ícone + badge)."""
        if not self._canvas or not self.window or not self.window.winfo_exists():
            return

        try:
            theme = self._theme
            self._canvas.delete('all')

            # v1.0.22: geometria com margem suficiente pro badge não clippar
            win_w = self.SIZE + 2 * self.WINDOW_MARGIN
            win_h = self.SIZE + 2 * self.WINDOW_MARGIN
            cx = win_w // 2
            cy = win_h // 2
            r = self.SIZE // 2

            # Círculo principal (botão)
            # Borda (anel externo) em accent
            self._canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=theme['bg_pill'],
                outline=theme['accent'],
                width=2,
            )

            # Ícone do app no centro
            if self._icon_photo:
                self._canvas.create_image(cx, cy, image=self._icon_photo)
            else:
                # Fallback: letra D dourada
                self._canvas.create_text(
                    cx, cy, text="D",
                    fill=theme['accent'],
                    font=('Segoe UI', 24, 'bold'),
                )

            # Badge (canto sup-direito do CÍRCULO) só se tem contador.
            # Posiciona ~ no quadrante sup-direito, levemente sobreposto à
            # borda do círculo (estilo "notification badge").
            if self._badge_count > 0:
                br = self.BADGE_SIZE // 2
                # Posição: 85% do raio na diagonal, dá efeito "colado na borda"
                badge_offset_from_center = int(r * 0.85)
                bx = cx + badge_offset_from_center
                by = cy - badge_offset_from_center

                # Sombra suave (offset 1px)
                self._canvas.create_oval(
                    bx - br + 1, by - br + 1, bx + br + 1, by + br + 1,
                    fill='#000000', outline='',
                )
                # Círculo do badge (vermelho)
                self._canvas.create_oval(
                    bx - br, by - br, bx + br, by + br,
                    fill='#e63946',
                    outline='#ffffff',
                    width=2,
                )
                # Texto do contador
                display_text = str(self._badge_count) if self._badge_count < 100 else "99+"
                font_size = 9 if len(display_text) >= 3 else 11
                self._canvas.create_text(
                    bx, by, text=display_text,
                    fill='#ffffff',
                    font=('Segoe UI', font_size, 'bold'),
                )
        except Exception as e:
            log.debug(f"_redraw falhou: {e}")

    # ========================================================================
    # Drag & click
    # ========================================================================

    def _on_press(self, event):
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._is_dragging = False

    def _on_drag(self, event):
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y

        if not self._is_dragging and (abs(dx) > self._drag_threshold or abs(dy) > self._drag_threshold):
            self._is_dragging = True

        if self._is_dragging and self.window:
            try:
                cur_x = self.window.winfo_rootx()
                cur_y = self.window.winfo_rooty()
                new_x = cur_x + dx
                new_y = cur_y + dy
                self.window.geometry(f"+{new_x}+{new_y}")
                self._drag_start_x = event.x_root
                self._drag_start_y = event.y_root
            except Exception as e:
                log.debug(f"Drag falhou: {e}")

    def _on_release(self, event):
        if not self._is_dragging:
            log.info(f"Mini-pill clicado, expandindo overlay (badge={self._badge_count})")
            if self._on_expand:
                try:
                    self._on_expand()
                except Exception as e:
                    log.error(f"on_expand callback falhou: {e}")
        self._is_dragging = False

    def _move(self, x: int, y: int):
        if self.window and self.window.winfo_exists():
            try:
                self.window.geometry(f"+{x}+{y}")
            except Exception as e:
                log.debug(f"_move falhou: {e}")
