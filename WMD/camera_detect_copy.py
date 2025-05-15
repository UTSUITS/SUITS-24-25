from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStatusBar, QToolBar, QAction, QComboBox, QFileDialog, QErrorMessage
)
from PyQt6.QtMultimedia import QCameraDevice, QCamera, QMediaCaptureSession, QImageCapture
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt
import os
import sys
import time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background : lightgrey;")

        # Get available cameras
        self.camera_devices = QMediaCaptureSession().availableCameras()

        if not self.camera_devices:
            QErrorMessage(self).showMessage("No cameras found.")
            sys.exit()

        # Status bar
        self.status = QStatusBar()
        self.status.setStyleSheet("background : white;")
        self.setStatusBar(self.status)

        # Save path
        self.save_path = os.getcwd()

        # Create camera viewfinder
        self.viewfinder = QVideoWidget()
        self.setCentralWidget(self.viewfinder)

        # Create toolbar
        toolbar = QToolBar("Camera Toolbar")
        toolbar.setStyleSheet("background : white;")
        self.addToolBar(toolbar)

        # Click photo action
        click_action = QAction("Click photo", self)
        click_action.setStatusTip("This will capture a picture")
        click_action.triggered.connect(self.click_photo)
        toolbar.addAction(click_action)

        # Change save location action
        change_folder_action = QAction("Change save location", self)
        change_folder_action.setStatusTip("Change the folder where pictures will be saved")
        change_folder_action.triggered.connect(self.change_folder)
        toolbar.addAction(change_folder_action)

        # Camera selector combo box
        self.camera_selector = QComboBox()
        self.camera_selector.setStatusTip("Choose camera to take pictures")
        self.camera_selector.addItems([device.description() for device in self.camera_devices])
        self.camera_selector.currentIndexChanged.connect(self.select_camera)
        toolbar.addWidget(self.camera_selector)

        # Set default camera
        self.select_camera(0)

        self.setWindowTitle("PyQt6 Cam")
        self.show()

    def select_camera(self, index):
        self.capture_session = QMediaCaptureSession()

        self.camera = QCamera(self.camera_devices[index])
        self.capture_session.setCamera(self.camera)

        self.capture_session.setVideoOutput(self.viewfinder)

        self.image_capture = QImageCapture(self.camera)
        self.capture_session.setImageCapture(self.image_capture)

        self.image_capture.imageCaptured.connect(
            lambda id, image: self.status.showMessage(f"Image captured: {self.save_seq}")
        )

        self.camera.start()

        self.current_camera_name = self.camera_devices[index].description()
        self.save_seq = 0

    def click_photo(self):
        timestamp = time.strftime("%d-%b-%Y-%H_%M_%S")
        filename = f"{self.current_camera_name}-{self.save_seq:04d}-{timestamp}.jpg"
        full_path = os.path.join(self.save_path, filename)
        self.image_capture.captureToFile(full_path)
        self.save_seq += 1

    def change_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Picture Location", "")
        if path:
            self.save_path = path
            self.save_seq = 0


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
