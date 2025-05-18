import sys
import os
import time
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QSizePolicy,
    QHBoxLayout, QStackedLayout, QComboBox, QTextEdit
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
        self.layout = QHBoxLayout()  # Main layout is horizontal

        # Left: Camera and buttons
        self.left_layout = QVBoxLayout()

        self.label = QLabel("Camera feed will appear here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedSize(640, 480)
        self.label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.left_layout.addWidget(self.label)

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

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.button)
        bottom_row.addWidget(self.capture_button)
        self.left_layout.addLayout(bottom_row)

        # Right: Field notes and thumbnail
        self.right_layout = QVBoxLayout()

        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(100, 75)
        self.thumbnail.setStyleSheet("border: 2px solid gray;")
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.thumbnail.setVisible(False)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setStyleSheet("color: gray; font-size: 10px;")
        self.thumbnail_label.setVisible(False)

        self.right_layout.addWidget(self.thumbnail, alignment=Qt.AlignmentFlag.AlignRight)
        self.right_layout.addWidget(self.thumbnail_label, alignment=Qt.AlignmentFlag.AlignRight)

        # Field Notes Section
        self.field_notes_layout = QVBoxLayout()
        self.field_notes_layout.addWidget(QLabel("Field Notes:"))

        self.size_shape = QComboBox()
        self.size_shape.addItems(["", "Small chip", "Fist sized", "Potato shaped"])
        self.field_notes_layout.addWidget(QLabel("Size/Shape"))
        self.field_notes_layout.addWidget(self.size_shape)

        self.color_tone = QComboBox()
        self.color_tone.addItems(["", "Grey", "Red", "Black", "Light toned"])
        self.field_notes_layout.addWidget(QLabel("Color/Tone"))
        self.field_notes_layout.addWidget(self.color_tone)

        self.texture = QComboBox()
        self.texture.addItems(["", "Fine", "Medium", "Coarse"])
        self.field_notes_layout.addWidget(QLabel("Texture (Grain Size)"))
        self.field_notes_layout.addWidget(self.texture)

        self.durability = QComboBox()
        self.durability.addItems(["", "Hard to break", "Crumbles"])
        self.field_notes_layout.addWidget(QLabel("Durability"))
        self.field_notes_layout.addWidget(self.durability)

        self.density = QComboBox()
        self.density.addItems(["", "Dense", "Not dense"])
        self.field_notes_layout.addWidget(QLabel("Density"))
        self.field_notes_layout.addWidget(self.density)

        self.surface_feature = QComboBox()
        self.surface_feature.addItems(["", "Weathering ring", "Impacts"])
        self.field_notes_layout.addWidget(QLabel("Surface Feature"))
        self.field_notes_layout.addWidget(self.surface_feature)

        self.save_notes_button = QPushButton("Save Field Notes")
        self.save_notes_button.clicked.connect(self.save_field_notes)
        self.field_notes_layout.addWidget(self.save_notes_button)

        self.right_layout.addLayout(self.field_notes_layout)

        # Combine layouts
        self.layout.addLayout(self.left_layout)
        self.layout.addLayout(self.right_layout)
        self.setLayout(self.layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.camera_running = False
        self.http_thread = None
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
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255, 255, 255), 2, cv2.LINE_AA)
            frame_rgb = frame[..., ::-1]  # Convert BGR to RGB
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(qt_image)
            pix = pix.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
            self.label.setPixmap(pix)

    def capture_photo(self):
        if shared_picam2 and self.camera_running:
            frame = shared_picam2.capture_array()
            corrected_frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(corrected_frame, cv2.COLOR_BGR2RGB)
            filename = f"captured_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            full_path = os.path.join(self.image_dir, filename)
            Image.fromarray(rgb_frame).save(full_path)
            print(f"Saved: {full_path}")

            thumb = QPixmap(full_path).scaled(self.thumbnail.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
            self.thumbnail.setPixmap(thumb)
            self.thumbnail.setVisible(True)
            self.thumbnail_label.setText(filename)
            self.thumbnail_label.setVisible(True)
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

    def save_field_notes(self):
        notes_path = os.path.join(self.image_dir, f"field_notes_{time.strftime('%Y%m%d')}.txt")
        with open(notes_path, 'a') as f:
            f.write(f"--- Observation at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(f"Size/Shape: {self.size_shape.currentText()}\n")
            f.write(f"Color/Tone: {self.color_tone.currentText()}\n")
            f.write(f"Texture: {self.texture.currentText()}\n")
            f.write(f"Durability: {self.durability.currentText()}\n")
            f.write(f"Density: {self.density.currentText()}\n")
            f.write(f"Surface Feature: {self.surface_feature.currentText()}\n")
            f.write("\n")
        print(f"Field notes saved to {notes_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraTab()
    window.setWindowTitle("Camera Capture with Field Notes")
    window.show()
    sys.exit(app.exec())