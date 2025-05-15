import sys
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap

from picamera2 import Picamera2
import numpy as np

class CameraTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()

        self.label = QLabel("Camera feed will appear here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedSize(640, 480)
        self.label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.layout.addWidget(self.label)

        self.button = QPushButton("Start Camera")
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)

        self.picam2 = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.button.clicked.connect(self.toggle_camera)
        self.camera_running = False

    def toggle_camera(self):
        if not self.camera_running:
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(main={"format": 'RGB888', "size": (640, 480)})
            self.picam2.configure(config)
            self.picam2.start()
            self.timer.start(60)  # roughly 30 FPS
            self.button.setText("Stop Camera")
        else:
            self.timer.stop()
            if self.picam2:
                self.picam2.stop()
                self.picam2 = None
            self.label.setText("Camera stopped")
            self.button.setText("Start Camera")
        self.camera_running = not self.camera_running

    def update_frame(self):
        if self.picam2:
            frame = self.picam2.capture_array()

            # Convert BGR to RGB if needed
            frame_rgb = frame[..., ::-1]

            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(qt_image)

            pix = pix.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.label.setPixmap(pix)


class WelcomeTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Welcome! Use the Camera tab to see your Raspberry Pi camera feed.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Picamera2 Tabs")
        self.resize(800, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.welcome_tab = WelcomeTab()
        self.camera_tab = CameraTab()

        self.tabs.addTab(self.welcome_tab, "Welcome")
        self.tabs.addTab(self.camera_tab, "Camera")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
