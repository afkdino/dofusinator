"""
Gerenciador de hotkeys globais.

v1.1 (Sub-bloco 3.2):
  - Suporta MÚLTIPLOS atalhos (não só o de quick_input).
  - 3 callbacks customizáveis: quick_input (tradução), overlay_toggle, lurker_toggle
  - Cada um tem chave própria nas settings.
  - Detecção de conflitos: 2 atalhos não podem ter a mesma combinação.

Padrão de uso:
    hotkey_mgr = HotkeyManager(settings)
    hotkey_mgr.set_callback('quick_input', lambda: quick_input.show())
    hotkey_mgr.set_callback('overlay_toggle', lambda: overlay.toggle())
    hotkey_mgr.set_callback('lurker_toggle', lambda: main_window.toggle_lurker())
    hotkey_mgr.start()  # registra todos baseado nas settings
"""
import logging
from typing import Callable, Dict, Optional

from settings import Settings

log = logging.getLogger(__name__)


# IDs dos atalhos suportados (devem coincidir com chaves das settings)
HOTKEY_IDS = {
    'quick_input': {
        'setting_key': 'hotkey_quick_input',
        'default': 'ctrl+shift+t',
        'description': 'Popup de tradução rápida',
    },
    'overlay_toggle': {
        'setting_key': 'hotkey_overlay_toggle',
        'default': 'ctrl+shift+o',
        'description': 'Mostrar/colapsar overlay',
    },
    'lurker_toggle': {
        'setting_key': 'hotkey_lurker_toggle',
        'default': 'ctrl+shift+l',
        'description': 'Modo Lurker liga/desliga',
    },
}


class HotkeyManager:
    def __init__(self, settings: Settings, quick_input_popup=None):
        """
        Args:
            settings: Settings do app
            quick_input_popup: opcional, mantido pra compat retro com código antigo.
                               Se passado, registra automaticamente como callback do quick_input.
        """
        self.settings = settings
        self._callbacks: Dict[str, Callable] = {}
        # Mapa hotkey_id → string atualmente registrada
        self._registered: Dict[str, str] = {}

        # Compat retro: se passou quick_input, registra automaticamente
        self.quick_input = quick_input_popup
        if quick_input_popup is not None:
            self._callbacks['quick_input'] = self._build_quick_input_callback()

    # ========================================================================
    # API pública
    # ========================================================================

    def set_callback(self, hotkey_id: str, callback: Callable):
        """
        Define o callback pra um hotkey_id ('quick_input', 'overlay_toggle', 'lurker_toggle').
        Se já tava registrado e o callback é diferente, re-registra.
        """
        if hotkey_id not in HOTKEY_IDS:
            log.warning(f"hotkey_id '{hotkey_id}' desconhecido")
            return
        self._callbacks[hotkey_id] = callback

    def start(self):
        """Registra TODOS os hotkeys baseado nas settings."""
        for hotkey_id in HOTKEY_IDS:
            self._register_one(hotkey_id)

    def reload(self):
        """
        Re-registra todos os hotkeys baseado nas settings atuais.
        Chamado quando user muda configuração.
        """
        log.info("HotkeyManager.reload() — re-registrando todos os hotkeys")
        self.stop()
        self.start()

    def stop(self):
        """Desregistra todos os hotkeys."""
        if not self._registered:
            return
        try:
            import keyboard
            keyboard.unhook_all_hotkeys()
            log.info(f"Desregistrados {len(self._registered)} hotkeys")
        except Exception as e:
            log.error(f"Erro ao desregistrar hotkeys: {e}")
        self._registered.clear()

    def is_conflict(self, hotkey_str: str, exclude_id: Optional[str] = None) -> Optional[str]:
        """
        Verifica se a combinação `hotkey_str` já está registrada por outro hotkey.

        Args:
            hotkey_str: string da hotkey a testar (ex: "ctrl+shift+y")
            exclude_id: id pra ignorar (ex: se tu tá editando 'overlay_toggle',
                        passa exclude_id='overlay_toggle' pra não considerar
                        conflito com ele mesmo).

        Returns:
            hotkey_id que conflita, ou None se não há conflito.
        """
        normalized = self._normalize(hotkey_str)
        for other_id in HOTKEY_IDS:
            if other_id == exclude_id:
                continue
            other_setting = HOTKEY_IDS[other_id]['setting_key']
            other_hk = self._normalize(self.settings.get(other_setting, ''))
            if other_hk and other_hk == normalized:
                return other_id
        return None

    # ========================================================================
    # Internal
    # ========================================================================

    def _normalize(self, hotkey_str: str) -> str:
        """Lowercase + ordena modificadores canonicamente."""
        if not hotkey_str:
            return ''
        s = hotkey_str.lower().strip()
        parts = [p.strip() for p in s.split('+') if p.strip()]
        modifiers = []
        main_keys = []
        for p in parts:
            if p in ('ctrl', 'alt', 'shift', 'win', 'cmd'):
                modifiers.append(p)
            else:
                main_keys.append(p)
        order = ['ctrl', 'alt', 'shift', 'win', 'cmd']
        modifiers.sort(key=lambda m: order.index(m) if m in order else 999)
        return '+'.join(modifiers + main_keys)

    def _register_one(self, hotkey_id: str):
        """Registra um único hotkey baseado nas settings."""
        if hotkey_id not in HOTKEY_IDS:
            return

        info = HOTKEY_IDS[hotkey_id]
        setting_key = info['setting_key']
        default_hk = info['default']
        hotkey_str = self.settings.get(setting_key, default_hk)

        if not hotkey_str:
            log.debug(f"Hotkey '{hotkey_id}' vazia nas settings, pulando")
            return

        callback = self._callbacks.get(hotkey_id)
        if not callback:
            log.debug(f"Hotkey '{hotkey_id}' sem callback definido, pulando")
            return

        try:
            import keyboard
        except ImportError:
            log.error("Lib 'keyboard' não instalada.")
            return

        try:
            keyboard.add_hotkey(hotkey_str, callback)
            self._registered[hotkey_id] = hotkey_str
            log.info(f"Hotkey '{hotkey_id}' registrada: {hotkey_str}")
        except Exception as e:
            log.error(f"Erro ao registrar hotkey '{hotkey_id}' ({hotkey_str}): {e}")

    def _build_quick_input_callback(self):
        """Wrapper compat retro pra abrir o popup quick_input."""
        def cb():
            try:
                if self.quick_input:
                    self.quick_input.master.after(0, self.quick_input.show)
            except Exception as e:
                log.error(f"Erro ao acionar quick input: {e}")
        return cb
