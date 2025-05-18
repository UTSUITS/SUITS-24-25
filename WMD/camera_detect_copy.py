# camera_detect_copy.py

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QSizePolicy, QHBoxLayout
from PyQt6.QtCore import QTimer, Qt, QUrl
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor
# from PyQt6.QtMultimedia import QSoundEffect

from picamera2 import Picamera2
import numpy as np
import threading
import http_server
import time
import os

# Create shared Picamera2 instance
shared_picam2 = Picamera2()


class CameraTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()

        self.label = QLabel("Camera feed will appear here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedSize(640, 480)
        self.label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.layout.addWidget(self.label)

        # Buttons
        self.button = QPushButton("Start Camera")
        self.button.setFixedSize(400, 70)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.button.clicked.connect(self.toggle_camera)

        self.capture_button = QPushButton("Capture Photo")
        self.capture_button.setFixedSize(200, 50)
        self.capture_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.capture_button.clicked.connect(self.capture_photo)

        # Layout buttons at bottom
        self.layout.addStretch(1)
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_row.addWidget(self.capture_button, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_row.addStretch(1)
        self.layout.addLayout(bottom_row)

        self.setLayout(self.layout)

        # Timer for updating the video feed
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.camera_running = False
        self.http_thread = None

        # Setup shutter sound
        # self.shutter_sound = QSoundEffect()
        # self.shutter_sound.setSource(QUrl.fromLocalFile(os.path.abspath("shutter.mp3")))
        # self.shutter_sound.setVolume(0.8)

    def toggle_camera(self):
        if not self.camera_running:
            config = shared_picam2.create_preview_configuration(main={"format": 'RGB888', "size": (1024, 600)})
            shared_picam2.configure(config)
            shared_picam2.start()
            self.timer.start(60)
            self.button.setText("Stop Camera")

            # Start HTTP server
            if not self.http_thread:
                self.http_thread = threading.Thread(
                    target=http_server.start_http_server,
                    args=(shared_picam2,),
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
            frame_rgb = frame[..., ::-1]  # Convert BGR to RGB
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(qt_image)
            pix = pix.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.label.setPixmap(pix)

    def capture_photo(self):
        if shared_picam2 and self.camera_running:
            frame = shared_picam2.capture_array()
            filename = f"captured_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            from PIL import Image
            Image.fromarray(frame).save(filename)
            print(f"Saved: {filename}")

            # Play sound
            # self.shutter_sound.play()

            # Flash effect
            self.flash_effect()

    def flash_effect(self):
        # Flash white overlay on label for 100 ms
        pixmap = self.label.pixmap()
        if pixmap is None:
            return

        painter = QPainter(pixmap)
        painter.setBrush(QColor(255, 255, 255, 180))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self.label.width(), self.label.height())
        painter.end()
        self.label.setPixmap(pixmap)
        self.label.repaint()
        QTimer.singleShot(100, self.update_frame)  # Reset after flash
