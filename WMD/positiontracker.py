import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QPen, QFont, QPixmap
from PyQt6.QtCore import Qt, QPointF, QThread, pyqtSignal, QTimer
from Compass.QMC_test import get_bearing  # Compass
from GPS.gps_reader import get_gps_position  # Replace with your GPS fetch function


class MapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Map with Breadcrumb Trail")
        self.setMinimumSize(800, 600)
        self.map_image = QPixmap("rockYardMap-min.png")
        self.breadcrumbs = []  # List of (lat, lon)
        self.heading = 0

        # Define the GPS bounds of your map (replace with real values)
        self.lat_top = 30.2850
        self.lat_bottom = 30.2840
        self.lon_left = -97.7370
        self.lon_right = -97.7360

        # Timer to update GPS and heading
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # Update every second

    def update_data(self):
        try:
            lat, lon = get_gps_position()
            self.breadcrumbs.append((lat, lon))
        except Exception as e:
            print(f"GPS Error: {e}")
        
        try:
            self.heading = get_bearing()
        except Exception as e:
            print(f"Bearing Error: {e}")

        self.update()

    def gps_to_pixel(self, lat, lon):
        """Convert GPS coordinates to image pixel coordinates."""
        img_width = self.map_image.width()
        img_height = self.map_image.height()

        x = ((lon - self.lon_left) / (self.lon_right - self.lon_left)) * img_width
        y = ((self.lat_top - lat) / (self.lat_top - self.lat_bottom)) * img_height
        return QPointF(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background map
        painter.drawPixmap(self.rect(), self.map_image)

        # Draw breadcrumbs
        pen = QPen(Qt.GlobalColor.blue, 4)
        painter.setPen(pen)

        if self.breadcrumbs:
            points = [self.gps_to_pixel(lat, lon) for lat, lon in self.breadcrumbs]
            for point in points:
                painter.drawEllipse(point, 3, 3)
            # Optionally draw path
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])

        # Draw heading arrow at last location
        if self.breadcrumbs:
            last = self.gps_to_pixel(*self.breadcrumbs[-1])
            arrow_length = 30
            angle_rad = math.radians(self.heading)
            dx = math.sin(angle_rad) * arrow_length
            dy = -math.cos(angle_rad) * arrow_length
            painter.setPen(QPen(Qt.GlobalColor.red, 4))
            painter.drawLine(last, QPointF(last.x() + dx, last.y() + dy))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MapWidget()
    widget.show()
    sys.exit(app.exec())
