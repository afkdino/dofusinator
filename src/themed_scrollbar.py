"""
ThemedScrollbar - Scrollbar custom estilizada com a paleta do tema.

Tk não permite estilizar scrollbar nativa de forma cross-platform decente.
Solução: scrollbar customizada baseada em tk.Canvas com:
  - Track invisível (transparente, mistura com bg)
  - Thumb (a parte que se arrasta) em cor do tema (bege/dourado dim)
  - Hover effect (thumb fica mais brilhante)
  - Largura fina (~8px) pra não roubar espaço do conteúdo
  - Drag funcional (clica e arrasta)
  - Click no track posiciona thumb naquele lugar

Uso (auto-conecta com Text/Listbox/Canvas):
    sb = ThemedScrollbar(parent, target_widget=text_widget,
                         bg='#1a1614', thumb='#8b7355', thumb_hover='#c5a572')
    sb.pack(side='right', fill='y')

v1.0.24 / Polimento visual
"""
import logging
import tkinter as tk

log = logging.getLogger(__name__)


class ThemedScrollbar(tk.Canvas):
    """
    Scrollbar custom baseada em Canvas. Conecta-se a um widget rolável
    (Text, Listbox, Canvas) via target_widget e funciona como uma scrollbar
    convencional.
    """

    DEFAULT_WIDTH = 8

    def __init__(self, parent, target_widget,
                 bg='#1a1614',
                 thumb='#8b7355',
                 thumb_hover='#c5a572',
                 width=None):
        width = width or self.DEFAULT_WIDTH
        super().__init__(
            parent,
            width=width,
            bg=bg,
            highlightthickness=0,
            bd=0,
        )

        self._target = target_widget
        self._bg = bg
        self._thumb_color = thumb
        self._thumb_hover = thumb_hover
        self._width = width

        self._thumb_id = None
        self._thumb_y0 = 0
        self._thumb_y1 = 0
        self._dragging = False
        self._drag_offset_y = 0

        # Conecta o widget alvo a essa scrollbar
        try:
            self._target.configure(yscrollcommand=self._on_target_scroll)
        except Exception as e:
            log.error(f"ThemedScrollbar: erro ao conectar target: {e}")

        # Binds
        self.bind('<Configure>', self._on_configure)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    # ========================================================================
    # API pública (atualização de cores quando tema muda)
    # ========================================================================

    def update_colors(self, bg=None, thumb=None, thumb_hover=None):
        """Atualiza cores quando user troca de tema."""
        if bg is not None:
            self._bg = bg
            try:
                self.configure(bg=bg)
            except Exception:
                pass
        if thumb is not None:
            self._thumb_color = thumb
        if thumb_hover is not None:
            self._thumb_hover = thumb_hover
        self._redraw_thumb()

    # ========================================================================
    # Conexão com o widget alvo
    # ========================================================================

    def _on_target_scroll(self, first: str, last: str):
        """
        Chamado pelo widget alvo quando o conteúdo rola.
        first/last são frações 0..1 indicando onde a janela visível está.
        """
        try:
            f = float(first)
            l = float(last)
        except (ValueError, TypeError):
            return

        # Se conteúdo cabe inteiro (l - f >= 1.0), esconde a scrollbar
        # IMPORTANTE: return aqui pra não cair no cálculo de tamanho mínimo
        # abaixo, que desenharia um thumb fantasma.
        if l - f >= 0.999:
            self._hide_thumb()
            self._thumb_y0 = 0
            self._thumb_y1 = 0
            return

        h = self.winfo_height()
        if h <= 1:
            return

        self._thumb_y0 = max(2, int(f * h))
        self._thumb_y1 = min(h - 2, int(l * h))

        # Mínimo de 20px pro thumb pra ser clicável
        if self._thumb_y1 - self._thumb_y0 < 20:
            self._thumb_y1 = self._thumb_y0 + 20
            if self._thumb_y1 > h - 2:
                self._thumb_y1 = h - 2
                self._thumb_y0 = self._thumb_y1 - 20

        self._redraw_thumb()

    def _redraw_thumb(self):
        try:
            self.delete('thumb')
            if self._thumb_y1 > self._thumb_y0:
                # Thumb com cantos arredondados (oval imitando rounded rect)
                w = self._width
                color = self._thumb_hover if self._dragging else self._thumb_color
                # Linha vertical "fat" mais arredondada nas pontas
                self.create_rectangle(
                    2, self._thumb_y0,
                    w - 2, self._thumb_y1,
                    fill=color, outline='',
                    tags='thumb',
                )
        except Exception as e:
            log.debug(f"redraw_thumb: {e}")

    def _hide_thumb(self):
        try:
            self.delete('thumb')
        except Exception:
            pass

    # ========================================================================
    # Interação (drag / click)
    # ========================================================================

    def _on_configure(self, event):
        # Quando a scrollbar é redimensionada, força refresh da posição
        # baseado no estado atual do widget alvo
        try:
            first, last = self._target.yview()
            self._on_target_scroll(str(first), str(last))
        except Exception:
            pass

    def _on_press(self, event):
        # Click no thumb → começa drag
        if self._thumb_y0 <= event.y <= self._thumb_y1:
            self._dragging = True
            self._drag_offset_y = event.y - self._thumb_y0
            self._redraw_thumb()  # cor hover
        else:
            # Click fora do thumb → centraliza thumb naquele lugar
            self._jump_to(event.y)

    def _on_drag(self, event):
        if not self._dragging:
            return
        h = self.winfo_height()
        if h <= 1:
            return
        new_y = event.y - self._drag_offset_y
        thumb_h = self._thumb_y1 - self._thumb_y0
        new_y = max(0, min(new_y, h - thumb_h))
        # Calcula a fração que isso corresponde
        frac = new_y / max(1, h)
        try:
            self._target.yview_moveto(frac)
        except Exception:
            pass

    def _on_release(self, event):
        self._dragging = False
        self._redraw_thumb()  # volta cor normal

    def _jump_to(self, y: int):
        h = self.winfo_height()
        if h <= 1:
            return
        thumb_h = self._thumb_y1 - self._thumb_y0
        new_y = y - thumb_h // 2
        new_y = max(0, min(new_y, h - thumb_h))
        frac = new_y / max(1, h)
        try:
            self._target.yview_moveto(frac)
        except Exception:
            pass

    def _on_enter(self, event):
        if not self._dragging:
            self._dragging = True  # truque pra ativar cor hover
            self._redraw_thumb()
            self._dragging = False

    def _on_leave(self, event):
        if not self._dragging:
            self._redraw_thumb()
