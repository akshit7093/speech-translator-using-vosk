from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_socketio import SocketIO, emit
from vosk import Model, KaldiRecognizer
import numpy as np
import json
import os
import logging
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["https://16.170.43.190", "http://localhost:*"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle proxy headers for HTTPS
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Initialize Socket.IO with enhanced configuration
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=300,
    ping_interval=60,
    engineio_logger=True,
    logger=True,
    max_http_buffer_size=100 * 1024 * 1024,  # 100MB
    transports=['websocket', 'polling']
)

# Path configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
audio_directory = os.path.join(BASE_DIR, "audio")
sentences_directory = os.path.join(BASE_DIR, "sentences")

# Validate directories
for directory in [audio_directory, sentences_directory]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

# Load Vosk model
model_path = os.path.join(BASE_DIR, "vosk-model-small-en-us-0.15")
if not os.path.exists(model_path):
    logger.error(f"Vosk model not found at {model_path}")
    raise RuntimeError(f"Vosk model not found at {model_path}")

model = Model(model_path)

# Predefined sentences and languages
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

# Global state
selected_language = None
latest_transcription = ""
text_content = ""
audio_buffer = bytearray()
MAX_BUFFER_SIZE = 48000  # 3 seconds of audio

# Initialize recognizer with predefined sentences
recognizer = KaldiRecognizer(model, 16000, '["[unk]", ' +
                           ','.join(f'"{word}"' for word in predefined_sentences) + ']')

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(502)
def bad_gateway(error):
    return jsonify({"error": "Bad gateway"}), 502

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    emit('connection_response', {'data': 'Connected successfully'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('audio_stream')
def handle_audio_stream(data):
    global audio_buffer, recognizer
    
    try:
        if isinstance(data, memoryview):
            chunk = data.tobytes()
        else:
            chunk = data

        # Validate audio chunk
        if len(chunk) % 2 != 0:  # 16-bit audio should be even length
            chunk = chunk[:-1]
            
        audio_buffer.extend(chunk)

        # Process in chunks of 8000 samples (0.5s at 16kHz)
        while len(audio_buffer) >= 8000:
            audio_chunk = bytes(audio_buffer[:8000])
            audio_buffer = audio_buffer[8000:]

            if recognizer.AcceptWaveform(audio_chunk):
                result = json.loads(recognizer.Result())
                process_recognition(result)

        # Prevent buffer overflow
        if len(audio_buffer) > MAX_BUFFER_SIZE:
            audio_buffer = bytearray()
            logger.warning("Audio buffer overflow - resetting buffer")

    except Exception as e:
        logger.error(f"Audio processing error: {str(e)}")
        audio_buffer = bytearray()
        recognizer.Reset()

def process_recognition(result):
    global latest_transcription, text_content
    
    transcription = result.get('text', '').lower()
    logger.info(f"Processing recognition: {transcription}")

    # Match against predefined sentences
    matched_sentence = next(
        (sentence for sentence in predefined_sentences
         if sentence in transcription),
        None
    )

    # Emit transcription result
    socketio.emit('transcription', {
        'transcription': transcription,
        'matched_sentence': matched_sentence
    })

    # Update global state if match found
    if matched_sentence:
        latest_transcription = transcription
        text_content = display_text(matched_sentence)
        logger.info(f"Recognized: {matched_sentence} (Language: {selected_language})")

def display_text(sentence):
    if not selected_language:
        return "No language selected"
        
    text_filename = f"{sentence.replace(' ', '_')}/{languages[selected_language]}.txt"
    text_path = os.path.join(sentences_directory, text_filename)
    
    if os.path.exists(text_path):
        try:
            with open(text_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading text file {text_path}: {str(e)}")
            return f"Error loading content for {sentence}"
    return f"Content not found for {sentence}"

# Flask routes
@app.route('/')
def index():
    return render_template('index.html', languages=languages)

@app.route('/select_language', methods=['POST'])
def select_language():
    global selected_language
    try:
        selected_language = request.form['language_id']
        if selected_language not in languages:
            raise ValueError("Invalid language selected")
            
        logger.info(f"Language selected: {selected_language}")
        return jsonify({'status': 'success', 'language': selected_language})
    except Exception as e:
        logger.error(f"Language selection error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/get_transcription', methods=['GET'])
def get_transcription():
    return jsonify({'transcription': latest_transcription})

@app.route('/get_text_content', methods=['GET'])
def get_text_content():
    return jsonify({'data1': text_content})

@app.route('/get_audio_path', methods=['POST'])
def get_audio_path():
    try:
        sentence = request.form['sentence']
        language = request.form['language']
        
        if language not in languages:
            raise ValueError("Invalid language specified")
            
        audio_filename = f"{sentence.replace(' ', '_')}/{languages[language]}.mp3"
        audio_path = os.path.join(audio_directory, audio_filename)

        if os.path.exists(audio_path):
            return jsonify({
                'audioPath': url_for('serve_audio', filename=audio_filename, _external=True)
            })
        return jsonify({'audioPath': None, 'message': 'Audio file not found'})
    except Exception as e:
        logger.error(f"Audio path error: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    try:
        return send_from_directory(audio_directory, filename)
    except Exception as e:
        logger.error(f"Audio serve error: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "ok",
        "environment": "AWS",
        "language": selected_language,
        "connections": len(socketio.server.manager.get_pids())
    })

if __name__ == '__main__':
    # Production configuration
    socketio.run(app,
                host='0.0.0.0',
                port=5000,
                debug=False,
                use_reloader=False,
                allow_unsafe_werkzeug=False,
                log_output=True)