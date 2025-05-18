from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QSizePolicy, QHBoxLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap

from picamera2 import Picamera2
import numpy as np
import threading
import http_server  # your server script

# Create shared Picamera2 instance
shared_picam2 = Picamera2()

class CameraTab(QWidget):
    def __init__(self):
        super().__init__()

        # Main vertical layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Camera feed label
        self.label = QLabel("Camera feed will appear here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedSize(640, 480)
        self.label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.layout.addWidget(self.label)

        # Spacer to push button to bottom
        self.layout.addStretch(1)

        # Bottom row layout
        button_row = QHBoxLayout()
        self.layout.addLayout(button_row)

        # Add button aligned to bottom left
        self.button = QPushButton("Start Camera")
        self.button.setFixedSize(100, 30)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_row.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignLeft)

        # Fill space to right of button
        button_row.addStretch(1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.button.clicked.connect(self.toggle_camera)
        self.camera_running = False
        self.http_thread = None

    def toggle_camera(self):
        if not self.camera_running:
            config = shared_picam2.create_preview_configuration(main={"format": 'RGB888', "size": (1024, 600)})
            shared_picam2.configure(config)
            shared_picam2.start()
            self.timer.start(60)
            self.button.setText("Stop Camera")

            # Start HTTP server and pass shared camera
            if not self.http_thread:
                self.http_thread = threading.Thread(
                    target=http_server.start_http_server,
                    args=(shared_picam2,),  # Pass camera to the server
                    daemon=True
                )
                self.http_thread.start()

        else:
            self.timer.stop()
            shared_picam2.stop()
            self.label.setText("Camera stopped")
            self.button.setText("Start Camera")
        self.camera_running = not self.camera_running

    def update_frame(self):
        if shared_picam2:
            frame = shared_picam2.capture_array()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(qt_image)
            pix = pix.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.label.setPixmap(pix)
