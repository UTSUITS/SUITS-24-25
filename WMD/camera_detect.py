import sys
import cv2
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer

# ==== Distance Estimation Constants ====
KNOWN_WIDTH = 50.0  # cm, average shoulder width of a person
FOCAL_LENGTH = 600  # pixels (calibrate this for your camera)

def estimate_distance(perceived_width):
    if perceived_width == 0:
        return None
    return (KNOWN_WIDTH * FOCAL_LENGTH) / perceived_width

class PeopleDetectionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("People Detection and Distance (Raspberry Pi Camera)")

        # Layout
        self.image_label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # Open camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera. Make sure it's connected and enabled.")

        # Set up timer to update frame
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

        # Set up HOG person detector
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Optionally resize for performance
        frame = cv2.resize(frame, (640, 480))

        # Detect people in the frame
        (rects, _) = self.hog.detectMultiScale(
            frame,
            winStride=(8, 8),
            padding=(16, 16),
            scale=1.05
        )

        # Draw rectangles and estimate distance
        for (x, y, w, h) in rects:
            distance = estimate_distance(w)
            if distance:
                label = f"{distance:.1f} cm"
                cv2.putText(frame, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)

        # Convert to Qt format
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PeopleDetectionApp()
    window.show()
    sys.exit(app.exec())
