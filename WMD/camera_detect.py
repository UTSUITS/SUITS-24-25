import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer
from picamera2 import Picamera2


class PiCameraViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Raspberry Pi Camera - PyQt6")

        # Layout and image label
        self.image_label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # Initialize camera
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
        self.picam2.configure(config)
        self.picam2.start()

        # Timer for periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

    def update_frame(self):
        # Get the latest frame
        frame = self.picam2.capture_array()

        # Convert to QImage and display
        height, width, channel = frame.shape
        bytes_per_line = width * channel
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_image))

    def closeEvent(self, event):
        self.picam2.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = PiCameraViewer()
    viewer.show()
    sys.exit(app.exec())
