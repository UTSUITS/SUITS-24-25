import sys
import threading
import time
from gps import *
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

gpsd = None

class GpsPoller(threading.Thread):
    def __init__(self):
        super().__init__()
        global gpsd
        gpsd = gps(mode=WATCH_ENABLE)
        self.running = True

    def run(self):
        global gpsd
        while self.running:
            gpsd.next()

class GpsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.gps_poller = GpsPoller()
        self.gps_poller.start()

        # Timer to update UI every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gps_data)
        self.timer.start(1000)

    def initUI(self):
        self.setWindowTitle("GPS Data")
        self.layout = QVBoxLayout()

        self.lat_label = QLabel("Latitude: N/A")
        self.lon_label = QLabel("Longitude: N/A")
        self.speed_label = QLabel("Speed (m/s): N/A")
        self.track_label = QLabel("Track (degrees): N/A")

        for label in [self.lat_label, self.lon_label, self.speed_label, self.track_label]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(label)

        self.setLayout(self.layout)
        self.resize(300, 150)

    def update_gps_data(self):
        # Update labels with latest GPS data, handle possible None values
        lat = getattr(gpsd.fix, 'latitude', 'N/A')
        lon = getattr(gpsd.fix, 'longitude', 'N/A')
        speed = getattr(gpsd.fix, 'speed', 'N/A')
        track = getattr(gpsd.fix, 'track', 'N/A')

        self.lat_label.setText(f"Latitude: {lat if lat is not None else 'N/A'}")
        self.lon_label.setText(f"Longitude: {lon if lon is not None else 'N/A'}")
        self.speed_label.setText(f"Speed (m/s): {speed if speed is not None else 'N/A'}")
        self.track_label.setText(f"Track (degrees): {track if track is not None else 'N/A'}")

    def closeEvent(self, event):
        # Stop the GPS poller thread when closing the widget
        self.gps_poller.running = False
        self.gps_poller.join()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GpsWidget()
    window.show()
    sys.exit(app.exec())
