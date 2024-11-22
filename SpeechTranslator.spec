# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['start.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Akshit\\anaconda3\\envs\\tf\\lib\\site-packages\\vosk', 'vosk'), ('templates', 'templates'), ('static', 'static'), ('audio', 'audio'), ('sentences', 'sentences'), ('vosk-model-small-en-us-0.15', 'vosk-model-small-en-us-0.15')],
    hiddenimports=['flask_socketio', 'vosk', 'numpy', 'numpy.core._methods', 'numpy.lib.format'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SpeechTranslator',
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
