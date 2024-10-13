from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
import uuid
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=10)

# Store active rooms and users
active_rooms = {}

@app.route('/')
def index():
    return render_template('testing.html')

@app.route('/<room_id>')
def join_specific_room(room_id):
    return render_template('join.html', room_id=room_id)

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    logger.info(f'Client connected: {client_id}')

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    logger.info(f'Client disconnected: {client_id}')
    
    # Remove user from any rooms they were in
    for room_id in active_rooms:
        if client_id in active_rooms[room_id]:
            active_rooms[room_id].remove(client_id)
            emit('user_left', {'client_id': client_id}, room=room_id)

@socketio.on('join')
def on_join(data):
    client_id = request.sid
    room_id = data.get('room_id')
    
    if not room_id:
        room_id = str(uuid.uuid4())
    
    join_room(room_id)
    
    if room_id not in active_rooms:
        active_rooms[room_id] = set()
    active_rooms[room_id].add(client_id)
    
    logger.info(f'Client {client_id} joined room {room_id}')
    emit('room_joined', {'room_id': room_id, 'client_id': client_id}, room=room_id)


@socketio.on('leave')
def on_leave(data):
    client_id = request.sid
    room_id = data['room_id']
    
    if room_id in active_rooms and client_id in active_rooms[room_id]:
        leave_room(room_id)
        active_rooms[room_id].remove(client_id)
        emit('user_left', {'client_id': client_id}, room=room_id)
        logger.info(f'Client {client_id} left room {room_id}')

@socketio.on('voice')
def handle_voice(data):
    room_id = data['room']
    audio_data = data['audio']
    emit('voice', {'audio': audio_data, 'client_id': request.sid}, room=room_id, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)