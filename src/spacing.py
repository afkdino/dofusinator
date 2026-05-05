"""
Sistema de espaçamento padronizado pro Dofusinator.

Constantes baseadas em escala 4px (padrão de design systems modernos).
Usar essas constantes em TODA a UI pra garantir consistência visual.

Convenção:
  - XS  (4px)  — espaçamento mínimo entre elementos super próximos
  - SM  (8px)  — entre elementos relacionados
  - MD  (12px) — padding base de containers e popups
  - LG  (16px) — separação de seções dentro de uma janela
  - XL  (24px) — separação de blocos grandes
  - XXL (32px) — padding externo de janelas grandes (ex: welcome)

Bônus:
  - WINDOW_PADDING — padding mínimo das bordas externas das janelas
  - BUTTON_PADDING_X / Y — padding interno padrão de botões
  - INPUT_PADDING — padding interno de inputs

v1.0.22 / Bloco 3.2 final
"""

# ============================================================================
# Escala base (4px)
# ============================================================================
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_XXL = 32

# ============================================================================
# Aliases semânticos (use estes ao invés dos básicos quando o contexto fizer sentido)
# ============================================================================

# Padding mínimo das bordas externas de uma janela (entre conteúdo e edge)
# IMPORTANTE: nunca menor que isso pra evitar texto colado na borda.
WINDOW_PADDING = SPACING_MD  # 12px

# Padding interno do conteúdo de uma janela (entre titlebar e widgets)
WINDOW_CONTENT_PADDING_X = SPACING_LG  # 16px
WINDOW_CONTENT_PADDING_Y = SPACING_MD  # 12px

# Status bar / footer padding
FOOTER_PADDING_X = SPACING_MD   # 12px
FOOTER_PADDING_Y = SPACING_SM   # 8px

# Padding interno dos botões padrões
BUTTON_PADDING_X = SPACING_MD   # 12px
BUTTON_PADDING_Y = SPACING_SM   # 8px

# Padding de inputs
INPUT_PADDING = SPACING_SM  # 8px

# Espaçamento entre títulos de seção e seu conteúdo
SECTION_HEADER_SPACING = SPACING_SM  # 8px

# Espaçamento entre seções consecutivas
SECTION_GAP = SPACING_LG  # 16px

# Espaçamento entre linhas de form (label + input)
FORM_ROW_GAP = SPACING_SM  # 8px

# ============================================================================
# Helpers (uso opcional, retornam tuplas pra pack/grid padx/pady)
# ============================================================================

def window_padding():
    """Tupla pra padx/pady de packing externo de uma janela."""
    return (WINDOW_PADDING, WINDOW_PADDING)

def section_padding():
    """Tupla pra packing entre seções."""
    return (SECTION_GAP, SECTION_GAP)

def footer_padding():
    """Tupla pra packing de barras de status/rodapé."""
    return (FOOTER_PADDING_X, FOOTER_PADDING_Y)
