import sys
import threading
import time
import random
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar, 
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QConicalGradient


# Simulated GPS fix data class (same as before)
class SimulatedFix:
    def __init__(self):
        self.latitude = None
        self.longitude = None
        self.speed = None
        self.track = None

    def update(self):
        self.latitude = 30.2672 + random.uniform(-0.001, 0.001)    # Austin TX approx
        self.longitude = -97.7431 + random.uniform(-0.001, 0.001)
        self.speed = random.uniform(0, 10)   # 0-10 m/s speed range for demo
        self.track = random.uniform(0, 360)  # 0-360 degrees


# Simulated GPSD class (same interface as gpsd)
class SimulatedGPSD:
    def __init__(self):
        self.fix = SimulatedFix()
        self.running = True

    def next(self):
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


class CompassWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.angle = 0  # Track angle in degrees
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def setAngle(self, angle):
        self.angle = angle % 360
        self.update()

    def paintEvent(self, event):
        size = min(self.width(), self.height())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Center and radius
        center = self.rect().center()
        radius = size // 2 - 10

        # Draw outer circle
        pen = QPen(QColor("#00bcff"))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(QColor("#121212"))
        painter.drawEllipse(center, radius, radius)

        # Draw compass ticks every 30 degrees
        painter.setPen(QPen(QColor("#00bcff"), 2))
        for i in range(12):
            angle_deg = i * 30
            rad = angle_deg * 3.14159265359 / 180
            inner = QPoint(
                center.x() + int((radius - 15) * -sin(rad)),
                center.y() + int((radius - 15) * -cos(rad))
            )
            outer = QPoint(
                center.x() + int(radius * -sin(rad)),
                center.y() + int(radius * -cos(rad))
            )
            painter.drawLine(inner, outer)

        # Draw N, E, S, W labels
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        directions = {"N": 0, "E": 90, "S": 180, "W": 270}
        for label, deg in directions.items():
            rad = deg * 3.14159265359 / 180
            point = QPoint(
                center.x() + int((radius - 35) * -sin(rad)),
                center.y() + int((radius - 35) * -cos(rad))
            )
            painter.drawText(point - QPoint(10, -7), label)

        # Draw needle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ff4c4c"))
        painter.save()
        painter.translate(center)
        painter.rotate(-self.angle)
        needle = [QPoint(0, -10), QPoint(-8, 0), QPoint(0, radius - 40), QPoint(8, 0)]
        painter.drawPolygon(*needle)
        painter.restore()


from math import sin, cos


class GpsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulated GPS Dashboard")
        self.setFixedSize(1100, 600)
        self.setStyleSheet("background-color: #121212; color: #e0e0e0; font-family: Arial;")

        # Simulated GPS
        self.gpsd = SimulatedGPSD()
        self.gps_poller = GpsPoller(self.gpsd)
        self.gps_poller.start()

        # Layouts
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Left panel: Data labels + speed bar
        left_panel = QVBoxLayout()
        left_panel.setSpacing(20)

        title = QLabel("GPS Data")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00bcff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(title)

        # Latitude and Longitude labels
        self.lat_label = QLabel("Latitude: N/A")
        self.lon_label = QLabel("Longitude: N/A")
        self.speed_label = QLabel("Speed (m/s): N/A")
        self.track_label = QLabel("Track (deg): N/A")

        label_style = "font-size: 22px; padding: 8px;"
        for lbl in [self.lat_label, self.lon_label, self.speed_label, self.track_label]:
            lbl.setStyleSheet(label_style)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            left_panel.addWidget(lbl)

        # Speed bar
        speed_label = QLabel("Speed Indicator")
        speed_label.setStyleSheet("font-size: 18px; color: #aaaaaa;")
        speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(speed_label)

        self.speed_bar = QProgressBar()
        self.speed_bar.setMinimum(0)
        self.speed_bar.setMaximum(20)  # Max speed 20 m/s (arbitrary)
        self.speed_bar.setTextVisible(True)
        self.speed_bar.setFormat("%v m/s")
        self.speed_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #00bcff;
                border-radius: 10px;
                background-color: #333333;
                height: 30px;
                font-size: 18px;
                color: #00bcff;
            }
            QProgressBar::chunk {
                background-color: #00bcff;
                border-radius: 10px;
            }
        """)
        left_panel.addWidget(self.speed_bar)

        left_panel.addStretch()
        main_layout.addLayout(left_panel, 3)

        # Right panel: Compass widget
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.setSpacing(10)

        compass_title = QLabel("Heading")
        compass_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compass_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00bcff;")
        right_panel.addWidget(compass_title)

        self.compass = CompassWidget()
        right_panel.addWidget(self.compass, alignment=Qt.AlignmentFlag.AlignCenter)

        right_panel.addStretch()

        main_layout.addLayout(right_panel, 4)

        self.setLayout(main_layout)

        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gps_data)
        self.timer.start(1000)

    def update_gps_data(self):
        fix = self.gpsd.fix

        self.lat_label.setText(f"Latitude: {fix.latitude:.6f}")
        self.lon_label.setText(f"Longitude: {fix.longitude:.6f}")
        self.speed_label.setText(f"Speed (m/s): {fix.speed:.2f}")
        self.track_label.setText(f"Track (deg): {fix.track:.2f}")

        self.speed_bar.setValue(int(fix.speed))
        self.compass.setAngle(fix.track)

    def closeEvent(self, event):
        self.gps_poller.running = False
        self.gps_poller.join()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GpsWidget()
    window.show()
    sys.exit(app.exec())
