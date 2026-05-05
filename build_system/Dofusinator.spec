# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec pra Dofusinator.
Modo: --onedir (pasta com .exe + DLLs lado a lado)

Mudou de --onefile pra --onedir em v1.0.4 pra resolver:
- Race condition no restart (Tcl/python DLL not found em _MEI temp)
- Tempo de abertura mais rápido (~1-2s vs 5-10s)
- Padrão usado por VS Code/Discord/Spotify

Como rodar:
    pyinstaller Dofusinator.spec

Output: dist/Dofusinator/Dofusinator.exe (pasta inteira)
"""
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Path config
PROJECT_ROOT = os.path.dirname(os.path.abspath(SPECPATH))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

# Adiciona src/ ao path de import
sys.path.insert(0, SRC_DIR)
from app_info import APP_NAME, APP_VERSION, APP_AUTHOR


# === Hidden imports (libs que PyInstaller pode não detectar automaticamente) ===
hidden_imports = [
    # CustomTkinter precisa de detecção explícita
    'customtkinter',
    # pystray e backend Windows
    'pystray',
    'pystray._win32',
    # Mouse/keyboard listeners
    'mouse',
    'keyboard',
    # Módulos novos do Sub-bloco 3.2 (importados lazy dentro de métodos)
    'selection_preview',
    'hotkey_capture_popup',
    'mini_pill',
    'f2_tooltip',
    # Módulo novo v1.0.21 (chat history)
    'chat_history_manager',
    'spacing',
    'themed_scrollbar',
    # Módulos novos v1.0.30 (auto-apply settings + toast notifications)
    'toast_notification',
    'auto_apply',
    # Pillow plugins (ícone, processamento)
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageGrab',
    'PIL.ImageEnhance',
    'PIL.ImageFilter',
    'PIL.ImageOps',
    'PIL.IcoImagePlugin',
    # OCR
    'pytesseract',
    # Translator backends
    'deep_translator',
    'deep_translator.google',
    'deep_translator.deepl',
    # Multi-monitor
    'screeninfo',
    'screeninfo.enumerators.windows',
    # WAV/audio
    'wave',
    'struct',
]

# Coleta data files do customtkinter (assets internos)
datas = []
datas += collect_data_files('customtkinter')

# Bundle ícones e sons (se existirem)
if os.path.exists(os.path.join(PROJECT_ROOT, 'assets')):
    datas.append((os.path.join(PROJECT_ROOT, 'assets'), 'assets'))
if os.path.exists(os.path.join(PROJECT_ROOT, 'sounds')):
    datas.append((os.path.join(PROJECT_ROOT, 'sounds'), 'sounds'))
if os.path.exists(os.path.join(PROJECT_ROOT, 'slang_dictionary.json')):
    datas.append((os.path.join(PROJECT_ROOT, 'slang_dictionary.json'), '.'))


a = Analysis(
    [os.path.join(SRC_DIR, 'main.py')],
    pathex=[SRC_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclui libs grandes que não usamos pra reduzir tamanho
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

# Modo --onedir: gera pasta com .exe + DLLs ao lado (sem _MEI temp)
# Mais rápido pra abrir, sem race conditions no restart, padrão usado
# por VS Code/Discord/Spotify/OBS.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # ← chave: NÃO embute binários no .exe
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI, sem console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_ROOT, 'assets', 'icon.ico') if os.path.exists(
        os.path.join(PROJECT_ROOT, 'assets', 'icon.ico')
    ) else None,
    version='version_info.txt' if os.path.exists(
        os.path.join(PROJECT_ROOT, 'build_system', 'version_info.txt')
    ) else None,
)

# COLLECT junta tudo numa pasta única — saída em dist/Dofusinator/
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,  # nome da pasta de saída
)
