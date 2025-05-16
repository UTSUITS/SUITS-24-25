import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer
import gpsd

class GPSWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPS Data")
        self.setGeometry(100, 100, 300, 150)

        gpsd.connect()  # Connect to local GPSD

        self.label = QLabel("Waiting for GPS fix...", self)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Timer to update every 1 second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

    def update_data(self):
        try:
            packet = gpsd.get_current()
            if packet.mode >= 2:  # 2D fix or better
                lat = packet.lat
                lon = packet.lon
                alt = packet.alt if packet.mode == 3 else "N/A"
                sats = packet.sats_used if hasattr(packet, 'sats_used') else "?"
                text = (
                    f"Latitude:  {lat:.6f}\n"
                    f"Longitude: {lon:.6f}\n"
                    f"Altitude:  {alt} m\n"
                    f"Fix Mode:  {packet.mode}D\n"
                    f"Satellites: {sats}"
                )
            else:
                text = "No fix yet... move outside if not already."
        except Exception as e:
            text = f"GPS error: {e}"

        self.label.setText(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = GPSWidget()
    widget.show()
    sys.exit(app.exec())
