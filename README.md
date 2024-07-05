

# Speech Recognition and Translation Web Application

This Flask-based web application performs real-time speech recognition and translates predefined sentences into multiple languages.

## Features

- Real-time speech recognition using Vosk
- Support for multiple languages (Apatani, Bhutanese, French, Hindi, Monpa)
- Audio playback of translated sentences
- Display of translated text

## Prerequisites

- Python 3.7+
- pip
- portaudio (for PyAudio)

## Installation

1. Clone the repository:
   ```
   git clone [https://github.com/yourusername/speech-recognition-translation-app.git](https://github.com/akshit7093/lang_convert.git)
   cd speech-recognition-translation-app
   ```

2. Set up a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Download the Vosk model:
   - Get the small English Vosk model from [Vosk's model repository](https://alphacephei.com/vosk/models)
   - Extract it into the project directory and ensure it's named `vosk-model-small-en-us-0.15`

## Project Structure

```
final_proj/
├── audio/                 # Audio files for each sentence and language
├── sentences/             # Text files for each sentence and language
├── templates/             # HTML templates
├── vosk-model-small-en-us-0.15/  # Vosk model directory
├── speech_app.py          # Main Flask application
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Setup Guide

1. Prepare audio and sentence files:
   - In the `audio` directory, create subdirectories for each predefined sentence.
   - Place corresponding .mp3 audio files for each language in these subdirectories.
   - In the `sentences` directory, create subdirectories for each predefined sentence.
   - Place text files for each language in these subdirectories.

2. Configure the application:
   - Open `speech_app.py`.
   - Verify paths to the model, audio, and sentences directories.
   - Ensure the list of predefined sentences and supported languages is up to date.

3. Set up the frontend:
   - Ensure the `templates` directory contains your HTML file (e.g., `indexx.html`).
   - Verify that any static files (CSS, JavaScript) are in the correct locations.

## Usage

1. Run the Flask application:
   ```
   python speech_app.py
   ```

2. Open a web browser and navigate to `http://127.0.0.1:5000/`

3. Select an input device and language from the dropdown menus

4. Click "Start" to begin speech recognition

5. Speak one of the predefined sentences

6. The application will display the recognized text and play the corresponding audio in the selected language

## Supported Languages

- Apatani
- Bhutanese
- French
- Hindi
- Monpa

## Predefined Sentences

- "hello"
- "goodbye"
- "how are you"
- "good wishes"
- "i will drink water"
- "i will have food"
- "my name is"
- "thank you"
- "will you drink water"
- "will you have food"

## Troubleshooting

- PyAudio installation issues:
  - macOS: `brew install portaudio`
  - Linux: `sudo apt-get install portaudio19-dev`
  - Windows: You may need to manually install a compatible PyAudio wheel file.

- Vosk model loading failure: Check the model path and ensure all files are present.

- Audio playback issues: Verify audio file format and location.

- Unrecognized sentences: Review the `predefined_sentences` list in the Python script.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.



## Acknowledgments

- [Vosk](https://github.com/alphacep/vosk-api) for the speech recognition model
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) for audio input handling
