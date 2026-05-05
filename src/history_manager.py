"""
Gerenciador de histórico de mensagens enviadas via quick input.
Persiste em history.json. Limite configurável.
"""
import json
import logging
from collections import deque
from pathlib import Path

from settings import Settings, get_app_dir

log = logging.getLogger(__name__)

HISTORY_FILE = get_app_dir() / "history.json"


class HistoryManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._history: deque = deque(maxlen=settings.get('history_max_entries', 20))
        self._load()

    def _load(self):
        if not HISTORY_FILE.exists():
            return
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                # Limita pelo max atual
                max_entries = self.settings.get('history_max_entries', 20)
                self._history = deque(data[-max_entries:], maxlen=max_entries)
            log.info(f"Histórico carregado: {len(self._history)} mensagens")
        except (json.JSONDecodeError, IOError) as e:
            log.error(f"Erro ao carregar histórico: {e}")

    def save(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self._history), f, indent=2, ensure_ascii=False)
        except IOError as e:
            log.error(f"Erro ao salvar histórico: {e}")

    def add(self, text: str):
        """Adiciona mensagem ao histórico (no fim = mais recente)."""
        if not self.settings.get('history_enabled', True):
            return
        text = text.strip()
        if not text:
            return
        # Remove duplicata (se já existe, vira a mais recente)
        try:
            self._history.remove(text)
        except ValueError:
            pass
        self._history.append(text)
        self.save()

    def all(self) -> list[str]:
        """Retorna mensagens em ordem decrescente (mais recente primeiro)."""
        return list(reversed(self._history))

    def clear(self):
        self._history.clear()
        self.save()
