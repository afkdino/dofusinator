"""
Hotkey Capture Popup - Captura de combinação de teclas por aperto.

Substitui o text_input "ctrl+shift+t" digitado por extenso por um popup que:
1. Mostra "Pressione qualquer combinação..."
2. Detecta a combinação real apertada pelo user (modificadores + tecla)
3. Valida (precisa ter pelo menos 1 modificador)
4. Retorna a string formatada (ex: "ctrl+shift+y")

Bloco 3 / Sub-bloco 3.2 da v1.1
"""
import logging
import tkinter as tk
from typing import Optional, Callable

import customtkinter as ctk

from theme import get_theme
from custom_titlebar import apply_custom_titlebar
from monitor_utils import center_window_on_parent
from i18n import t

log = logging.getLogger(__name__)


class HotkeyCapturePopup:
    """
    Popup modal pra capturar uma combinação de teclas.

    Uso:
        popup = HotkeyCapturePopup(parent_root, settings)
        popup.show(
            on_captured=lambda hotkey: print(f"Capturado: {hotkey}"),
            on_cancel=lambda: print("Cancelado"),
        )
    """

    WINDOW_WIDTH = 480
    WINDOW_HEIGHT = 280

    # Mapa de modificadores válidos (precisa pelo menos 1)
    MODIFIER_KEYS = {'ctrl', 'alt', 'shift', 'win', 'cmd'}

    # Teclas que NÃO podem ser usadas como tecla principal
    INVALID_MAIN_KEYS = MODIFIER_KEYS | {'caps lock', 'num lock', 'scroll lock', 'tab', 'esc', 'escape'}

    def __init__(self, parent, settings):
        self.parent = parent
        self.settings = settings
        self._theme = get_theme(settings.get('main_window_theme', 'dofus_retro'))

        self.window: Optional[ctk.CTkToplevel] = None
        self._on_captured: Optional[Callable[[str], None]] = None
        self._on_cancel: Optional[Callable[[], None]] = None
        self._captured = False

        # Refs UI
        self._instruction_label: Optional[ctk.CTkLabel] = None
        self._error_label: Optional[ctk.CTkLabel] = None
        self._cancel_btn: Optional[ctk.CTkButton] = None

        # Estado de captura
        self._keyboard_hook = None

    def show(self, on_captured: Callable[[str], None], on_cancel: Optional[Callable[[], None]] = None):
        """Mostra o popup e começa a escutar teclas."""
        self._on_captured = on_captured
        self._on_cancel = on_cancel
        self._captured = False
        self._build()
        self._start_listening()

    def _build(self):
        theme = self._theme

        self.window = ctk.CTkToplevel(self.parent)
        self.window.title(t("hotkey.capture.title"))
        self.window.configure(fg_color=theme['bg'])

        # Centraliza relativo ao parent (em cima do app)
        center_window_on_parent(self.window, self.parent, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        # Custom titlebar com tema do app
        apply_custom_titlebar(
            self.window,
            t("hotkey.capture.title"),
            on_close=self._on_cancel_pressed,
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

        # Conteúdo
        content = ctk.CTkFrame(self.window, fg_color="transparent")
        content.pack(fill='both', expand=True, padx=24, pady=20)

        # Ícone/heading
        heading = ctk.CTkLabel(
            content, text=t("hotkey.capture.heading"),
            text_color=theme['accent'],
            font=('Segoe UI', 18, 'bold'),
        )
        heading.pack(pady=(0, 12))

        # Instrução
        self._instruction_label = ctk.CTkLabel(
            content, text=t("hotkey.capture.instruction"),
            text_color=theme['text'],
            font=('Segoe UI', 12),
            wraplength=self.WINDOW_WIDTH - 60,
            justify='center',
        )
        self._instruction_label.pack(pady=(0, 8))

        # Texto auxiliar (pode mostrar erro de validação)
        self._error_label = ctk.CTkLabel(
            content, text="",
            text_color="#ff8888",  # vermelho suave
            font=('Segoe UI', 10),
            wraplength=self.WINDOW_WIDTH - 60,
            justify='center',
        )
        self._error_label.pack(pady=(0, 12))

        # Spacer
        spacer = ctk.CTkFrame(content, fg_color="transparent", height=10)
        spacer.pack(fill='both', expand=True)

        # Botão cancelar
        self._cancel_btn = ctk.CTkButton(
            content, text=t("hotkey.capture.cancel"),
            command=self._on_cancel_pressed,
            fg_color=theme['bg_pill'],
            hover_color=theme['bg_hover'],
            text_color=theme['text'],
            font=('Segoe UI', 11),
            corner_radius=8, height=36, width=120,
        )
        self._cancel_btn.pack(side='bottom', pady=(8, 0))

        # ESC fecha (cancela)
        self.window.bind('<Escape>', lambda e: self._on_cancel_pressed())

        # Foco e topmost
        try:
            self.window.update_idletasks()
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            self.window.update()
            # Sem transient (lição aprendida da Welcome) — evita fantasma
            self.window.attributes('-topmost', True)
            self.window.after(300, self._safe_grab_set)
        except Exception as e:
            log.error(f"Erro modal setup hotkey capture: {e}")

    def _safe_grab_set(self):
        """grab_set defensivo (mesmo padrão da Welcome screen)."""
        try:
            if self.window and self.window.winfo_exists() and self.window.winfo_viewable():
                self.window.grab_set()
                self.window.focus_force()
        except Exception as e:
            log.debug(f"grab_set hotkey capture falhou: {e}")

    def _start_listening(self):
        """
        Inicia escuta global por combinação de teclas usando 'keyboard'.

        Não dá pra usar bind do tk porque queremos pegar a combinação inteira
        (modificadores + tecla principal), e o tk separa em eventos diferentes.
        Usamos keyboard.read_hotkey() em uma thread separada.
        """
        try:
            import keyboard
        except ImportError:
            log.error("Lib 'keyboard' não disponível pra capturar hotkey")
            self._error_label.configure(text=t("hotkey.capture.error_lib_missing"))
            return

        import threading

        def reader_thread():
            try:
                # read_hotkey retorna a combinação na string padrão "ctrl+shift+y"
                # suppress=False = não bloqueia a tecla pra outras apps
                hotkey_str = keyboard.read_hotkey(suppress=False)
                log.info(f"Hotkey capturada: '{hotkey_str}'")
                # Volta pro main thread pra processar
                if self.window and self.window.winfo_exists():
                    self.window.after(0, lambda: self._on_captured_internal(hotkey_str))
            except Exception as e:
                log.error(f"Erro na captura de hotkey: {e}")

        thread = threading.Thread(target=reader_thread, daemon=True)
        thread.start()

    def _on_captured_internal(self, hotkey_str: str):
        """Validação + callback do user."""
        if self._captured:  # já processado, ignora duplicatas
            return

        # Normaliza: lowercase, remove espaços extras, ordena modificadores
        normalized = self._normalize_hotkey(hotkey_str)

        # Validação: precisa pelo menos 1 modificador + 1 tecla principal
        parts = normalized.split('+')
        if len(parts) < 2:
            self._show_error(t("hotkey.capture.error_no_modifier"))
            self._restart_listening()
            return

        # Pelo menos 1 modificador
        has_modifier = any(p in self.MODIFIER_KEYS for p in parts)
        if not has_modifier:
            self._show_error(t("hotkey.capture.error_no_modifier"))
            self._restart_listening()
            return

        # Última tecla deve ser válida (não pode ser só modificador)
        main_key = parts[-1]
        if main_key in self.INVALID_MAIN_KEYS:
            self._show_error(t("hotkey.capture.error_invalid_key"))
            self._restart_listening()
            return

        # Tudo ok, avisa o caller
        self._captured = True
        try:
            if self._on_captured:
                self._on_captured(normalized)
        finally:
            self._close()

    def _normalize_hotkey(self, hotkey_str: str) -> str:
        """Normaliza string de hotkey: lowercase, ordem canônica de modificadores."""
        s = hotkey_str.lower().strip()
        parts = [p.strip() for p in s.split('+') if p.strip()]
        # Ordem canônica: ctrl, alt, shift, win, depois tecla
        modifiers = []
        main_keys = []
        for p in parts:
            if p in self.MODIFIER_KEYS:
                modifiers.append(p)
            else:
                main_keys.append(p)
        # Ordena modificadores canonicamente
        order = ['ctrl', 'alt', 'shift', 'win', 'cmd']
        modifiers.sort(key=lambda m: order.index(m) if m in order else 999)
        return '+'.join(modifiers + main_keys)

    def _show_error(self, msg: str):
        """Mostra mensagem de erro no popup."""
        if self._error_label:
            self._error_label.configure(text=msg)

    def _restart_listening(self):
        """Re-inicia escuta após erro de validação."""
        if not self._captured:
            self._start_listening()

    def _on_cancel_pressed(self):
        """Cancela captura."""
        if self._on_cancel:
            try:
                self._on_cancel()
            except Exception as e:
                log.error(f"on_cancel callback falhou: {e}")
        self._close()

    def _close(self):
        """Fecha o popup limpando recursos."""
        try:
            if self.window and self.window.winfo_exists():
                self.window.grab_release()
                self.window.destroy()
        except Exception as e:
            log.debug(f"Erro ao fechar popup hotkey: {e}")
        self.window = None
