import sys
import cv2
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OBS Virtual Camera - 360° Feed")
        self.setFixedSize(1024, 600)

        # QLabel to display video
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 1024, 600)
        self.label.setAlignment(Qt.AlignCenter)

        # OpenCV to capture from OBS Virtual Camera (adjust the index as needed)
        self.cap = cv2.VideoCapture(4)

        # Timer for fetching frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Get original frame size (2880x1440)
            height, width = frame.shape[:2]

            # Convert the frame from BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Create QImage from the frame
            image = QImage(rgb_frame.data, width, height, width * 3, QImage.Format_RGB888)

            # Scale image to fit the label while preserving aspect ratio
            scaled_image = image.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Display the image on the label
            self.label.setPixmap(QPixmap.fromImage(scaled_image))

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
