from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import threading
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "vosk-model-small-en-us-0.15")

# Then in your initialize_audio function:
model = Model(model_path=MODEL_PATH)
app = Flask(__name__)

# Initialize PyAudio
p = pyaudio.PyAudio()

# Global variables
stream = None
recognizer = None
latest_transcription = ""
selected_device_index = None
selected_language = None
text_content = ""
transcription_thread = None

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

def list_input_devices():
    info = []
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:  # if it's an input device
            info.append(f"Index {i}: {device_info['name']}")
    return info

def initialize_audio():
    global stream, recognizer, selected_device_index

    # Close existing stream if it's open
    if stream:
        stream.stop_stream()
        stream.close()

    # Initialize Vosk model
    # model = Model(model_path="vosk-model-small-en-us-0.15")
    recognizer = KaldiRecognizer(model, 16000)
    
    # Initialize audio stream   
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, 
                    input=True, input_device_index=selected_device_index,
                    frames_per_buffer=8000)
    stream.start_stream()

def transcribe_audio():
    global latest_transcription, text_content
    while True:
        if stream and not stream.is_stopped():
            data = stream.read(4000, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                latest_transcription = result['text']
                
                # Check if the latest transcription matches a predefined sentence
                matched_sentence = None
                for sentence in predefined_sentences:
                    if sentence in latest_transcription.lower():
                        matched_sentence = sentence
                        break
                        
                if matched_sentence:
                    text_content = display_text(matched_sentence)
                    if text_content:
                        print(f"Text content for '{matched_sentence}': {text_content}")

def display_text(sentence):
    # Construct the path to the text file based on the matched sentence and selected language
    text_path = os.path.join(sentences_directory, sentence.replace(" ", "_"), f"{languages[selected_language]}.txt")
        
    # Read and return the contents of the text file
    if os.path.exists(text_path):
        with open(text_path, 'r', encoding='utf-8') as file:
            text_content = file.read()
            return text_content
    else:
        print(f"Text file '{text_path}' not found.")
        return None

@app.route('/')
def index():
    devices = list_input_devices()
    return render_template('indexx.html', devices=devices, languages=languages)

@app.route('/select_device', methods=['POST'])
def select_device():
    global selected_device_index, selected_language, latest_transcription, text_content, transcription_thread

    new_device_index = int(request.form['device_index'])
    new_language = request.form['language_id']

    # Only reinitialize if the device or language has changed
    if new_device_index != selected_device_index or new_language != selected_language:
        selected_device_index = new_device_index
        selected_language = new_language
        initialize_audio()
        
        # Reset variables
        latest_transcription = ""
        text_content = ""
        
        # Stop existing transcription thread if it's running
        if transcription_thread and transcription_thread.is_alive():
            # We need a way to stop the thread gracefully here
            # For now, we'll just start a new one, but this isn't ideal
            pass

        # Start the transcription thread
        transcription_thread = threading.Thread(target=transcribe_audio)
        transcription_thread.daemon = True
        transcription_thread.start()
    
    return jsonify({'status': 'success'})

@app.route('/get_transcription', methods=['GET'])
def get_transcription():
    global latest_transcription
    return jsonify({'transcription': latest_transcription})

@app.route('/get_text_content', methods=['GET'])
def get_text_content():
    global text_content
    return jsonify({'data1': text_content})

@app.route('/get_audio_path', methods=['POST'])
def get_audio_path():
    sentence = request.form['sentence']
    language = request.form['language']

    # Construct the path to the audio file based on the matched sentence and selected language
    audio_filename = f"{sentence.replace(' ', '_')}/{languages[language]}.mp3"
    audio_path = os.path.join(audio_directory, audio_filename)

    # Check if the file exists and return its URL
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