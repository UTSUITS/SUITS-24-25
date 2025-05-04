import sys
import cv2
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer

# ==== Distance Estimation Constants ====
KNOWN_FACE_WIDTH = 14.0  # cm, average adult face width
FOCAL_LENGTH = 600       # pixels (calibrate for your camera setup)

def estimate_distance(perceived_width):
    if perceived_width == 0:
        return None
    return (KNOWN_FACE_WIDTH * FOCAL_LENGTH) / perceived_width

class FaceDetectionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Detection and Distance (Raspberry Pi 4)")

        # === UI Layout ===
        self.image_label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        # === Load face detector ===
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        # === Open camera ===
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera. Check if it's connected and enabled.")

        # === Timer for frame update ===
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Resize for speed
        frame = cv2.resize(frame, (640, 480))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        # Draw rectangles and estimate distance
        for (x, y, w, h) in faces:
            distance = estimate_distance(w)
            if distance:
                label = f"{distance:.1f} cm"
                cv2.putText(frame, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)

        # Convert to Qt image
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
    window = FaceDetectionApp()
    window.show()
    sys.exit(app.exec())
