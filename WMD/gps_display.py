import sys
import threading
import time
import random
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

# Simulated GPS fix data class
class SimulatedFix:
    def __init__(self):
        self.latitude = None
        self.longitude = None
        self.speed = None
        self.track = None

    def update(self):
        # Simulate realistic GPS values:
        self.latitude = 30.2672 + random.uniform(-0.001, 0.001)    # Around Austin, TX
        self.longitude = -97.7431 + random.uniform(-0.001, 0.001)
        self.speed = random.uniform(0, 5)   # 0 to 5 m/s speed
        self.track = random.uniform(0, 360) # 0 to 360 degrees

# Simulated GPSD class to mimic gpsd interface
class SimulatedGPSD:
    def __init__(self):
        self.fix = SimulatedFix()
        self.running = True

    def next(self):
        # Update simulated GPS data periodically
        self.fix.update()
        time.sleep(1)

class GpsPoller(threading.Thread):
    def __init__(self, gpsd):
        super().__init__()
        self.gpsd = gpsd
        self.running = True

    def run(self):
        while self.running:
            self.gpsd.next()

class GpsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        # Use simulated GPSD
        self.gpsd = SimulatedGPSD()
        self.gps_poller = GpsPoller(self.gpsd)
        self.gps_poller.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gps_data)
        self.timer.start(1000)  # update every 1 second

    def initUI(self):
        self.setWindowTitle("Simulated GPS Data")
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
        fix = self.gpsd.fix

        self.lat_label.setText(f"Latitude: {fix.latitude:.6f}")
        self.lon_label.setText(f"Longitude: {fix.longitude:.6f}")
        self.speed_label.setText(f"Speed (m/s): {fix.speed:.2f}")
        self.track_label.setText(f"Track (degrees): {fix.track:.2f}")

    def closeEvent(self, event):
        self.gps_poller.running = False
        self.gps_poller.join()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GpsWidget()
    window.show()
    sys.exit(app.exec())
