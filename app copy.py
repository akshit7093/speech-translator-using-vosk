from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_socketio import SocketIO, emit
import speech_recognition as sr
import numpy as np
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    transports=['websocket', 'polling']
)

# Paths and configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
audio_directory = os.path.join(BASE_DIR, "audio")
sentences_directory = os.path.join(BASE_DIR, "sentences")

# Check if running on Vercel (production) or locally
IS_VERCEL = os.environ.get('VERCEL')

# Initialize speech recognizer
recognizer = sr.Recognizer()

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
audio_buffer = bytearray()
CHUNK_SIZE = 48000  # Increased to 3 seconds of audio at 16kHz

@socketio.on('audio_stream')
def handle_audio_stream(data):
    global audio_buffer
    
    if IS_VERCEL:
        emit('transcription', {
            'transcription': "Speech recognition not available in production",
            'matched_sentence': None
        })
        return
    
    try:
        # Accumulate audio data
        if isinstance(data, memoryview):
            audio_buffer.extend(data.tobytes())
        else:
            audio_buffer.extend(data)

        # Process when buffer reaches sufficient size
        if len(audio_buffer) >= CHUNK_SIZE:
            # Create an AudioData object with larger chunk
            audio = sr.AudioData(audio_buffer, sample_rate=16000, sample_width=2)
            
            try:
                # Perform speech recognition without timeout parameter
                text = recognizer.recognize_google(audio)
                process_recognition(text.lower())
            except sr.UnknownValueError:
                emit('transcription', {
                    'transcription': "",
                    'matched_sentence': None
                })
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                emit('transcription', {
                    'transcription': "Error processing speech",
                    'matched_sentence': None
                })
            
            # Clear the buffer after processing
            audio_buffer = bytearray()
                
    except Exception as e:
        print(f"Audio processing error: {e}")
        audio_buffer = bytearray()

def process_recognition(transcription):
    # Match against predefined sentences
    matched_sentence = next(
        (sentence for sentence in predefined_sentences 
         if sentence in transcription),
        None
    )
    
    # Emit transcription result
    emit('transcription', {
        'transcription': transcription,
        'matched_sentence': matched_sentence
    })
    
    # Update global state if match found
    if matched_sentence:
        global latest_transcription, text_content
        latest_transcription = transcription
        text_content = display_text(matched_sentence)
        
        # Log successful recognition
        print(f"Recognized: {matched_sentence}")

def display_text(sentence):
    text_path = os.path.join(sentences_directory, sentence.replace(" ", "_"), f"{languages[selected_language]}.txt")
    if os.path.exists(text_path):
        with open(text_path, 'r', encoding='utf-8') as file:
            return file.read()
    return None

@app.route('/')
def index():
    return render_template('index.html', languages=languages)

@app.route('/select_language', methods=['POST'])
def select_language():
    global selected_language
    selected_language = request.form['language_id']
    return jsonify({'status': 'success'})

@app.route('/get_transcription', methods=['GET'])
def get_transcription():
    return jsonify({'transcription': latest_transcription})

@app.route('/get_text_content', methods=['GET'])
def get_text_content():
    return jsonify({'data1': text_content})

@app.route('/get_audio_path', methods=['POST'])
def get_audio_path():
    sentence = request.form['sentence']
    language = request.form['language']
    audio_filename = f"{sentence.replace(' ', '_')}/{languages[language]}.mp3"
    audio_path = os.path.join(audio_directory, audio_filename)
    
    if os.path.exists(audio_path):
        return jsonify({'audioPath': url_for('serve_audio', filename=audio_filename)})
    return jsonify({'audioPath': None})

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(audio_directory, filename)

@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok", "environment": "Vercel" if IS_VERCEL else "Development"})

if __name__ == '__main__':
    socketio.run(app, debug=True)