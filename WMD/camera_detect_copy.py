import sys
import cv2
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap

class CameraTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()

        self.label = QLabel("Camera feed will appear here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        self.button = QPushButton("Start Camera")
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.button.clicked.connect(self.toggle_camera)
        self.camera_running = False

    def toggle_camera(self):
        if not self.camera_running:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.label.setText("Failed to open camera")
                return
            self.timer.start(30)  # 30 ms = ~33 FPS
            self.button.setText("Stop Camera")
        else:
            self.timer.stop()
            if self.cap:
                self.cap.release()
            self.label.setText("Camera stopped")
            self.button.setText("Start Camera")
        self.camera_running = not self.camera_running

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qt_image)
        self.label.setPixmap(pix.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio))

class WelcomeTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Welcome! Use the Camera tab to see your webcam feed.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 OpenCV Camera Tabs")
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
