import math
import json
import time

from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt6.QtCore import Qt, QTimer
from shared_data import shared_results, results_lock

class MapLabel(QLabel):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.measuring_distance = False
        self.measure_points = []
        self.base_pixmap = pixmap
        self.points_of_interest_display = []
        self.click_points = []
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lat_bottom = self.dms_to_decimal(29, 33, 51)
        self.lat_top = self.dms_to_decimal(29, 33, 56)
        self.lon_left = -self.dms_to_decimal(95, 4, 56)
        self.lon_right = -self.dms_to_decimal(95, 4, 50)
        self.trail = []
        self.rover_trail = []
        self.eva1_trail = []
        self.eva2_trail = []
        
        # Timer to update position data from Redis
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_position_from_redis)
        self.update_timer.start(500)  # Update every 500ms
        
    def update_position_from_redis(self): # CHECK THIS Richard G, naming for data variables might be wrong 
        """Fetches position data from Redis and updates trails"""
        try:
            with results_lock:
                data = shared_results
                
            # Update rover position if available
            if 23 in data and 24 in data:
                try:
                    mx = float(data[23])
                    my = float(data[24])
                    px, py = self.map_to_pixel(mx, my)
                    self.rover_trail.append((px, py))
                    # Limit trail length to prevent performance issues
                    if len(self.rover_trail) > 100:
                        self.rover_trail = self.rover_trail[-100:]
                except (ValueError, TypeError) as e:
                    pass
                    
            # Update EVA1 position if available
            if 17 in data and 18 in data:
                try:
                    mx = float(data[17])
                    my = float(data[18])
                    px, py = self.map_to_pixel(mx, my)
                    self.eva1_trail.append((px, py))
                    if len(self.eva1_trail) > 100:
                        self.eva1_trail = self.eva1_trail[-100:]
                except (ValueError, TypeError) as e:
                    pass
                    
            # Update EVA2 position if available
            if 20 in data and 21 in data:
                try:
                    mx = float(data[20])
                    my = float(data[21])
                    px, py = self.map_to_pixel(mx, my)
                    self.eva2_trail.append((px, py))
                    if len(self.eva2_trail) > 100:
                        self.eva2_trail = self.eva2_trail[-100:]
                except (ValueError, TypeError) as e:
                    pass
                
            # Update Points of Interest (POIs)
            poi_indices = [(25, 26), (27, 28), (29, 30)]  # Indices for POI X, Y
            for i, (x_idx, y_idx) in enumerate(poi_indices, start=1):
                if x_idx in data and y_idx in data:
                    try:
                        mx = float(data[x_idx])
                        my = float(data[y_idx])
                        px, py = self.map_to_pixel(mx, my)
                        # Assuming you have POI trails to store the points
                        poi_trail = getattr(self, f'poi{i}_trail', [])
                        poi_trail.append((px, py))
                        # Limit trail length
                        if len(poi_trail) > 100:
                            poi_trail = poi_trail[-100:]
                        setattr(self, f'poi{i}_trail', poi_trail)
                    except (ValueError, TypeError) as e:
                        pass

            self.update()
            
        except Exception as e:
            print(f"[ERROR] Failed to update position from Redis: {e}")

    def toggle_measure_mode(self, state):
        self.measuring_distance = state
        self.measure_points.clear()
        self.update()
    
    def pixel_to_map_coordinates(self, px, py):
        # X runs left→right
        scale_x   = 210.0 / (3637 - 240)
        offset_x  = -5760 - scale_x * 240
        map_x     = scale_x * px + offset_x

        # Y runs top→bottom
        pixel_y_min, pixel_y_max = 174, 2281
        map_y_min,   map_y_max   = -9940.0, -10070.0

        scale_y  = (map_y_max - map_y_min) / (pixel_y_max - pixel_y_min)
        offset_y = map_y_min - scale_y * pixel_y_min

        map_y    = scale_y * py + offset_y
        return map_x, map_y
    
    def map_to_pixel(self, map_x, map_y):
        scale_x  = 210.0 / (3637 - 240)
        offset_x = -5760 - scale_x * 240

        pixel_x  = (map_x - offset_x) / scale_x

        pixel_y_min, pixel_y_max = 174, 2281
        map_y_min,   map_y_max   = -9940.0, -10070.0
        scale_y   = (map_y_max - map_y_min) / (pixel_y_max - pixel_y_min)
        offset_y  = map_y_min - scale_y * pixel_y_min

        pixel_y  = (map_y - offset_y) / scale_y
        return pixel_x, pixel_y

    def save_clicks_to_file(self, path="click_log.json"):
        try:
            log_data = []
            for x, y in self.click_points:
                grid_x, grid_y = self.pixel_to_map_coordinates(x, y)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                log_data.append({
                    "grid_x": round(grid_x, 1),
                    "grid_y": round(grid_y, 1),
                    "timestamp": timestamp
                })
            with open(path, 'w') as f:
                json.dump(log_data, f, indent=4)
            print(f"[SAVED] {len(log_data)} grid points with timestamps to {path}")
        except Exception as e:
            print(f"[ERROR] Could not save clicks: {e}")

    def dms_to_decimal(self, deg, minutes, seconds):
        return deg + minutes / 60 + seconds / 3600

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            label_w, label_h = self.width(), self.height()
            img_w, img_h = self.base_pixmap.width(), self.base_pixmap.height()

            scaled = self.base_pixmap.scaled(
                label_w, label_h, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            drawn_w, drawn_h = scaled.width(), scaled.height()
            offset_x = (label_w - drawn_w) // 2
            offset_y = (label_h - drawn_h) // 2

            x = event.position().x() - offset_x
            y = event.position().y() - offset_y

            if 0 <= x <= drawn_w and 0 <= y <= drawn_h:
                orig_x = x * img_w / drawn_w
                orig_y = y * img_h / drawn_h

                if self.measuring_distance:
                    self.measure_points.append((orig_x, orig_y))
                    if len(self.measure_points) == 2:
                        x1, y1 = self.measure_points[0]
                        x2, y2 = self.measure_points[1]
                        feet_x_per_px = 530 / 964
                        feet_y_per_px = 505 / 923
                        dx_ft = (x2 - x1) * feet_x_per_px
                        dy_ft = (y2 - y1) * feet_y_per_px
                        dist_ft = math.hypot(dx_ft, dy_ft)
                        print(f"[MEASURE] Distance: {dist_ft:.2f} feet ≈ {dist_ft * 0.3048:.2f} meters")
                    self.update()
                    return

                orig_x = x * img_w / drawn_w
                orig_y = y * img_h / drawn_h

                map_x, map_y = self.pixel_to_map_coordinates(orig_x, orig_y)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print(f"[CLICKED] #{len(self.click_points) + 1} at {timestamp} → Pixel: ({int(orig_x)}, {int(orig_y)}) → Grid: ({map_x:.1f}, {map_y:.1f})")

                self.click_points.append((orig_x, orig_y))
                self.save_clicks_to_file()
                self.update()

    def clear_clicks(self):
        self.click_points = []
        self.update()

    def clear_trails(self):
        """Clear all position trails"""
        self.rover_trail = []
        self.eva1_trail = []
        self.eva2_trail = []
        self.update()

    def show_point_by_index(self, index):
        if 0 <= index < len(self.points_of_interest_display):
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # draw the base map
        label_w, label_h = self.width(), self.height()
        img_w, img_h     = self.base_pixmap.width(), self.base_pixmap.height()
        scaled = self.base_pixmap.scaled(
            label_w, label_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        drawn_w, drawn_h = scaled.width(), scaled.height()
        offset_x = (label_w - drawn_w) // 2
        offset_y = (label_h - drawn_h) // 2
        painter.drawPixmap(offset_x, offset_y, scaled)

        # Draw rover trail (red)
        if self.rover_trail:
            painter.setPen(QPen(Qt.GlobalColor.red, 3))
            for px, py in self.rover_trail:
                sx = round(px * drawn_w / img_w) + offset_x
                sy = round(py * drawn_h / img_h) + offset_y
                painter.drawPoint(sx, sy)
            
            # Draw current position (larger dot)
            px, py = self.rover_trail[-1]
            sx = round(px * drawn_w / img_w) + offset_x
            sy = round(py * drawn_h / img_h) + offset_y
            painter.setBrush(QBrush(Qt.GlobalColor.red))
            painter.drawEllipse(sx-5, sy-5, 10, 10)
            painter.drawText(sx+10, sy, "ROVER")

        # Draw EVA1 trail (green)
        if self.eva1_trail:
            painter.setPen(QPen(Qt.GlobalColor.green, 3))
            for px, py in self.eva1_trail:
                sx = round(px * drawn_w / img_w) + offset_x
                sy = round(py * drawn_h / img_h) + offset_y
                painter.drawPoint(sx, sy)
            
            # Draw current position (larger dot)
            px, py = self.eva1_trail[-1]
            sx = round(px * drawn_w / img_w) + offset_x
            sy = round(py * drawn_h / img_h) + offset_y
            painter.setBrush(QBrush(Qt.GlobalColor.green))
            painter.drawEllipse(sx-5, sy-5, 10, 10)
            painter.drawText(sx+10, sy, "EVA1")

        # Draw EVA2 trail (blue)
        if self.eva2_trail:
            painter.setPen(QPen(Qt.GlobalColor.blue, 3))
            for px, py in self.eva2_trail:
                sx = round(px * drawn_w / img_w) + offset_x
                sy = round(py * drawn_h / img_h) + offset_y
                painter.drawPoint(sx, sy)
            
            # Draw current position (larger dot)
            px, py = self.eva2_trail[-1]
            sx = round(px * drawn_w / img_w) + offset_x
            sy = round(py * drawn_h / img_h) + offset_y
            painter.setBrush(QBrush(Qt.GlobalColor.blue))
            painter.drawEllipse(sx-5, sy-5, 10, 10)
            painter.drawText(sx+10, sy, "EVA2")

        # Draw distance measurement line
        if len(self.measure_points) == 2:
            x1, y1 = self.measure_points[0]
            x2, y2 = self.measure_points[1]
            sx1 = round(x1 * drawn_w / img_w) + offset_x
            sy1 = round(y1 * drawn_h / img_h) + offset_y
            sx2 = round(x2 * drawn_w / img_w) + offset_x
            sy2 = round(y2 * drawn_h / img_h) + offset_y
            painter.setPen(QPen(QColor("cyan"), 2))
            painter.drawLine(sx1, sy1, sx2, sy2)
            
            # Calculate and display distance
            feet_x_per_px = 530 / 964
            feet_y_per_px = 505 / 923
            dx_ft = (x2 - x1) * feet_x_per_px
            dy_ft = (y2 - y1) * feet_y_per_px
            dist_ft = math.hypot(dx_ft, dy_ft)
            dist_m = dist_ft * 0.3048
            
            # Show measurement text
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("yellow"), 2))
            painter.drawText((sx1+sx2)//2, (sy1+sy2)//2 - 10, 
                            f"{dist_ft:.1f} ft / {dist_m:.1f} m")

        # POIs
        if self.points_of_interest_display:
            x, y = self.points_of_interest_display[0]
            sx = round(x * drawn_w / img_w) + offset_x
            sy = round(y * drawn_h / img_h) + offset_y
            painter.setPen(Qt.GlobalColor.red)
            painter.setBrush(Qt.GlobalColor.red)
            painter.drawEllipse(sx - 5, sy - 5, 10, 10)

        # click log
        painter.setPen(QColor("yellow"))
        painter.setBrush(QColor("yellow"))
        for x, y in self.click_points:
            sx = round(x * drawn_w / img_w) + offset_x
            sy = round(y * drawn_h / img_h) + offset_y
            painter.drawEllipse(sx - 4, sy - 4, 8, 8)

        painter.end()