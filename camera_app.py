import sys
import cv2
import requests
import threading
import socketio
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

class CameraApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Stream Application")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create video preview label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.video_label)

        # Create stream button
        self.stream_button = QPushButton("Start Streaming")
        self.stream_button.setFixedHeight(50)
        self.stream_button.clicked.connect(self.toggle_streaming)
        layout.addWidget(self.stream_button)

        # Initialize camera
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Initialize timer for video updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_streaming = False

        # Thread for sending frames
        self.send_thread = None
        self.stop_thread = False

        # Initialize SocketIO client
        self.sio = socketio.Client()
        self.sio.connect('http://localhost:9000')

    def toggle_streaming(self):
        if not self.is_streaming:
            self.stream_button.setText("Stop Streaming")
            self.timer.start(30)  # Update every 30ms
            self.is_streaming = True
            self.stop_thread = False
            self.send_thread = threading.Thread(target=self.send_frames)
            self.send_thread.start()
        else:
            self.stream_button.setText("Start Streaming")
            self.timer.stop()
            self.is_streaming = False
            self.stop_thread = True
            if self.send_thread:
                self.send_thread.join()

    def send_frames(self):
        while not self.stop_thread:
            ret, frame = self.camera.read()
            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                self.sio.emit('upload_frame', {'frame': buffer.tobytes()})

    def update_frame(self):
        ret, frame = self.camera.read()
        if ret:
            # Convert frame to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            # Convert to QImage
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Scale image to fit label while maintaining aspect ratio
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.stop_thread = True
        if self.send_thread:
            self.send_thread.join()
        self.camera.release()
        self.sio.disconnect()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_()) 