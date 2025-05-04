import sys
import cv2
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OBS Virtual Camera - 360° Feed")
        self.setFixedSize(1024, 600)

        # QLabel to display video
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 1024, 600)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # OpenCV to capture from OBS Virtual Camera (adjust the index as needed)
        self.cap = cv2.VideoCapture(2)

        # Timer for fetching frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            height, width = frame.shape[:2]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(rgb_frame.data, width, height, width * 3, QImage.Format.Format_RGB888)
            scaled_image = image.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.label.setPixmap(QPixmap.fromImage(scaled_image))

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

