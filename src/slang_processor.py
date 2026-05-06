"""
Processador de gírias.
Expande gírias gamer/Dofus antes de traduzir, melhora qualidade da tradução.
Lê dicionário de arquivo JSON externo (editável pelo usuário).
"""
import json
import logging
import re
from pathlib import Path

from settings import get_app_dir, get_resource_dir

log = logging.getLogger(__name__)

SLANG_FILE = get_resource_dir() / "slang_dictionary.json"

# Dicionário default - será gravado como JSON na primeira execução.
# Usuário pode editar livremente.
DEFAULT_SLANG = {
    "pt": {
        # Comuns brasileiros
        "vc": "você",
        "voce": "você",
        "vcs": "vocês",
        "blz": "beleza",
        "tb": "também",
        "tbm": "também",
        "tmj": "tamo junto",
        "pq": "porque",
        "q ": "que ",
        "n ": "não ",
        "ñ": "não",
        "obg": "obrigado",
        "vlw": "valeu",
        "flw": "falou",
        "msg": "mensagem",
        "mt": "muito",
        "mto": "muito",
        "td": "tudo",
        "tdo": "todo",
        "kkk": "haha",
        "kkkk": "haha",
        "kkkkk": "haha",
        "rs": "haha",
        "rsrs": "haha",
        # Gaming PT-BR
        "lvl": "nível",
        "xp": "experiência",
        "pvp": "PvP",
        "buff": "melhoramento",
        "nerf": "enfraquecimento",
        "drop": "item caído",
        "pt": "grupo",
        "guild": "guilda",
        "boss": "chefão",
        "mob": "monstro",
        # Dofus PT
        "carai": "caraca",
        "cara": "amigo",
        "mano": "amigo",
        "brother": "amigo",
        "tropa": "grupo",
    },
    "fr": {
        # Internet FR comuns
        "mdr": "mort de rire",
        "ptdr": "pété de rire",
        "lol": "haha",
        "bg": "beau gosse",
        "frérot": "frère",
        "frero": "frère",
        "reuf": "frère",
        "wsh": "wesh",
        "tkt": "ne t'inquiète pas",
        "askip": "à ce qu'il paraît",
        "stp": "s'il te plaît",
        "svp": "s'il vous plaît",
        "jpp": "je n'en peux plus",
        "qqn": "quelqu'un",
        "qqch": "quelque chose",
        "tt": "tout",
        "mrc": "merci",
        "cc": "coucou",
        "dsl": "désolé",
        "bsr": "bonsoir",
        "bjr": "bonjour",
        # Gaming FR
        "vend": "vends",
        "ach": "achète",
        "achete": "achète",
        "ech": "échange",
        "echange": "échange",
        "cherche": "cherche",
        "rch": "recherche",
        "recrute": "recrute",
        "grp": "groupe",
        "lvl": "niveau",
        "xp": "expérience",
        "tp": "téléport",
        "pa": "points d'action",
        "pm": "points de mouvement",
        "pdv": "points de vie",
        # Dofus FR específicas
        "dj": "donjon",
        "dnj": "donjon",
        "perco": "percepteur",
        "kk": "kamas",
        "k": "kamas",
        "kamas": "kamas",
        "piwi": "vitalité",
        "feca": "feca",
        "iop": "iop",
        "cra": "cra",
        "panda": "pandawa",
    },
    "es": {
        # Internet ES
        "xq": "por qué",
        "pq": "por qué",
        "q": "que",
        "k": "que",
        "tb": "también",
        "tmb": "también",
        "tbn": "también",
        "tk": "te quiero",
        "tkm": "te quiero mucho",
        "xfa": "por favor",
        "pf": "por favor",
        "salu2": "saludos",
        "bn": "bien",
        "vrd": "verdad",
        "wnas": "buenas",
        "jaja": "haha",
        "jajaja": "haha",
        # Gaming ES
        "lvl": "nivel",
        "xp": "experiencia",
        "pj": "personaje",
        "vendo": "vendo",
        "compro": "compro",
        "mp": "mensaje privado",
        "grupo": "grupo",
        "mazmorra": "mazmorra",
        "csm": "concha su madre",
        "ctm": "concha tu madre",
    },
    "en": {
        # Internet EN
        "lmao": "haha",
        "lmfao": "haha",
        "lol": "haha",
        "rofl": "haha",
        "smh": "I disagree",
        "brb": "be right back",
        "afk": "away from keyboard",
        "imo": "in my opinion",
        "imho": "in my humble opinion",
        "tbh": "to be honest",
        "ngl": "not gonna lie",
        "fml": "frustration",
        "wtf": "what",
        "wth": "what",
        "u": "you",
        "ur": "your",
        "r": "are",
        "thx": "thanks",
        "ty": "thank you",
        "np": "no problem",
        "yw": "you're welcome",
        "pls": "please",
        "plz": "please",
        # Gaming EN
        "gg": "good game",
        "wp": "well played",
        "ez": "easy",
        "op": "overpowered",
        "nerf": "weaken",
        "buff": "strengthen",
        "afk": "away",
        "lvl": "level",
        "xp": "experience",
        "pm": "private message",
        "dm": "direct message",
        "dps": "damage",
        "tank": "tank role",
        "heal": "healer",
    }
}


class SlangProcessor:
    def __init__(self):
        self._slang: dict = {}
        self._load_or_create()

    def _load_or_create(self):
        if not SLANG_FILE.exists():
            try:
                with open(SLANG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_SLANG, f, indent=2, ensure_ascii=False)
                log.info(f"Dicionário de gírias criado em {SLANG_FILE}")
                self._slang = DEFAULT_SLANG.copy()
                return
            except IOError as e:
                log.error(f"Erro ao criar dicionário: {e}. Usando defaults em memória.")
                self._slang = DEFAULT_SLANG.copy()
                return

        try:
            with open(SLANG_FILE, 'r', encoding='utf-8') as f:
                self._slang = json.load(f)
            log.info(f"Dicionário de gírias carregado: {sum(len(v) for v in self._slang.values())} entradas")
        except (json.JSONDecodeError, IOError) as e:
            log.error(f"Erro ao carregar dicionário: {e}. Usando defaults.")
            self._slang = DEFAULT_SLANG.copy()

    def expand(self, text: str, language: str) -> str:
        """Expande gírias do idioma especificado em um texto."""
        if not text or language not in self._slang:
            return text

        result = text
        slang_dict = self._slang[language]

        # Ordem por tamanho decrescente: gírias mais longas primeiro
        # (evita "kk" comer "kkkk")
        for slang in sorted(slang_dict.keys(), key=len, reverse=True):
            replacement = slang_dict[slang]
            # Substituição respeitando word boundary (não substitui dentro de palavras)
            # Exceto pra padrões como "kkk" que não tem boundary natural
            pattern = r'\b' + re.escape(slang) + r'\b'
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def reload(self):
        """Recarrega dicionário do disco. Útil pra editar gírias em runtime."""
        self._load_or_create()
