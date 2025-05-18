import sys
import os
import time
import threading
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QSizePolicy,
    QHBoxLayout, QComboBox, QMessageBox
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

        # Camera feed
        self.label = QLabel("Camera feed will appear here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedSize(640, 480)
        self.label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(100, 75)
        self.thumbnail.setStyleSheet("border: 2px solid gray;")
        self.thumbnail.setVisible(False)

        self.filename_label = QLabel()
        self.filename_label.setStyleSheet("color: white; font-size: 10px;")
        self.filename_label.setVisible(False)

        top_right_layout = QVBoxLayout()
        top_right_layout.addWidget(self.thumbnail)
        top_right_layout.addWidget(self.filename_label)
        top_right_layout.addStretch(1)

        camera_stack = QHBoxLayout()
        camera_stack.addWidget(self.label)
        camera_stack.addLayout(top_right_layout)

        # Field Notes Section
        field_notes_layout = QVBoxLayout()
        self.notes_fields = {}

        fields = {
            "Size/Shape": ["Small chip", "Fist sized", "Potato shaped"],
            "Color/Tone": ["Grey", "Red", "Black", "Light toned"],
            "Texture": ["Fine", "Medium", "Coarse"],
            "Durability": ["Hard to break", "Crumbles"],
            "Density": ["Dense", "Not dense"],
            "Surface Feature": ["Weathering ring", "Impacts"]
        }

        for field, options in fields.items():
            label = QLabel(field)
            combo = QComboBox()
            combo.addItems(options)
            combo.setStyleSheet("color: white;")
            self.notes_fields[field] = combo
            field_notes_layout.addWidget(label)
            field_notes_layout.addWidget(combo)

        # Save Notes button (triggers both photo + field note save)
        self.save_notes_button = QPushButton("Save Field Notes + Capture Photo")
        self.save_notes_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.save_notes_button.clicked.connect(self.save_notes)
        field_notes_layout.addWidget(self.save_notes_button)

        # Library button
        self.library_button = QPushButton("📁 Open Library")
        self.library_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                font-size: 14px;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        self.library_button.clicked.connect(self.open_library)
        field_notes_layout.addWidget(self.library_button)

        # Expand notes section fully to the right
        field_notes_layout.addStretch(1)
        field_notes_container = QVBoxLayout()
        field_notes_container.addLayout(field_notes_layout)

        camera_notes_layout = QHBoxLayout()
        camera_notes_layout.addLayout(camera_stack)
        camera_notes_layout.addLayout(field_notes_container)

        self.layout.addLayout(camera_notes_layout)

        # Start Camera Button
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

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_row.addStretch(1)

        self.layout.addStretch(1)
        self.layout.addLayout(bottom_row)
        self.setLayout(self.layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.camera_running = False
        self.http_thread = None

        self.image_dir = os.path.join(os.getcwd(), "WMD/captures")
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

            frame_rgb = frame[..., ::-1]
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
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            filename = f"captured_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            full_path = os.path.join(self.image_dir, filename)
            Image.fromarray(frame_rgb).save(full_path)

            thumb = QPixmap(full_path).scaled(self.thumbnail.size(),
                                              Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
            self.thumbnail.setPixmap(thumb)
            self.thumbnail.setVisible(True)
            self.filename_label.setText(filename)
            self.filename_label.setVisible(True)

            self.flash_effect()
            return filename  # return filename to pair with notes
        return None

    def save_notes(self):
        photo_filename = self.capture_photo()
        if not photo_filename:
            return

        notes_filename = f"field_notes_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        notes_path = os.path.join(self.image_dir, notes_filename)
        with open(notes_path, 'w') as f:
            for field, combo in self.notes_fields.items():
                f.write(f"{field}: {combo.currentText()}\n")
            f.write(f"\nAssociated Photo: {photo_filename}\n")

        # Confirmation Popup
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("✅ Field notes and photo captured.")
        msg.setWindowTitle("Capture Successful")
        msg.setStandardButtons(QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Close)

        if msg.exec() == QMessageBox.StandardButton.Open:
            self.open_file(notes_path)

    def open_file(self, path):
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])

    def open_library(self):
        self.open_file(self.image_dir)

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
    window.setWindowTitle("NASA SUITS: Camera and Field Notes")
    window.show()
    sys.exit(app.exec())
