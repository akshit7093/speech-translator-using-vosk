from flask import Flask, render_template, request, send_file
from gtts import gTTS
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_to_audio():
    sentence = request.form['sentence']
    language = request.form['language']
    text_file = f'sentences/{sentence}/{language}.txt'
    
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    return text

import time

@app.route('/synthesize', methods=['POST'])
def synthesize_audio():
    sentence = request.form['sentence']
    language = request.form['language']
    text_file = f'sentences/{sentence}/{language}.txt'
    audio_dir = f'audio/{sentence}/'

    # Read the text from the file
    try:
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        return {'error': 'File not found'}

    # Define the audio file path based on language with a timestamp
    timestamp = int(time.time())
    audio_file = f'{audio_dir}{language}_{timestamp}.mp3'

    # Synthesize audio using gTTS
    try:
        if language == 'ap':
            # Apatani language code
            language_code = 'en'  # Use English as a fallback language
            
        else:
            language_code = language  # Use the specified language code

        # Create audio directory if not exists
        os.makedirs(audio_dir, exist_ok=True)

        # Generate audio file with gTTS
        # tts = gTTS(text=text, lang=language_code)
        tts = gTTS(text=text, lang='en')
        tts.save(audio_file)
    except ValueError as e:
        # If synthesis fails, return an error message
        return {'error': str(e)}

    # Return the newly created audio file as an attachment
    return send_file(audio_file, as_attachment=True)

    


if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')
