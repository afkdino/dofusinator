"""
Metadados centrais do app. Single source of truth.
"""

APP_NAME = "Dofusinator"
APP_TAGLINE = "Translator"
APP_FULL_NAME = "Dofusinator (Translator)"
APP_VERSION = "1.1.0"
APP_AUTHOR = "@afkdino"
APP_AUTHOR_FULL = "@afkdino"
# v1.0.33: separação entre handle (usado em metadata técnico, paths, registry)
# e nome legal (usado em copyright). Misturar geraria registry keys com espaços
# e caracteres especiais.
APP_AUTHOR_LEGAL = "Guilherme G. Ferreira"
APP_ID = "Dofusinator"  # nome interno (sem espaços, usado em paths)
# v1.0.33: descrição corrigida pra refletir suporte real a 4 idiomas
# (FR, PT, EN, ES) e tradução bidirecional configurável, em vez de só PT↔FR
APP_DESCRIPTION = "Tradutor em tempo real do chat do Dofus Retro entre FR, PT, EN e ES"

# Identificadores únicos
APP_GUID = "{A7F3E2D8-5C4B-4F1E-9D7A-3B8E6F2C9A0E}"  # único, gerado uma vez
APP_REGISTRY_KEY = f"Software\\{APP_AUTHOR_FULL}\\{APP_ID}"
