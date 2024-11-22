import PyInstaller.__main__
import os
import vosk

vosk_path = os.path.dirname(vosk.__file__)

PyInstaller.__main__.run([
    'start.py',
    '--onefile',
    '--add-data', f'{vosk_path};vosk',
    '--add-data', 'templates;templates',
    '--add-data', 'static;static',
    '--add-data', 'audio;audio',
    '--add-data', 'sentences;sentences',
    '--add-data', 'vosk-model-small-en-us-0.15;vosk-model-small-en-us-0.15',
    '--hidden-import', 'flask_socketio',
    '--hidden-import', 'vosk',
    '--hidden-import', 'numpy.core._methods',
    '--hidden-import', 'numpy.lib.format',
    '--name', 'SpeechTranslator',
    '--noconfirm',
    '--clean'
])
