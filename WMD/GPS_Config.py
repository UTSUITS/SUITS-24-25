import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Dummy sensor class for testing, replace with your actual sensor
class QMC5883L:
    def __init__(self, i2c=None, offset=50.0):
        pass
    def read_scaled(self):
        # Return fake data: x, y, z in gauss, temp in °C
        import time
        t = time.time()
        x = math.cos(t)
        y = math.sin(t)
        z = 0.1
        temp = 25.0
        return (x, y, z, temp)

class CompassApp(QWidget):
    def __init__(self, sensor):
        super().__init__()
        self.sensor = sensor
        self.setWindowTitle("Simple QMC5883L Compass")
        self.resize(250, 150)

        self.label_xyz = QLabel("X: 0.00  Y: 0.00  Z: 0.00")
        self.label_temp = QLabel("Temp: 0.0 °C")
        self.label_heading = QLabel("Heading: 0.0°")

        font = QFont()
        font.setPointSize(12)
        self.label_xyz.setFont(font)
        self.label_temp.setFont(font)
        self.label_heading.setFont(font)

        self.label_xyz.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label_xyz)
        layout.addWidget(self.label_temp)
        layout.addWidget(self.label_heading)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_readings)
        self.timer.start(500)

    def update_readings(self):
        x, y, z, temp = self.sensor.read_scaled()

        self.label_xyz.setText(f"X: {x:.2f}  Y: {y:.2f}  Z: {z:.2f}")
        self.label_temp.setText(f"Temp: {temp:.1f} °C")

        heading_rad = math.atan2(y, x)
        heading_deg = math.degrees(heading_rad)
        if heading_deg < 0:
            heading_deg += 360
        self.label_heading.setText(f"Heading: {heading_deg:.1f}°")

def main():
    app = QApplication(sys.argv)

    sensor = QMC5883L()  # Replace with actual sensor instance

    window = CompassApp(sensor)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
