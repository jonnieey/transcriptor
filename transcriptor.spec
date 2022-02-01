# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['src/transcriptor/main.py'],
             pathex=['/home/kamikaze/.python/projects/transcriptor'],
             binaries=[],
             datas=[('src/transcriptor/commands', 'commands'), ('src/transcriptor', 'transcriptor'),],
             hiddenimports=['json', 'dataclasses', 'audioread', 'magic', 'jinja2', 'pdfkit', 'docxtpl', 'appdirs', 'rich'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
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
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
