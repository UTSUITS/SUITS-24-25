import sys
import math
import signal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtGui import QPainter, QPen, QFont, QPixmap
from PyQt6.QtCore import Qt, QPointF, QTimer, QRect, QCoreApplication
from Compass.QMC_test import get_bearing  # Your compass module
from GPS.GPS_testing import get_gps_data  # Your GPS fetch function


class MapWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Map with Breadcrumb Trail and GPS Info")
        self.setFixedSize(1100, 600)  # fixed window size

        self.map_image = QPixmap("rockYardMap-min.png")
        if self.map_image.isNull():
            print("Error: Failed to load rockYardMap-min.png")

        self.breadcrumbs = []  # List of (lat, lon)
        self.heading = 0.0
        self.tracking = False
        self.current_lat = None
        self.current_lon = None

        # Define GPS bounds of the map image (replace with your real values)
        self.lat_top = 30.2850
        self.lat_bottom = 30.2840
        self.lon_left = -97.7370
        self.lon_right = -97.7360

        # Map drawing rect size and position
        self.map_rect = QRect(10, 10, 600, 400)  # smaller map area on left

        # Floating box size and state
        self.floating_box_size = 40
        self.floating_box_pos = QPointF(0, 0)
        self.floating_box_visible = False

        # Setup timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # update every second

        # UI Buttons for controlling breadcrumbs
        self.start_btn = QPushButton("Start Breadcrumb Trail")
        self.stop_btn = QPushButton("Stop Breadcrumb Trail")
        self.clear_btn = QPushButton("Clear Breadcrumbs")
        self.status_label = QLabel("Status: Not Tracking")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        self.start_btn.clicked.connect(self.start_tracking)
        self.stop_btn.clicked.connect(self.stop_tracking)
        self.clear_btn.clicked.connect(self.clear_breadcrumbs)

        self.stop_btn.setEnabled(False)  # initially stop disabled

        # Info labels for Lat/Lon and Heading
        self.lat_label = QLabel("Latitude: N/A")
        self.lon_label = QLabel("Longitude: N/A")
        self.heading_label = QLabel("Heading: N/A °")
        self.lat_label.setFont(QFont("Arial", 11))
        self.lon_label.setFont(QFont("Arial", 11))
        self.heading_label.setFont(QFont("Arial", 11))

        # 3D XYZ display frame (numeric)
        self.xyz_frame = QFrame()
        self.xyz_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.xyz_frame.setFixedWidth(250)

        self.x_label = QLabel("X: N/A")
        self.y_label = QLabel("Y: N/A")
        self.z_label = QLabel("Z: N/A")
        for lbl in [self.x_label, self.y_label, self.z_label]:
            lbl.setFont(QFont("Arial", 11))
        xyz_layout = QVBoxLayout()
        xyz_layout.addWidget(QLabel("<b>GPS XYZ Coordinates</b>"))
        xyz_layout.addWidget(self.x_label)
        xyz_layout.addWidget(self.y_label)
        xyz_layout.addWidget(self.z_label)
        self.xyz_frame.setLayout(xyz_layout)

        # Compass display (textual for now)
        self.compass_label = QLabel("Compass: N/A")
        self.compass_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.compass_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Right side layout for info
        info_layout = QVBoxLayout()
        info_layout.addWidget(self.lat_label)
        info_layout.addWidget(self.lon_label)
        info_layout.addWidget(self.heading_label)
        info_layout.addWidget(self.compass_label)
        info_layout.addWidget(self.xyz_frame)
        info_layout.addStretch()

        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.status_label)

        # Main horizontal layout: map on left, info on right
        main_layout = QHBoxLayout()

        # Create a spacer to the left of map for breathing room (optional)
        main_layout.addSpacing(10)

        # Add map as a widget placeholder (since painting is custom, just space it)
        from PyQt6.QtWidgets import QWidget
        map_placeholder = QWidget()
        map_placeholder.setFixedSize(self.map_rect.width() + 20, self.map_rect.height() + 20)
        main_layout.addWidget(map_placeholder)

        main_layout.addSpacing(30)  # space between map and info labels

        main_layout.addLayout(info_layout)
        main_layout.addStretch(1)

        # Overall vertical layout
        vertical_layout = QVBoxLayout()
        vertical_layout.addLayout(main_layout)
        vertical_layout.addLayout(btn_layout)

        self.setLayout(vertical_layout)

    def start_tracking(self):
        self.tracking = True
        self.status_label.setText("Status: Tracking Breadcrumbs")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)

    def stop_tracking(self):
        self.tracking = False
        self.status_label.setText("Status: Breadcrumb Tracking Stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.clear_btn.setEnabled(True)

    def clear_breadcrumbs(self):
        self.breadcrumbs.clear()
        self.status_label.setText("Status: Breadcrumbs Cleared")
        self.update()

    def update_data(self):
        try:
            lat, lon = get_gps_data()
            self.current_lat = lat
            self.current_lon = lon
            print(f"GPS received: lat={lat}, lon={lon}")  # DEBUG print

            if self.tracking:
                if not self.breadcrumbs or self.distance(lat, lon, *self.breadcrumbs[-1]) > 0.00001:
                    self.breadcrumbs.append((lat, lon))
            self.floating_box_pos = self.gps_to_pixel(lat, lon)
            self.floating_box_visible = True
        except Exception as e:
            print(f"GPS Error: {e}")
            self.floating_box_visible = False
            self.current_lat = None
            self.current_lon = None

        try:
            self.heading = get_bearing()
            print(f"Compass bearing: {self.heading}")  # DEBUG print to terminal
        except Exception as e:
            print(f"Bearing Error: {e}")
            self.heading = 0.0

        # Update labels correctly
        if self.current_lat is not None:
            self.lat_label.setText(f"Latitude: {self.current_lat:.6f}")
        else:
            self.lat_label.setText("Latitude: N/A")

        if self.current_lon is not None:
            self.lon_label.setText(f"Longitude: {self.current_lon:.6f}")
        else:
            self.lon_label.setText("Longitude: N/A")

        # Heading label always updates to float formatted heading
        self.heading_label.setText(f"Heading: {self.heading:.1f} °")
        self.compass_label.setText(f"Compass Bearing: {self.heading:.1f} °")

        # Update XYZ coordinates
        if self.current_lat is not None and self.current_lon is not None:
            x, y, z = self.latlon_to_xyz(self.current_lat, self.current_lon)
            self.x_label.setText(f"X: {x:.2f} km")
            self.y_label.setText(f"Y: {y:.2f} km")
            self.z_label.setText(f"Z: {z:.2f} km")
        else:
            self.x_label.setText("X: N/A")
            self.y_label.setText("Y: N/A")
            self.z_label.setText("Z: N/A")

        self.update()  # repaint

    @staticmethod
    def distance(lat1, lon1, lat2, lon2):
        return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

    def gps_to_pixel(self, lat, lon):
        img_width = self.map_rect.width()
        img_height = self.map_rect.height()

        x = ((lon - self.lon_left) / (self.lon_right - self.lon_left)) * img_width + self.map_rect.left()
        y = ((self.lat_top - lat) / (self.lat_top - self.lat_bottom)) * img_height + self.map_rect.top()
        return QPointF(x, y)

    @staticmethod
    def latlon_to_xyz(lat, lon):
        R = 6371  # km
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        x = R * math.cos(lat_rad) * math.cos(lon_rad)
        y = R * math.cos(lat_rad) * math.sin(lon_rad)
        z = R * math.sin(lat_rad)
        return x, y, z

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw map in fixed rect
        if not self.map_image.isNull():
            painter.drawPixmap(self.map_rect, self.map_image)

        # Draw breadcrumb trail
        if len(self.breadcrumbs) > 1:
            pen = QPen(Qt.GlobalColor.blue, 3)
            painter.setPen(pen)
            for i in range(1, len(self.breadcrumbs)):
                pt1 = self.gps_to_pixel(*self.breadcrumbs[i - 1])
                pt2 = self.gps_to_pixel(*self.breadcrumbs[i])
                painter.drawLine(pt1, pt2)

        # Draw points (breadcrumbs)
        pen = QPen(Qt.GlobalColor.red, 10)
        painter.setPen(pen)
        for lat, lon in self.breadcrumbs:
            pt = self.gps_to_pixel(lat, lon)
            painter.drawPoint(pt)

        # Draw floating box near current position
        if self.floating_box_visible and self.current_lat is not None and self.current_lon is not None:
            rect_size = self.floating_box_size
            pos = self.floating_box_pos
            rect = QRect(int(pos.x() - rect_size / 2), int(pos.y() - rect_size / 2), rect_size, rect_size)
            painter.setBrush(Qt.GlobalColor.yellow)
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRect(rect)

            # Draw Lat/Lon text inside floating box
            painter.setPen(Qt.GlobalColor.black)
            font = QFont("Arial", 8)
            painter.setFont(font)
            text = f"{self.current_lat:.6f}\n{self.current_lon:.6f}"
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        # Draw heading arrow near bottom right of map
        if self.current_lat is not None and self.current_lon is not None:
            center_x = self.map_rect.left() + self.map_rect.width() - 50
            center_y = self.map_rect.top() + self.map_rect.height() - 50
            length = 40

            angle_rad = math.radians(self.heading - 90)  # Adjust so 0 deg points up
            x2 = center_x + length * math.cos(angle_rad)
            y2 = center_y + length * math.sin(angle_rad)

            pen = QPen(Qt.GlobalColor.green, 4)
            painter.setPen(pen)
            painter.drawLine(center_x, center_y, x2, y2)

            # Draw a circle at the base
            painter.setBrush(Qt.GlobalColor.green)
            painter.drawEllipse(QPointF(center_x, center_y), 8, 8)


def sigint_handler(*args):
    print("\nSIGINT received, exiting...")
    QCoreApplication.quit()


def main():
    app = QApplication(sys.argv)

    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, sigint_handler)

    # Timer to keep event loop responsive to signals
    timer = QTimer()
    timer.start(100)  # 100 ms
    timer.timeout.connect(lambda: None)  # no-op

    window = MapWidget()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
