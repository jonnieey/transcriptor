# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys
import os

block_cipher = None

# Collect all data files
datas = []
datas += collect_data_files('transcriptor')
datas += [('src/transcriptor/tui.css', 'transcriptor')]
datas += [('src/transcriptor/templates', 'transcriptor/templates')]
datas += [('src/transcriptor/invoice_templates', 'transcriptor/invoice_templates')]

# Collect hidden imports
hiddenimports = []
hiddenimports += collect_submodules('sqlalchemy')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('weasyprint')
# Add any other hidden imports as needed

a = Analysis(
    ['src/transcriptor/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='transcriptor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
