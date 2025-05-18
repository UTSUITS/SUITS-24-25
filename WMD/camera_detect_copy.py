import sys
import os
import time
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QSizePolicy, QHBoxLayout, QStackedLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor

from picamera2 import Picamera2
from libcamera import controls
import http_server  # Ensure this module is implemented
from PIL import Image
import cv2

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

        # Thumbnail preview
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(100, 75)
        self.thumbnail.setStyleSheet("border: 2px solid gray;")
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.thumbnail.setVisible(False)

        # Container for video + thumbnail
        camera_frame = QWidget()
        camera_layout = QStackedLayout(camera_frame)
        camera_layout.addWidget(self.label)
        camera_layout.addWidget(self.thumbnail)
        self.layout.addWidget(camera_frame)

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

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.camera_running = False
        self.http_thread = None

        # Ensure image directory exists
        self.image_dir = os.path.join(os.getcwd(), "images")
        os.makedirs(self.image_dir, exist_ok=True)

    def toggle_camera(self):
        if not self.camera_running:
            config = shared_picam2.create_preview_configuration(main={"format": 'RGB888', "size": (1024, 600)})
            shared_picam2.configure(config)
            shared_picam2.start()
            self.timer.start(60)
            self.button.setText("Stop Camera")

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

            # Add timestamp overlay
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            cv2.putText(
                frame, timestamp, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA
            )

            frame_rgb = frame[..., ::-1]
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
            full_path = os.path.join(self.image_dir, filename)

            Image.fromarray(frame).save(full_path)
            print(f"Saved: {full_path}")

            # Show thumbnail
            thumb = QPixmap(full_path).scaled(self.thumbnail.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.thumbnail.setPixmap(thumb)
            self.thumbnail.setVisible(True)

            # Flash white overlay
            self.flash_effect()

    def flash_effect(self):
        pixmap = self.label.pixmap()
        if pixmap is None:
            return

        flash_pixmap = pixmap.copy()
        painter = QPainter(flash_pixmap)
        painter.setBrush(QColor(255, 255, 255, 180))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self.label.width(), self.label.height())
        painter.end()

        self.label.setPixmap(flash_pixmap)
        self.label.repaint()
        QTimer.singleShot(100, self.update_frame)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraTab()
    window.setWindowTitle("Camera Capture with Timestamp and Flash")
    window.show()
    sys.exit(app.exec())
