from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import numpy as np
import json
import os
from flask_cors import CORS
from engineio.async_drivers import eventlet

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    async_mode='eventlet',  # Using eventlet for better production compatibility
    ping_timeout=120,  # Increased for AWS latency
    ping_interval=30,  # Increased for AWS latency
    transports=['websocket', 'polling'],
    logger=True,  # Enable logging for debugging
    engineio_logger=True  # Enable Engine.IO logging
)

# Paths and configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
audio_directory = os.path.join(BASE_DIR, "audio")
sentences_directory = os.path.join(BASE_DIR, "sentences")

# Load Vosk model - AWS allows loading the full model
model_path = os.path.join(BASE_DIR, "vosk-model-small-en-us-0.15")
if not os.path.exists(model_path):
    raise RuntimeError(f"Vosk model not found at {model_path}")
    
model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)

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

# Initialize recognizer with predefined sentences
recognizer = KaldiRecognizer(model, 16000, '["[unk]", ' + 
            ','.join(f'"{word}"' for word in predefined_sentences) + ']')

# Handle incoming audio stream
@socketio.on('audio_stream')
def handle_audio_stream(data):
    global audio_buffer, recognizer
    
    try:
        chunk_size = 16000  # 1 second of audio at 16kHz
        
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
        audio_buffer = bytearray()  # Reset buffer on error

def process_recognition(result):
    transcription = result.get('text', '').lower()
    
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
    
    print(f"Requested audio path: {audio_path}")
    if os.path.exists(audio_path):
        audio_url = url_for('serve_audio', filename=audio_filename, _external=True)
        print(f"Serving audio from: {audio_url}")
        return jsonify({'audioPath': audio_url})
    print(f"Audio file not found at: {audio_path}")
    return jsonify({'audioPath': None})

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    print(f"Serving audio file: {filename} from directory: {audio_directory}")
    return send_from_directory(audio_directory, filename)

def display_text(sentence):
    text_path = os.path.join(sentences_directory, sentence.replace(" ", "_"), f"{languages[selected_language]}.txt")
    print(f"Looking for text file at: {text_path}")
    if os.path.exists(text_path):
        try:
            with open(text_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return None
    print(f"Text file not found at: {text_path}")
    return None

# Health check endpoint for AWS
@app.route('/api/health')
def health_check():
    return jsonify({"status": "ok", "environment": "AWS"})

# Main entry point for AWS
if __name__ == '__main__':
    # Use eventlet WSGI server instead of Werkzeug
    import eventlet
    eventlet.monkey_patch()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
