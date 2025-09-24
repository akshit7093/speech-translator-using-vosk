import os
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Set up logging
logger = logging.getLogger(__name__)

# Configuration - DEFAULT PASSWORD IS 'admin123'
# In production, set ADMIN_PASSWORD environment variable
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# Reference language configuration - MUST MATCH YOUR JSON KEY
REFERENCE_LANGUAGE = 'English'  # Must match the key in your languages.json

# Paths - will be set when initialized
LOCAL_DATA_DIR = None
SENTENCES_DIR = None
LANGUAGES_FILE = None
INDEX_PATH_FILE = None

# Get the directory of the current file (admin.py)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Calculate the absolute path to templates/admin
TEMPLATES_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', 'templates', 'admin'))

admin_bp = Blueprint('admin', __name__, template_folder=TEMPLATES_DIR)

def init_admin(local_data_dir):
    """Initialize admin module with proper paths"""
    global LOCAL_DATA_DIR, SENTENCES_DIR, LANGUAGES_FILE, INDEX_PATH_FILE
    
    LOCAL_DATA_DIR = local_data_dir
    SENTENCES_DIR = os.path.join(LOCAL_DATA_DIR, 'sentences')
    LANGUAGES_FILE = os.path.join(LOCAL_DATA_DIR, 'languages.json')
    INDEX_PATH_FILE = os.path.join(LOCAL_DATA_DIR, 'index_path.json')
    
    # Ensure directories exist
    os.makedirs(SENTENCES_DIR, exist_ok=True)
    
    # Initialize JSON files if they don't exist
    if not os.path.exists(LANGUAGES_FILE):
        with open(LANGUAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2)
    
    if not os.path.exists(INDEX_PATH_FILE):
        with open(INDEX_PATH_FILE, 'w', encoding='utf-8') as f:
            json.dump({"sentences": []}, f, indent=2)
    
    logger.info(f"Admin module initialized with local_data directory: {LOCAL_DATA_DIR}")
    return admin_bp

def load_languages():
    """Load languages from languages.json"""
    try:
        with open(LANGUAGES_FILE, 'r', encoding='utf-8') as f:
            languages = json.load(f)
        return languages
    except Exception as e:
        logger.error(f"Error loading languages: {e}")
        return {}

def save_languages(languages):
    """Save languages to languages.json"""
    try:
        with open(LANGUAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(languages, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving languages: {e}")
        return False

def load_sentences():
    """Load sentences from index_path.json"""
    try:
        with open(INDEX_PATH_FILE, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
            return index_data.get('sentences', [])
    except Exception as e:
        logger.error(f"Error loading sentences: {e}")
        return []

def save_sentences(sentences):
    """Save sentences to index_path.json"""
    try:
        with open(INDEX_PATH_FILE, 'w', encoding='utf-8') as f:
            json.dump({"sentences": sentences}, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving sentences: {e}")
        return False

def get_sentence_path(sentence_id):
    """Get the path for a sentence directory"""
    return os.path.join(SENTENCES_DIR, sentence_id)

def get_language_files(sentence_id, language):
    """Get paths for text and audio files for a sentence and language"""
    sentence_path = get_sentence_path(sentence_id)
    text_path = os.path.join(sentence_path, 'text', f"{language}.txt")
    audio_path = os.path.join(sentence_path, 'audio', f"{language}.mp3")
    
    return {
        'text_path': text_path,
        'audio_path': audio_path,
        'text_dir': os.path.dirname(text_path),
        'audio_dir': os.path.dirname(audio_path)
    }

def create_sentence_directories(sentence_id):
    """Create necessary directories for a new sentence"""
    sentence_path = get_sentence_path(sentence_id)
    text_dir = os.path.join(sentence_path, 'text')
    audio_dir = os.path.join(sentence_path, 'audio')
    
    os.makedirs(text_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    
    return {
        'sentence_path': sentence_path,
        'text_dir': text_dir,
        'audio_dir': audio_dir
    }

def delete_sentence_directories(sentence_id):
    """Delete directories for a sentence"""
    sentence_path = get_sentence_path(sentence_id)
    
    # Remove all files first
    for root, _, files in os.walk(sentence_path, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
    
    # Remove directories
    if os.path.exists(sentence_path):
        os.rmdir(os.path.join(sentence_path, 'text'))
        os.rmdir(os.path.join(sentence_path, 'audio'))
        os.rmdir(sentence_path)
    
    return not os.path.exists(sentence_path)

def create_language_files(language, sentence_id, text_content, audio_file=None):
    """Create text and audio files for a language and sentence"""
    paths = get_language_files(sentence_id, language)
    
    # Create directories if they don't exist
    os.makedirs(paths['text_dir'], exist_ok=True)
    os.makedirs(paths['audio_dir'], exist_ok=True)
    
    # Save text file
    with open(paths['text_path'], 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    # Save audio file if provided
    if audio_file:
        audio_file.save(paths['audio_path'])
    
    return True

def get_sentence_data(sentence_id):
    """Get all data for a sentence"""
    sentences = load_sentences()
    if sentence_id not in sentences:
        return None
    
    languages = load_languages()
    sentence_data = {
        'id': sentence_id,
        'translations': {}
    }
    
    for lang_code in languages.keys():
        paths = get_language_files(sentence_id, lang_code)
        
        # Get text content
        text_content = ""
        if os.path.exists(paths['text_path']):
            try:
                with open(paths['text_path'], 'r', encoding='utf-8') as f:
                    text_content = f.read()
            except Exception as e:
                logger.error(f"Error reading text file for {sentence_id} in {lang_code}: {e}")
        
        # Check if audio exists
        audio_exists = os.path.exists(paths['audio_path'])
        
        sentence_data['translations'][lang_code] = {
            'text': text_content,
            'has_audio': audio_exists
        }
    
    return sentence_data

def get_all_sentence_data():
    """Get data for all sentences"""
    sentences = load_sentences()
    all_data = []
    
    for sentence_id in sentences:
        sentence_data = get_sentence_data(sentence_id)
        if sentence_data:
            all_data.append(sentence_data)
    
    return all_data

def validate_language_files(language):
    """Validate that all sentences have files for this language"""
    sentences = load_sentences()
    languages = load_languages()
    
    missing_sentences = []
    
    for sentence_id in sentences:
        paths = get_language_files(sentence_id, language)
        
        if not os.path.exists(paths['text_path']):
            missing_sentences.append(sentence_id)
    
    return len(missing_sentences) == 0, missing_sentences

# Admin Routes
@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['is_admin'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid password', 'error')
    
    return render_template('login.html')

@admin_bp.route('/admin/logout')
def logout():
    """Admin logout"""
    session.pop('is_admin', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@admin_bp.route('/admin/dashboard')
def dashboard():
    """Admin dashboard"""
    if not session.get('is_admin'):
        return redirect(url_for('admin.login'))
    
    languages = load_languages()
    sentences = load_sentences()
    
    return render_template('dashboard.html', 
                          languages=languages, 
                          sentences=sentences,
                          reference_language=REFERENCE_LANGUAGE)

# API Endpoints for Admin Panel
@admin_bp.route('/admin/api/languages', methods=['GET'])
def api_get_languages():
    """Get all languages"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    languages = load_languages()
    return jsonify({
        'languages': languages,
        'reference_language': REFERENCE_LANGUAGE
    })

@admin_bp.route('/admin/api/languages', methods=['POST'])
def api_add_language():
    """Add a new language"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    language_code = request.form.get('language_code', '').strip()
    language_name = request.form.get('language_name', '').strip()
    
    if not language_code or not language_name:
        return jsonify({'error': 'Language code and name are required'}), 400
    
    languages = load_languages()
    
    if language_code in languages:
        return jsonify({'error': 'Language code already exists'}), 400
    
    # Add to languages.json
    languages[language_code] = language_name
    if not save_languages(languages):
        return jsonify({'error': 'Failed to save language'}), 500
    
    # Check if all sentences have this language
    sentences = load_sentences()
    missing_sentences = []
    
    for sentence_id in sentences:
        paths = get_language_files(sentence_id, language_code)
        
        # Create empty text file if it doesn't exist
        if not os.path.exists(paths['text_path']):
            missing_sentences.append(sentence_id)
            os.makedirs(paths['text_dir'], exist_ok=True)
            with open(paths['text_path'], 'w', encoding='utf-8') as f:
                f.write("")
        
        # Create empty audio directory if it doesn't exist
        os.makedirs(paths['audio_dir'], exist_ok=True)
    
    return jsonify({
        'success': True,
        'language': {language_code: language_name},
        'missing_sentences': missing_sentences
    })

@admin_bp.route('/admin/api/languages/<language_code>', methods=['PUT'])
def api_update_language(language_code):
    """Update a language"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    new_name = request.form.get('language_name', '').strip()
    
    if not new_name:
        return jsonify({'error': 'Language name is required'}), 400
    
    languages = load_languages()
    
    if language_code not in languages:
        return jsonify({'error': 'Language not found'}), 404
    
    # Update in languages.json
    languages[language_code] = new_name
    if not save_languages(languages):
        return jsonify({'error': 'Failed to save language'}), 500
    
    return jsonify({'success': True, 'language': {language_code: new_name}})

@admin_bp.route('/admin/api/languages/<language_code>', methods=['DELETE'])
def api_delete_language(language_code):
    """Delete a language"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    languages = load_languages()
    
    if language_code not in languages:
        return jsonify({'error': 'Language not found'}), 404
    
    # Don't allow deleting the reference language
    if language_code == REFERENCE_LANGUAGE:
        return jsonify({'error': 'Cannot delete the reference language'}), 400
    
    # Remove from languages.json
    del languages[language_code]
    if not save_languages(languages):
        return jsonify({'error': 'Failed to save language'}), 500
    
    # Remove language files from all sentences
    sentences = load_sentences()
    for sentence_id in sentences:
        paths = get_language_files(sentence_id, language_code)
        
        # Remove text file if it exists
        if os.path.exists(paths['text_path']):
            os.remove(paths['text_path'])
        
        # Remove audio file if it exists
        if os.path.exists(paths['audio_path']):
            os.remove(paths['audio_path'])
    
    return jsonify({'success': True})

@admin_bp.route('/admin/api/sentences', methods=['GET'])
def api_get_sentences():
    """Get all sentences"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    sentences = load_sentences()
    return jsonify({'sentences': sentences})

@admin_bp.route('/admin/api/sentences', methods=['POST'])
def api_add_sentence():
    """Add a new sentence"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    sentence_id = request.form.get('sentence_id', '').strip()
    
    if not sentence_id:
        return jsonify({'error': 'Sentence ID is required'}), 400
    
    # Validate sentence ID format (only letters, numbers, underscores)
    if not sentence_id.replace('_', '').isalnum():
        return jsonify({'error': 'Invalid sentence ID format'}), 400
    
    sentences = load_sentences()
    
    if sentence_id in sentences:
        return jsonify({'error': 'Sentence ID already exists'}), 400
    
    # Create directories for the new sentence
    dirs = create_sentence_directories(sentence_id)
    
    # Add to index_path.json
    sentences.append(sentence_id)
    if not save_sentences(sentences):
        # Roll back directory creation if JSON save fails
        if os.path.exists(dirs['sentence_path']):
            delete_sentence_directories(sentence_id)
        return jsonify({'error': 'Failed to save sentence'}), 500
    
    # Add empty files for all existing languages
    languages = load_languages()
    for lang_code in languages.keys():
        create_language_files(lang_code, sentence_id, "")
    
    return jsonify({'success': True, 'sentence_id': sentence_id})

@admin_bp.route('/admin/api/sentences/<sentence_id>', methods=['PUT'])
def api_update_sentence(sentence_id):
    """Update a sentence (only for metadata, not the ID itself)"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # In our system, sentence_id is the identifier and shouldn't be changed
    # This endpoint is for updating the content for each language
    languages = load_languages()
    
    # Process text updates
    for lang_code in languages.keys():
        text_content = request.form.get(f'text_{lang_code}', '')
        create_language_files(lang_code, sentence_id, text_content)
    
    # Process audio updates
    for lang_code in languages.keys():
        if f'audio_{lang_code}' in request.files:
            audio_file = request.files[f'audio_{lang_code}']
            if audio_file.filename:
                # Verify it's an audio file
                if audio_file.filename.lower().endswith(('.mp3', '.wav')):
                    create_language_files(lang_code, sentence_id, 
                                         get_sentence_data(sentence_id)['translations'][lang_code]['text'], 
                                         audio_file)
    
    return jsonify({'success': True, 'sentence_id': sentence_id})

@admin_bp.route('/admin/api/sentences/<sentence_id>', methods=['DELETE'])
def api_delete_sentence(sentence_id):
    """Delete a sentence"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    sentences = load_sentences()
    
    if sentence_id not in sentences:
        return jsonify({'error': 'Sentence not found'}), 404
    
    # Remove from index_path.json
    sentences.remove(sentence_id)
    if not save_sentences(sentences):
        return jsonify({'error': 'Failed to save sentence list'}), 500
    
    # Remove sentence directories
    if not delete_sentence_directories(sentence_id):
        # Try to recover by adding back to JSON
        sentences.append(sentence_id)
        save_sentences(sentences)
        return jsonify({'error': 'Failed to delete sentence directories'}), 500
    
    return jsonify({'success': True})

@admin_bp.route('/admin/api/sentence/<sentence_id>', methods=['GET'])
def api_get_sentence(sentence_id):
    """Get data for a specific sentence"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    sentence_data = get_sentence_data(sentence_id)
    
    if not sentence_data:
        return jsonify({'error': 'Sentence not found'}), 404
    
    return jsonify(sentence_data)