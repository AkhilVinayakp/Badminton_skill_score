import sys
import socketio
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QSizePolicy, QLineEdit, QComboBox, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QImage, QPixmap
import requests
import os
import random
from datetime import datetime

class VideoLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aspect_ratio = 13.4 / 6.1
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(1340, 610)
        self.setStyleSheet("border: 2px solid white; background-color: black;")

    def sizeHint(self):
        return QSize(1920, 874)

    def resizeEvent(self, event):
        w = event.size().width()
        h = int(w / self.aspect_ratio)
        self.setFixedSize(w, h)

    def draw_badminton_court(self, frame):
        import cv2
        height, width = frame.shape[:2]

        # Real-world court size in meters
        court_width_m = 13.4  # horizontal in image
        court_height_m = 6.1  # vertical in image

        # Pixels per meter
        px_per_m_x = width / court_width_m
        px_per_m_y = height / court_height_m

        def m_to_px(m_x, m_y):
            return int(m_x * px_per_m_x), int(m_y * px_per_m_y)

        white = (255, 255, 255)
        thickness = max(2, int(width * 0.005))
        overlay = frame.copy()

        # Outer boundary (doubles)
        cv2.rectangle(overlay, m_to_px(0, 0), m_to_px(court_width_m, court_height_m), white, thickness)

        # Doubles sidelines (same as outer boundary)
        # Singles sidelines (0.46m in from each side)
        cv2.line(overlay, m_to_px(0.46, 0), m_to_px(0.46, court_height_m), white, thickness)
        cv2.line(overlay, m_to_px(court_width_m - 0.46, 0), m_to_px(court_width_m - 0.46, court_height_m), white, thickness)

        # Baselines (top and bottom)
        # Already drawn as part of outer boundary

        # Doubles service line (0.76m from each baseline)
        cv2.line(overlay, m_to_px(0, 0.76), m_to_px(court_width_m, 0.76), white, thickness)
        cv2.line(overlay, m_to_px(0, court_height_m - 0.76), m_to_px(court_width_m, court_height_m - 0.76), white, thickness)

        # Net (center)
        net_x = court_width_m / 2
        cv2.line(overlay, m_to_px(net_x, 0), m_to_px(net_x, court_height_m), white, thickness * 2)

        # Short service lines (1.98m from net on both sides)
        cv2.line(overlay, m_to_px(0, 1.98), m_to_px(court_width_m, 1.98), white, thickness)
        cv2.line(overlay, m_to_px(0, court_height_m - 1.98), m_to_px(court_width_m, court_height_m - 1.98), white, thickness)

        # Center line (vertical, from short service line to baseline, both sides)
        center_left = net_x
        cv2.line(overlay, m_to_px(center_left, 1.98), m_to_px(center_left, 0.76), white, thickness)
        cv2.line(overlay, m_to_px(center_left, court_height_m - 1.98), m_to_px(center_left, court_height_m - 0.76), white, thickness)

        # Left and right service courts (vertical lines from net to short service line)
        # Left side
        cv2.line(overlay, m_to_px(center_left - 3.05, 0.76), m_to_px(center_left - 3.05, 1.98), white, thickness)
        # Right side
        cv2.line(overlay, m_to_px(center_left + 3.05, court_height_m - 0.76), m_to_px(center_left + 3.05, court_height_m - 1.98), white, thickness)

        # Add semi-transparency
        alpha = 0.4
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        return frame



class ClientApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Badminton Skill Tracker")
        self.showMaximized()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.video_label = VideoLabel()
        layout.addWidget(self.video_label)

        # Custom feature input fields
        input_layout = QHBoxLayout()
        self.shot_type_box = QComboBox()
        self.shot_type_box.addItems(["smash", "drop", "slice", "clear", "back_hand", "cross_court"])
        input_layout.addWidget(QLabel("Shot Type:"))
        input_layout.addWidget(self.shot_type_box)

        self.landing_x_input = QLineEdit()
        self.landing_x_input.setPlaceholderText("Landing X (e.g. 7.5)")
        input_layout.addWidget(QLabel("Landing X:"))
        input_layout.addWidget(self.landing_x_input)

        self.landing_y_input = QLineEdit()
        self.landing_y_input.setPlaceholderText("Landing Y (e.g. 3.0)")
        input_layout.addWidget(QLabel("Landing Y:"))
        input_layout.addWidget(self.landing_y_input)

        self.speed_input = QLineEdit()
        self.speed_input.setPlaceholderText("Shuttle Speed (km/h)")
        input_layout.addWidget(QLabel("Speed (km/h):"))
        input_layout.addWidget(self.speed_input)

        self.predict_button = QPushButton("Predict Score")
        self.predict_button.clicked.connect(self.predict_score)
        input_layout.addWidget(self.predict_button)

        self.score_result_label = QLabel("")
        input_layout.addWidget(self.score_result_label)

        layout.addLayout(input_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_video)
        button_layout.addWidget(self.play_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_video)
        button_layout.addWidget(self.pause_button)

        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(self.analyze_video)
        button_layout.addWidget(self.analyze_button)

        self.map_field_button = QPushButton("MAP FIELD")
        self.map_field_button.clicked.connect(self.toggle_court_overlay)
        button_layout.addWidget(self.map_field_button)

        layout.addLayout(button_layout)

        self.sio = socketio.Client()
        self.sio.connect('http://localhost:9000')

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_playing = False
        self.is_tracking = False
        self.show_court = False

        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50, detectShadows=False)
        self.kernel = np.ones((3,3), np.uint8)

    def toggle_court_overlay(self):
        self.show_court = not self.show_court
        print("Court overlay:", "Enabled" if self.show_court else "Disabled")

    def play_video(self):
        self.is_playing = True
        self.timer.start(30)

    def pause_video(self):
        self.is_playing = False
        self.timer.stop()

    def analyze_video(self):
        self.is_tracking = not self.is_tracking
        print("Hand tracking:", "Enabled" if self.is_tracking else "Disabled")

    def detect_hand(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        mask = cv2.dilate(mask, self.kernel, iterations=4)
        mask = cv2.GaussianBlur(mask, (5,5), 100)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(max_contour) > 1000:
                cv2.drawContours(frame, [max_contour], -1, (0, 255, 0), 2)
                x, y, w, h = cv2.boundingRect(max_contour)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                M = cv2.moments(max_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        return frame

    def update_frame(self):
        if self.is_playing:
            self.sio.emit('request_frame')

            @self.sio.on('frame')
            def handle_frame(data):
                if data['status'] == 'success':
                    frame_data = data['frame']
                    nparr = np.frombuffer(frame_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    # Resize frame to match video_label
                    label_width = self.video_label.width()
                    label_height = self.video_label.height()
                    frame = cv2.resize(frame, (label_width, label_height))

                    if self.is_tracking:
                        frame = self.detect_hand(frame)
                    if self.show_court:
                        frame = self.video_label.draw_badminton_court(frame)

                    height, width, channel = frame.shape
                    bytes_per_line = 3 * width
                    q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                    pixmap = QPixmap.fromImage(q_image)
                    self.video_label.setPixmap(pixmap)

    def predict_score(self):
        shot_type = self.shot_type_box.currentText()
        try:
            landing_x = float(self.landing_x_input.text())
            landing_y = float(self.landing_y_input.text())
            speed = float(self.speed_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numeric values for landing positions and speed.")
            return
        payload = {
            "shot_type": shot_type,
            "landing_position_x": landing_x,
            "landing_position_y": landing_y,
            "shuttle_speed_kmh": speed
        }
        try:
            response = requests.post("http://localhost:9290/predict_score", json=payload)
            if response.status_code == 200:
                score = response.json().get("predicted_score", None)
                shot_value = self.get_shot_value(score)
                self.score_result_label.setText(f"Predicted Score: {score:.2f} ({shot_value})")
                # Prepare data for save_shot
                shot_data = {
                    "user_id": random.randint(1, 10),
                    "user_name": f"User{random.randint(1, 10)}",
                    "user_skill_level": random.choice(["beginner", "intermediate", "advanced", "expert"]),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "shot_type": shot_type,
                    "landing_position_x": landing_x,
                    "landing_position_y": landing_y,
                    "shuttle_speed_kmh": speed,
                    "score": score,
                    "score_type": shot_value
                }
                try:
                    save_response = requests.post("http://localhost:9290/save_shot", json=shot_data)
                    if save_response.status_code == 200:
                        print("Shot data saved successfully.")
                    else:
                        print(f"Failed to save shot data: {save_response.text}")
                except Exception as e:
                    print(f"Error saving shot data: {e}")
            else:
                self.score_result_label.setText("API Error")
        except Exception as e:
            self.score_result_label.setText(f"Error: {e}")

    def get_shot_value(self, score):
        if score < 30:
            return 'bad_shot'
        elif score < 50:
            return 'average_shot'
        elif score < 80:
            return 'good_shot'
        elif score <= 100:
            return 'perfect_shot'
        return 'unknown'

    def closeEvent(self, event):
        self.sio.disconnect()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ClientApp()
    window.show()
    sys.exit(app.exec_())
