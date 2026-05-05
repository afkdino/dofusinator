"""
Helper pra resolver caminhos de assets em dev e em .exe empacotado.

Em dev: assets ficam em <project>/assets/icon.ico
Em PyInstaller --onefile: assets ficam em sys._MEIPASS/assets/icon.ico
                          (descomprimidos num temp dir no startup)
"""
import logging
import sys
from pathlib import Path

log = logging.getLogger(__name__)


def get_resource_path(relative_path: str) -> Path:
    """
    Resolve caminho de asset (icon.ico, sounds/, etc).
    Funciona em dev e em PyInstaller bundle.
    """
    if hasattr(sys, '_MEIPASS'):
        # Rodando dentro do PyInstaller --onefile
        base = Path(sys._MEIPASS)
    else:
        # Dev mode: assume que estamos em src/, asset tá um nível acima
        base = Path(__file__).parent.parent
    return base / relative_path


def get_icon_path() -> Path | None:
    """Retorna caminho pro icon.ico se existir, senão None."""
    p = get_resource_path('assets/icon.ico')
    if p.exists():
        return p
    log.warning(f"icon.ico não encontrado em {p}")
    return None


def set_window_icon(window):
    """
    Aplica o icon.ico em uma janela tk/CTk.
    Silencioso se o ícone não existir ou não for Windows.

    IMPORTANTE: Em CTkToplevel/tk.Toplevel, chamar iconbitmap()
    imediatamente após criar a janela é IGNORADO silenciosamente
    pelo Tk (o window manager interno ainda não inicializou).
    Solução: agendar via after() pra dar tempo do tk montar.
    """
    icon = get_icon_path()
    if icon is None:
        return

    icon_str = str(icon)

    def _apply():
        try:
            window.iconbitmap(default=icon_str)
        except Exception:
            try:
                window.iconbitmap(icon_str)
            except Exception as e:
                log.debug(f"Não consegui setar ícone: {e}")

    # Tenta imediatamente (funciona pra root window CTk)
    _apply()
    # E agenda novamente após o tk montar tudo (necessário pra Toplevels)
    try:
        window.after(50, _apply)
        window.after(200, _apply)  # segundo retry pra garantir
    except Exception:
        pass


def apply_icon_via_win32(window):
    """
    Aplica ícone via Win32 SendMessage(WM_SETICON).
    Funciona em janelas com overrideredirect(True), onde iconbitmap() não cola.

    Deve ser chamada DEPOIS do overrideredirect e do update_idletasks da janela.
    """
    if sys.platform != 'win32':
        return

    icon = get_icon_path()
    if icon is None:
        return

    try:
        import ctypes
        from ctypes import wintypes

        # Constants
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        LR_DEFAULTSIZE = 0x00000040

        # Pega HWND da janela (top-level pai, não o widget interno)
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()

        user32 = ctypes.windll.user32
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.LoadImageW.argtypes = [
            wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
            ctypes.c_int, ctypes.c_int, wintypes.UINT
        ]

        # Carrega ícone pequeno (16x16) — pra titlebar/Alt+Tab pequeno
        h_icon_small = user32.LoadImageW(
            None, str(icon), IMAGE_ICON,
            16, 16, LR_LOADFROMFILE
        )
        # Carrega ícone grande (32x32) — pra Alt+Tab grande/taskbar
        h_icon_big = user32.LoadImageW(
            None, str(icon), IMAGE_ICON,
            32, 32, LR_LOADFROMFILE
        )

        if h_icon_small:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon_small)
        if h_icon_big:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon_big)

        log.debug(f"Ícone Win32 aplicado em hwnd {hwnd}")
    except Exception as e:
        log.debug(f"Erro ao aplicar ícone via Win32: {e}")


def set_app_user_model_id(app_id: str):
    """
    Define AppUserModelID no Windows pra agrupar janelas corretamente
    na taskbar e mostrar o ícone certo. SEM ISSO, o Windows agrupa apps
    Python pelo python.exe e ignora o ícone da janela.

    Chamar UMA VEZ no startup, antes de criar a janela principal.
    """
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        log.debug(f"AppUserModelID definido: {app_id}")
    except Exception as e:
        log.debug(f"Não consegui definir AppUserModelID: {e}")


def restart_app():
    """
    Reinicia o app atual.

    Funciona em 2 modos:
    - Em PyInstaller --onedir (.exe): re-executa sys.executable diretamente
      (sem race condition do _MEI porque --onedir não usa temp)
    - Em dev (rodando python main.py): re-executa python com mesmo argv

    Usa subprocess.Popen pra desacoplar do processo atual + os._exit pra
    fechar imediatamente sem chamar handlers (evita conflito com tk).
    """
    import os
    import subprocess

    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller bundle: sys.executable é o próprio .exe
            executable = sys.executable
            args = [executable] + sys.argv[1:]
        else:
            # Dev mode: re-roda o script Python
            executable = sys.executable
            args = [executable] + sys.argv

        log.info(f"Reiniciando app: {args}")
        # DETACHED_PROCESS = novo processo independente, não morre junto com este
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(
            args,
            close_fds=True,
            creationflags=DETACHED_PROCESS,
        )
        # Sai imediatamente sem rodar atexit handlers (que poderiam travar o tk)
        os._exit(0)
    except Exception as e:
        log.error(f"Erro ao reiniciar: {e}")
        os._exit(1)
