"""
Sistema central de temas pra janela principal e popups.
Contém 3 presets: dark, light, dofus_retro.
A janela overlay tem seu próprio sistema simplificado em overlay_window.py.
"""

THEMES = {
    'dark': {
        'bg': '#1a1a1a',
        'bg_panel': '#1e1e1e',
        'bg_input': '#2a2a2a',
        'bg_pill': '#3a3a3a',
        'bg_hover': '#4a4a4a',
        'border': '#444',
        'accent': '#e8d4a2',
        'accent_hover': '#b8a47a',
        'highlight': '#FF6100',
        'text': '#e0e0e0',
        'text_dim': '#888',
        'text_on_accent': '#1a1a1a',
        'text_on_highlight': '#ffffff',
        'success_bg': '#1f5c2e',
        'success_hover': '#2d7d40',
        'danger_bg': '#5a2222',
        'danger_hover': '#7d2d2d',
        'titlebar_bg': '#0f0f0f',
        'titlebar_close_hover': '#c44',
    },
    'light': {
        'bg': '#f5f5f5',
        'bg_panel': '#ffffff',
        'bg_input': '#ffffff',
        'bg_pill': '#e0e0e0',
        'bg_hover': '#d0d0d0',
        'border': '#cccccc',
        'accent': '#7a6b3f',
        'accent_hover': '#5a4f2e',
        'highlight': '#FF6100',
        'text': '#1a1a1a',
        'text_dim': '#666666',
        'text_on_accent': '#ffffff',
        'text_on_highlight': '#ffffff',
        'success_bg': '#2d7d40',
        'success_hover': '#1f5c2e',
        'danger_bg': '#c44',
        'danger_hover': '#a33',
        'titlebar_bg': '#e8e8e8',
        'titlebar_close_hover': '#c44',
    },
    'dofus_retro': {
        # Paleta nova baseada em #D5CFAA, #FF6100, #514A3C, #8C8368
        'bg': '#1a1614',
        'bg_panel': '#2a2520',
        'bg_input': '#3a3127',
        'bg_pill': '#514A3C',
        'bg_hover': '#8C8368',
        'border': '#514A3C',
        'accent': '#D5CFAA',
        'accent_hover': '#8C8368',
        'highlight': '#FF6100',
        'text': '#D5CFAA',
        'text_dim': '#8C8368',
        'text_on_accent': '#1a1614',
        'text_on_highlight': '#ffffff',
        'success_bg': '#3a5a3a',
        'success_hover': '#4a7a4a',
        'danger_bg': '#7a3a1a',
        'danger_hover': '#FF6100',
        'titlebar_bg': '#0f0c0a',
        'titlebar_close_hover': '#FF6100',
    },
}


def get_theme(name: str) -> dict:
    """Retorna paleta do tema. Fallback pra dofus_retro."""
    return THEMES.get(name, THEMES['dofus_retro'])


def list_theme_names() -> list[str]:
    return list(THEMES.keys())


THEME_LABELS = {
    'dark': 'Dark',
    'light': 'Light',
    'dofus_retro': 'Dofus Retro',
}
