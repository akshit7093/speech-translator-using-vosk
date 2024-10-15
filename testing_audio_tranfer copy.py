from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import base64
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Required for session handling
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=10)

# Keep track of connected clients
connected_clients = set()

@app.route('/')
def index():
    return render_template('testing.html')

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    connected_clients.add(client_id)
    logger.info(f'Client connected. ID: {client_id}. Total clients: {len(connected_clients)}')

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    connected_clients.discard(client_id)
    logger.info(f'Client disconnected. ID: {client_id}. Total clients: {len(connected_clients)}')

@socketio.on('audio')
def handle_audio(data):
    try:
        client_id = request.sid
        logger.debug(f'Received audio from client {client_id}')
        # Broadcast the audio data to all other clients
        emit('audio', data, broadcast=True, include_self=False)
    except Exception as e:
        logger.error(f'Error handling audio: {str(e)}')

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f'SocketIO error: {str(e)}')

if __name__ == '__main__':
    try:
        logger.info("Starting the server...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f'Failed to start server: {str(e)}')