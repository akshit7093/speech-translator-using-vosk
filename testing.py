from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from vosk import Model, KaldiRecognizer
from flask_socketio import SocketIO
import json
import os
import wave
import io

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "vosk-model-small-en-us-0.15")

model = Model(model_path=MODEL_PATH)
app = Flask(__name__)
socketio = SocketIO(app)

# Global variables
latest_transcription = ""
selected_language = None
text_content = ""

# Predefined sentences
predefined_sentences = [
    "hello", "goodbye", "how are you", "good wishes",
    "i will drink water", "i will have food", "my name is",
    "thank you", "will you drink water", "will you have food"
]

# Supported languages with their IDs
languages = {
    "Apatani": "Apatani",
    "Bhutanese": "Bhutanese",
    "French": "French",
    "Hindi": "Hindi",
    "Monpa": "Monpa"
}

# Path to the directory containing audio and text files
audio_directory = os.path.join(BASE_DIR, "audio")
sentences_directory = os.path.join(BASE_DIR, "sentences")

def display_text(sentence):
    global selected_language
    text_path = os.path.join(sentences_directory, sentence.replace(" ", "_"), f"{languages[selected_language]}.txt")
    
    if os.path.exists(text_path):
        with open(text_path, 'r', encoding='utf-8') as file:
            text_content = file.read()
            return text_content
    else:
        print(f"Text file '{text_path}' not found.")
        return None

@app.route('/')
def index():
    return render_template('testing.html', languages=languages)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    global latest_transcription, text_content, selected_language

    audio_data = request.files['audio'].read()
    selected_language = request.form['language_id']
    
    wf = wave.open(io.BytesIO(audio_data), 'rb')
    
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != 'NONE':
        return jsonify({'error': 'Audio file must be WAV format mono PCM.'})

    recognizer = KaldiRecognizer(model, wf.getframerate())
    
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            latest_transcription = result['text']
            
            matched_sentence = None
            for sentence in predefined_sentences:
                if sentence in latest_transcription.lower():
                    matched_sentence = sentence
                    break
                    
            if matched_sentence:
                text_content = display_text(matched_sentence)

    return jsonify({'transcription': latest_transcription, 'text_content': text_content})

@app.route('/get_audio_path', methods=['POST'])
def get_audio_path():
    sentence = request.form['sentence']
    language = request.form['language']

    audio_filename = f"{sentence.replace(' ', '_')}/{languages[language]}.mp3"
    audio_path = os.path.join(audio_directory, audio_filename)

    if os.path.exists(audio_path):
        audio_url = url_for('serve_audio', filename=audio_filename)
        return jsonify({'audioPath': audio_url})
    else:
        return jsonify({'audioPath': None})

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(audio_directory, filename)

if __name__ == '__main__':
    app.run(debug=True)
