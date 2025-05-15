import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QTabWidget, QPushButton
)
from PyQt6.QtMultimedia import QCamera, QMediaCaptureSession
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt


class WelcomeTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("👋 Welcome!\nSelect the 'Camera' tab to see your camera feed.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)


class CameraTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()

        self.video_widget = QVideoWidget()
        self.layout.addWidget(self.video_widget)

        self.button = QPushButton("Start Camera")
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)

        # Create the camera
        self.camera = QCamera()
        # Create the media capture session
        self.capture_session = QMediaCaptureSession()
        self.capture_session.setCamera(self.camera)
        self.capture_session.setVideoOutput(self.video_widget)

        self.camera_running = False
        self.button.clicked.connect(self.toggle_camera)

    def toggle_camera(self):
        if not self.camera_running:
            self.camera.start()
            self.button.setText("Stop Camera")
        else:
            self.camera.stop()
            self.button.setText("Start Camera")
        self.camera_running = not self.camera_running


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Multi-Tab Camera Feed")
        self.resize(800, 600)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.welcome_tab = WelcomeTab()
        self.camera_tab = CameraTab()

        self.tabs.addTab(self.welcome_tab, "Welcome")
        self.tabs.addTab(self.camera_tab, "Camera")

        layout.addWidget(self.tabs)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
