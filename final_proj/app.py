import struct
from flask import Flask, render_template, jsonify, request, send_from_directory, url_for
from flask_socketio import SocketIO, emit
from flask_cors import CORS  # Import CORS
from vosk import Model, KaldiRecognizer
import os
import json

# Initialize Flask app and Flask-SocketIO
app = Flask(__name__)
CORS(app)  # Enable CORS for all domains
socketio = SocketIO(app)

# Path to the Vosk model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "vosk-model-small-en-us-0.15")
model = Model(MODEL_PATH)

# Global variables
recognizer = KaldiRecognizer(model, 16000)
latest_transcription = ""
text_content = ""
selected_language = None
predefined_sentences = [
    "hello", "goodbye", "how are you", "good wishes",
    "i will drink water", "i will have food", "my name is",
    "thank you", "will you drink water", "will you have food"
]
languages = {
    "Apatani": "Apatani",
    "Bhutanese": "Bhutanese",
    "French": "French",
    "Hindi": "Hindi",
    "Monpa": "Monpa"
}
audio_directory = os.path.join(BASE_DIR, "audio")
sentences_directory = os.path.join(BASE_DIR, "sentences")

# Initialize recognizer
def initialize_recognizer():
    global recognizer
    recognizer = KaldiRecognizer(model, 16000)

# Route to handle audio data
@socketio.on('audio')
def handle_audio(data):
    # Convert the received bytes to 16-bit PCM
    pcm_data = struct.unpack('<' + ('h' * (len(data) // 2)), data)
    pcm_bytes = struct.pack('<' + ('h' * len(pcm_data)), *pcm_data)

    # Feed the PCM bytes into the recognizer
    if recognizer.AcceptWaveform(pcm_bytes):
        result = recognizer.Result()
        result_json = json.loads(result)
        transcription = result_json.get("text", "")
        
        # Send the transcription back to the client
        emit('transcription', {"transcription": transcription})

    # Handle partial results
    else:
        partial_result = recognizer.PartialResult()
        emit('transcription', {"transcription": json.loads(partial_result).get("partial", "")})

# Function to retrieve text content based on matched sentence
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

# Route to select language and reinitialize recognizer
@app.route('/select_language', methods=['POST'])
def select_language():
    global selected_language, latest_transcription, text_content
    new_language = request.form['language_id']

    # Only reinitialize if the language has changed
    if new_language != selected_language:
        selected_language = new_language
        initialize_recognizer()
        latest_transcription = ""
        text_content = ""

    return jsonify({'status': 'success'})

# Route to get text content based on the transcription
@app.route('/get_text_content', methods=['GET'])
def get_text_content():
    global text_content
    return jsonify({'data1': text_content})

# Route to serve the audio files based on the transcription
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

# Serve the audio file
@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(audio_directory, filename)

@app.route('/')
def index():
    return render_template('index.html', languages=languages)

if __name__ == '__main__':
    socketio.run(app, debug=True)
