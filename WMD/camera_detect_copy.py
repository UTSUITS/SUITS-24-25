import sys
import time
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                               QPushButton, QFileDialog, QLabel)
from PySide6.QtMultimedia import (QCamera, QCameraDevice,
                                  QImageCapture, QMediaCaptureSession)
from PySide6.QtMultimediaWidgets import QVideoWidget


class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Camera Example")

        # Layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Video Widget to show camera
        self.viewfinder = QVideoWidget()
        self.layout.addWidget(self.viewfinder)

        # Buttons
        self.capture_btn = QPushButton("Capture Photo")
        self.layout.addWidget(self.capture_btn)

        self.change_folder_btn = QPushButton("Change Save Folder")
        self.layout.addWidget(self.change_folder_btn)

        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)

        # Default save folder
        self.save_folder = "."

        # Get default camera device
        devices = QCameraDevice.availableDevices()
        if not devices:
            self.status_label.setText("No camera device found!")
            return
        self.camera_device = devices[0]

        # Camera and capture session setup
        self.camera = QCamera(self.camera_device)
        self.capture_session = QMediaCaptureSession()
        self.capture_session.setCamera(self.camera)

        self.viewfinder.show()
        self.capture_session.setVideoOutput(self.viewfinder)

        # Image capture
        self.image_capture = QImageCapture()
        self.capture_session.setImageCapture(self.image_capture)

        # Connect signals
        self.capture_btn.clicked.connect(self.capture_image)
        self.image_capture.imageCaptured.connect(self.on_image_captured)
        self.change_folder_btn.clicked.connect(self.change_folder)

        # Start the camera
        self.camera.start()

    def capture_image(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{self.save_folder}/photo_{timestamp}.jpg"
        self.image_capture.captureToFile(filename)
        self.status_label.setText(f"Capturing photo to {filename}")

    def on_image_captured(self, id, preview):
        self.status_label.setText(f"Photo captured with id {id}")

    def change_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Save Folder", self.save_folder)
        if path:
            self.save_folder = path
            self.status_label.setText(f"Save folder changed to: {self.save_folder}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
