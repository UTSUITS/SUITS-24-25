import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTabWidget
)
from PyQt6.QtCore import Qt

class CameraTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.button = QPushButton("Start Camera")
        self.button.clicked.connect(self.toggle_camera)

        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

        self.camera_initialized = False
        self.camera_running = False
        self.qpicamera2 = None
        self.picam2 = None

    def initialize_camera(self):
        # ✅ Lazy import and widget creation AFTER QApplication
        from picamera2 import Picamera2
        from picamera2.previews.qt import QGlPicamera2

        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration())
        self.qpicamera2 = QGlPicamera2(self.picam2, width=800, height=600, keep_ar=False)

        self.layout.insertWidget(0, self.qpicamera2)
        self.camera_initialized = True

    def toggle_camera(self):
        if not self.camera_initialized:
            self.initialize_camera()

        if not self.camera_running:
            self.picam2.start()
            self.qpicamera2.show()
            self.button.setText("Stop Camera")
        else:
            self.picam2.stop()
            self.qpicamera2.hide()
            self.button.setText("Start Camera")

        self.camera_running = not self.camera_running


class WelcomeTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("👋 Welcome to the NASA SUITS Wrist-Mounted UI!\nSelect the camera tab to begin your EVA.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; padding: 20px;")
        layout.addWidget(label)
        self.setLayout(layout)


class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NASA SUITS Camera Interface")
        self.resize(850, 700)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.welcome_tab = WelcomeTab()
        self.camera_tab = CameraTab()

        self.tabs.addTab(self.welcome_tab, "Welcome")
        self.tabs.addTab(self.camera_tab, "Camera View")

        layout.addWidget(self.tabs)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)  # ✅ Constructed FIRST
    window = MainApp()
    window.show()
    sys.exit(app.exec())
