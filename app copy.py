import os
import json
import re
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for, session, redirect

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DATA_DIR = os.environ.get('LOCAL_DATA', os.path.join(BASE_DIR, 'local_data'))
SENTENCES_DIR = os.path.join(LOCAL_DATA_DIR, 'sentences')
LANGUAGES_FILE = os.path.join(LOCAL_DATA_DIR, 'languages.json')
INDEX_PATH_FILE = os.path.join(LOCAL_DATA_DIR, 'index_path.json')

# Reference language configuration - MUST MATCH YOUR JSON KEY
# Since your JSON uses "English" as the key, we need to use that
REFERENCE_LANGUAGE = 'English'  # Must match the key in your languages.json
REFERENCE_LANGUAGE_NAME = 'English'

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # Change this in production!

def is_valid_path_component(component):
    """Check if a path component is valid (only letters, numbers, underscores, and hyphens)"""
    return bool(re.match(r'^[a-zA-Z0-9_\-]+$', component))

def load_languages():
    """Load languages from languages.json"""
    if not os.path.exists(LANGUAGES_FILE):
        logger.error(f"Languages file not found at {LANGUAGES_FILE}")
        return {}
    
    try:
        with open(LANGUAGES_FILE, 'r', encoding='utf-8') as f:
            languages = json.load(f)
        logger.debug(f"Loaded {len(languages)} languages: {languages}")
        return languages
    except Exception as e:
        logger.error(f"Error loading languages: {e}")
        return {}

def load_sentences():
    """Load sentences from index_path.json"""
    if not os.path.exists(INDEX_PATH_FILE):
        logger.error(f"Index file not found at {INDEX_PATH_FILE}")
        return []
    try:
        with open(INDEX_PATH_FILE, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
            sentences = index_data.get('sentences', [])
        logger.debug(f"Loaded {len(sentences)} sentences: {sentences}")
        return sentences
    except Exception as e:
        logger.error(f"Error loading sentences: {e}")
        return []

@app.route('/')
def index():
    logger.debug("Serving index page")
    languages = load_languages()
    sentences = load_sentences()
    logger.debug(f"Passing to template: languages={languages}, sentences={sentences}")
    return render_template('indexx.html', 
                          languages=languages, 
                          sentences=sentences,
                          reference_language=REFERENCE_LANGUAGE,
                          reference_language_name=REFERENCE_LANGUAGE_NAME)

@app.route('/api/health')
def health_check():
    logger.debug("Health check endpoint called")
    return jsonify({"status": "ok"})

@app.route('/api/languages')
def get_languages():
    """Return available languages"""
    languages = load_languages()
    logger.debug(f"API/languages returning: {languages}")
    
    # Return the full languages object
    return jsonify({'languages': languages})

@app.route('/api/sentences/<language>')
def get_sentences_for_language(language):
    """Return sentences available for a specific language"""
    # Validate language parameter
    if not is_valid_path_component(language):
        return jsonify({'error': 'Invalid language format'}), 400
    
    languages = load_languages()
    
    if language not in languages:
        return jsonify({'error': 'Language not found'}), 404
    
    sentences = load_sentences()
    
    # Filter sentences that have text for the selected language
    available_sentences = []
    for sentence in sentences:
        text_path = os.path.join(SENTENCES_DIR, sentence, 'text', f"{language}.txt")
        if os.path.exists(text_path):
            # Read the sentence text in the selected language
            try:
                with open(text_path, 'r', encoding='utf-8') as f:
                    sentence_text = f.read().strip()
                available_sentences.append({
                    'id': sentence,
                    'text': sentence_text
                })
            except Exception as e:
                logger.error(f"Error reading sentence text for {sentence} in {language}: {e}")
    
    logger.debug(f"API/sentences/{language} returning: {available_sentences}")
    return jsonify({'sentences': available_sentences})

@app.route('/api/content/<sentence>/<language>')
def get_content(sentence, language):
    """Return text and audio paths for a sentence in a language"""
    # Validate parameters
    if not is_valid_path_component(sentence) or not is_valid_path_component(language):
        return jsonify({'error': 'Invalid path format'}), 400
    
    text_path = os.path.join(SENTENCES_DIR, sentence, 'text', f"{language}.txt")
    audio_path = os.path.join(SENTENCES_DIR, sentence, 'audio', f"{language}.mp3")
    
    text_content = None
    if os.path.exists(text_path):
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
    
    audio_url = None
    if os.path.exists(audio_path):
        audio_url = url_for('serve_audio', 
                           sentence=sentence, 
                           language=language, 
                           _external=True)
    
    return jsonify({
        'text': text_content,
        'audio_url': audio_url
    })

@app.route('/audio/<sentence>/<language>')
def serve_audio(sentence, language):
    """Serve audio file for a sentence in a language"""
    # Validate parameters
    if not is_valid_path_component(sentence) or not is_valid_path_component(language):
        return jsonify({'error': 'Invalid path format'}), 400
    
    audio_path = os.path.join(SENTENCES_DIR, sentence, 'audio', f"{language}.mp3")
    audio_dir = os.path.dirname(audio_path)
    audio_filename = os.path.basename(audio_path)
    
    if not os.path.exists(audio_path):
        logger.warning(f"Audio file not found: {audio_path}")
        return jsonify({'error': 'Audio file not found'}), 404
    
    logger.debug(f"Serving audio file: {audio_filename} from {audio_dir}")
    return send_from_directory(audio_dir, audio_filename, mimetype='audio/mpeg')

@app.route('/admin')
def admin_index():
    """Redirect to login or dashboard"""
    if not session.get('is_admin'):
        return redirect(url_for('admin.login'))
    return redirect(url_for('admin.dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page"""
    # Check if it's an API request
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    
    # For regular pages, check if user is admin and redirect appropriately
    if request.path.startswith('/admin') and not session.get('is_admin'):
        return redirect(url_for('admin.login'))
    
    return render_template('404.html'), 404

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    os.makedirs(SENTENCES_DIR, exist_ok=True)
    
    # Initialize JSON files if they don't exist
    if not os.path.exists(LANGUAGES_FILE):
        with open(LANGUAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2)
    
    if not os.path.exists(INDEX_PATH_FILE):
        with open(INDEX_PATH_FILE, 'w', encoding='utf-8') as f:
            json.dump({"sentences": []}, f, indent=2)
    
    # Import admin module after paths are set up
    from admin import admin
    
    # Register admin blueprint
    admin_bp = admin.init_admin(LOCAL_DATA_DIR)
    app.register_blueprint(admin_bp)
    
    logger.info("Starting server on http://0.0.0.0:5000")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )