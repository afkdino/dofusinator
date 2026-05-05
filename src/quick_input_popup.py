"""
Popup de input rápido v3.3.
- Mais identidade Dofus Retro: borda accent, pill ativo highlight, separador
- Som corrigido (via sound_player)
"""
import logging
import sys
import threading
import time
import tkinter as tk
from typing import Optional

import customtkinter as ctk

from settings import Settings
from translator_service import TranslatorService
from history_manager import HistoryManager
from sound_player import SoundPlayer
from theme import get_theme
from i18n import t

log = logging.getLogger(__name__)


LANGUAGES = {
    "fr": "Français",
    "pt": "Português",
    "en": "English",
    "es": "Español",
}

EMOTES = [
    ":)", ":(", ":D", ":P", ":p", "xD", "XD",
    ";)", ":o", ":O", ":/", ":|", "<3", "</3",
    "x)", "^^", ">.<", "T_T", "o/", "o7"
]


class QuickInputPopup:

    POPUP_WIDTH = 480
    POPUP_HEIGHT = 105

    def __init__(
        self,
        master,
        settings: Settings,
        translator: TranslatorService,
        history: HistoryManager,
        sound_player: SoundPlayer,
    ):
        self.master = master
        self.settings = settings
        self.translator = translator
        self.history = history
        self.sound_player = sound_player

        self.window: Optional[ctk.CTkToplevel] = None
        self.input_text: Optional[tk.Text] = None
        self.result_text: Optional[tk.Text] = None  # campo de resultado (modo readonly)
        self.result_buttons_frame: Optional[ctk.CTkFrame] = None  # botões do modo resultado
        self._separator: Optional[tk.Frame] = None  # ref pro separator entre input e pills
        self._bottom_frame: Optional[ctk.CTkFrame] = None  # ref pro frame de pills + auto-send
        self.status_label: Optional[ctk.CTkLabel] = None
        self.lang_pill: Optional[ctk.CTkButton] = None
        self.emote_pill: Optional[ctk.CTkButton] = None
        self.history_pill: Optional[ctk.CTkButton] = None
        self.auto_send_var: Optional[tk.BooleanVar] = None

        self._popout: Optional[tk.Toplevel] = None
        self._popout_owner: Optional[str] = None
        self._global_click_handler_id = None

        self._status_after_id = None
        self._drag_start_x = 0
        self._drag_start_y = 0

        self._t = get_theme(self.settings.get('main_window_theme', 'dofus_retro'))

    def _refresh_theme(self):
        self._t = get_theme(self.settings.get('main_window_theme', 'dofus_retro'))

    # ===========================================================================
    # Lifecycle
    # ===========================================================================

    def show(self):
        self._refresh_theme()
        if self.window is not None and self.window.winfo_exists():
            self._destroy_popout()
            # Se popup foi reaberto e tava em modo resultado, volta pro input
            if self.result_text and self.result_text.winfo_ismapped():
                self._show_input_mode()
            self._reposition()
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            if self.input_text:
                self.input_text.focus_set()
            # Força foreground (rouba foco do jogo)
            self.master.after(30, self._force_foreground)
            return
        self._build()
        self._reposition()
        self._install_global_click_listener()
        # Força foreground após render inicial
        self.master.after(30, self._force_foreground)

    def hide(self):
        self._destroy_popout()
        self._save_position()
        self._uninstall_global_click_listener()
        if self.window and self.window.winfo_exists():
            self.window.withdraw()

    def _save_position(self):
        if self.window and self.window.winfo_exists():
            try:
                self.settings.set('quick_input_last_position',
                                   [self.window.winfo_x(), self.window.winfo_y()])
            except Exception:
                pass

    def _reposition(self):
        if not self.window:
            return
        mode = self.settings.get('quick_input_position_mode', 'cursor')

        if mode == 'cursor':
            try:
                import pyautogui
                cx, cy = pyautogui.position()
                ox, oy = self.settings.get('quick_input_cursor_offset', [15, 15])
                x, y = cx + ox, cy + oy
            except Exception:
                x, y = 100, 100
        else:
            last = self.settings.get('quick_input_last_position')
            if last and len(last) == 2:
                x, y = last
            else:
                x, y = 100, 100

        x, y = self._clamp_to_screen(x, y, self.POPUP_WIDTH, self.POPUP_HEIGHT)
        self.window.geometry(f"+{x}+{y}")

    def _clamp_to_screen(self, x: int, y: int, w: int, h: int) -> tuple[int, int]:
        try:
            sw = self.master.winfo_screenwidth()
            sh = self.master.winfo_screenheight()
            x = max(0, min(x, sw - w - 10))
            y = max(0, min(y, sh - h - 10))
        except Exception:
            pass
        return x, y

    def _force_foreground(self):
        """
        Força a janela do popup a vir pra frente e roubar o foco do teclado.
        Usa o truque AttachThreadInput pra contornar a restrição do Windows
        que normalmente impede um app de roubar foco de outro.

        Sem isso: quando o popup abre via hotkey enquanto o jogo está em foco,
        o usuário começa a digitar e os caracteres vão pro JOGO, não pro popup.
        """
        if not self.window or not self.window.winfo_exists():
            return

        # Tk-level focus primeiro (não custa nada)
        try:
            self.window.lift()
            self.window.focus_force()
            if self.input_text:
                self.input_text.focus_set()
        except Exception:
            pass

        # Win32 hack pra forçar foreground a nível de sistema
        if sys.platform != 'win32':
            return

        try:
            import ctypes

            # HWND da nossa janela
            self.window.update_idletasks()
            our_hwnd = ctypes.windll.user32.GetParent(self.window.winfo_id())
            if not our_hwnd:
                return

            # HWND da janela atualmente em foreground (provavelmente o jogo)
            fg_hwnd = ctypes.windll.user32.GetForegroundWindow()
            if fg_hwnd == our_hwnd:
                return  # já estamos em foreground

            # Thread IDs
            fg_thread = ctypes.windll.user32.GetWindowThreadProcessId(fg_hwnd, 0)
            our_thread = ctypes.windll.kernel32.GetCurrentThreadId()

            # Anexa nosso thread ao thread em foreground
            # Isso nos dá permissão pra chamar SetForegroundWindow
            attached = ctypes.windll.user32.AttachThreadInput(
                our_thread, fg_thread, True
            )
            try:
                ctypes.windll.user32.BringWindowToTop(our_hwnd)
                ctypes.windll.user32.SetForegroundWindow(our_hwnd)
                ctypes.windll.user32.SetActiveWindow(our_hwnd)
                ctypes.windll.user32.SetFocus(our_hwnd)
            finally:
                if attached:
                    ctypes.windll.user32.AttachThreadInput(
                        our_thread, fg_thread, False
                    )

            # Garante que o widget de texto pega foco depois
            if self.input_text:
                self.window.after(20, self.input_text.focus_set)
        except Exception as e:
            log.error(f"Erro ao forçar foreground: {e}")

    # ===========================================================================
    # Build UI
    # ===========================================================================

    def _build(self):
        theme = self._t

        self.window = ctk.CTkToplevel(self.master)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        # Borda externa: accent (mais identidade do tema)
        self.window.configure(fg_color=theme['accent'])

        # Container interno com 1.5px de "borda" criada pelo padding
        outer = ctk.CTkFrame(self.window, fg_color=theme['bg'], corner_radius=8)
        outer.pack(padx=2, pady=2, fill='both', expand=True)

        content = ctk.CTkFrame(outer, fg_color="transparent")
        content.pack(padx=10, pady=8, fill='both', expand=True)
        # Force content width — sem isso encolhe quando troca pro modo resultado
        # (botões mais curtos que o input). Fica fixo independente do conteúdo.
        content.configure(width=self.POPUP_WIDTH - 24)  # -24 = padx*2 + pady*2 dos containers

        # Campo de texto
        self.input_text = tk.Text(
            content,
            height=2,
            bg=theme['bg_input'], fg=theme['text'], insertbackground=theme['text'],
            relief='flat', font=('Segoe UI', 12),
            wrap='word', padx=10, pady=8,
            highlightthickness=1, highlightbackground=theme['border'],
            highlightcolor=theme['accent'],
        )
        self.input_text.pack(fill='x')

        # Campo de RESULTADO (oculto inicialmente, aparece após Enter sem auto-send)
        # Mesmo height/style do input mas readonly + cor accent na borda pra destacar
        self.result_text = tk.Text(
            content,
            height=2,
            bg=theme['bg_input'], fg=theme['accent'], insertbackground=theme['accent'],
            relief='flat', font=('Segoe UI', 12),
            wrap='word', padx=10, pady=8,
            highlightthickness=2, highlightbackground=theme['accent'],
            highlightcolor=theme['accent'],
        )
        # Não dá pack agora - só aparece quando entrar em modo resultado

        # Linha de separação accent (sutil) entre input e pills
        separator = tk.Frame(content, bg=theme['accent'], height=1)
        separator.pack(fill='x', pady=(8, 8))
        self._separator = separator  # ref pra usar como anchor de pack(before=...)

        # Pills + auto-send
        bottom = ctk.CTkFrame(content, fg_color="transparent")
        bottom.pack(fill='x')
        self._bottom_frame = bottom  # ref pra usar como anchor

        left = ctk.CTkFrame(bottom, fg_color="transparent")
        left.pack(side='left')

        current_lang = self.settings.get('target_language_write', 'fr')
        self.lang_pill = self._make_pill(
            left, f"[{current_lang.upper()}]",
            command=lambda: self._toggle_popout('lang'),
        )
        self.lang_pill.pack(side='left', padx=(0, 4))

        self.emote_pill = self._make_pill(
            left, "😊",
            command=lambda: self._toggle_popout('emote'),
        )
        self.emote_pill.pack(side='left', padx=(0, 4))

        if self.settings.get('history_enabled', True):
            self.history_pill = self._make_pill(
                left, "⌄",
                command=lambda: self._toggle_popout('history'),
            )
            self.history_pill.pack(side='left', padx=(0, 4))

        right = ctk.CTkFrame(bottom, fg_color="transparent")
        right.pack(side='right')

        self.auto_send_var = tk.BooleanVar(value=self.settings.get('auto_send', False))
        # Checkbox auto-send: usa highlight quando marcado
        cb = ctk.CTkCheckBox(
            right, text=t("popup.auto_send"),
            variable=self.auto_send_var,
            command=self._on_auto_send_toggle,
            text_color=theme['text_dim'],
            font=('Segoe UI', 10),
            fg_color=theme['highlight'], hover_color=theme['accent_hover'],
            border_color=theme['border'],
            checkbox_height=18, checkbox_width=18,
            corner_radius=3,
        )
        cb.pack(side='right')

        # Botões do modo resultado (ocultos inicialmente)
        self.result_buttons_frame = ctk.CTkFrame(content, fg_color="transparent")
        # Não dá pack agora - aparece junto com result_text

        copy_btn = ctk.CTkButton(
            self.result_buttons_frame,
            text=t("popup.btn.copy_again"),
            command=self._on_copy_result_again,
            fg_color=theme['bg_pill'], hover_color=theme['bg_hover'],
            text_color=theme['accent'], font=('Segoe UI', 11, 'bold'),
            corner_radius=6, height=32,
        )
        copy_btn.pack(side='left', padx=(0, 6))

        new_btn = ctk.CTkButton(
            self.result_buttons_frame,
            text=t("popup.btn.new_translation"),
            command=self._on_new_translation,
            fg_color=theme['accent'], hover_color=theme['accent_hover'],
            text_color=theme['text_on_accent'], font=('Segoe UI', 11, 'bold'),
            corner_radius=6, height=32,
        )
        new_btn.pack(side='left')

        self.status_label = ctk.CTkLabel(
            content, text="", text_color=theme['accent'], font=('Segoe UI', 10),
            anchor='w',
        )

        self.input_text.focus_set()
        self.input_text.bind('<Return>', lambda e: self._on_enter(e))
        self.input_text.bind('<Control-Return>', lambda e: self._insert_newline())
        self.window.bind('<Escape>', self._on_escape)

        for w in [outer, content, bottom, left, right]:
            try:
                w.bind('<ButtonPress-1>', self._on_drag_start)
                w.bind('<B1-Motion>', self._on_drag)
            except Exception:
                pass

    def _make_pill(self, parent, text: str, command) -> ctk.CTkButton:
        theme = self._t
        return ctk.CTkButton(
            parent, text=text,
            command=command,
            width=10, height=28,
            fg_color=theme['bg_pill'], hover_color=theme['bg_hover'],
            text_color=theme['accent'],
            font=('Segoe UI', 11, 'bold'),
            corner_radius=6,
        )

    def _set_pill_active(self, pill: ctk.CTkButton, active: bool):
        """Pill com popout aberto: usa cor highlight (laranja) pra destacar."""
        if pill is None:
            return
        theme = self._t
        if active:
            # Highlight laranja quando popout aberto
            pill.configure(
                fg_color=theme['highlight'], text_color=theme['text_on_highlight'],
                hover_color=theme['highlight'],
            )
        else:
            pill.configure(
                fg_color=theme['bg_pill'], text_color=theme['accent'],
                hover_color=theme['bg_hover'],
            )

    def _refresh_pills(self):
        self._set_pill_active(self.lang_pill, self._popout_owner == 'lang')
        self._set_pill_active(self.emote_pill, self._popout_owner == 'emote')
        self._set_pill_active(self.history_pill, self._popout_owner == 'history')

    # ===========================================================================
    # Drag
    # ===========================================================================

    def _on_drag_start(self, event):
        self._drag_start_x = event.x_root - self.window.winfo_x()
        self._drag_start_y = event.y_root - self.window.winfo_y()

    def _on_drag(self, event):
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self.window.geometry(f"+{x}+{y}")

    # ===========================================================================
    # Popouts
    # ===========================================================================

    def _toggle_popout(self, owner: str):
        if self._popout_owner == owner and self._popout is not None and self._popout.winfo_exists():
            self._destroy_popout()
            return
        self._destroy_popout()

        if owner == 'lang':
            self._open_lang_popout()
        elif owner == 'emote':
            self._open_emote_popout()
        elif owner == 'history':
            self._open_history_popout()

    def _destroy_popout(self):
        if self._popout is not None:
            try:
                self._popout.destroy()
            except Exception:
                pass
        self._popout = None
        self._popout_owner = None
        self._refresh_pills()

    def _make_popout(self) -> tk.Toplevel:
        theme = self._t
        po = tk.Toplevel(self.window)
        po.overrideredirect(True)
        po.attributes('-topmost', True)
        # Borda accent também nos popouts
        po.configure(bg=theme['accent'])
        return po

    def _open_lang_popout(self):
        theme = self._t
        po = self._make_popout()
        outer = tk.Frame(po, bg=theme['bg'])
        outer.pack(padx=2, pady=2)
        inner = tk.Frame(outer, bg=theme['bg'], padx=4, pady=4)
        inner.pack()

        current = self.settings.get('target_language_write', 'fr')
        for lang_code in LANGUAGES.keys():
            is_current = (lang_code == current)
            btn = tk.Label(
                inner,
                text=f"[{lang_code.upper()}]",
                bg=theme['accent'] if is_current else theme['bg_pill'],
                fg=theme['text_on_accent'] if is_current else theme['accent'],
                font=('Segoe UI', 10, 'bold'),
                padx=10, pady=5, cursor='hand2',
            )
            btn.pack(side='left', padx=2)
            btn.bind('<Button-1>', lambda e, c=lang_code: self._on_lang_select(c))
            if not is_current:
                btn.bind('<Enter>', lambda e, w=btn: w.config(bg=theme['bg_hover']))
                btn.bind('<Leave>', lambda e, w=btn: w.config(bg=theme['bg_pill']))

        self._popout = po
        self._popout_owner = 'lang'
        self._position_popout_above(po, self.lang_pill)
        self._refresh_pills()

    def _open_emote_popout(self):
        theme = self._t
        po = self._make_popout()
        outer = tk.Frame(po, bg=theme['bg'])
        outer.pack(padx=2, pady=2)
        inner = tk.Frame(outer, bg=theme['bg'], padx=6, pady=4)
        inner.pack()

        cols = 7
        for i, emote in enumerate(EMOTES):
            row, col = divmod(i, cols)
            btn = tk.Label(
                inner, text=emote, bg=theme['bg_pill'], fg=theme['accent'],
                font=('Consolas', 11), padx=8, pady=4, cursor='hand2',
            )
            btn.grid(row=row, column=col, padx=2, pady=2)
            btn.bind('<Button-1>', lambda e, em=emote: self._on_emote_select(em))
            btn.bind('<Enter>', lambda e, w=btn: w.config(bg=theme['bg_hover']))
            btn.bind('<Leave>', lambda e, w=btn: w.config(bg=theme['bg_pill']))

        self._popout = po
        self._popout_owner = 'emote'
        self._position_popout_above(po, self.emote_pill)
        self._refresh_pills()

    def _open_history_popout(self):
        items = self.history.all()
        if not items:
            self._set_status(t("popup.history.empty"), error=False)
            return

        theme = self._t
        po = self._make_popout()
        outer = tk.Frame(po, bg=theme['bg'])
        outer.pack(padx=2, pady=2)
        inner = tk.Frame(outer, bg=theme['bg'], padx=4, pady=4)
        inner.pack()

        tk.Label(inner, text=t("popup.history.title"),
                 bg=theme['bg'], fg=theme['text_dim'], font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 4))

        max_visible = min(len(items), 10)
        for msg in items[:max_visible]:
            display = msg if len(msg) < 60 else msg[:57] + '...'
            btn = tk.Label(
                inner, text=display, bg=theme['bg_input'], fg=theme['text'],
                font=('Segoe UI', 10), padx=10, pady=5, anchor='w',
                cursor='hand2', width=50,
            )
            btn.pack(fill='x', pady=1)
            btn.bind('<Button-1>', lambda e, m=msg: self._on_history_select(m))
            btn.bind('<Enter>', lambda e, w=btn: w.config(bg=theme['bg_hover']))
            btn.bind('<Leave>', lambda e, w=btn: w.config(bg=theme['bg_input']))

        self._popout = po
        self._popout_owner = 'history'
        self._position_popout_above(po, self.history_pill, width=400)
        self._refresh_pills()

    def _position_popout_above(self, po: tk.Toplevel, anchor_widget, width: Optional[int] = None):
        po.update_idletasks()
        try:
            ax = anchor_widget.winfo_rootx()
            ay = anchor_widget.winfo_rooty()
            pw = width or po.winfo_reqwidth()
            ph = po.winfo_reqheight()
            x = ax
            y = ay - ph - 5
            x, y = self._clamp_to_screen(x, y, pw, ph)
            po.geometry(f"+{x}+{y}")
        except Exception as e:
            log.error(f"Erro ao posicionar popout: {e}")

    # ===========================================================================
    # Global click listener
    # ===========================================================================

    def _install_global_click_listener(self):
        try:
            import mouse
            mouse.on_click(self._on_global_click)
            self._global_click_handler_id = self._on_global_click
        except ImportError:
            log.warning("Lib 'mouse' não disponível, popouts não fecharão clicando fora")
            self._global_click_handler_id = None

    def _uninstall_global_click_listener(self):
        if self._global_click_handler_id is not None:
            try:
                import mouse
                mouse.unhook_all()
            except Exception:
                pass
            self._global_click_handler_id = None

    def _on_global_click(self):
        if self._popout is None or not self._popout.winfo_exists():
            return
        try:
            import pyautogui
            mx, my = pyautogui.position()

            po = self._popout
            px = po.winfo_rootx()
            py = po.winfo_rooty()
            pw = po.winfo_width()
            ph = po.winfo_height()

            pill = self._get_active_pill()
            if pill:
                pill_x = pill.winfo_rootx()
                pill_y = pill.winfo_rooty()
                pill_w = pill.winfo_width()
                pill_h = pill.winfo_height()
                if pill_x <= mx <= pill_x + pill_w and pill_y <= my <= pill_y + pill_h:
                    return

            if not (px <= mx <= px + pw and py <= my <= py + ph):
                self.master.after(0, self._destroy_popout)
        except Exception as e:
            log.error(f"Erro no global click handler: {e}")

    def _get_active_pill(self):
        if self._popout_owner == 'lang':
            return self.lang_pill
        elif self._popout_owner == 'emote':
            return self.emote_pill
        elif self._popout_owner == 'history':
            return self.history_pill
        return None

    # ===========================================================================
    # Ações
    # ===========================================================================

    def _on_lang_select(self, code: str):
        self.settings.set('target_language_write', code)
        self.settings.save()
        if self.lang_pill:
            self.lang_pill.configure(text=f"[{code.upper()}]")
        self._destroy_popout()
        if self.input_text:
            self.input_text.focus_set()

    def _on_emote_select(self, emote: str):
        if self.input_text:
            self.input_text.insert(tk.INSERT, emote)
        self._destroy_popout()
        if self.input_text:
            self.input_text.focus_set()

    def _on_history_select(self, message: str):
        if self.input_text:
            self.input_text.delete('1.0', tk.END)
            self.input_text.insert('1.0', message)
        self._destroy_popout()
        if self.input_text:
            self.input_text.focus_set()

    def _on_auto_send_toggle(self):
        self.settings.set('auto_send', self.auto_send_var.get())

    def _insert_newline(self):
        if self.input_text:
            self.input_text.insert(tk.INSERT, '\n')

    def _on_enter(self, event):
        self._translate_and_send()
        return 'break'

    def _on_escape(self, event):
        self.hide()

    def _translate_and_send(self):
        if not self.input_text:
            return

        text = self.input_text.get('1.0', tk.END).strip()
        if not text:
            self._set_status(t("popup.msg.empty"), error=True)
            return

        src = self.settings.get('source_language_write', 'pt')
        dest = self.settings.get('target_language_write', 'fr')

        self._set_status(t("popup.msg.translating", src=src, dest=dest))

        threading.Thread(
            target=self._do_translate_and_send, args=(text, src, dest), daemon=True,
        ).start()

    def _do_translate_and_send(self, text: str, src: str, dest: str):
        try:
            translated = self.translator.translate(text, src, dest)
        except Exception as e:
            self.master.after(0, self._set_status, t("popup.msg.error", err=e), True)
            return
        self.master.after(0, self._handle_translation_result, text, translated)

    def _show_result_mode(self, translated: str):
        """
        Substitui input pelo campo de resultado read-only + mostra botões.
        Popup fica aberto até user fechar (Esc/X) ou clicar 'Nova tradução'.

        IMPORTANTE: usa pack(before=self._separator) pra garantir que
        result_text fica EXATAMENTE no lugar do input (acima do separator),
        e result_buttons_frame depois do bottom (pills+auto-send).
        """
        if not self.window or not self.window.winfo_exists():
            return

        # 1. Esconde input
        try:
            self.input_text.pack_forget()
        except Exception:
            pass

        # 2. Preenche resultado e mostra ANTES do separator (substitui input no layout)
        try:
            self.result_text.config(state='normal')
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', translated)
            self.result_text.config(state='disabled')
            if self._separator and self._separator.winfo_exists():
                self.result_text.pack(fill='x', before=self._separator)
            else:
                self.result_text.pack(fill='x')
        except Exception as e:
            log.error(f"Erro ao mostrar result_text: {e}")

        # 3. Mostra botões DEPOIS do bottom (pills+auto-send), ANTES do status
        try:
            if self.status_label and self.status_label.winfo_ismapped():
                self.result_buttons_frame.pack(
                    fill='x', pady=(8, 0),
                    before=self.status_label,
                )
            else:
                self.result_buttons_frame.pack(fill='x', pady=(8, 0))
        except Exception as e:
            log.error(f"Erro ao mostrar result_buttons_frame: {e}")

    def _show_input_mode(self):
        """Volta ao modo de input limpo (após 'Nova tradução')."""
        if not self.window or not self.window.winfo_exists():
            return

        # 1. Esconde resultado e botões
        try:
            self.result_text.pack_forget()
            self.result_buttons_frame.pack_forget()
        except Exception:
            pass

        # 2. Mostra input ANTES do separator (mesmo lugar que era originalmente)
        try:
            if self._separator and self._separator.winfo_exists():
                self.input_text.pack(fill='x', before=self._separator)
            else:
                self.input_text.pack(fill='x')
        except Exception as e:
            log.error(f"Erro ao mostrar input_text: {e}")

        # 3. Limpa input e foca
        try:
            self.input_text.delete('1.0', tk.END)
            self.input_text.focus_set()
        except Exception:
            pass

        # Limpa status
        self._clear_status()

    def _on_copy_result_again(self):
        """Botão 'Copiar de novo' - copia o resultado pra clipboard outra vez."""
        if not self.result_text:
            return
        try:
            text = self.result_text.get('1.0', tk.END).strip()
            if text:
                self._copy_to_clipboard(text)
                self._set_status(t("popup.msg.copied_again"), error=False)
        except Exception as e:
            log.error(f"Erro ao copiar de novo: {e}")

    def _on_new_translation(self):
        """Botão 'Nova tradução' - volta pro modo de input."""
        self._show_input_mode()

    def _handle_translation_result(self, original: str, translated: str):
        lurker = self.settings.get('lurker_mode', False)
        auto_send = self.auto_send_var.get() and not lurker

        if auto_send:
            chat_bar = self.settings.get('chat_bar')
            if not chat_bar:
                self._set_status(
                    t("popup.msg.no_chatbar"),
                    error=True,
                )
                self._copy_to_clipboard(translated)
                return

            countdown_visual = self.settings.get('send_countdown_visual', False)
            if countdown_visual:
                self._countdown_then_send(original, translated, chat_bar, seconds=2)
            else:
                self._do_send_to_chat(original, translated, chat_bar)
        else:
            # === Sem auto-send: ENTRA EM MODO RESULTADO ===
            # Popup fica aberto, mostra resultado, usuário copia/edita à vontade
            self._copy_to_clipboard(translated)
            self.history.add(original)
            self.sound_player.play()
            self._show_result_mode(translated)

            if lurker:
                self._set_status(t("popup.msg.translated_lurker"),
                                  error=False, persistent=True)
            else:
                self._set_status(t("popup.msg.translated"),
                                  error=False, persistent=True)
            # NÃO fecha o popup — usuário fecha quando quiser (Esc/X)

    def _countdown_then_send(self, original: str, text: str, coords, seconds: int):
        def tick(remaining):
            if remaining <= 0:
                self._do_send_to_chat(original, text, coords)
                return
            self._set_status(t("popup.msg.sending", sec=remaining))
            self._status_after_id = self.window.after(1000, tick, remaining - 1)

        def cancel(_e=None):
            if self._status_after_id:
                self.window.after_cancel(self._status_after_id)
                self._status_after_id = None
                self._set_status(t("popup.msg.cancelled"), error=True)

        self.window.bind('<Escape>', cancel)
        tick(seconds)

    def _do_send_to_chat(self, original: str, text: str, coords):
        try:
            import pyautogui
            x, y = coords[0], coords[1]
            pyautogui.click(x, y)
            time.sleep(0.15)

            try:
                import keyboard
                keyboard.write(text, delay=0.005)
            except ImportError:
                pyautogui.typewrite(text, interval=0.01)

            time.sleep(0.1)

            try:
                import keyboard
                keyboard.send('enter')
            except Exception:
                pyautogui.press('enter')

            preview = text[:50] + ('...' if len(text) > 50 else '')
            self._set_status(t("popup.msg.sent", preview=preview))
            self.history.add(original)
            self.sound_player.play()

            if self.input_text:
                self.input_text.delete('1.0', tk.END)
            self.master.after(400, self.hide)
        except Exception as e:
            self._set_status(f"Erro ao enviar: {e}", error=True)

    def _copy_to_clipboard(self, text: str):
        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(text)
            self.master.update()
        except Exception as e:
            log.error(f"Erro ao copiar pra clipboard: {e}")

    # ===========================================================================
    # Status
    # ===========================================================================

    def _set_status(self, message: str, error: bool = False, persistent: bool = False):
        """
        Mostra mensagem no rodapé.
        - error=True: cor highlight (laranja), não auto-limpa
        - persistent=True: não auto-limpa (uso pra "Tradução concluída" no modo resultado)
        """
        if not self.status_label:
            return
        theme = self._t
        color = theme['highlight'] if error else theme['accent']
        try:
            self.status_label.configure(text=message, text_color=color)
            self.status_label.pack(fill='x', pady=(4, 0))
        except Exception:
            pass

        if self._status_after_id:
            try:
                self.window.after_cancel(self._status_after_id)
                self._status_after_id = None
            except Exception:
                pass

        # Auto-limpa só se NÃO for error E NÃO for persistent
        if not error and not persistent:
            self._status_after_id = self.window.after(3000, self._clear_status)

    def _clear_status(self):
        if self.status_label:
            try:
                self.status_label.configure(text="")
                self.status_label.pack_forget()
            except Exception:
                pass
        self._status_after_id = None
