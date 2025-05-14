import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from picamera2.previews.qt import QGlPicamera2
from picamera2 import Picamera2


class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt Picamera2 App")

        # Initialize the Picamera2 object
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration())
        
        # Set up the GUI layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Create the QGlPicamera2 preview widget
        self.qpicamera2 = QGlPicamera2(self.picam2, width=800, height=600, keep_ar=False)
        self.layout.addWidget(self.qpicamera2)

        # Create a button to start/stop the camera stream
        self.button = QPushButton("Start Camera")
        self.button.clicked.connect(self.toggle_camera)
        self.layout.addWidget(self.button)

        # Flag to track whether the camera is running
        self.camera_running = False

    def toggle_camera(self):
        if not self.camera_running:
            # Start the camera
            self.picam2.start()
            self.qpicamera2.show()
            self.button.setText("Stop Camera")
        else:
            # Stop the camera
            self.picam2.stop()
            self.qpicamera2.hide()
            self.button.setText("Start Camera")
        
        # Toggle the flag
        self.camera_running = not self.camera_running


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec())
