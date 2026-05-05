"""
System tray icon usando pystray.
- Menu botão direito: Abrir, Modo Lurker [estado], Fechar
- Click esquerdo no ícone: abre janela
- Lurker é toggle dinâmico (atualiza visual do menu)
- Procura assets/icon.ico, icon.png; senão gera placeholder
"""
import logging
import threading
from pathlib import Path
from typing import Optional, Callable

from settings import Settings, get_app_dir
from app_info import APP_NAME, APP_FULL_NAME, APP_ID
from i18n import t

log = logging.getLogger(__name__)

ASSETS_DIR = get_app_dir() / "assets"


def _create_placeholder_icon(size: int = 64):
    """Gera ícone placeholder com letra D estilizada."""
    from PIL import Image, ImageDraw, ImageFont

    bg = (26, 22, 20)         # #1a1614
    fg = (213, 207, 170)      # #D5CFAA
    border = (255, 97, 0)     # #FF6100

    img = Image.new('RGBA', (size, size), bg + (255,))
    draw = ImageDraw.Draw(img)

    # Borda com cor highlight
    draw.rectangle([0, 0, size - 1, size - 1], outline=border + (255,), width=2)

    # Letra D no centro
    try:
        font = ImageFont.truetype("arial.ttf", size=int(size * 0.6))
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=int(size * 0.6))
        except (IOError, OSError):
            font = ImageFont.load_default()

    text = "D"
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (size - tw) // 2 - bbox[0]
        y = (size - th) // 2 - bbox[1]
    except Exception:
        x, y = size // 4, size // 8

    draw.text((x, y), text, fill=fg + (255,), font=font)
    return img


def _load_icon_image(size: int = 64):
    """Carrega ícone do disco se existir, senão gera placeholder."""
    if ASSETS_DIR.exists():
        for filename in ('icon.ico', 'icon.png'):
            path = ASSETS_DIR / filename
            if path.exists():
                try:
                    from PIL import Image
                    img = Image.open(str(path))
                    log.info(f"Ícone do tray carregado: {path}")
                    return img
                except Exception as e:
                    log.error(f"Erro ao carregar ícone {path}: {e}")

    log.info("Usando ícone placeholder (assets/icon.ico não encontrado)")
    return _create_placeholder_icon(size)


class TrayIcon:
    """
    Wrapper pra pystray.Icon. Roda em thread separada.
    Métodos pra abrir janela, toggle lurker, fechar app.
    """

    def __init__(
        self,
        settings: Settings,
        on_open: Callable,
        on_quit: Callable,
        on_toggle_lurker: Callable,
    ):
        self.settings = settings
        self.on_open = on_open
        self.on_quit = on_quit
        self.on_toggle_lurker = on_toggle_lurker

        self._icon = None
        self._thread: Optional[threading.Thread] = None

        ASSETS_DIR.mkdir(exist_ok=True)

    def start(self):
        """Inicia o tray icon em thread separada."""
        try:
            import pystray
        except ImportError:
            log.error("pystray não instalado. System tray indisponível.")
            return

        try:
            image = _load_icon_image()

            self._icon = pystray.Icon(
                APP_ID.lower(),
                image,
                title=APP_FULL_NAME,
                menu=self._build_menu(pystray),
            )

            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            log.info("Tray icon iniciado")
        except Exception as e:
            log.error(f"Erro ao iniciar tray: {e}", exc_info=True)

    def _run(self):
        try:
            self._icon.run()
        except Exception as e:
            log.error(f"Erro no run do tray: {e}")

    def _build_menu(self, pystray):
        """Constrói menu dinâmico. checked= é função pra atualizar visual."""

        def open_action(icon, item):
            try:
                self.on_open()
            except Exception as e:
                log.error(f"Erro no on_open: {e}")

        def lurker_action(icon, item):
            try:
                self.on_toggle_lurker()
                # Força menu atualizar
                icon.update_menu()
            except Exception as e:
                log.error(f"Erro no toggle lurker: {e}")

        def quit_action(icon, item):
            try:
                icon.stop()
                self.on_quit()
            except Exception as e:
                log.error(f"Erro no on_quit: {e}")

        def is_lurker_active(item):
            return self.settings.get('lurker_mode', False)

        return pystray.Menu(
            pystray.MenuItem(
                t("tray.menu.open"),
                open_action,
                default=True,  # Click esquerdo no ícone = abrir
            ),
            pystray.MenuItem(
                t("tray.menu.lurker"),
                lurker_action,
                checked=is_lurker_active,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                t("tray.menu.quit"),
                quit_action,
            ),
        )

    def stop(self):
        """Para o tray icon."""
        if self._icon is not None:
            try:
                self._icon.stop()
                log.info("Tray icon parado")
            except Exception as e:
                log.error(f"Erro ao parar tray: {e}")
        self._icon = None

    def notify(self, title: str, message: str):
        """Mostra notificação balão do tray (se suportado)."""
        if self._icon is None:
            return
        try:
            self._icon.notify(message, title)
        except Exception as e:
            log.debug(f"Notify não suportado: {e}")

    def refresh_menu(self):
        """Força atualização do menu (ex: depois de mudar lurker fora do tray)."""
        if self._icon is not None:
            try:
                self._icon.update_menu()
            except Exception as e:
                log.debug(f"Erro ao refresh menu: {e}")
