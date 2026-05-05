"""
Gerenciador de termos personalizados.
Termos cross-language (ex: FR 'pano' = PT 'conjunto') que devem ser
preservados na tradução via placeholders protegidos.
"""
import json
import logging
import re
from pathlib import Path
from typing import Optional

from settings import get_app_dir

log = logging.getLogger(__name__)

CUSTOM_TERMS_FILE = get_app_dir() / "custom_terms.json"


class CustomTermsManager:
    """
    Mantém lista de termos personalizados.

    Estrutura interna: lista de dicts:
        {"src_lang": "fr", "src_term": "pano", "dst_lang": "pt", "dst_term": "conjunto"}

    Quando um termo é adicionado com 'add_reverse=True', adiciona automaticamente
    o reverso (pt: conjunto -> fr: pano).
    """

    def __init__(self):
        self._terms: list[dict] = []
        self._load()

    def _load(self):
        if not CUSTOM_TERMS_FILE.exists():
            self._terms = []
            return
        try:
            with open(CUSTOM_TERMS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                self._terms = [
                    t for t in data
                    if all(k in t for k in ('src_lang', 'src_term', 'dst_lang', 'dst_term'))
                ]
            else:
                self._terms = []
            log.info(f"Termos personalizados carregados: {len(self._terms)}")
        except (json.JSONDecodeError, IOError) as e:
            log.error(f"Erro ao carregar custom_terms.json: {e}")
            self._terms = []

    def save(self):
        try:
            with open(CUSTOM_TERMS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._terms, f, indent=2, ensure_ascii=False)
            log.debug(f"Termos personalizados salvos: {len(self._terms)}")
        except IOError as e:
            log.error(f"Erro ao salvar custom_terms.json: {e}")

    def reload(self):
        self._load()

    def all(self) -> list[dict]:
        return list(self._terms)

    def add(
        self,
        src_lang: str,
        src_term: str,
        dst_lang: str,
        dst_term: str,
        add_reverse: bool = True,
    ) -> tuple[bool, str]:
        """
        Adiciona termo. Retorna (sucesso, mensagem).
        Se add_reverse=True, adiciona também o reverso automaticamente.
        """
        src_lang = src_lang.strip().lower()
        dst_lang = dst_lang.strip().lower()
        src_term = src_term.strip()
        dst_term = dst_term.strip()

        if not src_term or not dst_term:
            return False, "Os termos não podem estar vazios."
        if src_lang == dst_lang:
            return False, "Os idiomas de origem e destino devem ser diferentes."

        # Verifica duplicado (mesmo src_lang + src_term)
        for t in self._terms:
            if t['src_lang'] == src_lang and t['src_term'].lower() == src_term.lower():
                return False, f"Já existe um termo '{src_term}' em {src_lang.upper()}."

        self._terms.append({
            'src_lang': src_lang,
            'src_term': src_term,
            'dst_lang': dst_lang,
            'dst_term': dst_term,
        })

        added_reverse = False
        if add_reverse:
            # Verifica se já existe reverso
            already_exists = any(
                t['src_lang'] == dst_lang and t['src_term'].lower() == dst_term.lower()
                for t in self._terms
            )
            if not already_exists:
                self._terms.append({
                    'src_lang': dst_lang,
                    'src_term': dst_term,
                    'dst_lang': src_lang,
                    'dst_term': src_term,
                })
                added_reverse = True

        self.save()
        msg = f"Termo adicionado: {src_lang.upper()} '{src_term}' → {dst_lang.upper()} '{dst_term}'"
        if added_reverse:
            msg += " (+ reverso)"
        return True, msg

    def remove(self, index: int) -> bool:
        if 0 <= index < len(self._terms):
            removed = self._terms.pop(index)
            self.save()
            log.info(f"Termo removido: {removed}")
            return True
        return False

    def update(self, index: int, src_lang: str, src_term: str, dst_lang: str, dst_term: str) -> tuple[bool, str]:
        """Atualiza termo existente. Não cria reverso (edição é específica)."""
        if not (0 <= index < len(self._terms)):
            return False, "Índice inválido."

        src_lang = src_lang.strip().lower()
        dst_lang = dst_lang.strip().lower()
        src_term = src_term.strip()
        dst_term = dst_term.strip()

        if not src_term or not dst_term:
            return False, "Os termos não podem estar vazios."
        if src_lang == dst_lang:
            return False, "Idiomas devem ser diferentes."

        # Verifica duplicação com outros termos (excluindo o próprio)
        for i, t in enumerate(self._terms):
            if i == index:
                continue
            if t['src_lang'] == src_lang and t['src_term'].lower() == src_term.lower():
                return False, f"Já existe outro termo '{src_term}' em {src_lang.upper()}."

        self._terms[index] = {
            'src_lang': src_lang,
            'src_term': src_term,
            'dst_lang': dst_lang,
            'dst_term': dst_term,
        }
        self.save()
        return True, "Termo atualizado."

    def apply_protected(
        self, text: str, src_lang: str, dst_lang: str
    ) -> tuple[str, dict]:
        """
        Substitui termos custom por placeholders neutros antes da tradução.
        Retorna (texto_modificado, mapping {placeholder: termo_final}).

        Exemplo: text="qui vend ce pano?", src=fr, dst=pt
                -> ("qui vend ce __T0001__?", {"__T0001__": "conjunto"})
        """
        if not text or not self._terms:
            return text, {}

        src_lang = src_lang.lower()
        dst_lang = dst_lang.lower()

        relevant = [
            t for t in self._terms
            if t['src_lang'] == src_lang and t['dst_lang'] == dst_lang
        ]
        if not relevant:
            return text, {}

        # Ordena por tamanho do src_term decrescente (termos longos primeiro)
        relevant.sort(key=lambda t: len(t['src_term']), reverse=True)

        result = text
        mapping: dict[str, str] = {}
        counter = 0

        for term in relevant:
            src = term['src_term']
            dst = term['dst_term']
            # Lookaround: aceita transição com dígitos/símbolos mas não com letras.
            # Assim "50kk" pega o "kk", mas "panorama" não pega "pano".
            pattern = r'(?<![a-zA-Zà-ÿÀ-Ÿ])' + re.escape(src) + r'(?![a-zA-Zà-ÿÀ-Ÿ])'
            if not re.search(pattern, result, flags=re.IGNORECASE):
                continue

            placeholder = f"__T{counter:04d}__"
            counter += 1
            result = re.sub(pattern, placeholder, result, flags=re.IGNORECASE)
            mapping[placeholder] = dst

        return result, mapping

    @staticmethod
    def restore_placeholders(text: str, mapping: dict) -> str:
        """Substitui placeholders pelos termos finais."""
        if not mapping:
            return text
        result = text
        for placeholder, term in mapping.items():
            result = result.replace(placeholder, term)
        return result
