import sys
import threading
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from Compass.QMC_test import get_bearing  # Update to your actual heading sensor

# Simulated GPS classes for testing
class SimulatedGPSFix:
    def __init__(self):
        self.latitude = 37.7749
        self.longitude = -122.4194
        self.speed = 0.0
        self.track = 0.0

    def update(self):
        self.latitude += 0.0001
        self.longitude += 0.0001
        self.speed = (self.speed + 0.1) % 20
        self.track = (self.track + 5) % 360


class SimulatedGPSD:
    def __init__(self):
        self.fix = SimulatedGPSFix()


class GpsPoller(threading.Thread):
    def __init__(self, gpsd):
        super().__init__()
        self.gpsd = gpsd
        self.running = True

    def run(self):
        while self.running:
            self.gpsd.fix.update()
            time.sleep(0.1)


# Compass with rotating rose
class CompassWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.setMinimumSize(150, 150)
        self.setMaximumSize(150, 150)

    def setAngle(self, angle):
        self.angle = angle
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height())
        center = QPointF(self.width() / 2, self.height() / 2)

        # Draw background
        painter.setBrush(QColor("white"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size, size)

        painter.translate(center)

        # Draw rotating compass rose
        painter.save()
        painter.rotate(-self.angle)  # Rotate rose based on heading

        directions = ['N', 'E', 'S', 'W']
        for i, d in enumerate(directions):
            angle = i * 90
            radians = angle * 3.14159 / 180
            x = 0
            y = -size * 0.4
            painter.save()
            painter.rotate(angle)
            painter.setPen(QColor("black"))
            font = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(-5, int(y), d)
            painter.restore()

        painter.restore()

        # Draw needle (static up)
        painter.setPen(QPen(QColor("#222222"), 3))
        painter.setBrush(QColor("#222222"))

        needle_path = [
            QPointF(0, -size * 0.4),
            QPointF(-6, 0),
            QPointF(0, -6),
            QPointF(6, 0),
        ]
        painter.drawPolygon(*needle_path)


class SpeedometerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.speed = 0
        self.setMinimumSize(150, 150)
        self.setMaximumSize(150, 150)

    def setSpeed(self, speed):
        self.speed = speed
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor("white"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

        center = self.width() / 2, self.height() / 2

        painter.setPen(QPen(QColor("#222222"), 5))
        painter.drawArc(10, 10, self.width() - 20, self.height() - 20, 45 * 16, 90 * 16)

        painter.setPen(QPen(QColor("#222222"), 3))
        painter.translate(*center)

        angle = 45 + (min(self.speed, 20) / 20) * 90
        painter.rotate(angle)
        painter.drawLine(0, 0, 0, int(-self.height() * 0.4))


class BreadcrumbMapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.breadcrumbs = []
        self.setMinimumSize(400, 400)
        self.setStyleSheet("background-color: #222222;")

    def add_breadcrumb(self, lat, lon):
        self.breadcrumbs.append((lat, lon))
        self.update()

    def clear_breadcrumbs(self):
        self.breadcrumbs.clear()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#222222"))

        if not self.breadcrumbs:
            return

        lats = [pt[0] for pt in self.breadcrumbs]
        lons = [pt[1] for pt in self.breadcrumbs]

        lat_min, lat_max = min(lats), max(lats)
        lon_min, lon_max = min(lons), max(lons)

        if lat_max - lat_min < 0.0001:
            lat_max += 0.0001
            lat_min -= 0.0001
        if lon_max - lon_min < 0.0001:
            lon_max += 0.0001
            lon_min -= 0.0001

        def map_point(lat, lon):
            x = (lon - lon_min) / (lon_max - lon_min) * self.width()
            y = self.height() - (lat - lat_min) / (lat_max - lat_min) * self.height()
            return QPointF(x, y)

        points = [map_point(lat, lon) for lat, lon in self.breadcrumbs]

        painter.setPen(QPen(QColor("white"), 2))
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        painter.setBrush(QColor("red"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(points[-1], 6, 6)


class GpsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPS Dashboard")
        self.setStyleSheet("background-color: #000000;")

        self.gpsd = SimulatedGPSD()
        self.gpsp = GpsPoller(self.gpsd)
        self.gpsp.start()

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(100)

        self.breadcrumb_running = False

    def init_ui(self):
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.compass = CompassWidget()
        self.speedometer = SpeedometerWidget()
        left_layout.addWidget(self.compass)
        left_layout.addWidget(self.speedometer)

        self.lat_label = QLabel("Latitude: ---")
        self.lon_label = QLabel("Longitude: ---")
        self.speed_label = QLabel("Speed: --- m/s")
        self.bearing_label = QLabel("Bearing: ---°")

        for widget in [self.lat_label, self.lon_label, self.speed_label, self.bearing_label]:
            widget.setFont(QFont("Arial", 12))
            widget.setStyleSheet("color: white;")
            left_layout.addWidget(widget)

        self.start_breadcrumb_btn = QPushButton("Start Breadcrumb")
        self.start_breadcrumb_btn.setStyleSheet("background-color: #008000; color: white; padding: 6px;")
        self.start_breadcrumb_btn.clicked.connect(self.start_breadcrumb)
        left_layout.addWidget(self.start_breadcrumb_btn)

        self.stop_breadcrumb_btn = QPushButton("Stop Breadcrumb")
        self.stop_breadcrumb_btn.setStyleSheet("background-color: #800000; color: white; padding: 6px;")
        self.stop_breadcrumb_btn.clicked.connect(self.stop_breadcrumb)
        self.stop_breadcrumb_btn.setEnabled(False)
        left_layout.addWidget(self.stop_breadcrumb_btn)

        self.clear_breadcrumb_btn = QPushButton("Clear Breadcrumb")
        self.clear_breadcrumb_btn.setStyleSheet("background-color: #555555; color: white; padding: 6px;")
        self.clear_breadcrumb_btn.clicked.connect(self.clear_breadcrumb)
        left_layout.addWidget(self.clear_breadcrumb_btn)

        self.breadcrumb_map = BreadcrumbMapWidget()
        self.breadcrumb_map.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.breadcrumb_map, 3)

        self.setLayout(main_layout)

    def start_breadcrumb(self):
        self.breadcrumb_running = True
        self.start_breadcrumb_btn.setEnabled(False)
        self.stop_breadcrumb_btn.setEnabled(True)

    def stop_breadcrumb(self):
        self.breadcrumb_running = False
        self.start_breadcrumb_btn.setEnabled(True)
        self.stop_breadcrumb_btn.setEnabled(False)

    def clear_breadcrumb(self):
        self.breadcrumb_map.clear_breadcrumbs()

    def update_display(self):
        fix = self.gpsd.fix
        lat = fix.latitude
        lon = fix.longitude
        speed = fix.speed
        bearing = get_bearing()

        self.lat_label.setText(f"Latitude: {lat:.6f}")
        self.lon_label.setText(f"Longitude: {lon:.6f}")
        self.speed_label.setText(f"Speed: {speed:.1f} m/s")
        self.bearing_label.setText(f"Bearing: {bearing:.1f}°")

        self.speedometer.setSpeed(speed)
        self.compass.setAngle(bearing)

        if self.breadcrumb_running:
            self.breadcrumb_map.add_breadcrumb(lat, lon)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GpsWidget()
    window.show()
    sys.exit(app.exec())
