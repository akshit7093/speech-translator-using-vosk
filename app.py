from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, send_file, Response
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
from flask_cors import CORS
import numpy as np
import json
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    transports=['websocket', 'polling']
)

# Load Vosk model
model = Model("vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

# Paths and configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# audio_directory = os.path.join(BASE_DIR, "audio")
audio_directory="audio"
# sentences_directory = os.path.join(BASE_DIR, "sentences")
sentences_directory="sentences"

predefined_sentences = [
    "hello",
    "goodbye", "how are you", "good wishes",
    "i will drink water", "i will have food", "my name is",
    "thank you", 
    "will you drink water", "will you have food"
]

languages = {
    "Apatani": "Apatani",
    "Bhutanese": "Bhutanese",
    "French": "French",
    "Hindi": "Hindi",
    "Monpa": "Monpa"
}

selected_language = None
latest_transcription = ""
text_content = ""
audio_buffer = bytearray()

recognizer = KaldiRecognizer(model, 16000, '["[unk]", ' + 
             ','.join(f'"{word}"' for word in predefined_sentences) + ']')

@socketio.on('audio_stream')
def handle_audio_stream(data):
    global audio_buffer, recognizer

    try:
        chunk_size = 16000

        if isinstance(data, memoryview):
            audio_buffer.extend(data.tobytes())
        else:
            audio_buffer.extend(data)

        while len(audio_buffer) >= chunk_size:
            audio_chunk = bytes(audio_buffer[:chunk_size])
            audio_buffer = audio_buffer[chunk_size:]

            if recognizer.AcceptWaveform(audio_chunk):
                result = json.loads(recognizer.Result())
                process_recognition(result)

    except Exception as e:
        print(f"Audio processing error: {e}")
        audio_buffer = bytearray()

def process_recognition(result):
    transcription = result.get('text', '').lower()

    matched_sentence = next(
        (sentence for sentence in predefined_sentences 
         if sentence in transcription),
        None
    )

    emit('transcription', {
        'transcription': transcription,
        'matched_sentence': matched_sentence
    })

    if matched_sentence:
        global latest_transcription, text_content
        latest_transcription = transcription
        text_content = get_text_content(matched_sentence)
        print(f"Recognized: {matched_sentence}")

def get_text_content(sentence):
    text_path = os.path.join(sentences_directory, sentence.replace(" ", "_"), f"{languages[selected_language]}.txt")
    if os.path.exists(text_path):
        with open(text_path, 'r', encoding='utf-8') as file:
            return file.read()
    return None

@app.route('/')
def index():
    return render_template('index.html', languages=languages)

@app.route('/static/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/static/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/select_language', methods=['POST'])
def select_language():
    global selected_language
    selected_language = request.form['language_id']
    return jsonify({'status': 'success'})

@app.route('/play_audio/<sentence>/<language>')
def play_audio(sentence, language):
    audio_filename = f"{sentence.replace(' ', '_')}/{languages[language]}.mp3"
    audio_path = os.path.join(audio_directory, audio_filename)
    print(audio_path)
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/mp3')
    return Response(status=404)

@app.route('/display_text/<sentence>/<language>')
def display_text_route(sentence, language):
    text_path = os.path.join(sentences_directory, sentence.replace(" ", "_"), f"{languages[language]}.txt")
    print(text_path)
    if os.path.exists(text_path):
        with open(text_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    return Response(status=404)

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(audio_directory, filename)

@app.route('/download-apk')
def download_apk():
    apk_path = '.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists/speechtranslator/build/outputs/apk/debug/speechtranslator-debug.apk'
    if os.path.exists(apk_path):
        return send_file(apk_path, as_attachment=True, download_name='SpeechTranslator.apk')
    return "APK not found. Please build the project first.", 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
