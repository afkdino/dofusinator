"""
F2 Tooltip - Balão de instrução flutuante que segue o cursor.

Aparece próximo do mouse durante captura de perímetro/chat-bar:
  - Texto: "Posicione o mouse no canto superior-esquerdo do chat e aperte [F2]"
  - Tecla F2 estilizada (caixa com borda)
  - Antes de F2 ser apertado: tecla DIM
  - Momento do aperto: tecla acende dourado + texto muda pra "(capturando perímetro)" por ~300ms
  - Some quando o componente é destruído

Tecnicamente:
  - Toplevel borderless (overrideredirect)
  - Sempre no topo (-topmost)
  - Posicionado ~32px acima do cursor (offset configurable)
  - Update de posição via root.after(16, ...) (~60fps)

Bloco 3 / Sub-bloco 3.2 (refinamento v1.0.20)
"""
import logging
import tkinter as tk
from typing import Optional, Callable

from theme import get_theme
from spacing import SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG

log = logging.getLogger(__name__)


class F2Tooltip:
    """
    Balão flutuante posicionado próximo ao cursor com instrução de F2.

    Uso:
        tooltip = F2Tooltip(root, settings)
        tooltip.show("Aponte para o canto superior-esquerdo")
        # ... user aperta F2 ...
        tooltip.flash_capture()  # acende a tecla por 300ms
        tooltip.hide()
    """

    # Offset do mouse (posicionamento acima do cursor)
    OFFSET_X = 16
    OFFSET_Y = -56

    # Tamanho do balão
    WIDTH = 380
    HEIGHT = 56

    # Atualização de posição (~60fps)
    UPDATE_INTERVAL_MS = 16

    def __init__(self, master, settings):
        self.master = master
        self.settings = settings
        self._theme = get_theme(settings.get('main_window_theme', 'dofus_retro'))

        self.window: Optional[tk.Toplevel] = None
        self._text_label: Optional[tk.Label] = None
        self._key_label: Optional[tk.Label] = None
        self._update_after_id: Optional[str] = None
        self._instruction_text: str = ""
        self._is_flashing: bool = False

    def show(self, instruction_text: str):
        """
        Mostra o tooltip com a instrução dada.
        instruction_text vai aparecer ANTES da tecla [F2].
        """
        self._instruction_text = instruction_text

        if self.window and self.window.winfo_exists():
            # Já existe, só atualiza texto
            if self._text_label:
                self._text_label.configure(text=instruction_text)
            return

        self._build()
        self._start_following_mouse()

    def _build(self):
        theme = self._theme

        try:
            self.window = tk.Toplevel(self.master)
            self.window.overrideredirect(True)
            self.window.attributes('-topmost', True)
            # Click-through não é trivial em tk; o user vai estar movendo o
            # mouse, não clicando no tooltip, então não precisa.

            # Container principal
            container = tk.Frame(
                self.window,
                bg=theme['bg_pill'],
                highlightbackground=theme['accent'],
                highlightthickness=1,
                bd=0,
            )
            container.pack(fill='both', expand=True)

            # Texto da instrução
            self._text_label = tk.Label(
                container,
                text=self._instruction_text,
                bg=theme['bg_pill'],
                fg=theme['text'],
                font=('Segoe UI', 10),
                anchor='w',
                justify='left',
                wraplength=self.WIDTH - 70,
            )
            self._text_label.pack(side='left', fill='both', expand=True,
                                  padx=(SPACING_LG, SPACING_SM), pady=SPACING_MD)

            # "Tecla" F2 estilizada (caixa com borda, igual representação visual de tecla)
            self._key_label = tk.Label(
                container,
                text="F2",
                bg=theme['bg_input'],
                fg=theme['text_dim'],   # dim por padrão
                font=('Segoe UI', 11, 'bold'),
                relief='solid',
                bd=1,
                padx=SPACING_MD, pady=SPACING_XS,
            )
            # Highlight border (cor da borda) - usa highlight em vez de bd
            self._key_label.configure(
                highlightbackground=theme['border'],
                highlightthickness=1,
            )
            self._key_label.pack(side='right', padx=(SPACING_SM, SPACING_LG), pady=SPACING_MD)

            self.window.geometry(f"{self.WIDTH}x{self.HEIGHT}")
            log.debug("F2 tooltip criado")
        except Exception as e:
            log.error(f"Erro criando F2 tooltip: {e}", exc_info=True)
            self.hide()

    def _start_following_mouse(self):
        """Loop que atualiza posição do tooltip pra seguir o cursor."""
        if not self.window or not self.window.winfo_exists():
            return

        try:
            import pyautogui
            mx, my = pyautogui.position()
            # Posiciona acima do cursor com offset
            x = mx + self.OFFSET_X
            y = my + self.OFFSET_Y

            # Clamp pra não sair da tela
            screen_w = self.window.winfo_screenwidth()
            screen_h = self.window.winfo_screenheight()
            x = max(0, min(x, screen_w - self.WIDTH))
            y = max(0, min(y, screen_h - self.HEIGHT))

            self.window.geometry(f"+{x}+{y}")
        except Exception as e:
            log.debug(f"F2 tooltip update pos falhou: {e}")

        # Re-agenda
        if self.window and self.window.winfo_exists():
            self._update_after_id = self.window.after(
                self.UPDATE_INTERVAL_MS,
                self._start_following_mouse
            )

    def flash_capture(self, on_done: Optional[Callable[[], None]] = None):
        """
        Anima a tecla F2 com feedback prolongado (700ms verde + reset).

        Sequência visual:
          1. Tecla acende DOURADA + texto vira "✓ Capturado!" em verde/accent
          2. Mantém por 700ms (tempo suficiente pra user perceber claramente)
          3. Volta ao normal (caller geralmente vai destruir o tooltip ou trocar texto)

        Args:
            on_done: callback chamado APÓS o flash completar (700ms).
                     Útil pra trocar pro próximo passo só depois do feedback.
        """
        if not self.window or not self.window.winfo_exists():
            if on_done:
                on_done()
            return
        if self._is_flashing:
            if on_done:
                on_done()
            return

        self._is_flashing = True
        theme = self._theme

        try:
            # Acende a tecla em dourado (estado "capturado")
            if self._key_label:
                self._key_label.configure(
                    fg=theme['text_on_accent'],
                    bg=theme['accent'],
                )
            # Muda texto da instrução pra confirmação clara
            if self._text_label:
                from i18n import t
                self._text_label.configure(
                    text=t("f2_tooltip.captured"),  # "✓ Capturado!" em vez de "capturando..."
                    fg=theme['accent'],
                    font=('Segoe UI', 11, 'bold'),  # bold pra destacar mais
                )

            # Schedule de retorno ao normal após 700ms (era 300ms)
            def reset():
                self._is_flashing = False
                if self._key_label and self.window and self.window.winfo_exists():
                    try:
                        self._key_label.configure(
                            fg=theme['text_dim'],
                            bg=theme['bg_input'],
                        )
                        if self._text_label:
                            self._text_label.configure(
                                text=self._instruction_text,
                                fg=theme['text'],
                                font=('Segoe UI', 10),  # volta pro tamanho normal
                            )
                    except Exception:
                        pass
                # Notifica caller que pode prosseguir
                if on_done:
                    try:
                        on_done()
                    except Exception as e:
                        log.error(f"on_done callback do flash falhou: {e}")

            self.window.after(700, reset)
        except Exception as e:
            log.debug(f"flash_capture falhou: {e}")
            self._is_flashing = False
            if on_done:
                on_done()

    def update_text(self, new_text: str):
        """Atualiza só o texto (sem flash). Útil ao mudar de canto."""
        self._instruction_text = new_text
        if self._text_label and self.window and self.window.winfo_exists():
            try:
                self._text_label.configure(text=new_text, fg=self._theme['text'])
            except Exception:
                pass

    def hide(self):
        """Esconde e destrói o tooltip."""
        if self._update_after_id and self.window:
            try:
                self.window.after_cancel(self._update_after_id)
            except Exception:
                pass
            self._update_after_id = None

        if self.window:
            try:
                if self.window.winfo_exists():
                    self.window.destroy()
            except Exception as e:
                log.debug(f"Erro ao destruir F2 tooltip: {e}")
            self.window = None
