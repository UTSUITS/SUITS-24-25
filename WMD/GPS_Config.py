import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPolygon, QColor, QPen, QFont, QPoint

# Import your QMC5883L class here
# from qmc5883l import QMC5883L
# For example, if mag_base.py and qmc5883l.py are in same folder
# and mag_base is defined properly.

# Dummy stub to simulate sensor readings (remove this and import actual class)
class QMC5883L:
    def __init__(self, i2c=None, offset=50.0):
        pass
    def read_scaled(self):
        # Return fake data: x, y, z in gauss, temp in °C
        return (0.5, 0.0, 0.1, 25.0)

class CompassWidget(QWidget):
    def __init__(self, sensor):
        super().__init__()
        self.sensor = sensor

        self.setWindowTitle("QMC5883L Compass")
        self.resize(300, 400)

        self.label_xyz = QLabel("X: 0.0  Y: 0.0  Z: 0.0")
        self.label_temp = QLabel("Temp: 0.0 °C")
        self.label_heading = QLabel("Heading: 0.0°")

        self.label_xyz.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font = QFont()
        font.setPointSize(12)
        self.label_xyz.setFont(font)
        self.label_temp.setFont(font)
        self.label_heading.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(self.label_xyz)
        layout.addWidget(self.label_temp)
        layout.addWidget(self.label_heading)

        self.setLayout(layout)

        self.heading = 0.0

        # Update sensor and UI every 500ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_readings)
        self.timer.start(500)

    def update_readings(self):
        x, y, z, temp = self.sensor.read_scaled()
        self.label_xyz.setText(f"X: {x:.2f}  Y: {y:.2f}  Z: {z:.2f}")
        self.label_temp.setText(f"Temp: {temp:.1f} °C")

        # Calculate heading in degrees (0-360)
        heading_rad = math.atan2(y, x)
        heading_deg = math.degrees(heading_rad)
        if heading_deg < 0:
            heading_deg += 360
        self.heading = heading_deg

        self.label_heading.setText(f"Heading: {self.heading:.1f}°")
        self.update()  # trigger repaint for compass

    def paintEvent(self, event):
        painter = QPainter(self)
        center_x = self.width() // 2
        center_y = self.height() // 2 + 50
        radius = 100

        # Draw compass circle
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("black"), 3))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # Draw N, E, S, W labels
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        painter.drawText(center_x - 10, center_y - radius + 20, "N")
        painter.drawText(center_x + radius - 20, center_y + 10, "E")
        painter.drawText(center_x - 10, center_y + radius - 10, "S")
        painter.drawText(center_x - radius + 10, center_y + 10, "W")

        # Draw heading arrow
        painter.setPen(QPen(QColor("red"), 3))
        painter.setBrush(QColor("red"))

        # Arrow points: tip and two base corners
        arrow_size = 20
        angle_rad = math.radians(self.heading)

        tip = QPoint(
            center_x + int(radius * math.cos(angle_rad)),
            center_y + int(radius * math.sin(angle_rad))
        )
        left = QPoint(
            center_x + int(arrow_size * math.cos(angle_rad + math.pi * 0.75)),
            center_y + int(arrow_size * math.sin(angle_rad + math.pi * 0.75))
        )
        right = QPoint(
            center_x + int(arrow_size * math.cos(angle_rad - math.pi * 0.75)),
            center_y + int(arrow_size * math.sin(angle_rad - math.pi * 0.75))
        )

        arrow = QPolygon([tip, left, right])
        painter.drawPolygon(arrow)


def main():
    app = QApplication(sys.argv)

    # Initialize your I2C and sensor here
    # For example:
    # import board
    # import busio
    # i2c = busio.I2C(board.SCL, board.SDA)
    # sensor = QMC5883L(i2c)

    # For now, using dummy stub:
    sensor = QMC5883L()

    window = CompassWidget(sensor)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
