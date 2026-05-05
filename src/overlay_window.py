"""
Janela overlay de leitura.
v3.2: paleta dofus_retro nova + custom titlebar com resize grips.
"""
import logging
import threading
import time
import tkinter as tk
from typing import Optional, Callable

import customtkinter as ctk

from settings import Settings
from translator_service import TranslatorService
from ocr_engine import OCREngine
from i18n import t
from spacing import (
    SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    WINDOW_CONTENT_PADDING_X, WINDOW_CONTENT_PADDING_Y,
    FOOTER_PADDING_X, FOOTER_PADDING_Y,
)
from monitor_utils import (
    get_monitor_for_point, get_monitor_key, get_primary_monitor, parse_geometry
)
from custom_titlebar import apply_custom_titlebar, _win32_minimize
from theme import get_theme
from assets_helper import set_window_icon, apply_icon_via_win32
from spacing import (
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG,
    WINDOW_CONTENT_PADDING_X, WINDOW_CONTENT_PADDING_Y,
    FOOTER_PADDING_X, FOOTER_PADDING_Y,
)

log = logging.getLogger(__name__)


# Presets específicos pra texto do overlay (cores otimizadas pra leitura)
THEME_PRESETS = {
    "dark": {"bg": "#1a1a1a", "fg": "#e0e0e0", "alpha": 0.92},
    "light": {"bg": "#f5f5f5", "fg": "#1a1a1a", "alpha": 0.95},
    "dofus_retro": {"bg": "#1a1614", "fg": "#D5CFAA", "alpha": 0.92},
}

WAITING_MSG = "[ aguardando texto no chat... ]"
EMPTY_OCR_MSG = "[ OCR não retornou texto — verifica configuração ]"
EMPTY_THRESHOLD_SECONDS = 8


class OverlayWindow:
    def __init__(
        self, master, settings: Settings,
        translator: TranslatorService, ocr: OCREngine,
    ):
        self.master = master
        self.settings = settings
        self.translator = translator
        self.ocr = ocr

        # Callback opcional chamado quando o overlay é fechado/escondido.
        # MainWindow usa pra atualizar estado do botão "Iniciar/Parar Tradução".
        self.on_hide: Optional[Callable[[], None]] = None

        self.window: Optional[ctk.CTkToplevel] = None
        self.text_widget: Optional[tk.Text] = None
        self._titlebar_refs = None
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_hash = ""
        self._last_lines: list[str] = []
        self._last_text_time = 0.0
        self._showing_waiting_msg = False

        # === Última linha capturada (Sub-bloco 3.2 - mini-pill) ===
        # Guarda a última linha lida no idioma ORIGINAL pra exibir no mini-pill
        # quando o overlay for colapsado.
        self._last_captured_line: str = ""
        # Callback opcional pra notificar componentes externos (ex: mini-pill)
        # quando uma nova linha é capturada
        self.on_new_line: Optional[Callable[[str], None]] = None

        # Hash-based dedup (v1.0.21) ===
        from collections import deque
        self._seen_line_hashes: set = set()
        self._seen_line_hashes_order: deque = deque(maxlen=5000)

        # Callback pra notificar quando uma linha realmente NOVA (não vista antes)
        # foi capturada. Usado pelo histórico do chat.
        self.on_truly_new_line: Optional[Callable[[str, str], None]] = None  # (original, traduzido)

        # v1.0.21: referência ao chat_history pra carregar histórico no overlay
        # ao abrir (continuidade entre sessões). Setado externamente.
        self.chat_history = None

        # Contador de quantas linhas estão "marcadas como novas" pra destaque
        # visual após expandir do mini-pill. Resetado periodicamente.
        self._new_lines_to_highlight: int = 0

        # v1.0.21: callback chamado quando user clica botão "colapsar" na titlebar
        # (substitui o comportamento de "minimizar"). MainWindow seta isso pra
        # rotear pro mini-pill.
        self.on_collapse_request: Optional[Callable[[], None]] = None

    def show(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            return
        self._build_window()
        self._apply_theme()
        self._apply_geometry()
        # v1.0.21: carrega histórico do chat ao abrir overlay (continuidade)
        # Mostra entradas antigas no widget antes da mensagem de "aguardando".
        loaded = self._load_history_into_widget()
        if not loaded:
            self._show_waiting_message()

    def hide(self):
        """
        Esconde o overlay E para a captura.

        IMPORTANTE: também para o thread de captura — sem isso, o thread continua
        rodando em background mesmo com janela fechada (gastando CPU + descincronizando
        o estado do botão "Iniciar Tradução" no MainWindow).

        Notifica via callback `on_hide` pra MainWindow atualizar o botão.
        """
        # Para a captura PRIMEIRO (libera thread e CPU)
        if self.is_capturing():
            log.info("Overlay fechado: parando captura também")
            self.stop_capture()

        # Esconde a janela (preserva geometria pra próxima abertura)
        if self.window and self.window.winfo_exists():
            self._save_geometry()
            self.window.withdraw()

        # Notifica MainWindow (pra atualizar estado do botão Iniciar/Parar)
        if self.on_hide:
            try:
                self.on_hide()
            except Exception as e:
                log.error(f"on_hide callback falhou: {e}")

    def is_visible(self) -> bool:
        return (
            self.window is not None
            and self.window.winfo_exists()
            and self.window.state() != 'withdrawn'
        )

    def get_last_captured_line(self) -> str:
        """Retorna última linha capturada no idioma original (pra mini-pill)."""
        return self._last_captured_line

    def get_position(self) -> tuple:
        """Retorna (x, y) atuais do overlay. Pra preservar posição quando colapsa pra pill."""
        if self.window and self.window.winfo_exists():
            try:
                return (self.window.winfo_x(), self.window.winfo_y())
            except Exception:
                pass
        return (100, 100)

    def _build_window(self):
        # Tema da janela principal pra tba (mas overlay tem sua paleta interna pro texto)
        main_t = get_theme(self.settings.get('main_window_theme', 'dofus_retro'))

        self.window = ctk.CTkToplevel(self.master)
        # Define o título NATIVO antes do overrideredirect — aparece no Alt+Tab
        # e no preview da taskbar (sem isso, mostra "CTkToplevel" genérico)
        self.window.title(t("title.overlay"))
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

        on_top = self.settings.get('overlay_always_on_top', True)
        self.window.attributes('-topmost', on_top)

        # Custom titlebar + resize grips
        # v1.0.21: o botão de minimizar foi SUBSTITUÍDO por "colapsar pro mini-pill".
        # Faz mais sentido pro overlay porque:
        #   - Minimizar pra taskbar é redundante (já tem na main window)
        #   - Colapsar pra pill mantém captura rodando + acesso rápido
        # O ícone "⊙" representa visualmente "colapsar pra ponto".
        def on_collapse_btn():
            if self.on_collapse_request:
                try:
                    self.on_collapse_request()
                except Exception as e:
                    log.error(f"on_collapse_request callback falhou: {e}")
            else:
                # Fallback: se nada registrado, esconde como antes
                _win32_minimize(self.window)

        self._titlebar_refs = apply_custom_titlebar(
            self.window,
            title=t("title.overlay"),
            on_close=self.hide,
            on_minimize=on_collapse_btn,
            minimize_icon="⊙",  # v1.0.21: indica "colapsar"
            keep_taskbar=True,
            resizable=True,
            bg_color=main_t['bg'],
            bg_titlebar=main_t['titlebar_bg'],
            fg=main_t['text'],
            accent=main_t['accent'],
            bg_button_hover=main_t['bg_hover'],
            close_hover_bg=main_t['titlebar_close_hover'],
            min_width=350, min_height=200,
        )

        # Re-aplica ícone via Win32 DEPOIS do overrideredirect (iconbitmap perde
        # efeito quando overrideredirect é setado) E DEPOIS do withdraw+deiconify
        # do _force_taskbar_appearance (que reseta o ícone aplicado antes).
        # 300ms é seguro: garantido depois do after(10) do deiconify + overhead.
        self.window.after(300, lambda: apply_icon_via_win32(self.window))
        # Segundo retry pra garantir
        self.window.after(800, lambda: apply_icon_via_win32(self.window))

        container = ctk.CTkFrame(self.window, fg_color="transparent", corner_radius=0)
        container.pack(fill='both', expand=True)

        # v1.0.22 BUG FIX: empacota bottom bar PRIMEIRO com side='bottom' pra
        # garantir que aparece. Senão o text_widget com expand=True consome
        # todo o espaço vertical e empurra a bar pra fora da janela.
        self._build_bottom_bar(container, main_t)

        # v1.0.27: ESTRATÉGIA VALIDADA EM TESTE ISOLADO antes de integrar.
        # Aprendizado da v1.0.24: tk.Text NÃO aceita tupla em pady (option).
        # Tupla só funciona em .pack()/.grid() (geometry manager).
        #
        # Solução pra "texto colado no separador":
        #   - Wrapper Frame com pady=(12, 0) no PACK (assimétrico OK aqui)
        #   - text_widget com pady=2 simétrico (int único, sem tupla)
        #   - Scrollbar custom à direita do wrapper
        #   - Pack order: scrollbar primeiro (right) + text com side='left'
        #
        # Pady do wrapper (12, 0) → 12px no top, 0 no bottom
        # Pady do text widget (2 simétrico) → 2px in/out no widget interno
        # Resultado: texto cola praticamente no separador inferior.
        text_wrapper = ctk.CTkFrame(container, fg_color="transparent", corner_radius=0)
        text_wrapper.pack(fill='both', expand=True, pady=(WINDOW_CONTENT_PADDING_Y, 0))

        self.text_widget = tk.Text(
            text_wrapper, wrap='word', relief='flat', borderwidth=0,
            padx=WINDOW_CONTENT_PADDING_X,
            pady=2,  # int simétrico SEMPRE (NUNCA tupla aqui!)
            spacing1=2, spacing3=2,
        )
        # v1.0.27: scrollbar custom estilizada (8px, paleta do tema)
        # Cores reais setadas em _apply_theme.
        from themed_scrollbar import ThemedScrollbar
        self._scrollbar = ThemedScrollbar(
            text_wrapper,
            target_widget=self.text_widget,
            bg=main_t.get('bg', '#1a1614'),
            thumb=main_t.get('text_dim', '#8b7355'),
            thumb_hover=main_t.get('accent', '#c5a572'),
            width=8,
        )
        # Pack ORDER: scrollbar first (right), text second (left+expand)
        self._scrollbar.pack(side='right', fill='y')
        self.text_widget.pack(side='left', fill='both', expand=True)
        self.text_widget.config(state='disabled')
        self.text_widget.config(state='disabled')

        # v1.0.21: configura tag de destaque pra linhas novas após expandir do pill
        # Cor é setada em _apply_theme baseado no tema
        self.text_widget.tag_configure('highlight_new', background='#3a3324')

        self.window.bind('<Configure>', self._on_configure)

    def _build_bottom_bar(self, container, main_t):
        """
        Barra inferior do overlay com botão limpar e dica de dedup.
        v1.0.22: empacota com side='bottom' ANTES do text_widget pra garantir
        que aparece (text_widget com expand=True consumiria o espaço todo).
        v1.0.23: linha divisora 1px (bege sutil) acima do rodapé pra dar
        limite visual ao conteúdo, especialmente quando o texto é curto ou
        scrollado pra cima.

        ORDEM DE PACK (importante!): em Tk com side='bottom', widgets se
        empilham de baixo pra cima na ordem do pack. Pra ter [texto / linha
        / rodapé] de cima pra baixo:
            1) Pack bottom bar (vai pro fundo)
            2) Pack separator line (fica ACIMA do bottom)
            3) Text widget com expand=True consome o resto (já feito fora)
        """
        # 1) Bottom bar (rodapé) - vai pro fundo
        bottom = ctk.CTkFrame(container, fg_color="transparent", height=36)
        bottom.pack(fill='x', side='bottom',
                    padx=FOOTER_PADDING_X, pady=FOOTER_PADDING_Y)

        # 2) Linha divisora 1px ACIMA do rodapé (cor recalculada em _apply_theme)
        # Cor inicial: text_dim do tema. _apply_theme refina pra mix bg+fg.
        self._separator_line = tk.Frame(
            container, height=1, bg=main_t.get('text_dim', '#3a3324'),
        )
        self._separator_line.pack(fill='x', side='bottom')

        # Botão limpar (esquerda)
        self._clear_btn = ctk.CTkButton(
            bottom, text=t("overlay.btn.clear_history"),
            command=self._on_clear_clicked,
            fg_color="transparent",
            hover_color=main_t['bg_pill'],
            text_color=main_t['text_dim'],
            font=('Segoe UI', 9),
            corner_radius=4, height=24, width=130,
        )
        self._clear_btn.pack(side='left', padx=(0, SPACING_SM))
        # Hover: muda cor do texto pra ficar legível
        self._clear_btn.bind('<Enter>', lambda e: self._clear_btn.configure(text_color=main_t['text']))
        self._clear_btn.bind('<Leave>', lambda e: self._clear_btn.configure(text_color=main_t['text_dim']))

        # Dica de dedup (direita) - só aparece se setting habilitado
        if self.settings.get('chat_history_show_dedup_hint', True):
            self._dedup_hint = ctk.CTkLabel(
                bottom, text=t("overlay.hint.dedup"),
                text_color=main_t['text_dim'],
                font=('Segoe UI', 8, 'italic'),
            )
            self._dedup_hint.pack(side='right', padx=(SPACING_SM, 0))

    def _on_clear_clicked(self):
        """User clicou em 'Limpar histórico' no overlay."""
        # Confirmação simples (modal nativo)
        from tkinter import messagebox
        try:
            answer = messagebox.askyesno(
                t("overlay.clear.confirm_title"),
                t("overlay.clear.confirm_msg"),
                parent=self.window,
            )
            if answer:
                self.clear_chat_history()
                log.info("Chat history limpo pelo user via botão no overlay")
        except Exception as e:
            log.error(f"Erro ao confirmar limpeza: {e}")

    def _apply_theme(self):
        if self.window is None or self.text_widget is None:
            return

        preset_name = self.settings.get('overlay_theme_preset', 'dofus_retro')
        if preset_name == 'custom':
            bg = self.settings.get('overlay_bg_color', '#1a1614')
            fg = self.settings.get('overlay_fg_color', '#D5CFAA')
            alpha = self.settings.get('overlay_alpha', 0.92)
        else:
            preset = THEME_PRESETS.get(preset_name, THEME_PRESETS['dofus_retro'])
            bg = preset['bg']
            fg = preset['fg']
            alpha = self.settings.get('overlay_alpha', preset['alpha'])

        font_family = self.settings.get('overlay_font_family', 'Consolas')
        font_size = self.settings.get('overlay_font_size', 12)

        try:
            self.window.configure(fg_color=bg)
        except Exception:
            pass
        self.window.attributes('-alpha', alpha)
        self.text_widget.configure(
            bg=bg, fg=fg, font=(font_family, font_size),
            insertbackground=fg, selectbackground=fg, selectforeground=bg,
        )

        # v1.0.21: cor do destaque de linhas novas (background sutil)
        # Mistura uma versão dim do accent do tema. Pra Dofus Retro fica
        # marrom-dourado escuro. Pra dark fica cinza-azulado.
        # v1.0.23: a linha divisora do rodapé usa a MESMA cor pra coerência visual
        try:
            # v1.0.21: cor do destaque de linhas novas (background sutil)
            # v1.0.23: a linha divisora do rodapé usa a MESMA cor pra coerência visual
            highlight_bg = self._compute_highlight_color(bg, fg)
            self.text_widget.tag_configure('highlight_new', background=highlight_bg)
            if hasattr(self, '_separator_line') and self._separator_line:
                try:
                    self._separator_line.configure(bg=highlight_bg)
                except Exception:
                    pass
            # v1.0.27: scrollbar custom acompanha o tema
            if hasattr(self, '_scrollbar') and self._scrollbar:
                try:
                    self._scrollbar.update_colors(
                        bg=bg,
                        thumb=highlight_bg,  # mesmo bege sutil do separador
                        thumb_hover=fg,      # acende em fg (mais claro) no hover
                    )
                except Exception:
                    pass
        except Exception as e:
            log.debug(f"highlight color falhou: {e}")

        # Atualiza cor dos resize grips pra combinar com bg
        if self._titlebar_refs and self._titlebar_refs.get('grips'):
            self._titlebar_refs['grips'].update_bg(bg)

    def _apply_geometry(self):
        geom = self._get_geometry_for_default_monitor()
        try:
            self.window.geometry(geom)
        except Exception:
            self.window.geometry('600x400+100+100')

    def _get_geometry_for_default_monitor(self) -> str:
        geometries = self.settings.get('overlay_geometries_by_monitor', {}) or {}
        default_monitor_key = self.settings.get('overlay_default_monitor')
        if default_monitor_key and default_monitor_key in geometries:
            return geometries[default_monitor_key]

        primary = get_primary_monitor()
        if primary:
            key = get_monitor_key(primary)
            if key in geometries:
                return geometries[key]

        return self.settings.get('overlay_geometry', '600x400+100+100')

    def _save_geometry(self):
        if not self.window or not self.window.winfo_exists():
            return
        try:
            geom = self.window.geometry()
            parsed = parse_geometry(geom)
            if not parsed:
                return
            w, h, x, y = parsed
            cx = x + w // 2
            cy = y + h // 2
            monitor = get_monitor_for_point(cx, cy)
            if monitor:
                key = get_monitor_key(monitor)
                geometries = self.settings.get('overlay_geometries_by_monitor', {}) or {}
                geometries[key] = geom
                self.settings.set('overlay_geometries_by_monitor', geometries)
            self.settings.set('overlay_geometry', geom)
        except Exception as e:
            log.error(f"Erro ao salvar geometria: {e}")

    def _on_configure(self, event):
        if self.window and event.widget == self.window:
            self._save_geometry()

    def refresh_appearance(self):
        if self.window and self.window.winfo_exists():
            self._apply_theme()

    # ===========================================================================
    # Capture loop (mesma lógica)
    # ===========================================================================

    def start_capture(self):
        if self._capture_thread and self._capture_thread.is_alive():
            return
        if not self.settings.get('perimeter'):
            return
        self._stop_event.clear()
        self._last_text_time = time.time()
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

    def stop_capture(self):
        self._stop_event.set()
        if self._capture_thread:
            self._capture_thread.join(timeout=2.0)

    def is_capturing(self) -> bool:
        return self._capture_thread is not None and self._capture_thread.is_alive()

    def _capture_loop(self):
        while not self._stop_event.is_set():
            try:
                lines, img_hash = self.ocr.capture_and_extract()
                if img_hash and img_hash != self._last_hash:
                    self._last_hash = img_hash
                    if lines:
                        self._handle_new_capture(lines)
                        self._last_text_time = time.time()
                    else:
                        self._maybe_show_empty_msg()
                else:
                    self._maybe_show_empty_msg()
            except Exception as e:
                log.error(f"Erro no capture loop: {e}")

            interval = max(0.5, self.settings.get('check_interval', 1.0))
            self._stop_event.wait(interval)

    def _maybe_show_empty_msg(self):
        if not self._last_lines and not self._showing_waiting_msg:
            elapsed = time.time() - self._last_text_time
            if elapsed > EMPTY_THRESHOLD_SECONDS:
                self.master.after(0, self._show_empty_warning_message)

    def _handle_new_capture(self, lines: list[str]):
        """
        v1.0.21: Hash-based dedup pra resolver problema de scroll.

        Antes: se user scrollava o chat do jogo, OCR re-capturava linhas
        antigas e o app traduzia tudo de novo (gerando duplicatas no histórico
        e badge errado).

        Agora: cada linha tem hash único calculado. Linhas com hash já visto
        nesta sessão são IGNORADAS — não traduzem, não vão pro histórico, não
        contam pro badge.

        Limitação aceita: se 2 jogadores diferentes mandam exatamente a mesma
        frase (ex: "obrigado!"), só conta a primeira. UI deixa isso claro.
        """
        if not lines:
            return
        src = self.settings.get('source_language_read', 'fr')
        dest = self.settings.get('target_language_read', 'pt')

        if self._showing_waiting_msg:
            self._showing_waiting_msg = False

        # Filtra linhas: separa as VERDADEIRAMENTE novas (hash não visto)
        truly_new_lines: list[str] = []
        for line in lines:
            normalized = line.strip()
            if not normalized:
                continue
            line_hash = self._compute_line_hash(normalized)
            if line_hash not in self._seen_line_hashes:
                truly_new_lines.append(normalized)
                # Marca como vista
                self._seen_line_hashes.add(line_hash)
                self._seen_line_hashes_order.append(line_hash)
                # Se o deque alcançou maxlen, ele descarta o item mais antigo
                # automaticamente, mas a gente precisa remover do set também
                # pra não vazar memória.
                if len(self._seen_line_hashes) > self._seen_line_hashes_order.maxlen:
                    # Reconstrói o set baseado no deque (mantém só os recentes)
                    self._seen_line_hashes = set(self._seen_line_hashes_order)

        if not truly_new_lines:
            # Nada realmente novo — pode ser scroll, OCR redundante, etc.
            # Não atualiza nem o widget nem callbacks.
            log.debug(f"Captura sem linhas novas (provavelmente scroll). Total recebido: {len(lines)}")
            self._last_lines = lines  # ainda atualiza pra próxima comparação
            return

        # Traduz só as verdadeiramente novas
        translated = self.translator.translate_lines(truly_new_lines, src, dest)

        # Append no widget (sempre append agora, já que dedup garante novidade)
        self._append_to_widget(translated)

        self._last_lines = lines

        # Atualiza última linha capturada (idioma original) pro mini-pill
        for line in reversed(truly_new_lines):
            if line:
                self._last_captured_line = line
                break

        # Notifica callbacks
        if self.on_new_line and self._last_captured_line:
            try:
                self.on_new_line(self._last_captured_line)
            except Exception as e:
                log.error(f"on_new_line callback falhou: {e}")

        # Notifica histórico — uma chamada por linha REALMENTE nova,
        # passando original e traduzido pareados
        if self.on_truly_new_line:
            for original, translated_line in zip(truly_new_lines, translated):
                try:
                    self.on_truly_new_line(original, translated_line)
                except Exception as e:
                    log.error(f"on_truly_new_line callback falhou: {e}")

    @staticmethod
    def _compute_line_hash(line: str) -> str:
        """
        Calcula hash MD5 da linha (apenas 16 hex chars pra economizar memória).
        Normaliza pra lowercase + strip antes de hashear, pra OCR levemente
        diferente em frames adjacentes não dispararem como linhas distintas
        (ex: "Hello!" vs "Hello! " com espaço).
        """
        import hashlib
        normalized = line.strip().lower()
        return hashlib.md5(normalized.encode('utf-8', errors='ignore')).hexdigest()[:16]

    @staticmethod
    def _compute_highlight_color(bg: str, fg: str) -> str:
        """
        Calcula cor de fundo sutil pro destaque de linhas novas.
        Mistura bg + fg em proporção que dá contraste sutil.
        Funciona em qualquer tema (dark, light, dofus retro).
        """
        def hex_to_rgb(c):
            c = c.lstrip('#')
            if len(c) == 3:
                c = ''.join(ch * 2 for ch in c)
            return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)

        try:
            bg_rgb = hex_to_rgb(bg)
            fg_rgb = hex_to_rgb(fg)
            # 80% bg + 20% fg = destaque sutil
            mixed = tuple(int(b * 0.8 + f * 0.2) for b, f in zip(bg_rgb, fg_rgb))
            return rgb_to_hex(mixed)
        except Exception:
            return '#3a3324'  # fallback (marrom)

    @staticmethod
    def _is_append_scenario(old: list[str], new: list[str]) -> bool:
        if len(new) < len(old):
            return False
        return new[:len(old)] == old

    def _append_to_widget(self, lines: list[str]):
        if not self.text_widget or not lines:
            return
        self.master.after(0, self._do_append, lines)

    def _do_append(self, lines: list[str]):
        try:
            self.text_widget.config(state='normal')
            for line in lines:
                # v1.0.21: se tem linhas a destacar (acabou de expandir do pill),
                # aplica tag 'highlight' nelas. Senão, insere normal.
                if self._new_lines_to_highlight > 0:
                    start = self.text_widget.index(tk.END + "-1c")
                    self.text_widget.insert(tk.END, line + '\n')
                    end = self.text_widget.index(tk.END + "-1c")
                    self.text_widget.tag_add('highlight_new', start, end)
                    self._new_lines_to_highlight -= 1
                else:
                    self.text_widget.insert(tk.END, line + '\n')
            self.text_widget.yview_moveto(1.0)  # v1.0.24: scroll absoluto, evita buraco
            self.text_widget.config(state='disabled')
        except Exception as e:
            log.error(f"Erro ao escrever no widget: {e}")

    def _replace_widget_content(self, lines: list[str]):
        if not self.text_widget:
            return
        self.master.after(0, self._do_replace, lines)

    def _do_replace(self, lines: list[str]):
        try:
            self.text_widget.config(state='normal')
            self.text_widget.delete('1.0', tk.END)
            for line in lines:
                self.text_widget.insert(tk.END, line + '\n')
            self.text_widget.yview_moveto(1.0)  # v1.0.24: scroll absoluto, evita buraco
            self.text_widget.config(state='disabled')
        except Exception as e:
            log.error(f"Erro ao substituir conteúdo: {e}")

    # ========================================================================
    # v1.0.21: Histórico do chat (load/clear/highlight)
    # ========================================================================

    def _load_history_into_widget(self) -> bool:
        """
        Carrega últimas N entradas do chat_history.json no widget.

        Chamado em show() pra dar continuidade entre sessões.
        Retorna True se carregou algo, False se histórico vazio.
        """
        if not self.text_widget or not self.chat_history:
            return False

        try:
            entries = self.chat_history.all()
            if not entries:
                return False

            self.text_widget.config(state='normal')
            self.text_widget.delete('1.0', tk.END)
            for entry in entries:
                translated = entry.get('translated', '')
                if translated:
                    self.text_widget.insert(tk.END, translated + '\n')
            self.text_widget.yview_moveto(1.0)  # v1.0.24: scroll absoluto, evita buraco
            self.text_widget.config(state='disabled')

            # IMPORTANTE: também populamos o set de hashes pra que linhas já
            # carregadas do disco não sejam re-detectadas como "novas" se o
            # OCR capturar elas de novo (raro, mas possível em sessões longas).
            for entry in entries:
                original = entry.get('original', '').strip()
                if original:
                    h = self._compute_line_hash(original)
                    self._seen_line_hashes.add(h)
                    self._seen_line_hashes_order.append(h)

            log.info(f"Histórico carregado no overlay: {len(entries)} entradas")
            return True
        except Exception as e:
            log.error(f"Erro ao carregar histórico: {e}", exc_info=True)
            return False

    def clear_chat_history(self):
        """Limpa histórico (memória + disco) e widget."""
        if self.chat_history:
            self.chat_history.clear()
        # Reset dedup tbm pra "começar do zero"
        self._seen_line_hashes.clear()
        self._seen_line_hashes_order.clear()
        # Limpa widget
        if self.text_widget:
            try:
                self.text_widget.config(state='normal')
                self.text_widget.delete('1.0', tk.END)
                self.text_widget.config(state='disabled')
                self._show_waiting_message()
            except Exception as e:
                log.debug(f"clear widget falhou: {e}")

    def highlight_recent_lines(self, count: int, duration_ms: int = 5000):
        """
        Marca as próximas `count` linhas que chegarem com tag 'highlight_new'.
        Chamado quando expandindo do mini-pill — destaca as linhas que
        chegaram durante o colapso.

        Após `duration_ms`, remove o destaque.
        """
        self._new_lines_to_highlight = count
        # Remove highlight após duration_ms
        if self.text_widget:
            self.text_widget.after(duration_ms, self._clear_highlight_tag)

    def _clear_highlight_tag(self):
        if self.text_widget:
            try:
                self.text_widget.tag_remove('highlight_new', '1.0', tk.END)
            except Exception:
                pass

    def highlight_existing_recent(self, count: int, duration_ms: int = 5000):
        """
        Aplica destaque visual nas ÚLTIMAS `count` linhas JÁ existentes no widget.
        Usado quando expandindo do pill: as linhas novas já foram inseridas
        durante o tempo colapsado, então marcamos as últimas N pra destaque.
        """
        if not self.text_widget or count <= 0:
            return
        try:
            # Conta total de linhas no widget
            total_lines = int(self.text_widget.index('end-1c').split('.')[0])
            start_line = max(1, total_lines - count + 1)
            start = f"{start_line}.0"
            end = f"{total_lines}.end"
            self.text_widget.tag_add('highlight_new', start, end)
            self.text_widget.see(end)
            self.text_widget.after(duration_ms, self._clear_highlight_tag)
            log.info(f"Destacadas {count} linhas recentes (linhas {start_line}..{total_lines})")
        except Exception as e:
            log.debug(f"highlight_existing_recent falhou: {e}")

    def _show_waiting_message(self):
        if not self.text_widget:
            return
        self._showing_waiting_msg = True
        try:
            self.text_widget.config(state='normal')
            self.text_widget.delete('1.0', tk.END)
            self.text_widget.insert(tk.END, WAITING_MSG)
            self.text_widget.config(state='disabled')
        except Exception:
            pass

    def _show_empty_warning_message(self):
        if not self.text_widget or self._showing_waiting_msg:
            return
        self._showing_waiting_msg = True
        try:
            self.text_widget.config(state='normal')
            self.text_widget.delete('1.0', tk.END)
            self.text_widget.insert(tk.END, EMPTY_OCR_MSG)
            self.text_widget.config(state='disabled')
        except Exception:
            pass
