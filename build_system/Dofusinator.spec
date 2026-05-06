# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec pra Dofusinator.
Modo: --onedir (pasta com .exe + DLLs lado a lado)

v1.1.0 (final): Spec limpo. Modulos do src/ sao varridos automaticamente
                e listados como flat (nome direto, sem 'src.' prefix).
                Sem __init__.py em src/, sem collect_submodules('src')
                — esses 2 atrapalharam o bundle no PyInstaller 6.20.

Como rodar:
    pyinstaller Dofusinator.spec

Output: dist/Dofusinator/Dofusinator.exe (pasta inteira)
"""
import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ============================================================================
# Path config
# ============================================================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(SPECPATH))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

sys.path.insert(0, SRC_DIR)
from app_info import APP_NAME, APP_VERSION, APP_AUTHOR

# Sanity check: src/ NAO deve ter __init__.py.
# Se tiver, PyInstaller 6.20 bugga e descarta TODOS os modulos do projeto.
_init_path = os.path.join(SRC_DIR, '__init__.py')
if os.path.exists(_init_path):
    raise RuntimeError(
        f"\n\n!!! CONFLITO: src/__init__.py existe e DEVE ser deletado !!!\n"
        f"Path: {_init_path}\n"
        f"Quando esse arquivo existe, PyInstaller 6.20 silenciosamente\n"
        f"descarta os modulos do projeto do bundle final.\n"
        f"Apaga o arquivo e roda o build de novo.\n"
    )
print("[SPEC] OK: src/__init__.py NAO existe (correto)")


# ============================================================================
# Varredura automatica dos modulos do src/
# ============================================================================
src_module_names = []
for _filename in os.listdir(SRC_DIR):
    if _filename.endswith('.py') and _filename != '__init__.py':
        src_module_names.append(_filename[:-3])

print(f"[SPEC] Coletados {len(src_module_names)} modulos do src/: {src_module_names}")


# ============================================================================
# Hidden imports
# ============================================================================
hidden_imports = [
    # ---- Modulos do projeto (varridos do src/, formato flat) ----
    *src_module_names,

    # ---- CustomTkinter ----
    'customtkinter',

    # ---- pystray e backend Windows ----
    'pystray',
    'pystray._win32',

    # ---- Mouse/keyboard listeners ----
    'mouse',
    'keyboard',

    # ---- Pillow plugins ----
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageGrab',
    'PIL.ImageEnhance',
    'PIL.ImageFilter',
    'PIL.ImageOps',
    'PIL.IcoImagePlugin',

    # ---- OCR ----
    'pytesseract',

    # ---- Translator backends ----
    'deep_translator',
    'deep_translator.google',
    'deep_translator.deepl',

    # ---- Multi-monitor ----
    'screeninfo',
    'screeninfo.enumerators.windows',

    # ---- WAV/audio ----
    'wave',
    'struct',

    # ---- v1.1.0: Velopack auto-update ----
    'velopack',
]

# Submodulos do velopack (se a lib tiver estrutura interna)
try:
    hidden_imports += collect_submodules('velopack')
except Exception as e:
    print(f"[SPEC] WARN: collect_submodules('velopack') falhou: {e}")

# Dedup
hidden_imports = list(dict.fromkeys(hidden_imports))


# ============================================================================
# Data files
# ============================================================================
datas = []
datas += collect_data_files('customtkinter')

if os.path.exists(os.path.join(PROJECT_ROOT, 'assets')):
    datas.append((os.path.join(PROJECT_ROOT, 'assets'), 'assets'))
if os.path.exists(os.path.join(PROJECT_ROOT, 'sounds')):
    datas.append((os.path.join(PROJECT_ROOT, 'sounds'), 'sounds'))
if os.path.exists(os.path.join(PROJECT_ROOT, 'slang_dictionary.json')):
    datas.append((os.path.join(PROJECT_ROOT, 'slang_dictionary.json'), '.'))


# ============================================================================
# Analysis
# ============================================================================
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
