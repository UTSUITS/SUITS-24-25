import sys
import serial
import pynmea2
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

class GPSReader:
    def __init__(self, port="/dev/serial0", baudrate=9600):
        self.serial_port = serial.Serial(port, baudrate=baudrate, timeout=1)
        self.last_lat = None
        self.last_lon = None
        self.last_speed = 0.0
        self.last_heading = 0.0

    def read(self):
        while self.serial_port.in_waiting:
            line = self.serial_port.readline().decode(errors='ignore').strip()
            if line.startswith('$GPRMC') or line.startswith('$GNRMC'):
                try:
                    msg = pynmea2.parse(line)
                    if msg.status == 'A':  # Data Active
                        self.last_lat = msg.latitude
                        self.last_lon = msg.longitude
                        self.last_speed = float(msg.spd_over_grnd) * 1.852  # knots to km/h
                        self.last_heading = float(msg.true_course)
                except pynmea2.nmea.ParseError:
                    pass
        return self.last_lat, self.last_lon, self.last_speed, self.last_heading

class GPSApp(QWidget):
    def __init__(self, gps_reader):
        super().__init__()
        self.gps = gps_reader
        self.setWindowTitle("GPS Viewer")
        self.resize(300, 150)

        self.label_position = QLabel("Lat: 0.0000, Lon: 0.0000")
        self.label_speed = QLabel("Speed: 0.0 km/h")
        self.label_heading = QLabel("Heading: 0.0°")

        font = QFont()
        font.setPointSize(12)
        for label in [self.label_position, self.label_speed, self.label_heading]:
            label.setFont(font)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label_position)
        layout.addWidget(self.label_speed)
        layout.addWidget(self.label_heading)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

    def update_data(self):
        lat, lon, speed, heading = self.gps.read()
        if lat is not None and lon is not None:
            self.label_position.setText(f"Lat: {lat:.5f}, Lon: {lon:.5f}")
            self.label_speed.setText(f"Speed: {speed:.1f} km/h")
            self.label_heading.setText(f"Heading: {heading:.1f}°")

def main():
    app = QApplication(sys.argv)
    gps_reader = GPSReader()
    window = GPSApp(gps_reader)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
