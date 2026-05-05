"""
ChatHistoryManager - Histórico de linhas do chat capturadas pelo OCR.

DIFERENTE do `history_manager.py` que guarda mensagens ENVIADAS via quick input.
Esse aqui guarda o que foi LIDO/CAPTURADO do chat do jogo.

Cada entrada:
  {
    "ts": "2026-05-04T22:30:15",  # timestamp ISO
    "original": "Bonjour tout le monde",
    "translated": "Olá pessoal",
    "src": "fr",
    "dest": "pt"
  }

Persistência: chat_history.json no AppData. Limite default 500 entradas (FIFO).

v1.0.21 / Bloco 3.2 refinado
"""
import json
import logging
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from settings import Settings, get_app_dir

log = logging.getLogger(__name__)

CHAT_HISTORY_FILE = get_app_dir() / "chat_history.json"
DEFAULT_MAX_ENTRIES = 500


class ChatHistoryManager:
    """
    Gerencia histórico de linhas do chat capturadas e traduzidas.

    Uso:
        history = ChatHistoryManager(settings)
        history.add(original="Bonjour", translated="Olá", src="fr", dest="pt")
        for entry in history.all():
            print(entry['translated'])
        history.clear()
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._max = settings.get('chat_history_max_entries', DEFAULT_MAX_ENTRIES)
        self._history: deque = deque(maxlen=self._max)
        # Callbacks pra UI ser notificada quando algo muda
        self._observers: list[Callable[[], None]] = []
        self._load()

    # ========================================================================
    # API pública
    # ========================================================================

    def add(self, original: str, translated: str, src: str = "", dest: str = ""):
        """Adiciona uma entrada nova ao histórico."""
        original = (original or "").strip()
        translated = (translated or "").strip()
        if not original and not translated:
            return

        entry = {
            "ts": datetime.now().isoformat(timespec='seconds'),
            "original": original,
            "translated": translated,
            "src": src,
            "dest": dest,
        }
        self._history.append(entry)
        self._save()
        self._notify()

    def all(self) -> list[dict]:
        """Retorna todas as entradas em ordem cronológica (mais antiga primeiro)."""
        return list(self._history)

    def latest(self, n: int = 50) -> list[dict]:
        """Últimas N entradas (mais recente primeiro)."""
        return list(reversed(list(self._history)[-n:]))

    def count(self) -> int:
        return len(self._history)

    def clear(self):
        """Limpa todo o histórico (e o arquivo)."""
        self._history.clear()
        self._save()
        self._notify()
        log.info("Chat history limpo")

    def add_observer(self, callback: Callable[[], None]):
        """Registra um callback que é chamado a cada mudança."""
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[], None]):
        if callback in self._observers:
            self._observers.remove(callback)

    # ========================================================================
    # Internal
    # ========================================================================

    def _notify(self):
        """Chama todos os observers (UI atualiza)."""
        for cb in self._observers:
            try:
                cb()
            except Exception as e:
                log.error(f"ChatHistory observer falhou: {e}")

    def _load(self):
        if not CHAT_HISTORY_FILE.exists():
            return
        try:
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                # Limita pelo max atual
                self._history = deque(data[-self._max:], maxlen=self._max)
            log.info(f"Chat history carregado: {len(self._history)} entradas")
        except (json.JSONDecodeError, IOError) as e:
            log.error(f"Erro ao carregar chat history: {e}")

    def _save(self):
        try:
            with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self._history), f, ensure_ascii=False, indent=2)
        except IOError as e:
            log.error(f"Erro ao salvar chat history: {e}")
