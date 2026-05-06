"""
Janela principal v3.3.
- Abas com cor highlight #FF6100 quando selecionadas
- Setting close_to_tray (X minimiza pra tray ou fecha)
- Callbacks pra TrayIcon (show_window, toggle_lurker)
"""
import logging
import time
import tkinter as tk
from tkinter import colorchooser, messagebox, scrolledtext
from typing import Optional

import customtkinter as ctk

from app_info import APP_NAME, APP_FULL_NAME
from settings import Settings
from translator_service import TranslatorService
from ocr_engine import OCREngine
from overlay_window import OverlayWindow, THEME_PRESETS
from quick_input_popup import QuickInputPopup, LANGUAGES
from custom_terms_popup import CustomTermsPopup
from custom_terms import CustomTermsManager
from hotkey_manager import HotkeyManager
from sound_player import SoundPlayer
from monitor_utils import get_monitors, get_monitor_key
from custom_titlebar import apply_custom_titlebar, _win32_minimize
from theme import get_theme, list_theme_names, THEME_LABELS
from toast_notification import ToastManager
from update_dialog import UpdateDialog  # v1.0.34/Fase 4: modal de update Velopack
from auto_apply import AutoApply
from spacing import (
    SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL, SPACING_XXL,
    WINDOW_PADDING, WINDOW_CONTENT_PADDING_X, WINDOW_CONTENT_PADDING_Y,
    FOOTER_PADDING_X, FOOTER_PADDING_Y,
    BUTTON_PADDING_X, BUTTON_PADDING_Y,
    SECTION_GAP, SECTION_HEADER_SPACING, FORM_ROW_GAP,
)
from assets_helper import set_window_icon, apply_icon_via_win32, restart_app
from i18n import t, get_supported_languages, get_language_label

log = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")

PREVIEW_LINES = [
    "[12:34] Frérot: salut, qui vend un pano feca?",
    "[12:35] Player2: moi j'en ai un, 200kk",
    "[12:36] Player3: trop cher mdr",
    "[12:37] Frérot: tkt je vais farmer un peu",
    "[12:38] Player2: bg, dis-moi si tu changes d'avis",
]


class MainWindow:
    def __init__(
        self,
        root,
        settings: Settings,
        translator: TranslatorService,
        ocr: OCREngine,
        overlay: OverlayWindow,
        quick_input: QuickInputPopup,
        custom_terms: CustomTermsManager,
        hotkey_mgr: HotkeyManager,
        sound_player: SoundPlayer,
        chat_history=None,  # v1.0.21
        on_close_app=None,
        on_minimize_to_tray=None,
        updater=None,  # v1.1.0: auto-update service (placeholder — usado na Fase 4)
        ):
        self.root = root
        self.settings = settings
        self.translator = translator
        self.ocr = ocr
        self.overlay = overlay
        self.quick_input = quick_input
        self.custom_terms = custom_terms
        self.hotkey_mgr = hotkey_mgr
        self.sound_player = sound_player
        self.chat_history = chat_history  # v1.0.21: pra UI/limpar
        self.on_close_app = on_close_app
        self.on_minimize_to_tray = on_minimize_to_tray
        self.updater = updater
        self.custom_terms_popup = CustomTermsPopup(root, custom_terms, settings)

        self.preview_widget: Optional[tk.Text] = None

        self._t = get_theme(self.settings.get('main_window_theme', 'dofus_retro'))

        # === v1.0.30: Toast notifications + AutoApply ===
        # ToastManager: cria toasts no canto sup-direito da janela
        # AutoApply: conecta vars tk a settings.set + apply_fn + toast
        self._toast_mgr = ToastManager(root, self._t)
        self._auto_apply = AutoApply(self.settings, root, self._toast_mgr)

        self._build()

        # === Sincronização de estado overlay → botão Iniciar/Parar ===
        # Quando o overlay é fechado pelo X da titlebar (ou via tray/etc),
        # ele para a captura. Aqui registramos um callback pra refletir esse
        # estado no botão "Iniciar/Parar Tradução" da aba Captura.
        self.overlay.on_hide = self._on_overlay_hidden

        # === Mini-Pill (Sub-bloco 3.2) ===
        # Cria mas não mostra ainda. É instanciado on-demand quando user
        # aciona toggle_overlay com overlay já visível.
        from mini_pill import MiniPill
        self._mini_pill = MiniPill(root, settings)
        self._mini_pill.set_on_expand(self._on_mini_pill_clicked)

        # Conecta o callback de "nova linha" do overlay pro mini-pill
        # atualizar em tempo real quando estiver visível
        self.overlay.on_new_line = self._on_overlay_new_line

        # v1.0.21: registra callback do botão "colapsar" da titlebar do overlay
        self.overlay.on_collapse_request = self._collapse_overlay_to_pill

        # === v1.0.34/Fase 4: Auto-update check ===
        # 5 segundos após startup, checa GitHub Releases por update novo.
        # Em modo dev (updater.is_active=False), no-op silencioso.
        # Quando há update, mostra toast Discord-style topo-central que abre
        # modal de confirmação ao clicar.
        self._pending_update_version: Optional[str] = None  # cacheia versão detectada
        self._update_dialog: Optional[UpdateDialog] = None
        self.root.after(5000, self._check_for_updates)

    # ===========================================================================
    # v1.0.34/Fase 4 — Auto-update flow
    # ===========================================================================

    def _check_for_updates(self):
        """
        Dispara checagem assíncrona de update.

        Chamado 5s após startup pra não atrasar UI initial render.
        Em modo dev (updater.is_active=False), retorna imediatamente.
        Se updater encontrar versão nova, callback _on_update_available
        marshalla pra main thread e mostra o toast.
        """
        if self.updater is None or not self.updater.is_active:
            log.debug("Auto-update: skip (updater inativo / modo dev)")
            return

        log.info("Auto-update: checando GitHub Releases por nova versão...")

        def on_available(new_version: str):
            # Roda em background thread — marshalla pro main thread
            try:
                self.root.after(0, lambda: self._on_update_available(new_version))
            except Exception as e:
                log.error(f"Erro marshallando update available: {e}", exc_info=True)

        # v1.0.34/Fase 4: passa on_uptodate e on_error mas no startup auto-check
        # nao precisamos fazer nada nos casos negativos (silent no-op). UI manual
        # da aba Avancado eh quem usa esses callbacks.
        try:
            self.updater.check_async(on_available=on_available)
        except Exception as e:
            log.error(f"Erro ao iniciar check_async: {e}", exc_info=True)

    def _on_update_available(self, new_version: str):
        """
        Callback no main thread quando update foi detectado.
        Mostra toast Discord-style com callback de click.
        """
        log.info(f"Auto-update: versão {new_version} disponível!")
        self._pending_update_version = new_version

        toast_text = f"🚀 Nova versão {new_version} disponível! Clique pra atualizar."
        self._toast_mgr.show(
            text=toast_text,
            level='update',
            on_click=self._on_update_toast_clicked,
        )

    def _on_update_toast_clicked(self):
        """User clicou no toast → abre dialog modal de confirmação."""
        if not self._pending_update_version:
            log.warning("Update toast clicado mas sem versão pendente?")
            return
        if self._update_dialog is not None and \
           self._update_dialog.window is not None and \
           self._update_dialog.window.winfo_exists():
            log.debug("Update dialog ja aberto, focando...")
            self._update_dialog.window.lift()
            return

        # Pega versão atual de app_info (single source of truth)
        from app_info import APP_VERSION as current_v

        log.info(f"Abrindo UpdateDialog: {current_v} → {self._pending_update_version}")
        self._update_dialog = UpdateDialog(
            master=self.root,
            theme=self._t,
            current_version=current_v,
            new_version=self._pending_update_version,
            updater=self.updater,
            on_close=lambda: setattr(self, '_update_dialog', None),
        )
        self._update_dialog.show()

    def _on_check_updates_clicked(self):
        """
        v1.0.34/Fase 4: User clicou no botao 'Verificar atualizacoes' da aba
        Avancado. Faz check manual sincrono (com feedback inline no label).

        - Em modo dev: nao deveria nem ser clicavel (label ja mostra devmode),
          mas se chamar mesmo assim, atualiza pra devmode hint.
        - Em modo prod: dispara check_async, atualiza label conforme states.
        """
        if self.updater is None or not self.updater.is_active:
            self._set_update_status(
                t("advanced.updates.status.devmode"), dim=True,
            )
            return

        log.info("Check manual de update disparado pelo usuario")
        # Desabilita botao durante check pra evitar duplo clique
        try:
            self._update_check_btn.configure(state='disabled')
        except Exception:
            pass

        self._set_update_status(t("advanced.updates.status.checking"), dim=True)

        def _re_enable_btn():
            try:
                self._update_check_btn.configure(state='normal')
            except Exception:
                pass

        def on_available(new_version: str):
            # Marshalla pro main thread
            try:
                self.root.after(0, lambda: self._handle_check_available(new_version))
                self.root.after(0, _re_enable_btn)
            except Exception as e:
                log.error(f"on_available marshall: {e}", exc_info=True)

        def on_uptodate():
            try:
                self.root.after(0, lambda: self._set_update_status(
                    t("advanced.updates.status.uptodate"), dim=False,
                ))
                self.root.after(0, _re_enable_btn)
            except Exception as e:
                log.error(f"on_uptodate marshall: {e}", exc_info=True)

        def on_error(err_msg: str):
            try:
                self.root.after(0, lambda: self._set_update_status(
                    t("advanced.updates.status.error"), dim=True,
                ))
                self.root.after(0, _re_enable_btn)
            except Exception as e:
                log.error(f"on_error marshall: {e}", exc_info=True)

        try:
            self.updater.check_async(
                on_available=on_available,
                on_uptodate=on_uptodate,
                on_error=on_error,
            )
        except Exception as e:
            log.error(f"check_async manual falhou: {e}", exc_info=True)
            self._set_update_status(t("advanced.updates.status.error"), dim=True)
            _re_enable_btn()

    def _handle_check_available(self, new_version: str):
        """Helper: check manual encontrou update — atualiza label E armazena
        versao pra reaproveitar o flow do toast (clicar no label abre dialog)."""
        self._pending_update_version = new_version
        # Mostra label clicavel com a versao
        msg = t("advanced.updates.status.available").format(version=new_version)
        self._set_update_status(msg, dim=False, clickable=True)

    def _set_update_status(self, text_str: str, dim: bool = True,
                           clickable: bool = False):
        """Atualiza o label de status da seção Atualizações."""
        try:
            theme = self._t
            color = theme.get('text_dim', '#888') if dim else theme.get('accent', '#c5a572')
            self._update_status_label.configure(
                text=text_str, text_color=color,
            )
            # Se for clickable, bind do click → abre dialog
            if clickable:
                # Cursor mao + bind
                self._update_status_label.configure(cursor='hand2')
                self._update_status_label.bind(
                    '<Button-1>',
                    lambda e: self._on_update_toast_clicked(),
                )
            else:
                self._update_status_label.configure(cursor='')
                try:
                    self._update_status_label.unbind('<Button-1>')
                except Exception:
                    pass
        except Exception as e:
            log.error(f"_set_update_status: {e}", exc_info=True)

    def _build(self):
        theme = self._t
        WINDOW_W, WINDOW_H = 640, 900

        # === Centraliza na tela primária ===
        # winfo_screenwidth/height retornam dimensões da tela primária no Windows.
        # Se user tiver multi-monitor, o app sempre abre no monitor primário.
        try:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = max(0, (screen_w - WINDOW_W) // 2)
            # Y um pouco acima do centro pra não esbarrar na taskbar do Windows
            y = max(0, (screen_h - WINDOW_H) // 2 - 30)
            self.root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")
        except Exception as e:
            log.debug(f"Falha ao centralizar root: {e}")
            self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")

        self.root.configure(fg_color=theme['bg'])

        self._titlebar_refs = apply_custom_titlebar(
            self.root,
            title=APP_NAME,
            on_close=self._on_close_button,
            on_minimize=lambda: _win32_minimize(self.root),
            keep_taskbar=True,
            resizable=True,
            bg_color=theme['bg'],
            bg_titlebar=theme['titlebar_bg'],
            fg=theme['text'], accent=theme['accent'],
            bg_button_hover=theme['bg_hover'],
            close_hover_bg=theme['titlebar_close_hover'],
            min_width=550, min_height=600,
        )

        # Re-aplica ícone via Win32 DEPOIS do overrideredirect e do
        # withdraw+deiconify do _force_taskbar_appearance.
        self.root.after(300, lambda: apply_icon_via_win32(self.root))
        self.root.after(800, lambda: apply_icon_via_win32(self.root))

        self._build_lurker_button()

        # Abas com highlight #FF6100 quando selecionadas
        self.tabview = ctk.CTkTabview(
            self.root,
            fg_color=theme['bg_panel'],
            segmented_button_fg_color=theme['bg_panel'],
            # === MUDANÇA v3.3: aba selecionada usa highlight laranja ===
            segmented_button_selected_color=theme['highlight'],
            segmented_button_selected_hover_color=theme['accent_hover'],
            segmented_button_unselected_color=theme['bg_input'],
            segmented_button_unselected_hover_color=theme['bg_hover'],
            text_color=theme['text'],
            corner_radius=8,
        )
        self.tabview.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        self.tabview.add(t("tab.capture"))
        self.tabview.add(t("tab.translation"))
        self.tabview.add(t("tab.appearance"))
        self.tabview.add(t("tab.shortcut_sound"))
        self.tabview.add(t("tab.advanced"))

        self._build_capture_tab(self.tabview.tab(t("tab.capture")))
        self._build_translation_tab(self.tabview.tab(t("tab.translation")))
        self._build_appearance_tab(self.tabview.tab(t("tab.appearance")))
        self._build_shortcut_sound_tab(self.tabview.tab(t("tab.shortcut_sound")))
        self._build_advanced_tab(self.tabview.tab(t("tab.advanced")))

        self.status_var = tk.StringVar(value=t("msg.ready"))
        self.status_bar = ctk.CTkLabel(
            self.root, textvariable=self.status_var,
            fg_color=theme['titlebar_bg'], text_color=theme['accent'],
            anchor='w', font=('Segoe UI', 12), height=30,
            # v1.0.22: padding interno pra texto não colar na borda esquerda
            padx=FOOTER_PADDING_X, pady=FOOTER_PADDING_Y,
        )
        self.status_bar.pack(fill='x', side='bottom')

    def _on_close_button(self):
        """Botão X: minimiza pra tray OU fecha (depende de close_to_tray setting)."""
        if self.settings.get('close_to_tray', False) and self.on_minimize_to_tray:
            self.on_minimize_to_tray()
        else:
            self._on_close_app()

    def _on_close_app(self):
        """Fecha o app de verdade."""
        if self.on_close_app:
            self.on_close_app()
        else:
            self.root.destroy()

    # ==========================================================================
    # Métodos chamados pelo tray
    # ==========================================================================

    def show_window(self):
        """Chamado pelo tray pra reabrir a janela principal."""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception as e:
            log.error(f"Erro ao mostrar janela: {e}")

    def hide_to_tray(self):
        """Esconde a janela (vai pra tray)."""
        try:
            self.root.withdraw()
        except Exception as e:
            log.error(f"Erro ao esconder janela: {e}")

    def toggle_lurker_external(self):
        """Chamado pelo tray quando user toggle Lurker pelo menu da bandeja."""
        new_state = not self.settings.get('lurker_mode', False)
        self.settings.set('lurker_mode', new_state)
        self.settings.save()
        # Atualiza UI no main thread
        self.root.after(0, self._refresh_lurker_button)
        self.root.after(0, self._set_status,
                        t("lurker.activated") + " (via tray)" if new_state else t("lurker.deactivated") + " (via tray)")

    # ==========================================================================
    # Lurker Button
    # ==========================================================================

    def _build_lurker_button(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        frame.pack(fill='x', side='top', padx=10, pady=8)

        self.lurker_btn = ctk.CTkButton(
            frame, text="", height=50,
            font=('Segoe UI', 13, 'bold'),
            corner_radius=8,
            command=self._toggle_lurker_mode,
        )
        self.lurker_btn.pack(fill='x')
        self._refresh_lurker_button()

    def _refresh_lurker_button(self):
        theme = self._t
        active = self.settings.get('lurker_mode', False)
        if active:
            self.lurker_btn.configure(
                text=t("lurker.active"),
                fg_color=theme['highlight'], hover_color=theme['accent_hover'],
                text_color=theme['text_on_highlight'],
            )
        else:
            self.lurker_btn.configure(
                text=t("lurker.inactive"),
                fg_color=theme['danger_bg'], hover_color=theme['danger_hover'],
                text_color="#ffe0e0",
            )

    def _toggle_lurker_mode(self):
        new_state = not self.settings.get('lurker_mode', False)
        self.settings.set('lurker_mode', new_state)
        self.settings.save()
        self._refresh_lurker_button()
        self._set_status(t("lurker.activated") if new_state else t("lurker.deactivated"))

    # ==========================================================================
    # Helpers de UI
    # ==========================================================================

    def _section_header(self, parent, text, with_separator_above=True):
        """
        Cria um header de seção. Por default, retorna um Frame contendo:
          - Linha separadora 1px bege sutil (acima)
          - Label do header

        Quando with_separator_above=False, retorna só o Label (usado pra
        primeira seção de cada aba — não precisa de separador acima dela).

        v1.0.24: separadores entre seções pra organização visual.
        """
        if not with_separator_above:
            # Comportamento original: só o label
            return ctk.CTkLabel(
                parent, text=text, text_color=self._t['accent'],
                font=('Segoe UI', 14, 'bold'),
            )

        # v1.0.24: container com separator + label, retorna o container
        # (chamada .pack() no container empacota tudo junto)
        container = ctk.CTkFrame(parent, fg_color="transparent")
        # Separator 1px bege sutil (mesmo cálculo do overlay)
        sep_color = self._compute_section_separator_color()
        sep = tk.Frame(container, height=1, bg=sep_color)
        sep.pack(fill='x', side='top', pady=(0, SPACING_MD))
        # Label do header
        lbl = ctk.CTkLabel(
            container, text=text, text_color=self._t['accent'],
            font=('Segoe UI', 14, 'bold'),
        )
        lbl.pack(anchor='w')
        return container

    def _compute_section_separator_color(self) -> str:
        """
        Calcula cor do separador entre seções: bege sutil (mistura bg+fg do tema).
        Mesmo princípio do overlay (_compute_highlight_color), garantindo
        coerência visual em toda a app.
        """
        bg = self._t.get('bg', '#1a1614')
        fg = self._t.get('text', '#D5CFAA')

        def hex_to_rgb(c):
            c = c.lstrip('#')
            if len(c) == 3:
                c = ''.join(ch * 2 for ch in c)
            return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

        try:
            bg_rgb = hex_to_rgb(bg)
            fg_rgb = hex_to_rgb(fg)
            mixed = tuple(int(b * 0.78 + f * 0.22) for b, f in zip(bg_rgb, fg_rgb))
            return '#{:02x}{:02x}{:02x}'.format(*mixed)
        except Exception:
            return '#3a3324'  # fallback bege escuro

    def _label(self, parent, text, dim=False, **kwargs):
        return ctk.CTkLabel(
            parent, text=text,
            text_color=self._t['text_dim'] if dim else self._t['text'],
            font=('Segoe UI', 11) if dim else ('Segoe UI', 12),
            **kwargs,
        )

    def _primary_button(self, parent, text, command, **kwargs):
        theme = self._t
        return ctk.CTkButton(
            parent, text=text, command=command,
            fg_color=theme['accent'], hover_color=theme['accent_hover'],
            text_color=theme['text_on_accent'], font=('Segoe UI', 13, 'bold'),
            corner_radius=6, height=38, **kwargs,
        )

    def _secondary_button(self, parent, text, command, **kwargs):
        theme = self._t
        return ctk.CTkButton(
            parent, text=text, command=command,
            fg_color=theme['bg_pill'], hover_color=theme['bg_hover'],
            text_color=theme['text'], font=('Segoe UI', 12),
            corner_radius=6, height=36, **kwargs,
        )

    def _entry(self, parent, **kwargs):
        theme = self._t
        return ctk.CTkEntry(
            parent, fg_color=theme['bg_input'], text_color=theme['text'],
            border_color=theme['border'], border_width=1,
            corner_radius=6, height=36, font=('Segoe UI', 12), **kwargs,
        )

    def _combo(self, parent, variable, values, **kwargs):
        theme = self._t
        return ctk.CTkComboBox(
            parent, variable=variable, values=values, state='readonly',
            fg_color=theme['bg_input'], button_color=theme['accent'],
            button_hover_color=theme['accent_hover'],
            text_color=theme['text'], border_color=theme['border'], border_width=1,
            dropdown_fg_color=theme['bg_input'], dropdown_text_color=theme['text'],
            dropdown_hover_color=theme['bg_hover'],
            corner_radius=6, height=36, font=('Segoe UI', 12), **kwargs,
        )

    def _checkbox(self, parent, text, variable, **kwargs):
        theme = self._t
        return ctk.CTkCheckBox(
            parent, text=text, variable=variable,
            text_color=theme['text'], font=('Segoe UI', 12),
            fg_color=theme['accent'], hover_color=theme['bg_hover'],
            checkbox_height=22, checkbox_width=22, corner_radius=4,
            **kwargs,
        )

    def _radio(self, parent, text, variable, value, **kwargs):
        theme = self._t
        return ctk.CTkRadioButton(
            parent, text=text, variable=variable, value=value,
            text_color=theme['text'], fg_color=theme['accent'], hover_color=theme['accent_hover'],
            radiobutton_height=22, radiobutton_width=22, font=('Segoe UI', 12),
            **kwargs,
        )

    # ==========================================================================
    # Tab: Captura
    # ==========================================================================

    def _build_capture_tab(self, parent):
        """v1.0.30: espaçamento profissional + auto-apply no intervalo."""
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        frame.pack(fill='both', expand=True, padx=(SPACING_LG, 0), pady=SPACING_LG)  # v1.0.31: scrollbar cola na direita

        self._auto_apply.silent(True)

        self._section_header(frame, t("capture.section.perimeter"),
                             with_separator_above=False).pack(anchor='w')
        self._label(frame, t("capture.perimeter_help"),
                    justify='left').pack(anchor='w', pady=(SPACING_SM, SPACING_SM))

        self.perimeter_label = self._label(frame, self._perimeter_text(), dim=True)
        self.perimeter_label.pack(anchor='w')

        self._secondary_button(
            frame, t("capture.btn.set_perimeter"), self._set_perimeter,
        ).pack(anchor='w', pady=(SPACING_SM, SPACING_XL))

        self._section_header(frame, t("capture.section.chatbar")).pack(anchor='w')
        self._label(frame, t("capture.chatbar_help"),
                    justify='left').pack(anchor='w', pady=(SPACING_SM, SPACING_SM))

        self.chatbar_label = self._label(frame, self._chatbar_text(), dim=True)
        self.chatbar_label.pack(anchor='w')

        self._secondary_button(
            frame, t("capture.btn.set_chatbar"), self._set_chat_bar,
        ).pack(anchor='w', pady=(SPACING_SM, SPACING_XL))

        self._section_header(frame, t("capture.section.start")).pack(anchor='w')

        ctl = ctk.CTkFrame(frame, fg_color="transparent")
        ctl.pack(fill='x', pady=(SPACING_SM, 0))

        self.capture_btn = self._primary_button(
            ctl, t("capture.btn.start"), self._toggle_capture,
        )
        self.capture_btn.pack(side='left')

        self._secondary_button(
            ctl, t("capture.btn.test_ocr"), self._open_test_ocr_dialog,
        ).pack(side='left', padx=(SPACING_MD, 0))

        interval_frame = ctk.CTkFrame(frame, fg_color="transparent")
        interval_frame.pack(fill='x', pady=(SPACING_LG, 0))
        self._label(interval_frame, t("capture.label.interval")).pack(side='left')

        self.interval_var = tk.DoubleVar(value=self.settings.get('check_interval', 1.0))
        interval_entry = self._entry(interval_frame, width=80, textvariable=self.interval_var)
        interval_entry.pack(side='left', padx=SPACING_MD)
        # v1.0.30: auto-apply com debounce (user digita 1.5)
        self._auto_apply.bind(
            self.interval_var, 'check_interval',
            label=t('config.label.capture_interval'),
            apply_fn=self._on_interval_change,
            debounce_ms=600,
            validator=lambda v: float(v) if 0.1 <= float(v) <= 60 else None,
        )

        self._auto_apply.silent(False)

    def _perimeter_text(self):
        p = self.settings.get('perimeter')
        return t("capture.perimeter.current", x1=p[0], y1=p[1], x2=p[2], y2=p[3]) if p else t("capture.perimeter.not_set")

    def _chatbar_text(self):
        c = self.settings.get('chat_bar')
        return t("capture.chatbar.current", x=c[0], y=c[1]) if c else t("capture.perimeter.not_set")

    def _set_perimeter(self):
        """
        Captura perímetro do chat usando tecla F2 obrigatória (Sub-bloco 3.2 v2).

        Mudança v1.0.20: F2 é OBRIGATÓRIO (não há mais fallback de "segurar 2s").
        O 2s anterior causava captura indesejada quando o user soltava o mouse
        pra fazer outra coisa. Agora a captura SÓ dispara com F2.

        UX: tooltip flutuante segue o mouse com instrução visual da tecla F2.
        """
        from f2_tooltip import F2Tooltip
        from selection_preview import show_selection_preview

        coords = []
        tooltip = F2Tooltip(self.root, self.settings)

        def capture_corner_with_f2_only(label_key, on_done):
            """
            Aguarda F2 ser apertado. SEM fallback de 2s.
            User precisa apertar F2 explicitamente — anti-erro.
            """
            self._set_status(t(label_key))
            tooltip.show(t(label_key))

            try:
                import pyautogui
                import keyboard
            except ImportError as e:
                log.error(f"Lib não disponível: {e}")
                tooltip.hide()
                return

            f2_state = {'pressed': False, 'pos': None}

            def on_f2():
                """Callback quando F2 é pressionado."""
                if not f2_state['pressed']:
                    f2_state['pressed'] = True
                    f2_state['pos'] = pyautogui.position()
                    log.info(f"F2 pressionado, posição capturada: {f2_state['pos']}")
                    # Flash visual no tooltip (700ms de feedback)
                    # NÃO precisa de on_done aqui — o controle do timing é feito
                    # após o while loop, com sleep adicional pra dar pausa entre cantos
                    try:
                        tooltip.flash_capture()
                    except Exception:
                        pass

            try:
                keyboard.add_hotkey('f2', on_f2)
            except Exception as e:
                log.error(f"F2 hotkey falhou: {e}")
                tooltip.hide()
                self._set_status(t("capture.msg.f2_hotkey_failed"))
                return

            # Loop esperando APENAS F2 (sem timeout de 2s)
            # User pode mover o mouse à vontade entre apertos.
            try:
                while not f2_state['pressed']:
                    self.root.update()
                    time.sleep(0.02)
            finally:
                # Sempre limpa o hotkey, mesmo em erro
                try:
                    keyboard.remove_hotkey('f2')
                except Exception:
                    pass

            # Aguarda o flash visual completar antes de prosseguir.
            # Flash dura 700ms; esperamos 750ms pra garantir que terminou
            # e o user viu o "✓ Capturado!" claramente.
            wait_until = time.time() + 0.75
            while time.time() < wait_until:
                self.root.update()
                time.sleep(0.02)

            on_done(f2_state['pos'])

        def step_one():
            def after_corner_1(pos):
                if pos is None:
                    tooltip.hide()
                    return
                coords.append(pos)
                # Pausa intencional + atualiza tooltip pra próximo passo
                # com texto DIFERENTE ("Agora aponte...") pra deixar claro
                # que mudou de etapa.
                self.root.after(200, step_two)

            capture_corner_with_f2_only("capture.msg.top_left_f2_required", after_corner_1)

        def step_two():
            def after_corner_2(pos):
                if pos is None:
                    tooltip.hide()
                    return
                coords.append(pos)
                tooltip.hide()

                x1, y1 = coords[0]
                x2, y2 = coords[1]
                if x2 < x1:
                    x1, x2 = x2, x1
                if y2 < y1:
                    y1, y2 = y2, y1
                self.settings.set('perimeter', [int(x1), int(y1), int(x2), int(y2)])
                self.perimeter_label.configure(text=self._perimeter_text())
                self._set_status(t("capture.msg.perimeter_set", x1=x1, y1=y1, x2=x2, y2=y2))

                # Glimpse visual do retângulo selecionado (1.5s)
                try:
                    show_selection_preview(self.root, int(x1), int(y1), int(x2), int(y2), duration_ms=1500)
                except Exception as e:
                    log.error(f"Erro no preview de seleção (não crítico): {e}")

            capture_corner_with_f2_only("capture.msg.bottom_right_f2_required", after_corner_2)

        self.root.after(100, step_one)

    def _set_chat_bar(self):
        """
        Captura posição da barra de chat usando F2 obrigatório (Sub-bloco 3.2 v2).
        F2 é a ÚNICA forma de capturar — sem fallback de 2s. Tooltip flutuante
        guia o user.
        """
        from f2_tooltip import F2Tooltip

        def go():
            try:
                import pyautogui
                import keyboard
            except ImportError as e:
                self._set_status(t("popup.msg.error", err=e))
                return

            tooltip = F2Tooltip(self.root, self.settings)
            tooltip.show(t("capture.msg.point_chatbar_f2_required"))
            self._set_status(t("capture.msg.point_chatbar_f2_required"))

            f2_state = {'pressed': False, 'pos': None}

            def on_f2():
                if not f2_state['pressed']:
                    f2_state['pressed'] = True
                    f2_state['pos'] = pyautogui.position()
                    try:
                        tooltip.flash_capture()
                    except Exception:
                        pass

            try:
                keyboard.add_hotkey('f2', on_f2)
            except Exception as e:
                tooltip.hide()
                self._set_status(t("capture.msg.f2_hotkey_failed"))
                return

            try:
                while not f2_state['pressed']:
                    self.root.update()
                    time.sleep(0.02)

                # v1.0.22: aguarda flash visual completar (700ms + 50ms margem)
                # antes de fechar o tooltip. Sem isso, tooltip some na hora e
                # user não vê "✓ Capturado!".
                wait_until = time.time() + 0.75
                while time.time() < wait_until:
                    self.root.update()
                    time.sleep(0.02)

                last_pos = f2_state['pos']
                self.settings.set('chat_bar', [int(last_pos[0]), int(last_pos[1])])
                self.chatbar_label.configure(text=self._chatbar_text())
                self._set_status(t("capture.msg.chatbar_set", x=last_pos[0], y=last_pos[1]))
            except Exception as e:
                self._set_status(t("popup.msg.error", err=e))
            finally:
                tooltip.hide()
                try:
                    keyboard.remove_hotkey('f2')
                except Exception:
                    pass

        self.root.after(100, go)

    def _on_overlay_hidden(self):
        """
        Callback do overlay quando ele é fechado (X da titlebar do overlay).

        O overlay já parou a captura — aqui atualizamos o botão "Iniciar/Parar"
        pra refletir o estado real (volta pra "Iniciar Tradução").

        Bug que esse fix resolve: antes o botão ficava preso em "Parar Tradução"
        mesmo após fechar o overlay, dando impressão de captura ativa.
        """
        try:
            if hasattr(self, 'capture_btn') and self.capture_btn.winfo_exists():
                self.capture_btn.configure(text=t("capture.btn.start"))
            self._set_status(t("capture.msg.stop"))
        except Exception as e:
            log.error(f"Erro ao sincronizar botão após overlay hide: {e}")

    # ========================================================================
    # Sub-bloco 3.2 — Hotkeys: toggle_overlay e toggle_lurker_from_hotkey
    # ========================================================================

    def toggle_overlay(self):
        """
        Chamado pelo hotkey de overlay (Ctrl+Shift+O por padrão).

        Comportamento de toggle em 3 estados:
          1. Overlay invisível, sem mini-pill → mostra overlay (start_capture)
          2. Overlay visível → colapsa pra mini-pill (preserva posição)
          3. Mini-pill visível → expande pro overlay (na posição do pill)
        """
        try:
            # Caso 3: mini-pill visível → expande
            if self._mini_pill.is_visible():
                self._expand_overlay_from_pill()
                return

            # Caso 2: overlay visível → colapsa pro mini-pill
            if self.overlay.is_visible():
                self._collapse_overlay_to_pill()
                return

            # Caso 1: nada visível → comportamento normal de "Iniciar Tradução"
            self._toggle_capture()
        except Exception as e:
            log.error(f"Erro em toggle_overlay: {e}", exc_info=True)

    def _collapse_overlay_to_pill(self):
        """Esconde overlay e mostra mini-pill na mesma posição."""
        try:
            # Pega posição atual do overlay (preserva contexto)
            x, y = self.overlay.get_position()

            # Esconde overlay (mas mantém captura rodando!)
            # IMPORTANTE: NÃO usar self.overlay.hide() aqui porque ele para a
            # captura. Queremos que o mini-pill continue recebendo updates.
            if self.overlay.window and self.overlay.window.winfo_exists():
                self.overlay.window.withdraw()

            # Mostra mini-pill onde o overlay estava
            self._mini_pill.show(x=x, y=y)
            log.info(f"Overlay colapsado pra mini-pill em ({x}, {y})")
        except Exception as e:
            log.error(f"Erro ao colapsar overlay: {e}", exc_info=True)

    def _expand_overlay_from_pill(self):
        """Esconde mini-pill e mostra overlay (na posição do pill)."""
        try:
            # Pega posição atual do pill + quantas linhas chegaram durante o colapso
            px, py = self._mini_pill.get_position()
            new_lines_count = self._mini_pill.get_badge_count()

            self._mini_pill.hide()

            # Re-mostra o overlay
            # Tenta ajustar pra posição do pill (preserva contexto visual)
            if self.overlay.window and self.overlay.window.winfo_exists():
                self.overlay.window.geometry(f"+{px}+{py}")
                self.overlay.window.deiconify()
                self.overlay.window.lift()
            else:
                # Se overlay nem existia, faz show normal
                self.overlay.show()

            # v1.0.21: destaca visualmente as N linhas novas que chegaram
            # enquanto estava colapsado. Background sutil por 5s.
            if new_lines_count > 0:
                # Pequeno delay pra garantir que o overlay renderizou
                self.root.after(100, lambda: self.overlay.highlight_existing_recent(
                    count=new_lines_count, duration_ms=5000
                ))

            log.info(f"Mini-pill expandido pro overlay em ({px}, {py}), destacando {new_lines_count} linhas")
        except Exception as e:
            log.error(f"Erro ao expandir mini-pill: {e}", exc_info=True)

    def _on_mini_pill_clicked(self):
        """Callback do mini-pill quando user clica nele (pra expandir)."""
        self._expand_overlay_from_pill()

    def _on_overlay_new_line(self, line: str):
        """Callback do overlay quando uma nova linha é capturada.
        Incrementa badge do mini-pill se estiver visível."""
        try:
            if self._mini_pill.is_visible():
                self._mini_pill.increment_badge()
        except Exception as e:
            log.debug(f"_on_overlay_new_line falhou: {e}")

    def toggle_lurker_from_hotkey(self):
        """
        Chamado pelo hotkey de Lurker (Ctrl+Shift+L por padrão).

        Wrapper público pra _toggle_lurker_mode (que é privado/protegido).
        """
        try:
            self._toggle_lurker_mode()
        except Exception as e:
            log.error(f"Erro em toggle_lurker_from_hotkey: {e}", exc_info=True)

    def _capture_hotkey_for(self, hotkey_id: str, setting_key: str, entry_widget):
        """
        Abre o popup de captura de hotkey pra um id específico.
        Quando captura ok, atualiza o entry + valida conflito + salva.

        Args:
            hotkey_id: 'quick_input' | 'overlay_toggle' | 'lurker_toggle'
            setting_key: chave nas settings (ex: 'hotkey_quick_input')
            entry_widget: campo de texto que será atualizado com a nova hotkey
        """
        from hotkey_capture_popup import HotkeyCapturePopup
        from tkinter import messagebox

        popup = HotkeyCapturePopup(self.root, self.settings)

        def on_captured(new_hotkey: str):
            # Validação de conflito (decisão do user: BLOQUEIA + erro)
            conflict_id = self.hotkey_mgr.is_conflict(new_hotkey, exclude_id=hotkey_id)
            if conflict_id:
                from hotkey_manager import HOTKEY_IDS
                conflict_desc = HOTKEY_IDS.get(conflict_id, {}).get('description', conflict_id)
                messagebox.showerror(
                    t("hotkey.capture.title"),
                    t("hotkey.capture.error_conflict") +
                    f"\n\n({conflict_desc} = {self.settings.get(HOTKEY_IDS[conflict_id]['setting_key'], '?')})",
                )
                log.warning(f"Hotkey conflito: {new_hotkey} já usado por {conflict_id}")
                return

            # Atualiza UI
            try:
                entry_widget.delete(0, 'end')
                entry_widget.insert(0, new_hotkey)
            except Exception as e:
                log.error(f"Erro ao atualizar entry: {e}")

            # Salva nas settings + reload do hotkey_mgr
            self.settings.set(setting_key, new_hotkey)
            self.settings.save()
            self.hotkey_mgr.reload()
            self._set_status(t("shortcut.msg.hotkey_set", hotkey=new_hotkey))
            log.info(f"Hotkey '{hotkey_id}' atualizada pra: {new_hotkey}")

        def on_cancel():
            log.debug(f"Captura de hotkey '{hotkey_id}' cancelada")

        popup.show(on_captured=on_captured, on_cancel=on_cancel)

    def _toggle_capture(self):
        if self.overlay.is_capturing():
            self.overlay.stop_capture()
            self.capture_btn.configure(text=t("capture.btn.start"))
            self._set_status(t("capture.msg.stop"))
        else:
            if not self.settings.get('perimeter'):
                messagebox.showerror(t("title.error"), t("capture.msg.no_perimeter"))
                return
            self.overlay.show()
            self.overlay.start_capture()
            self.capture_btn.configure(text=t("capture.btn.stop"))
            self._set_status(t("capture.msg.start"))

    def _on_interval_change(self):
        try:
            self.settings.set('check_interval', float(self.interval_var.get()))
        except (ValueError, tk.TclError):
            pass

    def _open_test_ocr_dialog(self):
        if not self.settings.get('perimeter'):
            messagebox.showerror(t("title.error"), t("capture.msg.no_perimeter"))
            return

        self._set_status("Executando teste de OCR...")
        result = self.ocr.debug_capture()

        theme = self._t
        win = ctk.CTkToplevel(self.root)
        win.title(t("title.test_ocr"))
        from monitor_utils import center_window_on_parent
        center_window_on_parent(win, self.root, 720, 580)
        win.configure(fg_color=theme['bg'])

        apply_custom_titlebar(
            win, t("title.test_ocr"),
            on_close=win.destroy, show_minimize=False, resizable=True,
            bg_color=theme['bg'], bg_titlebar=theme['titlebar_bg'],
            fg=theme['text'], accent=theme['accent'],
            bg_button_hover=theme['bg_hover'],
            close_hover_bg=theme['titlebar_close_hover'],
            min_width=500, min_height=400,
        )

        # Re-aplica ícone via Win32 DEPOIS da custom titlebar
        win.after(300, lambda: apply_icon_via_win32(win))
        win.after(800, lambda: apply_icon_via_win32(win))

        ctk.CTkLabel(win, text=t("title.test_ocr"),
                     text_color=theme['accent'], font=('Segoe UI', 15, 'bold')
                     ).pack(anchor='w', padx=18, pady=(10, 6))

        tess_color = '#90ee90' if result['tesseract_ok'] else theme['highlight']
        ctk.CTkLabel(win, text=f"Tesseract: {result['tesseract_msg']}",
                     text_color=tess_color, justify='left',
                     wraplength=680, anchor='w', font=('Segoe UI', 12)
                     ).pack(anchor='w', padx=18, pady=2)

        ctk.CTkLabel(win, text=f"Perímetro: {result['perimeter']}",
                     text_color=theme['text'], anchor='w', font=('Segoe UI', 12)
                     ).pack(anchor='w', padx=18, pady=2)

        if result['image_size']:
            ctk.CTkLabel(win, text=f"Tamanho da imagem: {result['image_size']}",
                         text_color=theme['text'], anchor='w', font=('Segoe UI', 12)
                         ).pack(anchor='w', padx=18, pady=2)

        if result['error']:
            ctk.CTkLabel(win, text=f"⚠️ Erro: {result['error']}",
                         text_color=theme['highlight'], wraplength=680,
                         justify='left', anchor='w', font=('Segoe UI', 12)
                         ).pack(anchor='w', padx=18, pady=5)

        ctk.CTkLabel(win, text=f"Texto extraído ({result['lines_count']} linhas):",
                     text_color=theme['accent'], font=('Segoe UI', 13, 'bold'),
                     anchor='w').pack(anchor='w', padx=18, pady=(10, 2))

        text_box = scrolledtext.ScrolledText(
            win, height=12, bg=theme['bg_input'], fg=theme['text'],
            font=('Consolas', 12), relief='flat', wrap='word',
        )
        text_box.pack(fill='both', expand=True, padx=18, pady=(0, 10))
        text_box.insert(tk.END, result['raw_text'] if result['raw_text'] else "(vazio)")
        text_box.config(state='disabled')

        if result['raw_image_path']:
            ctk.CTkLabel(win, text=f"📂 Imagens em: {result['raw_image_path']}",
                         text_color=theme['text_dim'], font=('Segoe UI', 10),
                         wraplength=680, justify='left', anchor='w'
                         ).pack(anchor='w', padx=18, pady=(0, 6))

        self._primary_button(win, t("btn.close"), win.destroy).pack(pady=(0, 14))

        self._set_status(f"Teste OCR: {result['lines_count']} linhas extraídas.")

    # ==========================================================================
    # Tab: Tradução
    # ==========================================================================

    def _build_translation_tab(self, parent):
        """v1.0.30: auto-apply + sem botão Apply + espaçamento profissional."""
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        frame.pack(fill='both', expand=True, padx=(SPACING_LG, 0), pady=SPACING_LG)  # v1.0.31: scrollbar cola na direita

        self._auto_apply.silent(True)

        # === Modo de leitura (FR → PT) ===
        self._section_header(frame, t("translation.section.read_mode"),
                             with_separator_above=False).pack(anchor='w')

        rd = ctk.CTkFrame(frame, fg_color="transparent")
        rd.pack(fill='x', pady=(SPACING_SM, SPACING_XL))
        self._label(rd, t("translation.label.from")).pack(side='left')
        self.src_read = tk.StringVar(value=self.settings.get('source_language_read', 'fr'))
        self._combo(rd, self.src_read, list(LANGUAGES.keys()), width=90).pack(side='left', padx=SPACING_SM)
        self._label(rd, t("translation.label.to")).pack(side='left', padx=(SPACING_LG, 0))
        self.dest_read = tk.StringVar(value=self.settings.get('target_language_read', 'pt'))
        self._combo(rd, self.dest_read, list(LANGUAGES.keys()), width=90).pack(side='left', padx=SPACING_SM)

        self._auto_apply.bind(self.src_read, 'source_language_read',
                              label='Idioma origem (leitura)')
        self._auto_apply.bind(self.dest_read, 'target_language_read',
                              label='Idioma destino (leitura)')

        # === Modo de escrita (PT → FR) ===
        self._section_header(frame, t("translation.section.write_mode")).pack(anchor='w')

        wd = ctk.CTkFrame(frame, fg_color="transparent")
        wd.pack(fill='x', pady=(SPACING_SM, SPACING_XL))
        self._label(wd, t("translation.label.from")).pack(side='left')
        self.src_write = tk.StringVar(value=self.settings.get('source_language_write', 'pt'))
        self._combo(wd, self.src_write, list(LANGUAGES.keys()), width=90).pack(side='left', padx=SPACING_SM)
        self._label(wd, t("translation.label.to")).pack(side='left', padx=(SPACING_LG, 0))
        self.dest_write = tk.StringVar(value=self.settings.get('target_language_write', 'fr'))
        self._combo(wd, self.dest_write, list(LANGUAGES.keys()), width=90).pack(side='left', padx=SPACING_SM)

        self._auto_apply.bind(self.src_write, 'source_language_write',
                              label='Idioma origem (escrita)')
        self._auto_apply.bind(self.dest_write, 'target_language_write',
                              label='Idioma destino (escrita)')

        # === OCR ===
        self._section_header(frame, t("translation.section.ocr_lang")).pack(anchor='w')
        self.ocr_lang = tk.StringVar(value=self.settings.get('ocr_language', 'fra'))
        self._combo(frame, self.ocr_lang, ['fra', 'eng', 'spa', 'por'], width=130
                    ).pack(anchor='w', pady=(SPACING_SM, SPACING_XL))
        self._auto_apply.bind(self.ocr_lang, 'ocr_language', label='Idioma OCR')

        # === Backend ===
        self._section_header(frame, t("translation.section.backend")).pack(anchor='w')
        self.backend_var = tk.StringVar(value=self.settings.get('translator_backend', 'google'))
        bf = ctk.CTkFrame(frame, fg_color="transparent")
        bf.pack(fill='x', pady=(SPACING_SM, SPACING_LG))
        for label, value in [("Google (gratuito)", "google"), ("DeepL (premium)", "deepl")]:
            self._radio(bf, label, self.backend_var, value).pack(side='left', padx=(0, SPACING_MD))
        self._auto_apply.bind(self.backend_var, 'translator_backend', label='Backend de tradução')

        self._label(frame, "DeepL API Key (opcional):").pack(anchor='w', pady=(0, SPACING_SM))
        self.deepl_key_var = tk.StringVar(value=self.settings.get('deepl_api_key', ''))
        self.deepl_key = self._entry(frame, textvariable=self.deepl_key_var)
        self.deepl_key.pack(fill='x', pady=(0, SPACING_XL))
        self._auto_apply.bind(self.deepl_key_var, 'deepl_api_key',
                              label='DeepL API Key', debounce_ms=800)

        # === Termos Personalizados ===
        self._section_header(frame, t("translation.section.custom_terms")).pack(anchor='w')
        self._label(frame,
                    t("translation.custom_terms.help"),
                    dim=True, wraplength=520, justify='left').pack(anchor='w', pady=(SPACING_SM, SPACING_MD))
        self._secondary_button(
            frame, t("translation.btn.manage_terms"),
            self.custom_terms_popup.show,
        ).pack(anchor='w', pady=(0, SPACING_LG))

        self._auto_apply.silent(False)

    def _apply_translation_settings(self):
        self.settings.update(
            source_language_read=self.src_read.get(),
            target_language_read=self.dest_read.get(),
            source_language_write=self.src_write.get(),
            target_language_write=self.dest_write.get(),
            ocr_language=self.ocr_lang.get(),
            translator_backend=self.backend_var.get(),
            deepl_api_key=self.deepl_key.get().strip(),
        )
        self.settings.save()
        self._set_status(t("translation.msg.applied"))

    # ==========================================================================
    # Tab: Aparência
    # ==========================================================================

    def _build_appearance_tab(self, parent):
        """
        Bloco 3.3 v3 (v1.0.30): Aparência LINEAR + auto-apply + sem botão Apply.

        Mudanças v1.0.30:
          - Removido o botão "Aplicar e Salvar" — config aplica auto via trace
          - Auto-apply em todas as vars (toast aparece a cada mudança)
          - Espaçamentos profissionais (mais respiro entre seções)
          - Idioma e tema do app mostram toast warning de "reabra o app"

        Estrutura:
          - Tema do app (auto-apply, requires_restart)
          - Idioma (auto-apply, requires_restart)
          - Tema do overlay (3 presets, auto-apply)
          - Transparência (slider, auto-apply)
          - Always on top (auto-apply)
          - Preview ao vivo
          - ▶ Customização avançada (cores, fonte, tamanho)
        """
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        frame.pack(fill='both', expand=True,
                   padx=(SPACING_LG, 0), pady=SPACING_LG)  # v1.0.31: scrollbar cola na direita

        # Sentinel pra suprimir auto-apply durante o setup das vars
        self._auto_apply.silent(True)

        # === Tema do app ===
        self._section_header(frame, t("appearance.section.app_theme"),
                             with_separator_above=False).pack(anchor='w')
        self._label(frame, "Reabra o app pra aplicação completa do tema.",
                    dim=True).pack(anchor='w', pady=(0, SPACING_SM))

        self.main_theme_var = tk.StringVar(value=self.settings.get('main_window_theme', 'dofus_retro'))
        main_themes_frame = ctk.CTkFrame(frame, fg_color="transparent")
        main_themes_frame.pack(fill='x', pady=(SPACING_SM, SPACING_XL))
        for name in list_theme_names():
            self._radio(
                main_themes_frame, THEME_LABELS.get(name, name),
                self.main_theme_var, name,
            ).pack(side='left', padx=(0, SPACING_MD))

        self._auto_apply.bind(
            self.main_theme_var, 'main_window_theme',
            label=t('config.label.app_theme'),
            requires_restart=True,
        )

        # === Idioma do app ===
        self._section_header(frame, t('appearance.section.ui_lang')).pack(anchor='w', pady=(SPACING_LG, 0))
        self._label(frame,
                    "Idioma usado nos menus, botões e mensagens do app. "
                    "Trocar requer reabrir o app.",
                    dim=True, wraplength=520).pack(anchor='w', pady=(0, SPACING_SM))

        supported = get_supported_languages()
        self._lang_labels_to_codes = {get_language_label(c): c for c in supported}
        self._lang_codes_to_labels = {c: get_language_label(c) for c in supported}
        current_lang = self.settings.get('ui_language', 'pt')
        self.ui_lang_var = tk.StringVar(
            value=self._lang_codes_to_labels.get(current_lang, get_language_label('pt'))
        )
        self._combo(
            frame, self.ui_lang_var,
            list(self._lang_labels_to_codes.keys()),
            width=240,
        ).pack(anchor='w', pady=(0, SPACING_XL))

        def apply_lang():
            label = self.ui_lang_var.get()
            code = self._lang_labels_to_codes.get(label, 'pt')
            self.settings.set('ui_language', code)
            self.settings.save()

        self._auto_apply.bind(
            self.ui_lang_var, 'ui_language',
            label=t('config.label.app_language'),
            apply_fn=apply_lang,
            requires_restart=True,
        )

        # === Tema do overlay ===
        self._section_header(frame, t("appearance.section.overlay_theme")).pack(anchor='w', pady=(0, 0))

        self.theme_var = tk.StringVar(value=self.settings.get('overlay_theme_preset', 'dofus_retro'))

        self._theme_radios_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self._theme_radios_frame.pack(fill='x', pady=(SPACING_SM, SPACING_XL))
        for name, label in [
            ('dark', 'Dark'), ('light', 'Light'),
            ('dofus_retro', 'Dofus Retro'),
        ]:
            self._radio(self._theme_radios_frame, label, self.theme_var, name,
                        command=self._update_preview).pack(side='left', padx=(0, SPACING_MD))

        self._auto_apply.bind(
            self.theme_var, 'overlay_theme_preset',
            label=t('config.label.overlay_theme'),
            apply_fn=lambda: (self._update_preview(), self._apply_overlay_theme_live()),
        )

        # === Transparência do overlay ===
        self._label(frame, t("appearance.section.overlay_alpha")).pack(anchor='w', pady=(0, SPACING_SM))
        self.alpha_var = tk.DoubleVar(value=self.settings.get('overlay_alpha', 0.92))
        ctk.CTkSlider(
            frame, from_=0.2, to=1.0, variable=self.alpha_var,
            fg_color=self._t['bg_input'], progress_color=self._t['accent'],
            button_color=self._t['accent'], button_hover_color=self._t['accent_hover'],
            height=18, command=lambda v: self._update_overlay_alpha(),
        ).pack(fill='x', pady=(0, SPACING_XL))

        self._auto_apply.bind(
            self.alpha_var, 'overlay_alpha',
            label=t('config.label.overlay_alpha'),
            apply_fn=self._update_overlay_alpha,
            debounce_ms=300,  # slider dispara muito, debounce pra não inundar
        )

        # === Always on top ===
        self.aot_var = tk.BooleanVar(value=self.settings.get('overlay_always_on_top', True))
        self._checkbox(frame, t("appearance.always_on_top"), self.aot_var
                       ).pack(anchor='w', pady=(0, SPACING_LG))

        self._auto_apply.bind(
            self.aot_var, 'overlay_always_on_top',
            label=t('config.label.always_on_top'),
            apply_fn=self._apply_overlay_always_on_top_live,
        )

        # === Preview ===
        self._section_header(frame, t("appearance.section.preview")).pack(anchor='w', pady=(0, SPACING_SM))
        self._build_preview_widget(frame)

        # === Expander: Customização avançada ===
        self._build_advanced_expander(frame)

        # Reativa auto-apply (terminado o setup)
        self._auto_apply.silent(False)

        self._populate_preview()
        self._update_preview()

    def _apply_overlay_theme_live(self):
        """Aplica o tema do overlay ao vivo, se ele estiver aberto."""
        if self.overlay.window and self.overlay.window.winfo_exists():
            try:
                self.overlay._apply_theme()
            except Exception as e:
                log.debug(f"Apply overlay theme falhou: {e}")

    def _apply_overlay_always_on_top_live(self):
        """Aplica AOT no overlay aberto."""
        if self.overlay.window and self.overlay.window.winfo_exists():
            try:
                self.overlay.window.attributes('-topmost', self.aot_var.get())
            except Exception as e:
                log.debug(f"Apply AOT falhou: {e}")

    def _build_advanced_expander(self, parent):
        """
        Expander colapsável "▶ Customização avançada" / "▼ Customização avançada".

        Container outer com header clicável + body que esconde/aparece via pack/pack_forget.
        Estado persiste em settings (appearance_advanced_expanded).

        v1.0.29: substitui as sub-abas Básico/Avançado da v1.0.28 que ficaram
        artificiais ("avançado pra inglês ver"). Expander é padrão moderno
        (VS Code, Figma, Photoshop) e mais natural.
        """
        # Container externo (sempre visível)
        outer = ctk.CTkFrame(parent, fg_color="transparent")
        outer.pack(fill='x', pady=(20, 0))

        # Linha separadora 1px bege sutil acima do expander (consistência visual)
        sep_color = self._compute_section_separator_color()
        tk.Frame(outer, height=1, bg=sep_color).pack(fill='x', pady=(0, SPACING_MD))

        # Header clicável (toggle)
        header_frame = ctk.CTkFrame(outer, fg_color="transparent")
        header_frame.pack(fill='x')

        self._adv_expanded = self.settings.get('appearance_advanced_expanded', False)

        # Ícone indicador (▶ colapsado / ▼ expandido) + label
        self._adv_chevron = ctk.CTkLabel(
            header_frame,
            text='▼' if self._adv_expanded else '▶',
            text_color=self._t['accent'],
            font=('Segoe UI', 12, 'bold'),
            width=20,
            cursor='hand2',
        )
        self._adv_chevron.pack(side='left', padx=(0, 4))

        adv_label_text = t("appearance.expander.advanced")
        self._adv_label = ctk.CTkLabel(
            header_frame,
            text=adv_label_text,
            text_color=self._t['accent'],
            font=('Segoe UI', 14, 'bold'),
            cursor='hand2',
        )
        self._adv_label.pack(side='left')

        # Hint (subtítulo dim)
        self._label(outer, t("appearance.expander.advanced_hint"),
                    dim=True, wraplength=520).pack(anchor='w', pady=(0, 6))

        # Body (conteúdo avançado) — pack/pack_forget controla visibilidade
        self._adv_body = ctk.CTkFrame(outer, fg_color="transparent")
        if self._adv_expanded:
            self._adv_body.pack(fill='x', pady=(4, 0))

        # === Conteúdo do body: 4º radio Custom + cores + fonte ===
        # v1.0.31: elementos centralizados pra diferenciar visualmente do
        # padrão das customizações normais (que ficam à esquerda)
        # Radio "Custom" extra (fora do _theme_radios_frame que tem só os 3 presets)
        custom_radio_frame = ctk.CTkFrame(self._adv_body, fg_color="transparent")
        custom_radio_frame.pack(anchor='center', pady=(0, 6))
        self._label(custom_radio_frame, "Tema overlay (extra):").pack(side='left', padx=(0, 8))
        self._radio(custom_radio_frame, 'Custom', self.theme_var, 'custom',
                    command=self._update_preview).pack(side='left')

        # Cores customizadas
        self.bg_color = self.settings.get('overlay_bg_color', '#1a1614')
        self.fg_color = self.settings.get('overlay_fg_color', '#D5CFAA')

        cf = ctk.CTkFrame(self._adv_body, fg_color="transparent")
        cf.pack(anchor='center', pady=(4, 0))

        self.bg_swatch = ctk.CTkButton(
            cf, text='Fundo overlay', width=140, height=36,
            fg_color=self.bg_color, hover_color=self.bg_color, text_color="#fff",
            corner_radius=6, border_width=1, border_color=self._t['border'],
            font=('Segoe UI', 12),
            command=lambda: self._pick_color('bg'),
        )
        self.bg_swatch.pack(side='left', padx=(0, 5))

        self.fg_swatch = ctk.CTkButton(
            cf, text='Texto overlay', width=140, height=36,
            fg_color=self.fg_color, hover_color=self.fg_color, text_color="#000",
            corner_radius=6, border_width=1, border_color=self._t['border'],
            font=('Segoe UI', 12),
            command=lambda: self._pick_color('fg'),
        )
        self.fg_swatch.pack(side='left', padx=5)

        # Fonte + Tamanho
        ff = ctk.CTkFrame(self._adv_body, fg_color="transparent")
        ff.pack(anchor='center', pady=(10, 0))
        self._label(ff, "Fonte:").pack(side='left')
        self.font_family = tk.StringVar(value=self.settings.get('overlay_font_family', 'Consolas'))
        font_combo = self._combo(
            ff, self.font_family,
            ['Consolas', 'Courier New', 'Segoe UI', 'Arial', 'Verdana', 'Georgia'],
            width=150,
        )
        font_combo.pack(side='left', padx=5)
        font_combo.configure(command=lambda choice: self._update_preview())

        self._label(ff, "Tamanho:").pack(side='left', padx=(SPACING_LG, 0))
        self.font_size = tk.IntVar(value=self.settings.get('overlay_font_size', 12))
        size_entry = self._entry(ff, textvariable=self.font_size, width=70)
        size_entry.pack(side='left', padx=SPACING_SM)
        size_entry.bind('<KeyRelease>', lambda e: self._update_preview())

        # === v1.0.30: Auto-apply nas vars do expander ===
        # font_family: muda no combo, dispara imediato
        self._auto_apply.bind(
            self.font_family, 'overlay_font_family',
            label=t('config.label.overlay_font'),
            apply_fn=lambda: (self._update_preview(), self._apply_overlay_theme_live()),
        )
        # font_size: digitado, debounce 500ms pra não disparar a cada keystroke
        self._auto_apply.bind(
            self.font_size, 'overlay_font_size',
            label=t('config.label.overlay_font_size'),
            apply_fn=lambda: (self._update_preview(), self._apply_overlay_theme_live()),
            debounce_ms=500,
            validator=lambda v: int(v) if str(v).strip().isdigit() and 6 <= int(v) <= 72 else None,
        )

        # Bind do toggle no chevron + label do header
        def toggle_advanced(event=None):
            self._adv_expanded = not self._adv_expanded
            if self._adv_expanded:
                self._adv_body.pack(fill='x', pady=(4, 0))
                self._adv_chevron.configure(text='▼')
            else:
                self._adv_body.pack_forget()
                self._adv_chevron.configure(text='▶')
            # Persiste estado
            self.settings.set('appearance_advanced_expanded', self._adv_expanded)
            self.settings.save()

        self._adv_chevron.bind('<Button-1>', toggle_advanced)
        self._adv_label.bind('<Button-1>', toggle_advanced)
        # Bind também no header_frame pra área toda ser clicável
        header_frame.bind('<Button-1>', toggle_advanced)

    def _build_preview_widget(self, parent):
        """
        Constrói o widget de preview do overlay com scrollbar custom.

        v1.0.29: simplificado pra um único widget (não há mais sub-abas).
        Mantém compat com `_populate_preview` e `_update_preview` que
        iteram sobre `_preview_widgets` (lista com 1 elemento agora).
        """
        # Inicializa lista (vazia) — manter pra compat com _populate/_update
        self._preview_widgets = []
        self._preview_scrollbars = []

        preview_frame = ctk.CTkFrame(
            parent, fg_color=self._t['bg_input'], corner_radius=6,
            border_width=1, border_color=self._t['border'],
        )
        preview_frame.pack(fill='both', expand=True, pady=(0, 10), ipady=4)

        from themed_scrollbar import ThemedScrollbar
        preview_inner = tk.Frame(preview_frame, bg=self._t.get('bg', '#1a1614'))
        preview_inner.pack(fill='both', expand=True, padx=2, pady=2)

        widget = tk.Text(
            preview_inner, height=8, wrap='word',
            relief='flat', borderwidth=0, padx=12, pady=10,
        )
        scrollbar = ThemedScrollbar(
            preview_inner, target_widget=widget,
            bg=self._t.get('bg', '#1a1614'),
            thumb=self._t.get('text_dim', '#8b7355'),
            thumb_hover=self._t.get('accent', '#c5a572'),
            width=8,
        )
        scrollbar.pack(side='right', fill='y')
        widget.pack(side='left', fill='both', expand=True)

        self.preview_widget = widget
        self._preview_scrollbar = scrollbar
        self._preview_widgets.append(widget)
        self._preview_scrollbars.append(scrollbar)

    def _populate_preview(self):
        """v1.0.28: popula TODOS os preview widgets (Básico + Avançado)."""
        widgets = getattr(self, '_preview_widgets', None) or [self.preview_widget]
        for widget in widgets:
            if not widget:
                continue
            try:
                widget.config(state='normal')
                widget.delete('1.0', tk.END)
                for line in PREVIEW_LINES:
                    widget.insert(tk.END, line + '\n')
                widget.config(state='disabled')
            except Exception:
                pass

    def _update_preview(self):
        """v1.0.28: atualiza TODOS os preview widgets + scrollbars."""
        widgets = getattr(self, '_preview_widgets', None) or ([self.preview_widget] if self.preview_widget else [])
        scrollbars = getattr(self, '_preview_scrollbars', None) or ([self._preview_scrollbar] if hasattr(self, '_preview_scrollbar') and self._preview_scrollbar else [])
        if not widgets:
            return

        preset_name = self.theme_var.get() if hasattr(self, 'theme_var') else 'dofus_retro'
        if preset_name == 'custom':
            bg_c = self.bg_color
            fg_c = self.fg_color
        else:
            preset = THEME_PRESETS.get(preset_name, THEME_PRESETS['dofus_retro'])
            bg_c = preset['bg']
            fg_c = preset['fg']

        try:
            font_family = self.font_family.get() if hasattr(self, 'font_family') else 'Consolas'
            font_size = self.font_size.get() if hasattr(self, 'font_size') else 12
        except Exception:
            font_family, font_size = 'Consolas', 12

        # Cor da scrollbar do preview (mix bg+fg pra coerência)
        def hex_to_rgb(c):
            c = c.lstrip('#')
            return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        thumb_color = None
        try:
            bg_rgb = hex_to_rgb(bg_c)
            fg_rgb = hex_to_rgb(fg_c)
            mixed = tuple(int(b * 0.78 + f * 0.22) for b, f in zip(bg_rgb, fg_rgb))
            thumb_color = '#{:02x}{:02x}{:02x}'.format(*mixed)
        except Exception:
            pass

        # Atualiza cada par (widget + scrollbar)
        for i, widget in enumerate(widgets):
            try:
                widget.config(
                    bg=bg_c, fg=fg_c, font=(font_family, font_size),
                    insertbackground=fg_c, selectbackground=fg_c, selectforeground=bg_c,
                )
            except Exception as e:
                log.error(f"Erro ao atualizar preview #{i}: {e}")

            # Scrollbar correspondente (se existir)
            if i < len(scrollbars) and scrollbars[i] and thumb_color:
                try:
                    scrollbars[i].update_colors(
                        bg=bg_c, thumb=thumb_color, thumb_hover=fg_c,
                    )
                except Exception:
                    pass

    def _update_overlay_alpha(self):
        if self.overlay.window and self.overlay.window.winfo_exists():
            try:
                self.overlay.window.attributes('-alpha', float(self.alpha_var.get()))
            except Exception:
                pass

    def _pick_color(self, which: str):
        """v1.0.30: Persiste cor escolhida no settings + dispara toast."""
        current = self.bg_color if which == 'bg' else self.fg_color
        result = colorchooser.askcolor(color=current, title="Escolha uma cor")
        if result and result[1]:
            color = result[1]
            if which == 'bg':
                self.bg_color = color
                self.bg_swatch.configure(fg_color=color, hover_color=color)
                self.settings.set('overlay_bg_color', color)
            else:
                self.fg_color = color
                self.fg_swatch.configure(fg_color=color, hover_color=color)
                self.settings.set('overlay_fg_color', color)
            self.theme_var.set('custom')
            self.settings.save()
            self._update_preview()
            self._apply_overlay_theme_live()

            # Toast
            if self._toast_mgr:
                label_key = 'config.label.overlay_bg' if which == 'bg' else 'config.label.overlay_fg'
                msg = t('toast.config_changed', label=t(label_key))
                self._toast_mgr.show(msg, level='success')

    def _apply_appearance(self):
        old_main_theme = self.settings.get('main_window_theme')
        new_main_theme = self.main_theme_var.get()

        # Detecta mudança de idioma (Bloco 2 v1.1)
        old_lang = self.settings.get('ui_language', 'pt')
        selected_label = self.ui_lang_var.get()
        new_lang = self._lang_labels_to_codes.get(selected_label, 'pt')

        self.settings.update(
            main_window_theme=new_main_theme,
            ui_language=new_lang,
            overlay_theme_preset=self.theme_var.get(),
            overlay_bg_color=self.bg_color,
            overlay_fg_color=self.fg_color,
            overlay_font_family=self.font_family.get(),
            overlay_font_size=int(self.font_size.get()),
            overlay_alpha=float(self.alpha_var.get()),
            overlay_always_on_top=bool(self.aot_var.get()),
        )
        self.settings.save()
        self.overlay.refresh_appearance()

        # Decide qual diálogo de restart mostrar (prioridade: idioma > tema)
        # Idioma tem prioridade porque mexe em strings em todo lugar.
        if old_lang != new_lang:
            self._set_status(t("appearance.msg.theme_saved"))
            self._offer_restart_for_lang_change()
        elif old_main_theme != new_main_theme:
            self._set_status(t("appearance.msg.theme_saved"))
            self._offer_restart_for_theme()
        else:
            self._set_status(t("appearance.msg.applied"))

    def _offer_restart_for_lang_change(self):
        """Oferece reabrir o app pra aplicar o novo idioma (Bloco 2 v1.1)."""
        result = messagebox.askyesno(
            t("restart.title"),
            t("restart.lang.message"),
            parent=self.root,
        )
        if result:
            self._cleanup_services_for_restart()
            restart_app()

    def _offer_restart_for_theme(self):
        """Oferece reabrir o app pra aplicar o novo tema."""
        result = messagebox.askyesno(
            t("restart.title"),
            t("restart.theme.message"),
            parent=self.root,
        )
        if result:
            self._cleanup_services_for_restart()
            restart_app()

    def _cleanup_services_for_restart(self):
        """
        Cleanup de serviços antes do restart_app() — fecha de forma limpa
        SEM chamar root.destroy() (o restart_app vai fazer via os._exit).
        """
        try:
            if self.on_close_app:
                self.translator.cache.save()
                self.hotkey_mgr.stop()
                self.overlay.stop_capture()
        except Exception as e:
            log.error(f"Erro ao fazer cleanup pre-restart: {e}")

    # ==========================================================================
    # Tab: Avançado (com close_to_tray)
    # ==========================================================================

    # ==========================================================================
    # Tab: Atalho & Som (NOVA em v1.1 - extraída de Avançado)
    # ==========================================================================

    def _build_shortcut_sound_tab(self, parent):
        """v1.0.30: auto-apply + sem botão Apply + espaçamento."""
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        frame.pack(fill='both', expand=True, padx=(SPACING_LG, 0), pady=SPACING_LG)  # v1.0.31: scrollbar cola na direita

        self._auto_apply.silent(True)

        # === Hotkeys (Sub-bloco 3.2: 3 atalhos customizáveis) ===
        self._section_header(frame, t("shortcut.section.hotkey"), with_separator_above=False).pack(anchor='w')

        # Helper interno pra criar uma linha de hotkey [Label] [Entry] [Btn]
        def build_hotkey_row(parent_frame, hotkey_id: str, setting_key: str,
                             default: str, label_key: str):
            row = ctk.CTkFrame(parent_frame, fg_color="transparent")
            row.pack(fill='x', anchor='w', pady=4)

            # Label descritiva
            label = ctk.CTkLabel(
                row, text=t(label_key),
                text_color=self._t['text'],
                font=('Segoe UI', 11),
                anchor='w', width=180,
            )
            label.pack(side='left', padx=(0, 8))

            # Entry (mantém compat — user pode digitar manualmente)
            entry = self._entry(row, width=180)
            entry.pack(side='left', padx=(0, 6))
            entry.insert(0, self.settings.get(setting_key, default))

            # Botão "Capturar tecla" (Sub-bloco 3.2)
            btn = ctk.CTkButton(
                row, text=t("shortcut.btn.capture"),
                command=lambda: self._capture_hotkey_for(hotkey_id, setting_key, entry),
                fg_color=self._t['bg_pill'],
                hover_color=self._t['bg_hover'],
                text_color=self._t['text'],
                font=('Segoe UI', 10),
                corner_radius=6, height=28, width=110,
            )
            btn.pack(side='left')

            return entry

        # Hotkey 1: Tradução rápida (já existe)
        self.hotkey_entry = build_hotkey_row(
            frame, 'quick_input',
            'hotkey_quick_input', 'ctrl+shift+t',
            'shortcut.label.quick_input',
        )

        # Hotkey 2: Toggle Overlay (Sub-bloco 3.2 - novo)
        self.hotkey_overlay_entry = build_hotkey_row(
            frame, 'overlay_toggle',
            'hotkey_overlay_toggle', 'ctrl+shift+o',
            'shortcut.label.overlay_toggle',
        )

        # Hotkey 3: Toggle Lurker (Sub-bloco 3.2 - novo)
        self.hotkey_lurker_entry = build_hotkey_row(
            frame, 'lurker_toggle',
            'hotkey_lurker_toggle', 'ctrl+shift+l',
            'shortcut.label.lurker_toggle',
        )

        # Posição popup
        self._section_header(frame, t("shortcut.section.position")).pack(anchor='w', pady=(14, 0))
        self.position_mode_var = tk.StringVar(
            value=self.settings.get('quick_input_position_mode', 'cursor')
        )
        for label, val in [
            (t("shortcut.position.cursor"), "cursor"),
            (t("shortcut.position.last"), "last_position"),
        ]:
            self._radio(frame, label, self.position_mode_var, val).pack(anchor='w', pady=2)

        # Monitor
        self._section_header(frame, t("shortcut.section.monitor")).pack(anchor='w', pady=(14, 0))
        monitors = get_monitors()
        monitor_options = [t('shortcut.monitor.auto')]
        monitor_keys = [None]
        for m in monitors:
            label = f"{m['name']} ({m['width']}x{m['height']})"
            if m.get('is_primary'):
                label += " ★"
            monitor_options.append(label)
            monitor_keys.append(get_monitor_key(m))

        self.monitor_var = tk.StringVar(value=monitor_options[0])
        current_key = self.settings.get('overlay_default_monitor')
        if current_key:
            try:
                idx = monitor_keys.index(current_key)
                self.monitor_var.set(monitor_options[idx])
            except ValueError:
                pass

        self._combo(frame, self.monitor_var, monitor_options, width=380).pack(anchor='w', pady=4)
        self._monitor_keys_map = dict(zip(monitor_options, monitor_keys))

        # Som
        self._section_header(frame, t("sound.section")).pack(anchor='w', pady=(14, 0))

        self.sound_enabled_var = tk.BooleanVar(value=self.settings.get('sound_enabled', True))
        self._checkbox(
            frame, t("sound.enabled"),
            self.sound_enabled_var,
        ).pack(anchor='w', pady=2)

        sf = ctk.CTkFrame(frame, fg_color="transparent")
        sf.pack(fill='x', pady=4)
        self._label(sf, t("sound.label.file")).pack(side='left')

        available_sounds = self.sound_player.list_available_sounds()
        if not available_sounds:
            available_sounds = ['(coloque .wav em sounds/)']

        current_sound = self.settings.get('sound_file', 'pop.wav')
        if current_sound not in available_sounds and available_sounds[0] != '(coloque .wav em sounds/)':
            current_sound = available_sounds[0]

        self.sound_file_var = tk.StringVar(value=current_sound)
        self._combo(sf, self.sound_file_var, available_sounds, width=220).pack(side='left', padx=5)

        self._secondary_button(sf, t("sound.btn.test"), self._test_sound).pack(side='left', padx=5)

        # Slider de volume
        vf = ctk.CTkFrame(frame, fg_color="transparent")
        vf.pack(fill='x', pady=(8, 4))
        self._label(vf, t("sound.label.volume")).pack(side='left')

        self.sound_volume_var = tk.IntVar(value=self.settings.get('sound_volume', 50))
        self.volume_label = self._label(vf, f"{self.sound_volume_var.get()}%", dim=True)

        ctk.CTkSlider(
            vf, from_=0, to=100, variable=self.sound_volume_var,
            fg_color=self._t['bg_input'], progress_color=self._t['accent'],
            button_color=self._t['accent'], button_hover_color=self._t['accent_hover'],
            height=18, number_of_steps=20,
            command=self._on_volume_change,
        ).pack(side='left', fill='x', expand=True, padx=SPACING_MD)
        self.volume_label.pack(side='left')

        # v1.0.30: auto-apply nos campos de atalho/som
        # Lurker mode
        if hasattr(self, 'lurker_var'):
            self._auto_apply.bind(
                self.lurker_var, 'lurker_mode_enabled',
                label=t('config.label.lurker_mode'),
            )
        # v1.0.31: Posição do popup (radios cursor/last_position) — estava órfão
        self._auto_apply.bind(
            self.position_mode_var, 'quick_input_position_mode',
            label='Posição do popup',
        )
        # v1.0.31: Monitor padrão — caso especial, var guarda LABEL mas settings
        # quer a KEY. trace manual + toast manual em vez de auto_apply.bind
        # (auto_apply assume var.get() == valor a salvar, não rola aqui)
        def _on_monitor_change(*_args):
            if self._auto_apply._silent:
                return
            label = self.monitor_var.get()
            key = self._monitor_keys_map.get(label)
            self.settings.set('overlay_default_monitor', key)
            self.settings.save()
            if self._toast_mgr:
                msg = t('toast.config_changed', label='Monitor padrão')
                self._toast_mgr.show(msg, level='success')
            log.info(f"Auto-apply: overlay_default_monitor = {key!r}")
        self.monitor_var.trace_add('write', _on_monitor_change)
        # Sound enabled
        if hasattr(self, 'sound_enabled_var'):
            self._auto_apply.bind(
                self.sound_enabled_var, 'sound_enabled',
                label='Som ativado',
            )
        # Sound file
        self._auto_apply.bind(
            self.sound_file_var, 'sound_file',
            label='Som de notificação',
        )
        # Volume (debounce pra slider)
        self._auto_apply.bind(
            self.sound_volume_var, 'sound_volume',
            label='Volume',
            debounce_ms=300,
        )

        self._auto_apply.silent(False)

    # ==========================================================================
    # Tab: Avançado (limpo em v1.1 - itens de atalho/som migraram)
    # ==========================================================================

    def _build_advanced_tab(self, parent):
        """v1.0.30: auto-apply + sem botão Apply + espaçamento."""
        frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        frame.pack(fill='both', expand=True, padx=(SPACING_LG, 0), pady=SPACING_LG)  # v1.0.31: scrollbar cola na direita

        self._auto_apply.silent(True)

        # Tesseract
        self._section_header(frame, t("advanced.section.tesseract"), with_separator_above=False).pack(anchor='w')
        self._label(frame,
                    t("advanced.tesseract.help"),
                    dim=True, wraplength=520).pack(anchor='w', pady=(0, SPACING_SM))
        # v1.0.30: convertido pra StringVar pra dar trace_add
        self.tess_path_var = tk.StringVar(value=self.settings.get('tesseract_path', ''))
        self.tess_path = self._entry(frame, textvariable=self.tess_path_var)
        self.tess_path.pack(fill='x', pady=(0, SPACING_XL))

        # System Tray
        self._section_header(frame, t("advanced.section.tray")).pack(anchor='w', pady=(0, SPACING_SM))

        self.close_to_tray_var = tk.BooleanVar(value=self.settings.get('close_to_tray', False))
        self._checkbox(
            frame,
            t("advanced.close_to_tray"),
            self.close_to_tray_var,
        ).pack(anchor='w', pady=2)

        self._label(frame,
                    t("advanced.tray.help"),
                    dim=True, wraplength=520, justify='left').pack(anchor='w', pady=(2, 0))

        # Comportamento
        self._section_header(frame, t("advanced.section.behavior")).pack(anchor='w', pady=(14, 0))

        self.countdown_var = tk.BooleanVar(value=self.settings.get('send_countdown_visual', False))
        self._checkbox(frame, t("advanced.countdown"),
                       self.countdown_var).pack(anchor='w', pady=2)

        self.cache_var = tk.BooleanVar(value=self.settings.get('cache_enabled', True))
        self._checkbox(frame, t("advanced.cache"),
                       self.cache_var).pack(anchor='w', pady=2)

        self.history_var = tk.BooleanVar(value=self.settings.get('history_enabled', True))
        self._checkbox(frame, t("advanced.history"),
                       self.history_var).pack(anchor='w', pady=2)

        # Debug
        self._section_header(frame, t("advanced.section.debug")).pack(anchor='w', pady=(14, 0))

        self.log_var = tk.BooleanVar(value=self.settings.get('logging_enabled', False))
        self._checkbox(frame, t("advanced.logging"),
                       self.log_var).pack(anchor='w', pady=2)

        # === v1.0.34/Fase 4: Atualizações ===
        # Seção pra checagem manual de updates Velopack. Em modo dev (is_active=False)
        # mostra mensagem informativa em vez do botão funcional.
        self._section_header(frame, t("advanced.section.updates")).pack(anchor='w', pady=(14, 0))

        from app_info import APP_VERSION as _current_v
        self._label(
            frame,
            t("advanced.updates.current").format(version=_current_v),
            dim=True,
        ).pack(anchor='w', pady=(0, SPACING_SM))

        # Botão de check
        self._update_check_btn = self._secondary_button(
            frame,
            t("advanced.updates.btn.check"),
            self._on_check_updates_clicked,
        )
        self._update_check_btn.pack(anchor='w', pady=(0, 4))

        # Label de status (vazio inicial, preenchido conforme estados)
        # Se o updater nao for ativo (modo dev), mostra mensagem informativa logo de cara
        if self.updater is None or not self.updater.is_active:
            initial_status = t("advanced.updates.status.devmode")
            initial_dim = True
        else:
            initial_status = ""
            initial_dim = True

        self._update_status_label = self._label(
            frame, initial_status, dim=initial_dim, wraplength=520,
        )
        self._update_status_label.pack(anchor='w', pady=(0, SPACING_SM))

        # v1.0.30: auto-apply nas vars principais do Avançado
        if hasattr(self, 'tess_path_var'):
            self._auto_apply.bind(self.tess_path_var, 'tesseract_path',
                                  label='Caminho Tesseract', debounce_ms=600)
        if hasattr(self, 'close_to_tray_var'):
            self._auto_apply.bind(self.close_to_tray_var, 'close_to_tray',
                                  label='Fechar pra tray')
        if hasattr(self, 'minimize_to_tray_var'):
            self._auto_apply.bind(self.minimize_to_tray_var, 'minimize_to_tray',
                                  label='Minimizar pra tray')
        # v1.0.31: bind dos checkboxes de Comportamento que estavam órfãos
        if hasattr(self, 'countdown_var'):
            self._auto_apply.bind(self.countdown_var, 'send_countdown_visual',
                                  label='Contador visual de envio')
        if hasattr(self, 'cache_var'):
            self._auto_apply.bind(self.cache_var, 'cache_enabled',
                                  label='Cache de tradução')
        if hasattr(self, 'history_var'):
            self._auto_apply.bind(self.history_var, 'history_enabled',
                                  label='Histórico de mensagens')
        if hasattr(self, 'log_var'):
            # v1.0.31: chave correta é 'logging_enabled' (não 'debug_log_enabled')
            # — combina com o default usado em settings.get acima
            self._auto_apply.bind(self.log_var, 'logging_enabled',
                                  label='Log de debug', requires_restart=True)

        self._auto_apply.silent(False)

        # Reportar Problema (ação independente, abaixo)
        self._section_header(frame, t("advanced.section.support")).pack(anchor='w', pady=(20, 0))
        self._secondary_button(
            frame, t("advanced.btn.report"),
            self._open_report_problem,
        ).pack(anchor='w', pady=(4, 0))
        self._label(frame,
                    t("advanced.report.help"),
                    dim=True, wraplength=520).pack(anchor='w', pady=(2, 0))

        # Sobre (informativo, no fim)
        self._section_header(frame, t("advanced.section.about")).pack(anchor='w', pady=(14, 0))
        self._secondary_button(
            frame, t("advanced.btn.about"),
            self._open_about,
        ).pack(anchor='w', pady=(4, 12))

    def _on_volume_change(self, value):
        try:
            v = int(float(value))
            self.volume_label.configure(text=f"{v}%")
        except Exception:
            pass

    def _test_sound(self):
        sound_file = self.sound_file_var.get()
        if sound_file == '(coloque .wav em sounds/)':
            self._set_status(t("sound.msg.no_files"))
            return
        old_enabled = self.settings.get('sound_enabled', True)
        old_volume = self.settings.get('sound_volume', 50)
        self.settings.set('sound_enabled', True)
        self.settings.set('sound_volume', int(self.sound_volume_var.get()))
        self.sound_player.play(sound_file)
        self.settings.set('sound_enabled', old_enabled)
        self.settings.set('sound_volume', old_volume)
        self._set_status(t("sound.msg.testing", file=sound_file, volume=int(self.sound_volume_var.get())))

    def _apply_shortcut_sound(self):
        """Aplica configurações da aba Atalho & Som."""
        old_hotkey = self.settings.get('hotkey_quick_input', 'ctrl+shift+t')
        new_hotkey = self.hotkey_entry.get().strip() or 'ctrl+shift+t'

        # Sub-bloco 3.2: 3 hotkeys customizáveis
        old_overlay = self.settings.get('hotkey_overlay_toggle', 'ctrl+shift+o')
        new_overlay = self.hotkey_overlay_entry.get().strip() or 'ctrl+shift+o'
        old_lurker = self.settings.get('hotkey_lurker_toggle', 'ctrl+shift+l')
        new_lurker = self.hotkey_lurker_entry.get().strip() or 'ctrl+shift+l'

        # === Validação de conflitos entre os 3 hotkeys ===
        # Detecta se duas configurações estão iguais ANTES de salvar
        normalized = lambda s: '+'.join(sorted(p.strip().lower() for p in s.split('+')))
        new_hotkeys_map = {
            'quick_input': normalized(new_hotkey),
            'overlay_toggle': normalized(new_overlay),
            'lurker_toggle': normalized(new_lurker),
        }
        # Verifica duplicatas
        seen = {}
        from tkinter import messagebox
        for hk_id, hk_str in new_hotkeys_map.items():
            if hk_str in seen:
                messagebox.showerror(
                    t("hotkey.capture.title"),
                    t("hotkey.capture.error_conflict") +
                    f"\n\n{seen[hk_str]} = {hk_id} = {hk_str}",
                )
                log.warning(f"Conflito ao aplicar: {hk_id} e {seen[hk_str]} têm a mesma combinação")
                return
            seen[hk_str] = hk_id

        selected_label = self.monitor_var.get()
        monitor_key = self._monitor_keys_map.get(selected_label)

        sound_file = self.sound_file_var.get()
        if sound_file == '(coloque .wav em sounds/)':
            sound_file = 'pop.wav'

        self.settings.update(
            hotkey_quick_input=new_hotkey,
            hotkey_overlay_toggle=new_overlay,
            hotkey_lurker_toggle=new_lurker,
            quick_input_position_mode=self.position_mode_var.get(),
            overlay_default_monitor=monitor_key,
            sound_enabled=bool(self.sound_enabled_var.get()),
            sound_file=sound_file,
            sound_volume=int(self.sound_volume_var.get()),
        )
        self.settings.save()

        # Reload se ANY das 3 hotkeys mudou
        any_changed = (
            old_hotkey != new_hotkey or
            old_overlay != new_overlay or
            old_lurker != new_lurker
        )
        if any_changed:
            self.hotkey_mgr.reload()
            self._set_status(t("shortcut.msg.applied_with_hotkey", hotkey=new_hotkey))
        else:
            self._set_status(t("shortcut.msg.applied"))

    def _apply_advanced(self):
        """Aplica configurações da aba Avançado."""
        self.settings.update(
            tesseract_path=self.tess_path.get().strip(),
            close_to_tray=bool(self.close_to_tray_var.get()),
            send_countdown_visual=bool(self.countdown_var.get()),
            cache_enabled=bool(self.cache_var.get()),
            history_enabled=bool(self.history_var.get()),
            logging_enabled=bool(self.log_var.get()),
        )
        self.settings.save()
        self.ocr._configure_tesseract()
        self._set_status(t("advanced.msg.applied"))

    # ==========================================================================
    # Helpers
    # ==========================================================================

    def _open_about(self):
        """Abre tela 'Sobre' com versão, autor, créditos."""
        from app_info import APP_FULL_NAME, APP_VERSION, APP_AUTHOR
        from assets_helper import get_icon_path, apply_icon_via_win32
        from monitor_utils import center_window_on_parent

        theme = self._t
        win = ctk.CTkToplevel(self.root)
        win.title(t("title.about"))
        # Centraliza relativa à main window (em cima dela) — substitui
        # o win.geometry("440x460") que abria no canto da tela.
        center_window_on_parent(win, self.root, 440, 460)
        win.configure(fg_color=theme['bg'])
        # NOTA: NÃO chamar set_window_icon antes da custom titlebar.
        # O iconbitmap conflita com o withdraw/deiconify do _force_taskbar_appearance.
        # Vamos só usar apply_icon_via_win32 com delay, igual nas outras toplevels.

        apply_custom_titlebar(
            win, t("title.about"),
            on_close=win.destroy, show_minimize=False, resizable=False,
            bg_color=theme['bg'], bg_titlebar=theme['titlebar_bg'],
            fg=theme['text'], accent=theme['accent'],
            bg_button_hover=theme['bg_hover'],
            close_hover_bg=theme['titlebar_close_hover'],
            min_width=440, min_height=460,
        )
        win.after(300, lambda: apply_icon_via_win32(win))
        win.after(800, lambda: apply_icon_via_win32(win))

        # Conteúdo
        content = ctk.CTkFrame(win, fg_color="transparent")
        content.pack(fill='both', expand=True, padx=24, pady=20)

        # Ícone grande no topo (centralizado)
        icon_path = get_icon_path()
        if icon_path:
            try:
                from PIL import Image, ImageTk
                img = Image.open(str(icon_path))
                img = img.resize((96, 96), Image.LANCZOS)
                self._about_icon_photo = ImageTk.PhotoImage(img)  # mantém ref
                icon_lbl = tk.Label(content, image=self._about_icon_photo, bg=theme['bg'])
                icon_lbl.pack(pady=(0, 12))
            except Exception as e:
                log.debug(f"Icon no About falhou: {e}")

        # Nome do app
        ctk.CTkLabel(
            content, text=APP_FULL_NAME,
            text_color=theme['accent'], font=('Segoe UI', 18, 'bold'),
        ).pack()

        # Versão
        ctk.CTkLabel(
            content, text=t("about.version", ver=APP_VERSION),
            text_color=theme['text'], font=('Segoe UI', 12),
        ).pack(pady=(2, 0))

        # Linha separadora
        sep = tk.Frame(content, bg=theme['border'], height=1)
        sep.pack(fill='x', pady=14)

        # Descrição
        ctk.CTkLabel(
            content,
            text=t("about.description"),
            text_color=theme['text_dim'], font=('Segoe UI', 11),
            justify='center',
        ).pack(pady=(0, 14))

        # Crédito
        ctk.CTkLabel(
            content, text=t("about.developer", author=APP_AUTHOR),
            text_color=theme['accent'], font=('Segoe UI', 12, 'bold'),
        ).pack()

        ctk.CTkLabel(
            content, text=t("about.tagline"),
            text_color=theme['text_dim'], font=('Segoe UI', 10, 'italic'),
        ).pack(pady=(2, 18))

        # Botão fechar
        self._primary_button(content, t("btn.close"), win.destroy).pack(pady=(8, 0))

    def _open_report_problem(self):
        """Abre diálogo de Reportar Problema com export de logs+settings."""
        from app_info import APP_FULL_NAME, APP_VERSION
        from settings import get_app_dir
        import zipfile
        import json
        import datetime
        import platform
        import urllib.parse
        import webbrowser

        theme = self._t
        win = ctk.CTkToplevel(self.root)
        win.title(t("title.report"))
        from assets_helper import apply_icon_via_win32
        from monitor_utils import center_window_on_parent
        center_window_on_parent(win, self.root, 560, 520)
        win.configure(fg_color=theme['bg'])

        apply_custom_titlebar(
            win, t("title.report"),
            on_close=win.destroy, show_minimize=False, resizable=True,
            bg_color=theme['bg'], bg_titlebar=theme['titlebar_bg'],
            fg=theme['text'], accent=theme['accent'],
            bg_button_hover=theme['bg_hover'],
            close_hover_bg=theme['titlebar_close_hover'],
            min_width=480, min_height=400,
        )
        win.after(300, lambda: apply_icon_via_win32(win))
        win.after(800, lambda: apply_icon_via_win32(win))

        content = ctk.CTkFrame(win, fg_color="transparent")
        content.pack(fill='both', expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            content, text=t("report.title"),
            text_color=theme['accent'], font=('Segoe UI', 16, 'bold'),
        ).pack(anchor='w')

        ctk.CTkLabel(
            content,
            text=t("report.help"),
            text_color=theme['text_dim'], font=('Segoe UI', 10),
            justify='left', anchor='w',
        ).pack(anchor='w', pady=(2, 12))

        ctk.CTkLabel(
            content, text=t("report.label.description"),
            text_color=theme['text'], font=('Segoe UI', 11, 'bold'),
        ).pack(anchor='w')

        desc_text = tk.Text(
            content, height=8,
            bg=theme['bg_input'], fg=theme['text'], insertbackground=theme['text'],
            relief='flat', font=('Segoe UI', 11),
            wrap='word', padx=10, pady=8,
            highlightthickness=1, highlightbackground=theme['border'],
            highlightcolor=theme['accent'],
        )
        desc_text.pack(fill='x', pady=(4, 12))
        desc_text.focus_set()

        status_lbl = ctk.CTkLabel(
            content, text="", text_color=theme['accent'], font=('Segoe UI', 10),
        )
        status_lbl.pack(anchor='w')

        def _gerar_zip():
            description = desc_text.get('1.0', tk.END).strip()
            if not description:
                status_lbl.configure(
                    text=t("report.msg.empty"),
                    text_color=theme['highlight'],
                )
                return

            try:
                app_dir = get_app_dir()
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                zip_path = app_dir / f"dofusinator_report_{timestamp}.zip"

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    # 1. Descrição
                    info = {
                        'app': APP_FULL_NAME,
                        'version': APP_VERSION,
                        'timestamp': datetime.datetime.now().isoformat(),
                        'os': platform.platform(),
                        'description': description,
                    }
                    zf.writestr('report_info.json', json.dumps(info, indent=2, ensure_ascii=False))

                    # 2. Settings (filtrando dados sensíveis)
                    settings_safe = self.settings.all().copy()
                    # Remove API keys
                    if 'deepl_api_key' in settings_safe and settings_safe['deepl_api_key']:
                        settings_safe['deepl_api_key'] = '[REDACTED]'
                    zf.writestr('settings.json', json.dumps(settings_safe, indent=2, ensure_ascii=False))

                    # 3. debug.log se existir
                    log_path = app_dir / 'debug.log'
                    if log_path.exists():
                        zf.write(str(log_path), 'debug.log')

                # Abre cliente de e-mail com mensagem pronta
                subject = urllib.parse.quote(f"[Dofusinator v{APP_VERSION}] Bug Report")
                body = urllib.parse.quote(
                    f"Descrição:\n{description}\n\n"
                    f"---\n"
                    f"Anexei o arquivo: {zip_path.name}\n"
                    f"Local: {zip_path}\n\n"
                    f"App: {APP_FULL_NAME} v{APP_VERSION}\n"
                    f"OS: {platform.platform()}\n"
                )
                mailto = f"mailto:dinozzera@gmail.com?subject={subject}&body={body}"

                try:
                    webbrowser.open(mailto)
                except Exception:
                    pass

                # Mostra confirmação + caminho do .zip
                status_lbl.configure(
                    text=t("report.msg.generated", file=zip_path.name),
                    text_color=theme['accent'],
                )
                # Tenta abrir o explorer no arquivo (Windows)
                try:
                    import subprocess
                    subprocess.Popen(['explorer', '/select,', str(zip_path)])
                except Exception:
                    pass

            except Exception as e:
                log.error(f"Erro ao gerar relatório: {e}", exc_info=True)
                status_lbl.configure(
                    text=t("report.msg.error", err=e),
                    text_color=theme['highlight'],
                )

        # Botões
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill='x', pady=(12, 0))

        self._primary_button(
            btn_frame, t("report.btn.generate"), _gerar_zip,
        ).pack(side='left')

        self._secondary_button(
            btn_frame, t("btn.cancel"), win.destroy,
        ).pack(side='left', padx=(8, 0))

    def _set_status(self, msg: str):
        self.status_var.set(msg)
        log.info(msg)
