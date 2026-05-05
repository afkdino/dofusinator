"""
Selection Preview - Glimpse visual da área selecionada após captura de perímetro.

Quando o user finaliza a captura do perímetro do chat (via F2 ou segurar mouse 2s),
mostramos um retângulo verde semi-transparente sobreposto à área pra confirmar
visualmente como ficou a seleção.

Aparece por ~1.5s e some sozinho.

Implementação:
- Toplevel borderless (overrideredirect=True)
- Sempre no topo (-topmost True)
- Click-through (transparente pra mouse, ignored input)
- Background semi-transparente verde + borda mais opaca
- attributes('-alpha', 0.3) pra transparência geral

Bloco 3 / Sub-bloco 3.2 da v1.1
"""
import logging
import tkinter as tk
from typing import Optional

log = logging.getLogger(__name__)


class SelectionPreview:
    """
    Janela borderless verde semi-transparente que aparece em cima da área
    selecionada e some após `duration_ms` milissegundos.

    Uso:
        preview = SelectionPreview(root)
        preview.show(x1, y1, x2, y2, duration_ms=1500)
    """

    # Cor verde tipo highlight de captura (similar a print screen tools)
    PREVIEW_COLOR = "#00ff66"
    # Alpha geral (0.0 = invisível, 1.0 = opaco)
    ALPHA = 0.35

    def __init__(self, master):
        self.master = master
        self._window: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None

    def show(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 1500):
        """Mostra o retângulo de preview na área (x1,y1)→(x2,y2) por duration_ms."""
        # Garante coordenadas normalizadas
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        width = x2 - x1
        height = y2 - y1

        if width < 5 or height < 5:
            log.warning(f"Preview: área muito pequena ({width}x{height}), pulando")
            return

        # Limpa qualquer preview anterior
        self.hide()

        try:
            self._window = tk.Toplevel(self.master)
            # Remove decoração da janela (sem barra de título, sem bordas)
            self._window.overrideredirect(True)
            # Sempre no topo
            self._window.attributes('-topmost', True)
            # Posiciona e dimensiona EXATAMENTE na área selecionada
            self._window.geometry(f"{width}x{height}+{x1}+{y1}")
            # Cor de fundo verde
            self._window.configure(bg=self.PREVIEW_COLOR)
            # Transparência geral
            self._window.attributes('-alpha', self.ALPHA)

            # Borda interna mais densa pra demarcar bem o perímetro.
            # Usamos um Canvas com retângulo de borda grossa.
            canvas = tk.Canvas(
                self._window,
                width=width, height=height,
                bg=self.PREVIEW_COLOR,
                highlightthickness=0, bd=0,
            )
            canvas.pack(fill='both', expand=True)
            # Retângulo de borda (mais opaco visualmente porque desenhado em cima)
            canvas.create_rectangle(
                2, 2, width - 2, height - 2,
                outline=self.PREVIEW_COLOR,
                width=4,  # borda grossa
            )

            log.info(f"Preview de seleção: ({x1},{y1}) → ({x2},{y2}) [{width}x{height}] por {duration_ms}ms")

            # Agenda fechamento automático
            self._after_id = self._window.after(duration_ms, self.hide)

        except Exception as e:
            log.error(f"Erro ao mostrar preview de seleção: {e}", exc_info=True)
            self.hide()

    def hide(self):
        """Remove o preview imediatamente (chamado pelo timer ou manualmente)."""
        # Cancela timer pendente
        if self._after_id and self._window:
            try:
                self._window.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        if self._window:
            try:
                if self._window.winfo_exists():
                    self._window.destroy()
            except Exception as e:
                log.debug(f"Erro ao destruir preview: {e}")
            self._window = None


# Função conveniente pra uso direto sem instanciar classe
def show_selection_preview(master, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 1500):
    """Helper: cria e mostra um preview de seleção."""
    preview = SelectionPreview(master)
    preview.show(x1, y1, x2, y2, duration_ms)
    return preview
