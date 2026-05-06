"""
Sistema de internacionalização (i18n) do Dofusinator.

Uso:
    from i18n import t, set_language

    set_language('en')  # PT-BR, EN, FR, ES
    label.configure(text=t('btn.save'))

Convenção de chaves: usar dot notation por escopo
    btn.* — botões
    label.* — labels descritivos
    section.* — section headers
    tab.* — abas
    msg.* — mensagens de status / diálogos
    title.* — títulos de janelas
    tooltip.* — dicas

Pra adicionar idioma novo: copia o dicionário e traduz cada string.
Strings com placeholder usam {var} estilo str.format().
"""
import logging

log = logging.getLogger(__name__)


SUPPORTED_LANGUAGES = ['pt', 'en', 'fr', 'es']
DEFAULT_LANGUAGE = 'pt'

# Idioma atual em memória — set_language() altera
_current_lang = DEFAULT_LANGUAGE


# =============================================================================
# DICIONÁRIO DE TRADUÇÕES
# =============================================================================
TRANSLATIONS = {
    # ========================================================================
    # ABAS DA JANELA PRINCIPAL
    # ========================================================================
    'tab.capture': {
        'pt': 'Captura', 'en': 'Capture', 'fr': 'Capture', 'es': 'Captura',
    },
    'tab.translation': {
        'pt': 'Tradução', 'en': 'Translation', 'fr': 'Traduction', 'es': 'Traducción',
    },
    'tab.appearance': {
        'pt': 'Aparência', 'en': 'Appearance', 'fr': 'Apparence', 'es': 'Apariencia',
    },
    'tab.shortcut_sound': {
        'pt': 'Atalho & Som', 'en': 'Shortcut & Sound', 'fr': 'Raccourci & Son', 'es': 'Atajo & Sonido',
    },
    'tab.advanced': {
        'pt': 'Avançado', 'en': 'Advanced', 'fr': 'Avancé', 'es': 'Avanzado',
    },

    # ========================================================================
    # BOTÕES GLOBAIS
    # ========================================================================
    'btn.apply_save': {
        'pt': 'Aplicar e Salvar', 'en': 'Apply & Save', 'fr': 'Appliquer et Enregistrer', 'es': 'Aplicar y Guardar',
    },
    'btn.apply_settings': {
        'pt': 'Aplicar Configurações', 'en': 'Apply Settings', 'fr': 'Appliquer Paramètres', 'es': 'Aplicar Configuración',
    },
    'btn.close': {
        'pt': 'Fechar', 'en': 'Close', 'fr': 'Fermer', 'es': 'Cerrar',
    },
    'btn.cancel': {
        'pt': 'Cancelar', 'en': 'Cancel', 'fr': 'Annuler', 'es': 'Cancelar',
    },
    'btn.ok': {
        'pt': 'OK', 'en': 'OK', 'fr': 'OK', 'es': 'OK',
    },
    'btn.yes': {
        'pt': 'Sim', 'en': 'Yes', 'fr': 'Oui', 'es': 'Sí',
    },
    'btn.no': {
        'pt': 'Não', 'en': 'No', 'fr': 'Non', 'es': 'No',
    },

    # ========================================================================
    # LURKER MODE (botão grande)
    # ========================================================================
    'lurker.active': {
        'pt': '🟢 LURKER ATIVO  (apenas leitura — clique pra desativar)',
        'en': '🟢 LURKER ACTIVE  (read-only — click to disable)',
        'fr': '🟢 LURKER ACTIF  (lecture seule — cliquez pour désactiver)',
        'es': '🟢 LURKER ACTIVO  (sólo lectura — clic para desactivar)',
    },
    'lurker.inactive': {
        'pt': '🛑 ATIVAR MODO LURKER  (somente leitura — bloqueia auto-send)',
        'en': '🛑 ENABLE LURKER MODE  (read-only — blocks auto-send)',
        'fr': '🛑 ACTIVER MODE LURKER  (lecture seule — bloque auto-envoi)',
        'es': '🛑 ACTIVAR MODO LURKER  (sólo lectura — bloquea auto-envío)',
    },
    'lurker.activated': {
        'pt': '🟢 Lurker ATIVADO',
        'en': '🟢 Lurker ENABLED',
        'fr': '🟢 Lurker ACTIVÉ',
        'es': '🟢 Lurker ACTIVADO',
    },
    'lurker.deactivated': {
        'pt': '🛑 Lurker desativado',
        'en': '🛑 Lurker disabled',
        'fr': '🛑 Lurker désactivé',
        'es': '🛑 Lurker desactivado',
    },

    # ========================================================================
    # ABA CAPTURA
    # ========================================================================
    'capture.section.perimeter': {
        'pt': '1. Definir região do chat',
        'en': '1. Define chat region',
        'fr': '1. Définir la zone du chat',
        'es': '1. Definir región del chat',
    },
    'capture.perimeter_help': {
        'pt': 'Aponta o mouse no canto superior-esquerdo do chat\ne segura por 2s. Depois aponta no canto inferior-direito.',
        'en': 'Point the mouse at the top-left corner of the chat\nand hold for 2s. Then point at the bottom-right corner.',
        'fr': 'Pointez la souris dans le coin supérieur-gauche du chat\net maintenez 2s. Puis pointez dans le coin inférieur-droit.',
        'es': 'Apunta el mouse en la esquina superior-izquierda del chat\ny mantén por 2s. Luego apunta en la esquina inferior-derecha.',
    },
    'capture.btn.set_perimeter': {
        'pt': 'Definir Perímetro do Chat',
        'en': 'Set Chat Perimeter',
        'fr': 'Définir Périmètre du Chat',
        'es': 'Definir Perímetro del Chat',
    },
    'capture.section.chatbar': {
        'pt': '2. Definir barra de input',
        'en': '2. Define input bar',
        'fr': '2. Définir la barre de saisie',
        'es': '2. Definir barra de entrada',
    },
    'capture.chatbar_help': {
        'pt': 'Aponta o mouse na barra de digitação do chat e segura por 2s.',
        'en': 'Point the mouse at the chat input bar and hold for 2s.',
        'fr': 'Pointez la souris sur la barre de saisie du chat et maintenez 2s.',
        'es': 'Apunta el mouse en la barra de entrada del chat y mantén por 2s.',
    },
    'capture.btn.set_chatbar': {
        'pt': 'Definir Barra de Input',
        'en': 'Set Input Bar',
        'fr': 'Définir Barre de Saisie',
        'es': 'Definir Barra de Entrada',
    },
    'capture.section.start': {
        'pt': '3. Iniciar leitura',
        'en': '3. Start reading',
        'fr': '3. Démarrer lecture',
        'es': '3. Iniciar lectura',
    },
    'capture.btn.start': {
        'pt': '▶ Iniciar Tradução do Chat',
        'en': '▶ Start Chat Translation',
        'fr': '▶ Démarrer Traduction Chat',
        'es': '▶ Iniciar Traducción del Chat',
    },
    'capture.btn.stop': {
        'pt': '■ Parar Tradução',
        'en': '■ Stop Translation',
        'fr': '■ Arrêter Traduction',
        'es': '■ Detener Traducción',
    },
    'capture.btn.test_ocr': {
        'pt': '🔍 Testar OCR',
        'en': '🔍 Test OCR',
        'fr': '🔍 Tester OCR',
        'es': '🔍 Probar OCR',
    },
    'capture.label.interval': {
        'pt': 'Intervalo (s):',
        'en': 'Interval (s):',
        'fr': 'Intervalle (s):',
        'es': 'Intervalo (s):',
    },
    'capture.perimeter.current': {
        'pt': 'Atual: ({x1}, {y1}) → ({x2}, {y2})',
        'en': 'Current: ({x1}, {y1}) → ({x2}, {y2})',
        'fr': 'Actuel: ({x1}, {y1}) → ({x2}, {y2})',
        'es': 'Actual: ({x1}, {y1}) → ({x2}, {y2})',
    },
    'capture.perimeter.not_set': {
        'pt': 'Não configurado.',
        'en': 'Not configured.',
        'fr': 'Non configuré.',
        'es': 'No configurado.',
    },
    'capture.chatbar.current': {
        'pt': 'Atual: ({x}, {y})',
        'en': 'Current: ({x}, {y})',
        'fr': 'Actuel: ({x}, {y})',
        'es': 'Actual: ({x}, {y})',
    },
    'capture.msg.top_left': {
        'pt': 'Canto SUPERIOR-ESQUERDO... segure o mouse parado por 2s',
        'en': 'TOP-LEFT corner... hold mouse still for 2s',
        'fr': 'Coin SUPÉRIEUR-GAUCHE... maintenez la souris immobile 2s',
        'es': 'Esquina SUPERIOR-IZQUIERDA... mantén el mouse quieto por 2s',
    },
    'capture.msg.bottom_right': {
        'pt': 'Canto INFERIOR-DIREITO... segure o mouse parado por 2s',
        'en': 'BOTTOM-RIGHT corner... hold mouse still for 2s',
        'fr': 'Coin INFÉRIEUR-DROIT... maintenez la souris immobile 2s',
        'es': 'Esquina INFERIOR-DERECHA... mantén el mouse quieto por 2s',
    },
    'capture.msg.point_chatbar': {
        'pt': 'Aponte o mouse na barra de input e segure 2s...',
        'en': 'Point mouse at input bar and hold for 2s...',
        'fr': 'Pointez la souris sur la barre et maintenez 2s...',
        'es': 'Apunta el mouse en la barra y mantén 2s...',
    },
    # === Versões com F2 (Sub-bloco 3.2) ===
    # Mensagens novas que mencionam F2 como atalho preferencial.
    # O fallback de "segurar 2s" continua funcionando.
    'capture.msg.top_left_f2': {
        'pt': 'Aponte o mouse no canto SUPERIOR-ESQUERDO e aperte F2 (ou segure 2s)',
        'en': 'Point mouse at TOP-LEFT corner and press F2 (or hold 2s)',
        'fr': 'Pointez la souris au coin SUPÉRIEUR-GAUCHE et appuyez sur F2 (ou maintenez 2s)',
        'es': 'Apunta el mouse a la esquina SUPERIOR-IZQUIERDA y presiona F2 (o mantén 2s)',
    },
    'capture.msg.bottom_right_f2': {
        'pt': 'Aponte o mouse no canto INFERIOR-DIREITO e aperte F2 (ou segure 2s)',
        'en': 'Point mouse at BOTTOM-RIGHT corner and press F2 (or hold 2s)',
        'fr': 'Pointez la souris au coin INFÉRIEUR-DROIT et appuyez sur F2 (ou maintenez 2s)',
        'es': 'Apunta el mouse a la esquina INFERIOR-DERECHA y presiona F2 (o mantén 2s)',
    },
    'capture.msg.point_chatbar_f2': {
        'pt': 'Aponte o mouse na barra de input e aperte F2 (ou segure 2s)',
        'en': 'Point mouse at input bar and press F2 (or hold 2s)',
        'fr': 'Pointez la souris sur la barre et appuyez sur F2 (ou maintenez 2s)',
        'es': 'Apunta el mouse en la barra y presiona F2 (o mantén 2s)',
    },
    # === F2 obrigatório (v1.0.20 - removeu fallback de 2s) ===
    'capture.msg.top_left_f2_required': {
        'pt': 'Aponte o canto SUPERIOR-ESQUERDO do chat e aperte F2',
        'en': 'Point at TOP-LEFT corner of chat and press F2',
        'fr': 'Pointez le coin SUPÉRIEUR-GAUCHE et appuyez sur F2',
        'es': 'Apunta a la esquina SUPERIOR-IZQUIERDA y presiona F2',
    },
    'capture.msg.bottom_right_f2_required': {
        'pt': '➡ Agora aponte o canto INFERIOR-DIREITO e aperte F2',
        'en': '➡ Now point at BOTTOM-RIGHT corner and press F2',
        'fr': '➡ Pointez maintenant le coin INFÉRIEUR-DROIT et appuyez sur F2',
        'es': '➡ Ahora apunta la esquina INFERIOR-DERECHA y presiona F2',
    },
    'capture.msg.point_chatbar_f2_required': {
        'pt': 'Aponte o mouse na barra de input e aperte F2',
        'en': 'Point mouse at input bar and press F2',
        'fr': 'Pointez la souris sur la barre et appuyez sur F2',
        'es': 'Apunta el mouse en la barra y presiona F2',
    },
    'capture.msg.f2_hotkey_failed': {
        'pt': '⚠ Não foi possível registrar F2. Tente novamente.',
        'en': '⚠ Could not register F2. Try again.',
        'fr': '⚠ Impossible d\'enregistrer F2. Réessayez.',
        'es': '⚠ No se pudo registrar F2. Inténtalo de nuevo.',
    },
    'f2_tooltip.capturing': {
        'pt': '✓ Capturando perímetro...',
        'en': '✓ Capturing perimeter...',
        'fr': '✓ Capture du périmètre...',
        'es': '✓ Capturando perímetro...',
    },
    # NOVO v1.0.21: feedback mais explícito de "capturado"
    'f2_tooltip.captured': {
        'pt': '✓ Capturado!',
        'en': '✓ Captured!',
        'fr': '✓ Capturé !',
        'es': '✓ ¡Capturado!',
    },
    'capture.msg.perimeter_set': {
        'pt': 'Perímetro definido: {x1},{y1} → {x2},{y2}',
        'en': 'Perimeter set: {x1},{y1} → {x2},{y2}',
        'fr': 'Périmètre défini: {x1},{y1} → {x2},{y2}',
        'es': 'Perímetro definido: {x1},{y1} → {x2},{y2}',
    },
    'capture.msg.chatbar_set': {
        'pt': 'Chat bar definida: {x},{y}',
        'en': 'Chat bar set: {x},{y}',
        'fr': 'Barre définie: {x},{y}',
        'es': 'Barra definida: {x},{y}',
    },
    'capture.msg.no_perimeter': {
        'pt': 'Defina o perímetro do chat primeiro!',
        'en': 'Define the chat perimeter first!',
        'fr': 'Définissez le périmètre du chat d\'abord!',
        'es': '¡Define el perímetro del chat primero!',
    },
    'capture.msg.start': {
        'pt': 'Captura iniciada. Janela de leitura aberta.',
        'en': 'Capture started. Reading window opened.',
        'fr': 'Capture démarrée. Fenêtre de lecture ouverte.',
        'es': 'Captura iniciada. Ventana de lectura abierta.',
    },
    'capture.msg.stop': {
        'pt': 'Captura parada.',
        'en': 'Capture stopped.',
        'fr': 'Capture arrêtée.',
        'es': 'Captura detenida.',
    },

    # ========================================================================
    # ABA TRADUÇÃO
    # ========================================================================
    'translation.section.read_mode': {
        'pt': 'Modo Leitura (chat → você)',
        'en': 'Read Mode (chat → you)',
        'fr': 'Mode Lecture (chat → vous)',
        'es': 'Modo Lectura (chat → tú)',
    },
    'translation.section.write_mode': {
        'pt': 'Modo Escrita (você → chat)',
        'en': 'Write Mode (you → chat)',
        'fr': 'Mode Écriture (vous → chat)',
        'es': 'Modo Escritura (tú → chat)',
    },
    'translation.label.from': {
        'pt': 'De:', 'en': 'From:', 'fr': 'De:', 'es': 'De:',
    },
    'translation.label.to': {
        'pt': 'Para:', 'en': 'To:', 'fr': 'Vers:', 'es': 'Para:',
    },
    'translation.section.ocr_lang': {
        'pt': 'Idioma do OCR (Tesseract)',
        'en': 'OCR Language (Tesseract)',
        'fr': 'Langue OCR (Tesseract)',
        'es': 'Idioma OCR (Tesseract)',
    },
    'translation.section.backend': {
        'pt': 'Backend de tradução',
        'en': 'Translation backend',
        'fr': 'Moteur de traduction',
        'es': 'Backend de traducción',
    },
    'translation.backend.google': {
        'pt': 'Google (gratuito)', 'en': 'Google (free)',
        'fr': 'Google (gratuit)', 'es': 'Google (gratis)',
    },
    'translation.backend.deepl': {
        'pt': 'DeepL (premium)', 'en': 'DeepL (premium)',
        'fr': 'DeepL (premium)', 'es': 'DeepL (premium)',
    },
    'translation.label.deepl_key': {
        'pt': 'DeepL API Key (opcional):',
        'en': 'DeepL API Key (optional):',
        'fr': 'Clé API DeepL (optionnel):',
        'es': 'API Key de DeepL (opcional):',
    },
    'translation.section.custom_terms': {
        'pt': 'Termos Personalizados',
        'en': 'Custom Terms',
        'fr': 'Termes Personnalisés',
        'es': 'Términos Personalizados',
    },
    'translation.custom_terms.help': {
        'pt': 'Define traduções específicas pra termos do jogo (nicknames, gírias, items) que o tradutor genérico não acerta bem.',
        'en': 'Define specific translations for game terms (nicknames, slang, items) that the generic translator misses.',
        'fr': 'Définissez des traductions spécifiques pour les termes du jeu (pseudos, argot, items) que le traducteur générique rate.',
        'es': 'Define traducciones específicas para términos del juego (nicknames, jergas, items) que el traductor genérico falla.',
    },
    'translation.btn.manage_terms': {
        'pt': '📝 Gerenciar Termos Personalizados...',
        'en': '📝 Manage Custom Terms...',
        'fr': '📝 Gérer Termes Personnalisés...',
        'es': '📝 Gestionar Términos Personalizados...',
    },
    'translation.msg.applied': {
        'pt': 'Configurações de tradução aplicadas.',
        'en': 'Translation settings applied.',
        'fr': 'Paramètres de traduction appliqués.',
        'es': 'Configuración de traducción aplicada.',
    },

    # ========================================================================
    # ABA APARÊNCIA
    # ========================================================================
    'appearance.section.app_theme': {
        'pt': 'Tema do app (janela principal)',
        'en': 'App theme (main window)',
        'fr': 'Thème de l\'app (fenêtre principale)',
        'es': 'Tema de la app (ventana principal)',
    },
    'appearance.section.ui_lang': {
        'pt': 'Idioma do app',
        'en': 'App language',
        'fr': 'Langue de l\'app',
        'es': 'Idioma de la app',
    },
    'appearance.ui_lang.help': {
        'pt': 'Idioma usado nos menus, botões e mensagens do app.',
        'en': 'Language used in menus, buttons and app messages.',
        'fr': 'Langue utilisée dans les menus, boutons et messages.',
        'es': 'Idioma usado en menús, botones y mensajes de la app.',
    },
    'appearance.section.overlay_theme': {
        'pt': 'Tema da janela de leitura (overlay)',
        'en': 'Reading window theme (overlay)',
        'fr': 'Thème de la fenêtre de lecture (overlay)',
        'es': 'Tema de la ventana de lectura (overlay)',
    },
    'appearance.section.overlay_alpha': {
        'pt': 'Transparência da janela overlay',
        'en': 'Overlay window transparency',
        'fr': 'Transparence de la fenêtre overlay',
        'es': 'Transparencia de la ventana overlay',
    },
    'appearance.always_on_top': {
        'pt': 'Sempre no topo (always on top)',
        'en': 'Always on top',
        'fr': 'Toujours au-dessus',
        'es': 'Siempre encima',
    },
    'appearance.section.preview': {
        'pt': 'Preview ao vivo (overlay)',
        'en': 'Live preview (overlay)',
        'fr': 'Aperçu en direct (overlay)',
        'es': 'Vista previa en vivo (overlay)',
    },
    # === Bloco 3.3 v2 (v1.0.29): Expander de customização avançada ===
    'appearance.expander.advanced': {
        'pt': 'Customização avançada',
        'en': 'Advanced customization',
        'fr': 'Personnalisation avancée',
        'es': 'Personalización avanzada',
    },
    'appearance.expander.advanced_hint': {
        'pt': 'Cores customizadas, fonte e tamanho do texto.',
        'en': 'Custom colors, font and text size.',
        'fr': 'Couleurs personnalisées, police et taille du texte.',
        'es': 'Colores personalizados, fuente y tamaño del texto.',
    },
    # === Toasts (v1.0.30) ===
    'toast.config_changed': {
        'pt': '✓ {label} alterado',
        'en': '✓ {label} changed',
        'fr': '✓ {label} modifié',
        'es': '✓ {label} cambiado',
    },
    'toast.restart_required': {
        'pt': '⚠️ {label}: reabra o app pra aplicar',
        'en': '⚠️ {label}: reopen app to apply',
        'fr': '⚠️ {label}: rouvrez l\'app pour appliquer',
        'es': '⚠️ {label}: reabre la app para aplicar',
    },
    # Labels usados nos toasts (descritivos)
    'config.label.app_theme': {
        'pt': 'Tema do app',
        'en': 'App theme',
        'fr': 'Thème de l\'app',
        'es': 'Tema de la app',
    },
    'config.label.app_language': {
        'pt': 'Idioma do app',
        'en': 'App language',
        'fr': 'Langue de l\'app',
        'es': 'Idioma de la app',
    },
    'config.label.overlay_theme': {
        'pt': 'Tema do overlay',
        'en': 'Overlay theme',
        'fr': 'Thème overlay',
        'es': 'Tema del overlay',
    },
    'config.label.overlay_alpha': {
        'pt': 'Transparência',
        'en': 'Transparency',
        'fr': 'Transparence',
        'es': 'Transparencia',
    },
    'config.label.always_on_top': {
        'pt': 'Sempre no topo',
        'en': 'Always on top',
        'fr': 'Toujours au-dessus',
        'es': 'Siempre encima',
    },
    'config.label.overlay_bg': {
        'pt': 'Cor de fundo',
        'en': 'Background color',
        'fr': 'Couleur de fond',
        'es': 'Color de fondo',
    },
    'config.label.overlay_fg': {
        'pt': 'Cor do texto',
        'en': 'Text color',
        'fr': 'Couleur du texte',
        'es': 'Color del texto',
    },
    'config.label.overlay_font': {
        'pt': 'Fonte',
        'en': 'Font',
        'fr': 'Police',
        'es': 'Fuente',
    },
    'config.label.overlay_font_size': {
        'pt': 'Tamanho da fonte',
        'en': 'Font size',
        'fr': 'Taille de la police',
        'es': 'Tamaño de la fuente',
    },
    'config.label.capture_interval': {
        'pt': 'Intervalo de captura',
        'en': 'Capture interval',
        'fr': 'Intervalle de capture',
        'es': 'Intervalo de captura',
    },
    'config.label.lurker_mode': {
        'pt': 'Modo Lurker',
        'en': 'Lurker mode',
        'fr': 'Mode Lurker',
        'es': 'Modo Lurker',
    },
    'appearance.label.font': {
        'pt': 'Fonte:', 'en': 'Font:', 'fr': 'Police:', 'es': 'Fuente:',
    },
    'appearance.label.size': {
        'pt': 'Tamanho:', 'en': 'Size:', 'fr': 'Taille:', 'es': 'Tamaño:',
    },
    'appearance.swatch.bg': {
        'pt': 'Fundo overlay', 'en': 'Overlay BG', 'fr': 'Fond overlay', 'es': 'Fondo overlay',
    },
    'appearance.swatch.fg': {
        'pt': 'Texto overlay', 'en': 'Overlay text', 'fr': 'Texte overlay', 'es': 'Texto overlay',
    },
    'appearance.theme.dark': {
        'pt': 'Dark', 'en': 'Dark', 'fr': 'Sombre', 'es': 'Oscuro',
    },
    'appearance.theme.light': {
        'pt': 'Light', 'en': 'Light', 'fr': 'Clair', 'es': 'Claro',
    },
    'appearance.theme.dofus_retro': {
        'pt': 'Dofus Retro', 'en': 'Dofus Retro', 'fr': 'Dofus Retro', 'es': 'Dofus Retro',
    },
    'appearance.theme.custom': {
        'pt': 'Custom', 'en': 'Custom', 'fr': 'Personnalisé', 'es': 'Personalizado',
    },
    'appearance.msg.applied': {
        'pt': 'Aparência aplicada.',
        'en': 'Appearance applied.',
        'fr': 'Apparence appliquée.',
        'es': 'Apariencia aplicada.',
    },
    'appearance.msg.theme_saved': {
        'pt': 'Configurações salvas.',
        'en': 'Settings saved.',
        'fr': 'Paramètres enregistrés.',
        'es': 'Configuración guardada.',
    },

    # ========================================================================
    # ABA ATALHO & SOM
    # ========================================================================
    'shortcut.section.hotkey': {
        'pt': 'Atalho global pra input rápido',
        'en': 'Global shortcut for quick input',
        'fr': 'Raccourci global pour saisie rapide',
        'es': 'Atajo global para entrada rápida',
    },
    'shortcut.section.position': {
        'pt': 'Posição do popup de tradução rápida',
        'en': 'Quick translation popup position',
        'fr': 'Position du popup de traduction rapide',
        'es': 'Posición del popup de traducción rápida',
    },
    'shortcut.position.cursor': {
        'pt': 'Próximo ao cursor',
        'en': 'Near cursor',
        'fr': 'Près du curseur',
        'es': 'Cerca del cursor',
    },
    'shortcut.position.last': {
        'pt': 'Último local fechado',
        'en': 'Last closed location',
        'fr': 'Dernier emplacement',
        'es': 'Última ubicación',
    },
    'shortcut.section.monitor': {
        'pt': 'Monitor padrão pra janela overlay',
        'en': 'Default monitor for overlay window',
        'fr': 'Moniteur par défaut pour overlay',
        'es': 'Monitor predeterminado para overlay',
    },
    'shortcut.monitor.auto': {
        'pt': '(automático - primário)',
        'en': '(automatic - primary)',
        'fr': '(automatique - primaire)',
        'es': '(automático - primario)',
    },
    'sound.section': {
        'pt': 'Som', 'en': 'Sound', 'fr': 'Son', 'es': 'Sonido',
    },
    'sound.enabled': {
        'pt': 'Tocar som ao enviar mensagem com sucesso',
        'en': 'Play sound when message is sent successfully',
        'fr': 'Jouer un son à l\'envoi réussi du message',
        'es': 'Reproducir sonido al enviar mensaje con éxito',
    },
    'sound.label.file': {
        'pt': 'Arquivo:', 'en': 'File:', 'fr': 'Fichier:', 'es': 'Archivo:',
    },
    'sound.label.volume': {
        'pt': 'Volume:', 'en': 'Volume:', 'fr': 'Volume:', 'es': 'Volumen:',
    },
    'sound.btn.test': {
        'pt': '🔊 Testar', 'en': '🔊 Test', 'fr': '🔊 Tester', 'es': '🔊 Probar',
    },
    'sound.msg.testing': {
        'pt': '🔊 Testando: {file} ({volume}%)',
        'en': '🔊 Testing: {file} ({volume}%)',
        'fr': '🔊 Test: {file} ({volume}%)',
        'es': '🔊 Probando: {file} ({volume}%)',
    },
    'sound.msg.no_files': {
        'pt': 'Coloque arquivos .wav na pasta sounds/ primeiro.',
        'en': 'Put .wav files in the sounds/ folder first.',
        'fr': 'Placez des fichiers .wav dans le dossier sounds/.',
        'es': 'Pon archivos .wav en la carpeta sounds/ primero.',
    },
    'shortcut.msg.applied': {
        'pt': 'Configurações de atalho e som salvas.',
        'en': 'Shortcut and sound settings saved.',
        'fr': 'Paramètres raccourci et son enregistrés.',
        'es': 'Configuración de atajo y sonido guardada.',
    },
    'shortcut.msg.applied_with_hotkey': {
        'pt': 'Configurações salvas. Hotkey: {hotkey}',
        'en': 'Settings saved. Hotkey: {hotkey}',
        'fr': 'Paramètres enregistrés. Raccourci: {hotkey}',
        'es': 'Configuración guardada. Atajo: {hotkey}',
    },

    # ========================================================================
    # ABA AVANÇADO
    # ========================================================================
    'advanced.section.tesseract': {
        'pt': 'Caminho do Tesseract',
        'en': 'Tesseract path',
        'fr': 'Chemin Tesseract',
        'es': 'Ruta de Tesseract',
    },
    'advanced.tesseract.help': {
        'pt': 'Geralmente detectado automaticamente. Configure manual só se necessário.',
        'en': 'Usually auto-detected. Configure manually only if needed.',
        'fr': 'Généralement détecté automatiquement. Configurez manuellement si besoin.',
        'es': 'Generalmente detectado automáticamente. Configurar manual solo si es necesario.',
    },
    'advanced.section.tray': {
        'pt': 'System Tray', 'en': 'System Tray', 'fr': 'Barre d\'état système', 'es': 'Bandeja del sistema',
    },
    'advanced.close_to_tray': {
        'pt': 'Ao clicar no X, minimizar para system tray (em vez de fechar)',
        'en': 'Clicking X minimizes to system tray (instead of closing)',
        'fr': 'Cliquer sur X minimise dans la barre d\'état (au lieu de fermer)',
        'es': 'Al hacer clic en X, minimizar a la bandeja (en vez de cerrar)',
    },
    'advanced.tray.help': {
        'pt': 'Independente disso, você sempre pode acessar o app pelo ícone na bandeja (área de notificação do Windows).',
        'en': 'Either way, you can always access the app via the tray icon (Windows notification area).',
        'fr': 'Vous pouvez toujours accéder à l\'app via l\'icône de la barre d\'état.',
        'es': 'Igualmente, siempre puedes acceder a la app desde el icono de la bandeja.',
    },
    'advanced.section.behavior': {
        'pt': 'Comportamento', 'en': 'Behavior', 'fr': 'Comportement', 'es': 'Comportamiento',
    },
    'advanced.countdown': {
        'pt': 'Mostrar countdown antes de auto-enviar',
        'en': 'Show countdown before auto-sending',
        'fr': 'Afficher décompte avant auto-envoi',
        'es': 'Mostrar cuenta regresiva antes de auto-enviar',
    },
    'advanced.cache': {
        'pt': 'Cache de tradução (mais rápido)',
        'en': 'Translation cache (faster)',
        'fr': 'Cache de traduction (plus rapide)',
        'es': 'Caché de traducción (más rápido)',
    },
    'advanced.history': {
        'pt': 'Histórico de mensagens enviadas',
        'en': 'Sent messages history',
        'fr': 'Historique des messages envoyés',
        'es': 'Historial de mensajes enviados',
    },
    'advanced.section.debug': {
        'pt': 'Debug', 'en': 'Debug', 'fr': 'Debug', 'es': 'Debug',
    },
    'advanced.logging': {
        'pt': 'Logging detalhado (debug.log)',
        'en': 'Detailed logging (debug.log)',
        'fr': 'Logging détaillé (debug.log)',
        'es': 'Logging detallado (debug.log)',
    },
    'advanced.section.support': {
        'pt': 'Suporte', 'en': 'Support', 'fr': 'Support', 'es': 'Soporte',
    },
    # v1.0.34/Fase 4: Verificação manual de updates Velopack
    'advanced.section.updates': {
        'pt': 'Atualizações', 'en': 'Updates', 'fr': 'Mises à jour', 'es': 'Actualizaciones',
    },
    'advanced.updates.current': {
        'pt': 'Versão atual: {version}',
        'en': 'Current version: {version}',
        'fr': 'Version actuelle: {version}',
        'es': 'Versión actual: {version}',
    },
    'advanced.updates.btn.check': {
        'pt': '🔍 Verificar atualizações',
        'en': '🔍 Check for updates',
        'fr': '🔍 Vérifier les mises à jour',
        'es': '🔍 Buscar actualizaciones',
    },
    'advanced.updates.status.checking': {
        'pt': 'Verificando...',
        'en': 'Checking...',
        'fr': 'Vérification...',
        'es': 'Verificando...',
    },
    'advanced.updates.status.uptodate': {
        'pt': '✓ Você está usando a versão mais recente.',
        'en': '✓ You are using the latest version.',
        'fr': '✓ Vous utilisez la dernière version.',
        'es': '✓ Estás usando la versión más reciente.',
    },
    'advanced.updates.status.available': {
        'pt': '🚀 Versão {version} disponível! Clique pra atualizar.',
        'en': '🚀 Version {version} available! Click to update.',
        'fr': '🚀 Version {version} disponible! Cliquez pour mettre à jour.',
        'es': '🚀 ¡Versión {version} disponible! Haz clic para actualizar.',
    },
    'advanced.updates.status.error': {
        'pt': 'Erro ao verificar. Tente novamente em instantes.',
        'en': 'Check failed. Try again in a moment.',
        'fr': 'Échec de la vérification. Réessayez dans un instant.',
        'es': 'Falló la verificación. Inténtalo de nuevo en un momento.',
    },
    'advanced.updates.status.devmode': {
        'pt': 'Atualizações automáticas só funcionam no app instalado.',
        'en': 'Auto-updates only work on the installed app.',
        'fr': 'Les mises à jour ne fonctionnent que sur l\'app installée.',
        'es': 'Las actualizaciones solo funcionan en la app instalada.',
    },
    'advanced.btn.report': {
        'pt': '📧 Reportar Problema...',
        'en': '📧 Report a Problem...',
        'fr': '📧 Signaler un Problème...',
        'es': '📧 Reportar Problema...',
    },
    'advanced.report.help': {
        'pt': 'Envia logs e configurações pro desenvolvedor analisar.',
        'en': 'Sends logs and settings for the developer to analyze.',
        'fr': 'Envoie logs et paramètres au développeur pour analyse.',
        'es': 'Envía logs y configuraciones al desarrollador para análisis.',
    },
    'advanced.section.about': {
        'pt': 'Sobre', 'en': 'About', 'fr': 'À propos', 'es': 'Acerca',
    },
    'advanced.btn.about': {
        'pt': 'ℹ Sobre o Dofusinator...',
        'en': 'ℹ About Dofusinator...',
        'fr': 'ℹ À propos de Dofusinator...',
        'es': 'ℹ Acerca de Dofusinator...',
    },
    'advanced.msg.applied': {
        'pt': 'Configurações avançadas salvas.',
        'en': 'Advanced settings saved.',
        'fr': 'Paramètres avancés enregistrés.',
        'es': 'Configuración avanzada guardada.',
    },

    # ========================================================================
    # POPUP QUICK INPUT
    # ========================================================================
    'popup.auto_send': {
        'pt': 'auto-send', 'en': 'auto-send', 'fr': 'auto-envoi', 'es': 'auto-envío',
    },
    'popup.btn.copy_again': {
        'pt': '📋 Copiar de novo',
        'en': '📋 Copy again',
        'fr': '📋 Copier à nouveau',
        'es': '📋 Copiar de nuevo',
    },
    'popup.btn.new_translation': {
        'pt': '↩ Nova tradução',
        'en': '↩ New translation',
        'fr': '↩ Nouvelle traduction',
        'es': '↩ Nueva traducción',
    },
    'popup.msg.translating': {
        'pt': 'Traduzindo {src} → {dest}...',
        'en': 'Translating {src} → {dest}...',
        'fr': 'Traduction {src} → {dest}...',
        'es': 'Traduciendo {src} → {dest}...',
    },
    'popup.msg.empty': {
        'pt': 'Digite alguma coisa primeiro 😅',
        'en': 'Type something first 😅',
        'fr': 'Tapez quelque chose d\'abord 😅',
        'es': 'Escribe algo primero 😅',
    },
    'popup.msg.translated': {
        'pt': '✓ Tradução concluída e copiada para a área de transferência.',
        'en': '✓ Translation complete and copied to clipboard.',
        'fr': '✓ Traduction terminée et copiée dans le presse-papiers.',
        'es': '✓ Traducción completa y copiada al portapapeles.',
    },
    'popup.msg.translated_lurker': {
        'pt': '🛑 LURKER — Tradução concluída e copiada.',
        'en': '🛑 LURKER — Translation complete and copied.',
        'fr': '🛑 LURKER — Traduction terminée et copiée.',
        'es': '🛑 LURKER — Traducción completa y copiada.',
    },
    'popup.msg.copied_again': {
        'pt': '📋 Copiado novamente.',
        'en': '📋 Copied again.',
        'fr': '📋 Copié à nouveau.',
        'es': '📋 Copiado nuevamente.',
    },
    'popup.msg.sent': {
        'pt': '✓ Enviado: {preview}',
        'en': '✓ Sent: {preview}',
        'fr': '✓ Envoyé: {preview}',
        'es': '✓ Enviado: {preview}',
    },
    'popup.msg.sending': {
        'pt': 'Enviando em {sec}s... (Esc cancela)',
        'en': 'Sending in {sec}s... (Esc cancels)',
        'fr': 'Envoi dans {sec}s... (Esc annule)',
        'es': 'Enviando en {sec}s... (Esc cancela)',
    },
    'popup.msg.cancelled': {
        'pt': 'Cancelado.', 'en': 'Cancelled.', 'fr': 'Annulé.', 'es': 'Cancelado.',
    },
    'popup.msg.error': {
        'pt': 'Erro: {err}', 'en': 'Error: {err}', 'fr': 'Erreur: {err}', 'es': 'Error: {err}',
    },
    'popup.msg.no_chatbar': {
        'pt': "Auto-send: configure 'Chat Bar' nas configurações primeiro.",
        'en': "Auto-send: configure 'Chat Bar' in settings first.",
        'fr': "Auto-envoi: configurez 'Chat Bar' dans les paramètres.",
        'es': "Auto-envío: configura 'Chat Bar' en ajustes primero.",
    },
    'popup.history.title': {
        'pt': 'Histórico (clique pra reusar):',
        'en': 'History (click to reuse):',
        'fr': 'Historique (cliquez pour réutiliser):',
        'es': 'Historial (clic para reusar):',
    },
    'popup.history.empty': {
        'pt': 'Nenhuma mensagem no histórico ainda.',
        'en': 'No messages in history yet.',
        'fr': 'Aucun message dans l\'historique.',
        'es': 'Aún no hay mensajes en el historial.',
    },

    # ========================================================================
    # CUSTOM TERMS POPUP
    # ========================================================================
    'terms.title': {
        'pt': 'Termos Personalizados',
        'en': 'Custom Terms',
        'fr': 'Termes Personnalisés',
        'es': 'Términos Personalizados',
    },
    'terms.section.add': {
        'pt': 'Adicionar novo termo',
        'en': 'Add new term',
        'fr': 'Ajouter un nouveau terme',
        'es': 'Agregar nuevo término',
    },
    'terms.section.list': {
        'pt': 'Termos cadastrados (duplo-clique pra editar)',
        'en': 'Registered terms (double-click to edit)',
        'fr': 'Termes enregistrés (double-clic pour modifier)',
        'es': 'Términos registrados (doble clic para editar)',
    },
    'terms.label.source_lang': {
        'pt': 'Idioma origem:',
        'en': 'Source language:',
        'fr': 'Langue source:',
        'es': 'Idioma origen:',
    },
    'terms.label.target_lang': {
        'pt': 'Idioma destino:',
        'en': 'Target language:',
        'fr': 'Langue cible:',
        'es': 'Idioma destino:',
    },
    'terms.label.term': {
        'pt': 'Termo:', 'en': 'Term:', 'fr': 'Terme:', 'es': 'Término:',
    },
    'terms.label.translation': {
        'pt': 'Tradução:', 'en': 'Translation:', 'fr': 'Traduction:', 'es': 'Traducción:',
    },
    'terms.add_reverse': {
        'pt': 'Adicionar reverso (ex: PT→FR e FR→PT)',
        'en': 'Add reverse (e.g. PT→FR and FR→PT)',
        'fr': 'Ajouter inverse (ex: PT→FR et FR→PT)',
        'es': 'Agregar inverso (ej: PT→FR y FR→PT)',
    },
    'terms.btn.add': {
        'pt': 'Adicionar', 'en': 'Add', 'fr': 'Ajouter', 'es': 'Agregar',
    },
    'terms.btn.remove': {
        'pt': 'Remover Selecionado',
        'en': 'Remove Selected',
        'fr': 'Supprimer Sélectionné',
        'es': 'Eliminar Seleccionado',
    },
    'terms.btn.reload': {
        'pt': 'Recarregar', 'en': 'Reload', 'fr': 'Recharger', 'es': 'Recargar',
    },

    # ========================================================================
    # TRAY ICON
    # ========================================================================
    'tray.menu.open': {
        'pt': 'Abrir', 'en': 'Open', 'fr': 'Ouvrir', 'es': 'Abrir',
    },
    'tray.menu.lurker': {
        'pt': 'Modo Lurker', 'en': 'Lurker Mode', 'fr': 'Mode Lurker', 'es': 'Modo Lurker',
    },
    'tray.menu.quit': {
        'pt': 'Fechar', 'en': 'Quit', 'fr': 'Fermer', 'es': 'Cerrar',
    },

    # ========================================================================
    # TÍTULOS DE JANELAS
    # ========================================================================
    'title.main': {
        'pt': 'Dofusinator', 'en': 'Dofusinator', 'fr': 'Dofusinator', 'es': 'Dofusinator',
    },
    'title.overlay': {
        'pt': 'Chat Traduzido', 'en': 'Translated Chat', 'fr': 'Chat Traduit', 'es': 'Chat Traducido',
    },
    'title.terms': {
        'pt': 'Termos Personalizados', 'en': 'Custom Terms', 'fr': 'Termes Personnalisés', 'es': 'Términos Personalizados',
    },
    'title.about': {
        'pt': 'Sobre', 'en': 'About', 'fr': 'À propos', 'es': 'Acerca',
    },
    'title.report': {
        'pt': 'Reportar Problema', 'en': 'Report a Problem', 'fr': 'Signaler un Problème', 'es': 'Reportar Problema',
    },
    'title.test_ocr': {
        'pt': 'Teste de OCR', 'en': 'OCR Test', 'fr': 'Test OCR', 'es': 'Prueba OCR',
    },
    'title.error': {
        'pt': 'Erro', 'en': 'Error', 'fr': 'Erreur', 'es': 'Error',
    },

    # ========================================================================
    # TELA SOBRE
    # ========================================================================
    'about.version': {
        'pt': 'Versão {ver}', 'en': 'Version {ver}', 'fr': 'Version {ver}', 'es': 'Versión {ver}',
    },
    'about.description': {
        'pt': 'Tradutor em tempo real do chat do Dofus.\nLê o chat via OCR, traduz, e te ajuda\na responder em qualquer idioma.',
        'en': 'Real-time chat translator for Dofus.\nReads the chat via OCR, translates,\nand helps you reply in any language.',
        'fr': 'Traducteur de chat Dofus en temps réel.\nLit le chat via OCR, traduit, et vous aide\nà répondre dans n\'importe quelle langue.',
        'es': 'Traductor de chat de Dofus en tiempo real.\nLee el chat vía OCR, traduce, y te ayuda\na responder en cualquier idioma.',
    },
    'about.developer': {
        'pt': 'Desenvolvido por {author}',
        'en': 'Developed by {author}',
        'fr': 'Développé par {author}',
        'es': 'Desarrollado por {author}',
    },
    'about.tagline': {
        'pt': 'Feito com 💙 pra galera do Dofus Retro',
        'en': 'Made with 💙 for the Dofus Retro community',
        'fr': 'Fait avec 💙 pour la communauté Dofus Retro',
        'es': 'Hecho con 💙 para la comunidad Dofus Retro',
    },

    # ========================================================================
    # REPORTAR PROBLEMA
    # ========================================================================
    'report.title': {
        'pt': 'Reportar Problema', 'en': 'Report a Problem',
        'fr': 'Signaler un Problème', 'es': 'Reportar Problema',
    },
    'report.help': {
        'pt': 'Descreva o problema brevemente. O app vai gerar um arquivo .zip\ncom logs e configurações que ajudam o desenvolvedor a investigar.\nNenhum dado pessoal sensível é incluído.',
        'en': 'Briefly describe the problem. The app will generate a .zip file\nwith logs and settings to help the developer investigate.\nNo sensitive personal data is included.',
        'fr': 'Décrivez brièvement le problème. L\'app génère un .zip\navec logs et paramètres pour aider le développeur.\nAucune donnée sensible incluse.',
        'es': 'Describe brevemente el problema. La app generará un .zip\ncon logs y configuraciones que ayudan al desarrollador.\nNo se incluyen datos personales sensibles.',
    },
    'report.label.description': {
        'pt': 'Descrição do problema:',
        'en': 'Problem description:',
        'fr': 'Description du problème:',
        'es': 'Descripción del problema:',
    },
    'report.btn.generate': {
        'pt': '📧 Gerar relatório e abrir e-mail',
        'en': '📧 Generate report and open email',
        'fr': '📧 Générer rapport et ouvrir email',
        'es': '📧 Generar informe y abrir email',
    },
    'report.msg.empty': {
        'pt': '⚠ Descreva o problema antes de continuar.',
        'en': '⚠ Describe the problem before continuing.',
        'fr': '⚠ Décrivez le problème avant de continuer.',
        'es': '⚠ Describe el problema antes de continuar.',
    },
    'report.msg.generated': {
        'pt': '✓ Arquivo gerado: {file}\nAnexe ele no e-mail e envie!',
        'en': '✓ File generated: {file}\nAttach it to the email and send!',
        'fr': '✓ Fichier généré: {file}\nAttachez-le à l\'email et envoyez!',
        'es': '✓ Archivo generado: {file}\n¡Adjúntalo al email y envía!',
    },
    'report.msg.error': {
        'pt': '✗ Erro: {err}', 'en': '✗ Error: {err}',
        'fr': '✗ Erreur: {err}', 'es': '✗ Error: {err}',
    },

    # ========================================================================
    # MENSAGENS GLOBAIS
    # ========================================================================
    'msg.ready': {
        'pt': 'Pronto.', 'en': 'Ready.', 'fr': 'Prêt.', 'es': 'Listo.',
    },
    'msg.error': {
        'pt': 'Erro', 'en': 'Error', 'fr': 'Erreur', 'es': 'Error',
    },

    # ========================================================================
    # DIÁLOGO DE RESTART (tema/idioma)
    # ========================================================================
    'restart.title': {
        'pt': 'Reabrir Dofusinator',
        'en': 'Reopen Dofusinator',
        'fr': 'Rouvrir Dofusinator',
        'es': 'Reabrir Dofusinator',
    },
    'restart.theme.message': {
        'pt': 'O tema da janela principal foi alterado.\n\nPra aplicar o novo tema completamente, o Dofusinator precisa ser reaberto.\n\nDeseja reabrir agora?',
        'en': 'The main window theme has changed.\n\nTo apply the new theme completely, Dofusinator needs to reopen.\n\nReopen now?',
        'fr': 'Le thème de la fenêtre principale a changé.\n\nPour appliquer le nouveau thème complètement, Dofusinator doit redémarrer.\n\nRedémarrer maintenant?',
        'es': 'El tema de la ventana principal cambió.\n\nPara aplicar completamente, Dofusinator necesita reabrirse.\n\n¿Reabrir ahora?',
    },
    'restart.lang.message': {
        'pt': 'O idioma do app foi alterado.\n\nPra aplicar em todos os menus completamente, o Dofusinator precisa ser reaberto.\n\nDeseja reabrir agora?',
        'en': 'The app language has changed.\n\nTo apply it to all menus completely, Dofusinator needs to reopen.\n\nReopen now?',
        'fr': 'La langue de l\'app a changé.\n\nPour l\'appliquer à tous les menus, Dofusinator doit redémarrer.\n\nRedémarrer maintenant?',
        'es': 'El idioma de la app cambió.\n\nPara aplicarlo en todos los menús, Dofusinator necesita reabrirse.\n\n¿Reabrir ahora?',
    },

    # ========================================================================
    # NOMES DOS IDIOMAS (pra dropdown)
    # ========================================================================
    'lang.pt': {
        'pt': 'Português (BR)', 'en': 'Portuguese (BR)', 'fr': 'Portugais (BR)', 'es': 'Portugués (BR)',
    },
    'lang.en': {
        'pt': 'English', 'en': 'English', 'fr': 'Anglais', 'es': 'Inglés',
    },
    'lang.fr': {
        'pt': 'Français', 'en': 'French', 'fr': 'Français', 'es': 'Francés',
    },
    'lang.es': {
        'pt': 'Español', 'en': 'Spanish', 'fr': 'Espagnol', 'es': 'Español',
    },

    # ========================================================================
    # HOTKEY CAPTURE POPUP (Sub-bloco 3.2)
    # ========================================================================
    'hotkey.capture.title': {
        'pt': 'Capturar Atalho',
        'en': 'Capture Shortcut',
        'fr': 'Capturer le Raccourci',
        'es': 'Capturar Atajo',
    },
    'hotkey.capture.heading': {
        'pt': '⌨️ Pressione o atalho',
        'en': '⌨️ Press the shortcut',
        'fr': '⌨️ Appuyez sur le raccourci',
        'es': '⌨️ Presiona el atajo',
    },
    'hotkey.capture.instruction': {
        'pt': 'Pressione qualquer combinação de teclas que você queira usar como atalho.\n\nExemplo: Ctrl + Shift + T',
        'en': 'Press any key combination you want to use as a shortcut.\n\nExample: Ctrl + Shift + T',
        'fr': 'Appuyez sur n\'importe quelle combinaison de touches à utiliser comme raccourci.\n\nExemple : Ctrl + Maj + T',
        'es': 'Presiona cualquier combinación de teclas para usar como atajo.\n\nEjemplo: Ctrl + Shift + T',
    },
    'hotkey.capture.cancel': {
        'pt': 'Cancelar',
        'en': 'Cancel',
        'fr': 'Annuler',
        'es': 'Cancelar',
    },
    'hotkey.capture.error_no_modifier': {
        'pt': '⚠ O atalho precisa ter pelo menos um modificador (Ctrl, Alt, Shift ou Win). Tente novamente.',
        'en': '⚠ The shortcut needs at least one modifier (Ctrl, Alt, Shift or Win). Try again.',
        'fr': '⚠ Le raccourci a besoin d\'au moins un modificateur (Ctrl, Alt, Maj ou Win). Réessayez.',
        'es': '⚠ El atajo necesita al menos un modificador (Ctrl, Alt, Shift o Win). Inténtalo de nuevo.',
    },
    'hotkey.capture.error_invalid_key': {
        'pt': '⚠ Tecla principal inválida. Use uma letra ou número (ex: Ctrl+Shift+T).',
        'en': '⚠ Invalid main key. Use a letter or number (ex: Ctrl+Shift+T).',
        'fr': '⚠ Touche principale invalide. Utilisez une lettre ou un chiffre (ex : Ctrl+Maj+T).',
        'es': '⚠ Tecla principal inválida. Usa una letra o número (ej: Ctrl+Shift+T).',
    },
    'hotkey.capture.error_lib_missing': {
        'pt': '⚠ Biblioteca de captura não disponível. Use o campo de texto.',
        'en': '⚠ Capture library not available. Use the text field.',
        'fr': '⚠ Bibliothèque de capture non disponible. Utilisez le champ de texte.',
        'es': '⚠ Biblioteca de captura no disponible. Usa el campo de texto.',
    },
    'hotkey.capture.error_conflict': {
        'pt': '⚠ Esse atalho já está em uso por outra função. Escolha outro.',
        'en': '⚠ This shortcut is already used by another function. Choose another.',
        'fr': '⚠ Ce raccourci est déjà utilisé par une autre fonction. Choisissez-en un autre.',
        'es': '⚠ Este atajo ya está siendo usado por otra función. Elige otro.',
    },

    # === Labels e botões da aba Atalho & Som (Sub-bloco 3.2) ===
    'shortcut.label.quick_input': {
        'pt': 'Tradução rápida:',
        'en': 'Quick translation:',
        'fr': 'Traduction rapide :',
        'es': 'Traducción rápida:',
    },
    'shortcut.label.overlay_toggle': {
        'pt': 'Overlay (toggle/colapsar):',
        'en': 'Overlay (toggle/collapse):',
        'fr': 'Overlay (basculer/réduire) :',
        'es': 'Overlay (alternar/colapsar):',
    },
    'shortcut.label.lurker_toggle': {
        'pt': 'Modo Lurker (liga/desliga):',
        'en': 'Lurker mode (on/off):',
        'fr': 'Mode Lurker (act./désact.) :',
        'es': 'Modo Lurker (act./desact.):',
    },
    'shortcut.btn.capture': {
        'pt': '🎯 Capturar',
        'en': '🎯 Capture',
        'fr': '🎯 Capturer',
        'es': '🎯 Capturar',
    },
    'shortcut.msg.hotkey_set': {
        'pt': 'Atalho atualizado: {hotkey}',
        'en': 'Shortcut updated: {hotkey}',
        'fr': 'Raccourci mis à jour : {hotkey}',
        'es': 'Atajo actualizado: {hotkey}',
    },

    # === Mini-pill (Sub-bloco 3.2) ===
    'mini_pill.placeholder': {
        'pt': '(aguardando captura...)',
        'en': '(waiting for capture...)',
        'fr': '(en attente de capture...)',
        'es': '(esperando captura...)',
    },

    # === Overlay: histórico (v1.0.21) ===
    'overlay.btn.clear_history': {
        'pt': '🗑️ Limpar histórico',
        'en': '🗑️ Clear history',
        'fr': '🗑️ Effacer l\'historique',
        'es': '🗑️ Limpiar historial',
    },
    'overlay.hint.dedup': {
        'pt': 'Linhas duplicadas só contam uma vez',
        'en': 'Duplicate lines only count once',
        'fr': 'Les lignes dupliquées ne comptent qu\'une fois',
        'es': 'Las líneas duplicadas solo cuentan una vez',
    },
    'overlay.clear.confirm_title': {
        'pt': 'Limpar histórico do chat',
        'en': 'Clear chat history',
        'fr': 'Effacer l\'historique du chat',
        'es': 'Limpiar historial del chat',
    },
    'overlay.clear.confirm_msg': {
        'pt': 'Tem certeza que quer limpar todo o histórico de traduções do chat?\n\nEssa ação não pode ser desfeita.',
        'en': 'Are you sure you want to clear all chat translation history?\n\nThis cannot be undone.',
        'fr': 'Êtes-vous sûr de vouloir effacer tout l\'historique de traduction du chat ?\n\nCette action est irréversible.',
        'es': '¿Seguro que quieres borrar todo el historial de traducciones del chat?\n\nEsta acción no se puede deshacer.',
    },

    # ========================================================================
    # WELCOME SCREEN (Bloco 3)
    # ========================================================================
    'welcome.title': {
        'pt': 'Bem-vindo ao Dofusinator!',
        'en': 'Welcome to Dofusinator!',
        'fr': 'Bienvenue sur Dofusinator!',
        'es': '¡Bienvenido a Dofusinator!',
    },

    # === Step 1: Boas-vindas ===
    'welcome.step1.heading': {
        'pt': '👋 Olá!',
        'en': '👋 Hello!',
        'fr': '👋 Bonjour!',
        'es': '👋 ¡Hola!',
    },
    'welcome.step1.body': {
        'pt': 'O Dofusinator lê o chat do Dofus em tempo real e traduz pra você. Também ajuda você a responder em outro idioma — ele lê seu texto, traduz e cola direto no jogo.\n\nEm poucos passos, vamos configurar tudo.',
        'en': 'Dofusinator reads the Dofus chat in real time and translates it for you. It also helps you reply in another language — it reads your text, translates and pastes directly into the game.\n\nIn a few steps, we\'ll get everything set up.',
        'fr': 'Dofusinator lit le chat de Dofus en temps réel et le traduit pour vous. Il vous aide aussi à répondre dans une autre langue — il lit votre texte, le traduit et le colle directement dans le jeu.\n\nEn quelques étapes, nous allons tout configurer.',
        'es': 'Dofusinator lee el chat de Dofus en tiempo real y lo traduce para ti. También te ayuda a responder en otro idioma — lee tu texto, traduce y pega directamente en el juego.\n\nEn pocos pasos, vamos a configurar todo.',
    },

    # === Step 2: Idioma da UI ===
    'welcome.step2.heading': {
        'pt': '🌍 Idioma do app',
        'en': '🌍 App language',
        'fr': '🌍 Langue de l\'app',
        'es': '🌍 Idioma de la app',
    },
    'welcome.step2.body': {
        'pt': 'Em qual idioma você quer ver os menus e mensagens do Dofusinator?\n\nIsso pode ser alterado depois em Aparência → Idioma do app.',
        'en': 'In which language do you want to see Dofusinator\'s menus and messages?\n\nThis can be changed later in Appearance → App language.',
        'fr': 'Dans quelle langue voulez-vous voir les menus et messages de Dofusinator?\n\nCeci peut être modifié plus tard dans Apparence → Langue de l\'app.',
        'es': '¿En qué idioma quieres ver los menús y mensajes de Dofusinator?\n\nEsto se puede cambiar después en Apariencia → Idioma de la app.',
    },

    # === Step 3: Captura ===
    'welcome.step3.heading': {
        'pt': '📐 Definir região do chat',
        'en': '📐 Define chat region',
        'fr': '📐 Définir la zone du chat',
        'es': '📐 Definir región del chat',
    },
    'welcome.step3.body': {
        'pt': 'Pra ler o chat, o app precisa saber ONDE ele tá na tela.\n\nApós este tutorial, vá na aba "Captura" e clique em "Definir Perímetro do Chat". O app vai pedir que você aponte os 2 cantos do chat com o mouse.\n\nÉ rápido — leva uns 5 segundos.',
        'en': 'To read the chat, the app needs to know WHERE it is on the screen.\n\nAfter this tutorial, go to the "Capture" tab and click "Set Chat Perimeter". The app will ask you to point the 2 corners of the chat with the mouse.\n\nIt\'s fast — takes about 5 seconds.',
        'fr': 'Pour lire le chat, l\'app doit savoir OÙ il se trouve sur l\'écran.\n\nAprès ce tutoriel, allez dans l\'onglet "Capture" et cliquez sur "Définir Périmètre du Chat". L\'app vous demandera de pointer les 2 coins du chat avec la souris.\n\nC\'est rapide — environ 5 secondes.',
        'es': 'Para leer el chat, la app necesita saber DÓNDE está en la pantalla.\n\nDespués de este tutorial, ve a la pestaña "Captura" y haz clic en "Definir Perímetro del Chat". La app te pedirá que apuntes las 2 esquinas del chat con el mouse.\n\nEs rápido — toma unos 5 segundos.',
    },

    # === Step 4: Hotkey ===
    'welcome.step4.heading': {
        'pt': '⌨️ Atalho mágico',
        'en': '⌨️ Magic shortcut',
        'fr': '⌨️ Raccourci magique',
        'es': '⌨️ Atajo mágico',
    },
    'welcome.step4.body': {
        'pt': 'Pra responder em outro idioma, aperte:\n\n   Ctrl + Shift + T\n\nUm popup vai abrir. Você digita em português, ele traduz, e cola direto no chat do Dofus.\n\nEsse atalho pode ser personalizado em Atalho & Som.',
        'en': 'To reply in another language, press:\n\n   Ctrl + Shift + T\n\nA popup will open. You type in your language, it translates, and pastes directly into Dofus chat.\n\nThis shortcut can be customized in Shortcut & Sound.',
        'fr': 'Pour répondre dans une autre langue, appuyez sur:\n\n   Ctrl + Shift + T\n\nUn popup s\'ouvrira. Vous tapez dans votre langue, il traduit, et colle directement dans le chat Dofus.\n\nCe raccourci peut être personnalisé dans Raccourci & Son.',
        'es': 'Para responder en otro idioma, presiona:\n\n   Ctrl + Shift + T\n\nSe abrirá un popup. Escribes en tu idioma, lo traduce, y pega directamente en el chat de Dofus.\n\nEste atajo se puede personalizar en Atajo y Sonido.',
    },

    # === Step 5: Pronto ===
    'welcome.step5.heading': {
        'pt': '🎉 Tudo pronto!',
        'en': '🎉 All set!',
        'fr': '🎉 Tout est prêt!',
        'es': '🎉 ¡Todo listo!',
    },
    'welcome.step5.body': {
        'pt': 'Você está pronto pra usar o Dofusinator!\n\n💡 Dicas rápidas:\n• Modo Lurker (botão grande no topo): bloqueia auto-envios — útil pra apenas ler\n• Termos Personalizados (aba Tradução): ensina o app a traduzir gírias do jogo\n• Reportar Problema (aba Avançado): se algo não funcionar, manda um relatório\n\nBoa caçada! 🎮',
        'en': 'You\'re ready to use Dofusinator!\n\n💡 Quick tips:\n• Lurker Mode (big button at top): blocks auto-sends — useful for just reading\n• Custom Terms (Translation tab): teach the app game slang\n• Report Problem (Advanced tab): if something doesn\'t work, send a report\n\nHappy hunting! 🎮',
        'fr': 'Vous êtes prêt à utiliser Dofusinator!\n\n💡 Astuces rapides:\n• Mode Lurker (gros bouton en haut): bloque les auto-envois — utile pour juste lire\n• Termes Personnalisés (onglet Traduction): apprenez l\'argot du jeu à l\'app\n• Signaler un Problème (onglet Avancé): si quelque chose ne marche pas, envoyez un rapport\n\nBonne chasse! 🎮',
        'es': '¡Estás listo para usar Dofusinator!\n\n💡 Consejos rápidos:\n• Modo Lurker (botón grande arriba): bloquea auto-envíos — útil para solo leer\n• Términos Personalizados (pestaña Traducción): enseña jerga del juego a la app\n• Reportar Problema (pestaña Avanzado): si algo no funciona, envía un reporte\n\n¡Buena cacería! 🎮',
    },

    # === Botões ===
    'welcome.btn.next': {
        'pt': 'Próximo →',
        'en': 'Next →',
        'fr': 'Suivant →',
        'es': 'Siguiente →',
    },
    'welcome.btn.back': {
        'pt': '← Voltar',
        'en': '← Back',
        'fr': '← Retour',
        'es': '← Atrás',
    },
    'welcome.btn.skip': {
        'pt': 'Pular tutorial',
        'en': 'Skip tutorial',
        'fr': 'Passer le tutoriel',
        'es': 'Omitir tutorial',
    },
    'welcome.btn.finish': {
        'pt': '✓ Começar a usar',
        'en': '✓ Start using',
        'fr': '✓ Commencer',
        'es': '✓ Empezar a usar',
    },
    'welcome.step_indicator': {
        'pt': 'Passo {current} de {total}',
        'en': 'Step {current} of {total}',
        'fr': 'Étape {current} sur {total}',
        'es': 'Paso {current} de {total}',
    },
}


def set_language(lang: str):
    """Define o idioma atual em memória."""
    global _current_lang
    if lang in SUPPORTED_LANGUAGES:
        _current_lang = lang
        log.info(f"i18n: idioma alterado pra '{lang}'")
    else:
        log.warning(f"i18n: idioma '{lang}' não suportado. Usando '{_current_lang}'.")


def get_language() -> str:
    """Retorna o idioma atual."""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """
    Traduz uma chave pro idioma atual.

    Args:
        key: Chave do dicionário (ex: 'btn.save')
        **kwargs: Variáveis pra str.format() na string traduzida

    Returns:
        String traduzida. Se chave não existir, retorna a própria chave (debug).
    """
    entry = TRANSLATIONS.get(key)
    if entry is None:
        log.warning(f"i18n: chave '{key}' não encontrada")
        return key

    # Tenta o idioma atual, fallback pra PT, fallback pra a chave
    text = entry.get(_current_lang) or entry.get('pt') or key

    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError) as e:
            log.error(f"i18n: erro ao formatar '{key}' com {kwargs}: {e}")
            return text
    return text


def get_supported_languages() -> list[str]:
    """Lista de códigos de idioma suportados."""
    return list(SUPPORTED_LANGUAGES)


def get_language_label(code: str) -> str:
    """Nome amigável do idioma (no idioma atual). Ex: 'pt' → 'Portuguese (BR)' em EN."""
    return t(f'lang.{code}')
