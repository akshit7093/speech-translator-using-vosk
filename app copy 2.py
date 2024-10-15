from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import numpy as np
import json
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load Vosk model
model = Model("vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

# Paths for predefined sentences, audio, etc.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
audio_directory = os.path.join(BASE_DIR, "audio")

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

selected_language = None
latest_transcription = ""
text_content = ""

# Buffer to store audio data
audio_buffer = bytearray()

@socketio.on('audio_stream')
def handle_audio_stream(data):
    global audio_buffer, recognizer

    # Append new audio data to the buffer
    audio_buffer.extend(data)

    # Process audio if enough data is available (e.g., 0.5 seconds worth)
    while len(audio_buffer) >= 16000:  # 16000 samples/second * 0.5 seconds
        # Get 0.5 seconds worth of audio
        audio_chunk = audio_buffer[:16000]
        audio_buffer = audio_buffer[16000:]  # Remove the processed chunk

        # Convert bytearray to bytes
        audio_chunk_bytes = bytes(audio_chunk)

        # Feed the audio chunk to the recognizer
        if recognizer.AcceptWaveform(audio_chunk_bytes):
            result = json.loads(recognizer.Result())
            transcription = result.get('text', '')

            # Check if transcription matches a predefined sentence
            matched_sentence = None
            for sentence in predefined_sentences:
                if sentence in transcription.lower():
                    matched_sentence = sentence
                    break

            # Send the transcription result back to the client
            emit('transcription', {'transcription': transcription, 'matched_sentence': matched_sentence})


# Route for the main page
@app.route('/')
def index():
    return render_template('index.html', languages=languages)

# API for selecting language
@app.route('/select_language', methods=['POST'])
def select_language():
    global selected_language
    selected_language = request.form['language_id']
    return jsonify({'status': 'success'})

# API to get the latest transcription
@app.route('/get_transcription', methods=['GET'])
def get_transcription():
    global latest_transcription
    return jsonify({'transcription': latest_transcription})

# API to get the text content for a matched sentence
@app.route('/get_text_content', methods=['GET'])
def get_text_content():
    global text_content
    return jsonify({'data1': text_content})

# Serve audio files from the audio directory
@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(audio_directory, filename)

if __name__ == '__main__':
    socketio.run(app, debug=True)
