import eventlet
eventlet.monkey_patch()

import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_socketio import SocketIO
from flask_cors import CORS
from vosk import Model, KaldiRecognizer

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure SocketIO with EVENTLET (not gevent)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',  # Changed from 'gevent' to 'eventlet'
    logger=False,  # Set to False to reduce log spam
    engineio_logger=False,  # Set to False to reduce log spam
    debug=False  # Set to False for production
)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
audio_directory = os.path.join(BASE_DIR, "audio")
sentences_directory = os.path.join(BASE_DIR, "sentences")

# Load Vosk model
try:
    model_path = os.path.join(BASE_DIR, "vosk-model-small-en-us-0.15")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    model = Model(model_path)
    logger.info("Vosk model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    exit(1)

# Predefined sentences
predefined_sentences = [
    "hello", "goodbye", "how are you", "good wishes",
    "i will drink water", "i will have food", "my name is",
    "thank you", "will you drink water", "will you have food"
]

# Initialize recognizer
recognizer = KaldiRecognizer(
    model, 16000,
    '["[unk]", ' + ','.join(f'"{word}"' for word in predefined_sentences) + ']'
)

# Global variables
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

@app.route('/')
def index():
    logger.debug("Serving index page")
    return render_template('index.html', languages=languages)

@app.route('/api/health')
def health_check():
    logger.debug("Health check endpoint called")
    return jsonify({"status": "ok"})

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('audio_stream')
def handle_audio_stream(data):
    global audio_buffer, recognizer
    logger.debug(f"Received audio data: {len(data)} bytes")

    try:
        chunk_size = 4000

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
        logger.error(f"Audio processing error: {e}")
        audio_buffer = bytearray()

def process_recognition(result):
    transcription = result.get('text', '').lower()
    matched_sentence = next(
        (sentence for sentence in predefined_sentences if sentence in transcription),
        None
    )

    socketio.emit('transcription', {
        'transcription': transcription,
        'matched_sentence': matched_sentence
    })
    logger.debug(f"Emitted transcription: {transcription}")

    if matched_sentence:
        global latest_transcription, text_content
        latest_transcription = transcription
        text_content = read_text_file(matched_sentence)
        logger.info(f"Recognized: {matched_sentence}")

def read_text_file(sentence):
    if not selected_language:
        return None

    text_path = os.path.join(
        sentences_directory,
        sentence.replace(" ", "_"),
        f"{languages[selected_language]}.txt"
    )
    logger.debug(f"Looking for text file at: {text_path}")

    if os.path.exists(text_path):
        try:
            with open(text_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
    return None

@app.route('/select_language', methods=['POST'])
def select_language():
    global selected_language
    selected_language = request.form['language_id']
    logger.info(f"Language set to: {selected_language}")
    return jsonify({'status': 'success'})

@app.route('/get_transcription', methods=['GET'])
def get_transcription():
    logger.debug("Getting transcription")
    return jsonify({'transcription': latest_transcription})

@app.route('/get_text_content', methods=['GET'])
def get_text_content():
    logger.debug("Getting text content")
    return jsonify({'data1': text_content})

@app.route('/get_audio_path', methods=['POST'])
def get_audio_path():
    sentence = request.form['sentence']
    language = request.form['language']
    audio_filename = f"{sentence.replace(' ', '_')}/{languages[language]}.mp3"
    audio_path = os.path.join(audio_directory, audio_filename)

    logger.debug(f"Requested audio path: {audio_path}")
    if os.path.exists(audio_path):
        return jsonify({'audioPath': url_for('serve_audio', filename=audio_filename, _external=True)})
    return jsonify({'audioPath': None})

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    logger.debug(f"Serving audio file: {filename}")
    return send_from_directory(audio_directory, filename, mimetype='audio/mpeg')

if __name__ == '__main__':
    # Create directories if they don't exist
    os.makedirs(audio_directory, exist_ok=True)
    os.makedirs(sentences_directory, exist_ok=True)

    logger.info("Starting server on http://localhost:5000")
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,  # Set to False for production
        use_reloader=False,
        log_output=True  # Added for better debugging
    )