"""
Serviço de tradução. Suporta Google (default) e DeepL (opcional).
Tem cache em memória + persistência e termos personalizados protegidos.
"""
import json
import logging
from collections import OrderedDict
from typing import Optional

from settings import Settings, get_app_dir
from slang_processor import SlangProcessor
from custom_terms import CustomTermsManager

log = logging.getLogger(__name__)

CACHE_FILE = get_app_dir() / "cache.json"


class TranslationCache:
    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._load()

    def _key(self, text: str, src: str, dest: str, backend: str) -> str:
        return f"{backend}|{src}->{dest}|{text}"

    def get(self, text: str, src: str, dest: str, backend: str) -> Optional[str]:
        key = self._key(text, src, dest, backend)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, text: str, src: str, dest: str, backend: str, translation: str):
        key = self._key(text, src, dest, backend)
        self._cache[key] = translation
        self._cache.move_to_end(key)
        while len(self._cache) > self.max_entries:
            self._cache.popitem(last=False)

    def _load(self):
        if not CACHE_FILE.exists():
            return
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._cache = OrderedDict(data.items())
            while len(self._cache) > self.max_entries:
                self._cache.popitem(last=False)
            log.info(f"Cache carregado: {len(self._cache)} entradas")
        except (json.JSONDecodeError, IOError) as e:
            log.error(f"Erro ao carregar cache: {e}")

    def save(self):
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(dict(self._cache), f, ensure_ascii=False)
            log.debug(f"Cache salvo: {len(self._cache)} entradas")
        except IOError as e:
            log.error(f"Erro ao salvar cache: {e}")


class TranslatorService:
    def __init__(
        self,
        settings: Settings,
        slang: SlangProcessor,
        custom_terms: CustomTermsManager,
    ):
        self.settings = settings
        self.slang = slang
        self.custom_terms = custom_terms
        self.cache = TranslationCache(
            max_entries=settings.get('cache_max_entries', 1000)
        )

    def _backend(self) -> str:
        return self.settings.get('translator_backend', 'google')

    def _translate_google(self, text: str, src: str, dest: str) -> str:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source=src, target=dest).translate(text)

    def _translate_deepl(self, text: str, src: str, dest: str) -> str:
        from deep_translator import DeeplTranslator
        api_key = self.settings.get('deepl_api_key', '').strip()
        if not api_key:
            log.warning("DeepL selecionado mas API key vazia. Caindo pra Google.")
            return self._translate_google(text, src, dest)
        return DeeplTranslator(
            api_key=api_key, source=src, target=dest, use_free_api=True
        ).translate(text)

    def translate(
        self,
        text: str,
        src: str,
        dest: str,
        expand_slang: bool = True,
    ) -> str:
        if not text or not text.strip():
            return text

        text_with_placeholders, restore_map = self.custom_terms.apply_protected(
            text, src, dest
        )

        if expand_slang:
            text_with_placeholders = self.slang.expand(text_with_placeholders, src)

        backend = self._backend()

        if self.settings.get('cache_enabled', True):
            cached = self.cache.get(text_with_placeholders, src, dest, backend)
            if cached is not None:
                log.debug(f"Cache hit: {text_with_placeholders[:30]!r}")
                return self.custom_terms.restore_placeholders(cached, restore_map)

        try:
            if backend == 'deepl':
                result = self._translate_deepl(text_with_placeholders, src, dest)
            else:
                result = self._translate_google(text_with_placeholders, src, dest)
        except Exception as e:
            log.error(f"Erro de tradução ({backend}): {e}")
            raise  # Repassa pra UI poder mostrar mensagem

        if result is None:
            return text

        if self.settings.get('cache_enabled', True):
            self.cache.put(text_with_placeholders, src, dest, backend, result)

        result = self.custom_terms.restore_placeholders(result, restore_map)
        return result

    def translate_lines(self, lines: list[str], src: str, dest: str) -> list[str]:
        out = []
        for line in lines:
            if not line.strip():
                continue
            try:
                out.append(self.translate(line, src, dest))
            except Exception as e:
                log.error(f"Linha falhou na tradução: {e}")
                out.append(line)  # Mantém original em caso de erro
        return out
