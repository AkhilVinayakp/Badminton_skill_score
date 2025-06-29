from flask import Flask
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Thread-safe storage for the latest frame
latest_frame = None
frame_lock = threading.Lock()

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('upload_frame')
def handle_upload_frame(data):
    global latest_frame
    with frame_lock:
        latest_frame = data['frame']
    emit('frame_uploaded', {'status': 'success'})

@socketio.on('request_frame')
def handle_request_frame():
    with frame_lock:
        if latest_frame is None:
            emit('frame', {'status': 'error', 'message': 'No frame available'})
        else:
            emit('frame', {'status': 'success', 'frame': latest_frame})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=9000, debug=True) 