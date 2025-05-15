import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStatusBar, QToolBar, QComboBox,
    QFileDialog, QErrorMessage, QVBoxLayout, QWidget
)
from PyQt6.QtGui import QAction
from PyQt6.QtMultimedia import (
    QCamera, QCameraDevice, QMediaCaptureSession,
    QImageCapture, QMediaDevices
)
from PyQt6.QtMultimediaWidgets import QVideoWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background : lightgrey;")

        # Get available cameras
        self.available_cameras = QMediaDevices.videoInputs()
        if not self.available_cameras:
            sys.exit("No cameras found")

        self.status = QStatusBar()
        self.status.setStyleSheet("background : white;")
        self.setStatusBar(self.status)

        self.save_path = ""
        self.save_seq = 0

        # Viewfinder
        self.viewfinder = QVideoWidget()
        self.setCentralWidget(self.viewfinder)

        self.capture_session = QMediaCaptureSession()
        self.capture_session.setVideoOutput(self.viewfinder)

        self.select_camera(0)

        # Toolbar
        toolbar = QToolBar("Camera Tool Bar")
        self.addToolBar(toolbar)

        # Click photo action
        click_action = QAction("Click photo", self)
        click_action.setStatusTip("Capture picture")
        click_action.setToolTip("Capture picture")
        click_action.triggered.connect(self.click_photo)
        toolbar.addAction(click_action)

        # Change folder action
        change_folder_action = QAction("Change save location", self)
        change_folder_action.setStatusTip("Change folder where picture will be saved")
        change_folder_action.setToolTip("Change save location")
        change_folder_action.triggered.connect(self.change_folder)
        toolbar.addAction(change_folder_action)

        # Camera selector
        self.camera_selector = QComboBox()
        self.camera_selector.setStatusTip("Choose camera")
        self.camera_selector.setToolTip("Select Camera")
        self.camera_selector.addItems([device.description() for device in self.available_cameras])
        self.camera_selector.currentIndexChanged.connect(self.select_camera)
        toolbar.addWidget(self.camera_selector)

        toolbar.setStyleSheet("background : white;")
        self.setWindowTitle("PyQt6 Cam")
        self.show()

    def select_camera(self, index):
        self.camera = QCamera(self.available_cameras[index])
        self.capture_session.setCamera(self.camera)

        self.image_capture = QImageCapture(self.camera)
        self.capture_session.setImageCapture(self.image_capture)

        self.camera.start()

        self.current_camera_name = self.available_cameras[index].description()
        self.save_seq = 0

        self.image_capture.imageCaptured.connect(
            lambda id, img: self.status.showMessage(f"Image captured: {self.save_seq}")
        )

    def click_photo(self):
        timestamp = time.strftime("%d-%b-%Y-%H_%M_%S")
        filename = f"{self.current_camera_name}-{self.save_seq:04d}-{timestamp}.jpg"
        filepath = os.path.join(self.save_path, filename)

        self.image_capture.captureToFile(filepath)
        self.save_seq += 1

    def change_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Picture Location", "")
        if path:
            self.save_path = path
            self.save_seq = 0

    def alert(self, msg):
        error = QErrorMessage(self)
        error.showMessage(msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
