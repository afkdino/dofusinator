"""
Gerenciamento de configurações em JSON portátil.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def get_app_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def get_resource_dir() -> Path:
    """
    Retorna a pasta onde estao os assets bundleados (sounds, assets, dicts).

    v1.0.34: PyInstaller --onedir poe assets em _internal/ ao lado do .exe.
    Antes desse fix, o app procurava em get_app_dir()/sounds (raiz do exe)
    e nao achava nada quando empacotado, mesmo PyInstaller bundleando ok.

    - Modo dev (python src/main.py): raiz do projeto.
    - Modo empacotado (PyInstaller --onedir): pasta _internal/ ao lado do .exe.

    Use isso pra recursos READ-ONLY que vem com a instalacao (sons, icones,
    dicts, etc). Pra arquivos READ/WRITE do usuario (settings, cache,
    history) continua usando get_app_dir() — esses ficam ao lado do .exe.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / "_internal"
    return Path(__file__).parent.parent


SETTINGS_FILE = get_app_dir() / "settings.json"

DEFAULTS = {
    # Tradução
    "source_language_read": "fr",
    "target_language_read": "pt",
    "source_language_write": "pt",
    "target_language_write": "fr",
    "translator_backend": "google",
    "deepl_api_key": "",

    # Captura/OCR
    "perimeter": None,
    "chat_bar": None,
    "check_interval": 1.0,
    "ocr_language": "fra",
    "tesseract_path": "",

    # Pré-processamento OCR
    "ocr_preprocess_invert": True,
    "ocr_preprocess_contrast": 2.0,
    "ocr_preprocess_scale": 2,
    "ocr_preprocess_grayscale": True,
    "ocr_save_debug_images": False,

    # Cache
    "cache_enabled": True,
    "cache_max_entries": 1000,

    # Write mode
    "auto_send": False,
    "send_countdown_visual": False,

    # Modo Lurker
    "lurker_mode": False,

    # Quick input
    "quick_input_position_mode": "cursor",
    "quick_input_last_position": None,
    "quick_input_cursor_offset": [15, 15],

    # Histórico
    "history_enabled": True,
    "history_max_entries": 20,

    # Multi-monitor
    "overlay_geometries_by_monitor": {},
    "overlay_default_monitor": None,

    # Overlay
    "overlay_enabled": True,
    "overlay_geometry": "600x400+100+100",
    "overlay_alpha": 0.92,
    "overlay_bg_color": "#1a1614",
    "overlay_fg_color": "#D5CFAA",
    "overlay_font_family": "Consolas",
    "overlay_font_size": 12,
    "overlay_always_on_top": True,
    "overlay_theme_preset": "dofus_retro",

    # Hotkey
    "hotkey_quick_input": "ctrl+shift+t",
    # Hotkeys novas (Sub-bloco 3.2)
    "hotkey_overlay_toggle": "ctrl+shift+o",
    "hotkey_lurker_toggle": "ctrl+shift+l",
    # === Chat history (v1.0.21) ===
    # Histórico das linhas capturadas/traduzidas do chat. Persiste em
    # chat_history.json no AppData. FIFO com limite abaixo.
    "chat_history_max_entries": 500,
    # Mostrar dica de "linhas duplicadas só contam uma vez" (informativo)
    "chat_history_show_dedup_hint": True,
    # === Bloco 3.3 v2 (v1.0.29): Expander de customização avançada em Aparência ===
    # Estado do expander "▶ Customização avançada" (colapsado/expandido).
    # Persiste entre sessões pra user que sempre customiza não precisar
    # clicar pra abrir toda vez.
    "appearance_advanced_expanded": False,

    # Som
    "sound_enabled": True,
    "sound_file": "pop.wav",
    "sound_volume": 50,

    # Tema
    "main_window_theme": "dofus_retro",

    # === Idioma da UI (v1.1 / Bloco 2) ===
    # 'pt' (default), 'en', 'fr', 'es'. Trocar requer restart (oferecido em diálogo).
    "ui_language": "pt",

    # === Welcome screen (v1.1 / Bloco 3) ===
    # False = primeira execução, mostra tutorial. True = já fez ou pulou.
    "first_run_completed": False,

    # === NOVA v3.3 ===
    # Comportamento do botão X
    "close_to_tray": False,  # False = X fecha; True = X minimiza pra tray

    # Logging
    "logging_enabled": False,
}


class Settings:
    def __init__(self):
        self._data: dict = DEFAULTS.copy()

    def load(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                for key, value in loaded.items():
                    if key in DEFAULTS:
                        self._data[key] = value
                log.info(f"Settings carregadas de {SETTINGS_FILE}")
            except (json.JSONDecodeError, IOError) as e:
                log.error(f"Erro ao carregar settings: {e}. Usando defaults.")

    def save(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            log.debug(f"Settings salvas")
        except IOError as e:
            log.error(f"Erro ao salvar settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value

    def update(self, **kwargs):
        self._data.update(kwargs)

    def all(self) -> dict:
        return self._data.copy()
