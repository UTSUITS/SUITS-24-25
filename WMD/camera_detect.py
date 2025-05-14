import sys
import cv2
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer
from picamera2 import Picamera2


class CameraStreamApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Camera Stream (Raspberry Pi 4)")

        # === UI Layout ===
        self.image_label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # === Initialize PiCamera2 ===
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration({'format': 'RGB888', 'size': (640, 480)})
        self.picam2.configure(config)
        self.picam2.start()

        # === Timer for frame update ===
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

    def update_frame(self):
        # Capture frame
        frame = self.picam2.capture_array()

        # Convert to Qt image
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.picam2.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraStreamApp()
    window.show()
    sys.exit(app.exec())
