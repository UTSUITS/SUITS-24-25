import sys
import json
import time
import math
from pathlib import Path
from PyQt6.QtWidgets import (
    QSizePolicy,
    QApplication, QWidget, QLabel, QVBoxLayout, QTextEdit,
    QHBoxLayout, QPushButton, QTabWidget, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QScreen
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtWidgets import QSlider
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPixmap

base_path = Path(__file__).parent
json_path = base_path / "output_results.json"
image_path = base_path / "mapgridattempt.png"


class ToggleSwitch(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setEnabled(False)
        self.setFixedSize(80, 40)
        self._color = "green"
        self.setStyleSheet("background: transparent; border: none;")
        self.clicked.connect(self.on_click)

    def set_color(self, color: str):
        self._color = color
        self.setChecked(color == "green")
        self.setEnabled(color == "red")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        radius = height // 2
        knob_margin = 4
        knob_diameter = height - 2 * knob_margin

        painter.setBrush(QBrush(QColor(self._color)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, width, height, radius, radius)

        knob_x = width - knob_diameter - knob_margin if self._color == "green" else knob_margin
        knob_y = knob_margin
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(knob_x, knob_y, knob_diameter, knob_diameter)

    def on_click(self):
        if self._color == "red":
            self.set_color("green")
            parent = self.parent()
            while parent and not isinstance(parent, SystemStatusDisplay):
                parent = parent.parent()
            if isinstance(parent, SystemStatusDisplay):
                parent.handle_clear_state(self)


class LEDIndicator(QFrame):
    def __init__(self, label_text="", parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.label_text = label_text
        self.color = "gray"
        self.blink = False
        self.blink_state = True

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(30)
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_blink)

        self.update_style()

    def set_color(self, color: str):
        self.color = color

        glow_map = {
            "red": QColor(255, 60, 60),
            "green": QColor(60, 255, 60),
            "gray": QColor(120, 120, 120),
            "yellow": QColor(255, 255, 120)
        }
        self.shadow.setColor(glow_map.get(color, QColor(100, 100, 100)))

        if self.label_text.lower() == "oxygen" and color == "red":
            self.blink = True
            self.blink_timer.start(500)
        else:
            self.blink = False
            self.setVisible(True)
            self.blink_timer.stop()

        self.update_style()

    def toggle_blink(self):
        if self.blink:
            self.blink_state = not self.blink_state
            self.setVisible(self.blink_state)

    def update_style(self):
        gradients = {
            "red": "qradialgradient(cx:0.4, cy:0.4, radius:1, fx:0.4, fy:0.4, stop:0 white, stop:1 red)",
            "green": "qradialgradient(cx:0.4, cy:0.4, radius:1, fx:0.4, fy:0.4, stop:0 white, stop:1 green)",
            "gray": "qradialgradient(cx:0.4, cy:0.4, radius:1, fx:0.4, fy:0.4, stop:0 white, stop:1 gray)",
            "yellow": "qradialgradient(cx:0.4, cy:0.4, radius:1, fx:0.4, fy:0.4, stop:0 white, stop:1 yellow)"
        }
        self.setStyleSheet(f"""
            background: {gradients.get(self.color, 'gray')};
            border-radius: 25px;
            border: 2px solid white;
        """)


class SystemStatusDisplay(QWidget):

    def __init__(self, title_text, keys_labels, use_leds=False, notify_parent=None):
        super().__init__()
        self.notify_parent = notify_parent

        self.title_text = title_text
        self.keys_labels = keys_labels
        self.use_leds = use_leds
        self.manual_resets = {}  # key: bool
        self.error_states = {key: None for key, _ in keys_labels}
        self.manual_resets = {key: False for key, _ in keys_labels}
        self.slider_states = {key: False for key, _ in keys_labels}
        self.widgets = {}

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        title = QLabel(self.title_text)
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white;")
        self.layout.addWidget(title)

        buttons_per_row = 4  # Adjusted layout alignment for toggle buttons
        row_layouts = []
        for _ in range((len(keys_labels) + buttons_per_row - 1) // buttons_per_row):
            row = QHBoxLayout()
            row.setSpacing(40)
            row_layouts.append(row)

        for idx, (key, label_text) in enumerate(keys_labels):
            if key in range(59, 102) and not use_leds:
                widget = GradientSlider()
            else:
                widget = LEDIndicator(label_text) if use_leds else ToggleSwitch()
            self.widgets[key] = widget
            widget_box = self.create_labeled_widget(label_text, widget)
            row_layouts[idx // buttons_per_row].addWidget(widget_box, alignment=Qt.AlignmentFlag.AlignCenter)

        for row in row_layouts:
            self.layout.addLayout(row)

        self.chat_box = QTextEdit()
        self.chat_box.setFixedHeight(260)
        self.chat_box.setReadOnly(True)
        self.chat_box.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.8); color: white; "
            "border-radius: 10px; padding: 10px; border: 2px solid #333;"
        )
        self.layout.addWidget(self.chat_box)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1000)

    def create_labeled_widget(self, label_text, widget):
        container = QWidget()
        layout = QVBoxLayout(container)

        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: white; font-size: 16px;")

        layout.addWidget(label)
        layout.addWidget(widget)

        return container

    def read_json(self):
        try:
            with open(json_path, 'r') as file:
                return json.load(file)
        except Exception:
            return None

    def refresh_data(self):
        data = self.read_json()
        if data:
            for key, label in self.keys_labels:
                value = data.get(str(key))
                if value is not None and value != self.error_states[key]:
                    self.update_status(key, label, value)
            if self.notify_parent:
                self.notify_parent.check_tab_statuses()

    def update_status(self, key, label, value):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        widget = self.widgets[key]

        if isinstance(widget, GradientSlider):
            widget.setValue(int(value))
            self.slider_states[key] = (int(value) == 0)

            self.chat_box.append(f"[{timestamp}] {label}: {value}%")
            return

        if self.use_leds:
            if value == 1:
                widget.set_color("red")
                self.log_to_chat(f"[{timestamp}] {label} Error Detected!")
             #   self.chat_box.append(f"[{timestamp}] {label} Error Detected!")
            elif value == 0:
                widget.set_color("green")
                self.chat_box.append(f"[{timestamp}] {label} :- OK")
            else:
                widget.set_color("gray")
                self.chat_box.append(f"[{timestamp}] {label} Unknown State")
        else:
            if value == 1:
                if not self.manual_resets.get(key, False):  # 🚨 Only set red if not manually overridden
                    widget.set_color("red")
              #     self.chat_box.append(f"[{timestamp}] {label} Error Detected!")
                    self.log_to_chat(f"[{timestamp}] {label} Error Detected!")
                else:
                    print(f"[DEBUG] Suppressed red update for {label} due to manual override")
                return
            else:
                if not self.manual_resets[key]:  # Only update green if not manually cleared
                    widget.set_color("green")
                    self.chat_box.append(f"[{timestamp}] {label} :- OK")

        self.error_states[key] = value
        print(f"[DEBUG] Key: {key}, Value: {value}, Manual Reset: {self.manual_resets[key]}")

    def has_red(self):
        for key, widget in self.widgets.items():
            if isinstance(widget, LEDIndicator) and widget.color == "red":
                return True
            elif isinstance(widget, ToggleSwitch) and widget._color == "red":
                return True
            elif isinstance(widget, GradientSlider) and self.slider_states.get(key, False):
                return True
        return False

    def handle_clear_state(self, widget):
        for key, w in self.widgets.items():
            if w == widget:
                label = [label for k, label in self.keys_labels if k == key][0]
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                self.chat_box.append(f"[{timestamp}] {label}: State Cleared!")
                self.error_states[key] = 0
                self.manual_resets[key] = True
      #          self.update_json_key(key, 0)
                break

    def log_to_chat(self, message):
        # Max scroll value (at bottom)
        max_scroll = self.chat_box.verticalScrollBar().maximum()
        current_scroll = self.chat_box.verticalScrollBar().value()

        if current_scroll >= max_scroll:
            # User is at bottom — auto-clear if too long
            if self.chat_box.document().blockCount() > 12:  # adjust threshold as needed
                self.chat_box.clear()

        self.chat_box.append(message)

#   def update_json_key(self, key, value):
#        try:
#            with open(json_path, 'r+') as file:
#                data = json.load(file)
#                data[str(key)] = value
#                file.seek(0)
#                json.dump(data, file, indent=4)
#                file.truncate()
#        except Exception as e:
#            print(f"[ERROR] Could not update JSON: {e}")

class GradientSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setRange(0, 100)
        self.setFixedSize(200, 30)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 10px;
                border-radius: 5px;
                background: qlineargradient(
                    x1: 0, y1: 0.5, x2: 1, y2: 0.5,
                    stop: 0 red, stop: 0.5 yellow, stop: 1 green
                );
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #666;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        self.setEnabled(False)


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


    def toggle_measure_mode(self, state):
        self.measuring_distance = state
        self.measure_points.clear()
        self.update()

    def save_clicks_to_file(self, path="click_log.json"):
        try:
            log_data = []
            for x, y in self.click_points:
                lat = self.lat_bottom + (self.lat_top - self.lat_bottom) * ((self.base_pixmap.height() - y) / self.base_pixmap.height())
                lon = self.lon_left + (self.lon_right - self.lon_left) * (x / self.base_pixmap.width())
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                log_data.append({
                    "latitude": round(lat, 6),
                    "longitude": round(lon, 6),
                    "timestamp": timestamp
                })
            with open(path, 'w') as f:
                json.dump(log_data, f, indent=4)
            print(f"[SAVED] {len(log_data)} GPS points with timestamps to {path}")
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

                # Bottom-left origin interpolation
                lat_bottom = self.dms_to_decimal(29, 33, 51)
                lat_top = self.dms_to_decimal(29, 33, 56)
                lon_left = -self.dms_to_decimal(95, 4, 56)
                lon_right = -self.dms_to_decimal(95, 4, 50)

                # Flip Y to start from bottom
                lat = lat_bottom + (lat_top - lat_bottom) * ((img_h - orig_y) / img_h)
                lon = lon_left + (lon_right - lon_left) * (orig_x / img_w)

                print(f"[CLICKED] Pixel: ({int(orig_x)}, {int(orig_y)}) → Lat/Lon: ({lat:.6f}, {lon:.6f})")

                self.click_points.append((orig_x, orig_y))
                self.save_clicks_to_file()
                self.update()

    def clear_clicks(self):
        self.click_points = []
        self.update()

    def show_point_by_index(self, index):
        if 0 <= index < len(self.points_of_interest_display):
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        label_w, label_h = self.width(), self.height()
        img_w, img_h = self.base_pixmap.width(), self.base_pixmap.height()
        scaled = self.base_pixmap.scaled(
            label_w, label_h, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        drawn_w, drawn_h = scaled.width(), scaled.height()
        offset_x = (label_w - drawn_w) // 2
        offset_y = (label_h - drawn_h) // 2

        painter.drawPixmap(offset_x, offset_y, scaled)
        if len(self.measure_points) == 2:
            x1, y1 = self.measure_points[0]
            x2, y2 = self.measure_points[1]
            sx1 = round(x1 * drawn_w / img_w) + offset_x
            sy1 = round(y1 * drawn_h / img_h) + offset_y
            sx2 = round(x2 * drawn_w / img_w) + offset_x
            sy2 = round(y2 * drawn_h / img_h) + offset_y
            painter.setPen(QColor("cyan"))
            painter.drawLine(sx1, sy1, sx2, sy2)


        # Draw task point (red)
        if self.points_of_interest_display:
            x, y = self.points_of_interest_display[0]
            scaled_x = round(x * drawn_w / img_w) + offset_x
            scaled_y = round(y * drawn_h / img_h) + offset_y
            painter.setPen(Qt.GlobalColor.red)
            painter.setBrush(Qt.GlobalColor.red)
            painter.drawEllipse(scaled_x - 5, scaled_y - 5, 10, 10)

        # Draw click points (yellow)
        painter.setPen(QColor("yellow"))
        painter.setBrush(QColor("yellow"))
        for x, y in self.click_points:
            scaled_x = round(x * drawn_w / img_w) + offset_x
            scaled_y = round(y * drawn_h / img_h) + offset_y
            painter.drawEllipse(scaled_x - 4, scaled_y - 4, 8, 8)

        painter.end()





class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.image_width = 3907
        self.image_height = 2578

        self.setWindowTitle("Wrist-Mounted System Display")
        self.setStyleSheet("background-color: black;")

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tab_labels = []
        self.blink_state = True
        self.displays = []

        tab_definitions = [
            ("EVA1 DCU", [(2, "Battery"), (3, "Oxygen"), (4, "Comm"), (5, "Fan"), (6, "Pump"), (7, "CO2")]),
            ("EVA2 DCU", [(8, "Battery"), (9, "Oxygen"), (10, "Comm"), (11, "Fan"), (12, "Pump"), (13, "CO2")]),
            ("Error Tracking", [(14, "Fan"), (15, "Oxygen"), (16, "Pump")], True),
            ("EVA1 IMU", [(17, "PosX"), (18, "PosY"), (19, "Heading")]),
            ("EVA2 IMU", [(20, "PosX"), (21, "PosY"), (22, "Heading")]),
            ("ROVER", [(20, "PosX"), (21, "PosY"), (22, "QR_ID")]),
            ("EVA1 SPEC", [(26, "SiO2"), (27, "TiO2"), (28, "Al2O3"), (29, "FeO"), (30, "MnO"),
                           (31, "MgO"), (32, "CaO"), (33, "K2O"), (35, "P2O3"), (36, "Other")]),
            ("EVA2 SPEC", [(37, "SiO2"), (38, "TiO2"), (39, "Al2O3"), (40, "FeO"), (41, "MnO"),
                           (42, "MgO"), (43, "CaO"), (44, "K2O"), (45, "P2O3"), (46, "Other")]),
            ("UIA", [(48, "EVA1 Power"), (49, "EVA1 Oxy"), (50, "EVA1 Water Supply"), (51, "EVA1 Water Waste"),
                     (52, "EVA2 Power"), (53, "EVA2 Oxy"), (54, "EVA2 Water Supply"), (55, "EVA2 Water Waste"),
                     (56, "Oxy Vent"), (57, "Depress")])
        ]

        for name, keys, *use_leds in tab_definitions:
            use_led = use_leds[0] if use_leds else False
            icon_map = {
                "EVA1 DCU": "🔋",
                "EVA2 DCU": "🔋",
                "EVA1 IMU": "🧭",
                "EVA2 IMU": "🧭",
                "ROVER": "🚙",
                "EVA1 SPEC": "🧪",
                "EVA2 SPEC": "🧪",
                "UIA": "🛰️",
                "Error Tracking": "⚠️"
            }
            icon = icon_map.get(name, "🔧")
            display = SystemStatusDisplay(f"{icon} {name} {icon}", keys, use_leds=use_led, notify_parent=self)
            self.displays.append(display)
            self.tabs.addTab(display, name)
            self.tab_labels.append(name)

        eva_telemetry_tab = self.create_eva_telemetry_tab()
        self.tabs.addTab(eva_telemetry_tab, "EVA1 TELEMETRY")
        self.tab_labels.append("EVA1 TELEMETRY")

        eva2_telemetry_tab = self.create_eva2_telemetry_tab()
        self.tabs.addTab(eva2_telemetry_tab, "EVA2 TELEMETRY")
        self.tab_labels.append("EVA2 TELEMETRY")

        eva_states_tab = self.create_eva_states_tab()
        self.tabs.addTab(eva_states_tab, "EVA States")
        self.tab_labels.append("EVA States")

        rock_yard_map_tab = self.create_rock_yard_map_tab()
        self.tabs.addTab(rock_yard_map_tab, "Rock Yard Map")
        self.tab_labels.append("Rock Yard Map")

        self.layout.addWidget(self.tabs)

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.update_blinking_tabs)
        self.blink_timer.start(500)
   
    def grid_to_pixel(self, col, row):
        left_padding = 243
        right_padding = 272
        top_padding = 180
        bottom_padding = 151

        usable_width = self.image_width - left_padding - right_padding  # 3392
        usable_height = self.image_height - top_padding - bottom_padding  # 2247

        cell_w = usable_width / 22
        cell_h = usable_height / 14

        x = left_padding + col * cell_w + cell_w / 2
        y = top_padding + row * cell_h + cell_h / 2

        return int(x), int(y)


    def create_eva_telemetry_tab(self):
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        sub_tabs = QTabWidget()
        sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid white;
                border-radius: 10px;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                font-size: 12px;
                background: #333;
                color: white;
                padding: 8px;
                border: 1px solid white;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 120px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #555;
                color: yellow;
            }
        """)

        eva1_display = SystemStatusDisplay("📡 EVA1 TELEMETRY-1 📡", [
            (59, "Batt Time Left"),
            (60, "Oxy Pri Storage"),
            (61, "Oxy Sec Storage"),
            (62, "Oxy Pri Pressure"),
            (63, "Oxy Sec Pressure"),
            (64, "Oxy Time Left"),
            (65, "Heart Rate"),
            (66, "Oxy Consumption")
        ])
        sub_tabs.addTab(eva1_display, "EVA1 TELEMETRY-1")
        self.displays.append(eva1_display)
        self.tab_labels.append("EVA1 TELEMETRY")

        eva2_display = SystemStatusDisplay("📡 EVA1 TELEMETRY-2 📡", [
            (67, "CO2 Production"),
            (68, "Suit Pressure Oxy"),
            (69, "Suit Pressure CO2"),
            (70, "Suit Pressure Other"),
            (71, "Suit Pressure Total"),
            (72, "Fan Pri RPM"),
            (73, "Fan Sec RPM")
        ])
        sub_tabs.addTab(eva2_display, "EVA1 TELEMETRY-2")
        self.displays.append(eva2_display)
        self.tab_labels.append("EVA2 TELEMETRY")

        eva3_display = SystemStatusDisplay("📡 EVA TELEMETRY-3 📡", [
            (74, "Helmet Pressure CO2"),
            (75, "Scrubber A CO2 Storage"),
            (76, "Scrubber B CO2 Storage"),
            (77, "Temperature"),
            (78, "Coolant mL"),
            (79, "Coolant Gas Pressure"),
            (80, "Coolant Liquid Pressure")
        ])
        sub_tabs.addTab(eva3_display, "EVA TELEMETRY-3")
        self.displays.append(eva3_display)
        self.tab_labels.append("EVA TELEMETRY-3")

        layout.addWidget(sub_tabs)
        return container

    def create_eva2_telemetry_tab(self):
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        sub_tabs = QTabWidget()
        sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid white;
                border-radius: 10px;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background: #333;
                color: white;
                padding: 8px;
                border: 1px solid white;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 120px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #555;
                color: yellow;
            }
        """)

        eva1_display = SystemStatusDisplay("📡 EVA2 TELEMETRY-1 📡", [
            (81, "Batt Time Left"),
            (82, "Oxy Pri Storage"),
            (83, "Oxy Sec Storage"),
            (84, "Oxy Pri Pressure"),
            (85, "Oxy Sec Pressure"),
            (86, "Oxy Time Left"),
            (87, "Heart Rate"),
            (88, "Oxy Consumption")
        ])
        sub_tabs.addTab(eva1_display, "EVA2 TELEMETRY-1")
        self.displays.append((eva1_display, sub_tabs))
        self.tab_labels.append("EVA2 TELEMETRY-1")

        eva2_display = SystemStatusDisplay("📡 EVA2 TELEMETRY-2 📡", [
            (89, "CO2 Production"),
            (90, "Suit Pressure Oxy"),
            (91, "Suit Pressure CO2"),
            (92, "Suit Pressure Other"),
            (93, "Suit Pressure Total"),
            (94, "Fan Pri RPM"),
            (95, "Fan Sec RPM")
        ])
        sub_tabs.addTab(eva2_display, "EVA2 TELEMETRY-2")
        self.displays.append((eva2_display, sub_tabs))
        self.tab_labels.append("EVA2 TELEMETRY-2")

        eva3_display = SystemStatusDisplay("📡 EVA TELEMETRY-3 📡", [
            (96, "Helmet Pressure CO2"),
            (97, "Scrubber A CO2 Storage"),
            (98, "Scrubber B CO2 Storage"),
            (99, "Temperature"),
            (100, "Coolant mL"),
            (101, "Coolant Gas Pressure"),
            (102, "Coolant Liquid Pressure")
        ])
        sub_tabs.addTab(eva3_display, "EVA TELEMETRY-3")
        self.displays.append((eva3_display, sub_tabs))
        self.tab_labels.append("EVA2 TELEMETRY-3")

        layout.addWidget(sub_tabs)
        return container

    def create_eva_states_tab(self):
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        sub_tabs = QTabWidget()
        sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid white;
                border-radius: 10px;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                font-size: 12px;
                background: #333;
                color: white;
                padding: 8px;
                border: 1px solid white;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 120px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #555;
                color: yellow;
            }
        """)

        state1 = SystemStatusDisplay("📡 EVA STATES - 1 📡", [
            (103, "EVA-Started"), (104, "EVA-Paused"), (105, "EVA-Completed"),
            (106, "EVA-Total_time"), (107, "UIA-Started"), (108, "UIA-completed"),
            (109, "UIA-Time"), (110, "DCU-Started")
        ])
        sub_tabs.addTab(state1, "EVA STATES-1")
        self.displays.append(state1)
        self.tab_labels.append("EVA STATES-1")

        state2 = SystemStatusDisplay("📡 EVA STATES - 2 📡", [
            (111, "DCU-completed"), (112, "DCU-Time"), (113, "Rover-Started"),
            (114, "Rover-completed"), (115, "Rover-Time"), (116, "Spec-Started"),
            (117, "Spec-completed"), (118, "Spec-Time")
        ])
        sub_tabs.addTab(state2, "EVA STATES-2")
        self.displays.append(state2)
        self.tab_labels.append("EVA STATES-2")

        layout.addWidget(sub_tabs)
        return container

    def check_tab_statuses(self):
        pass

    def update_blinking_tabs(self):
        tab_bar = self.tabs.tabBar()
        self.blink_state = not self.blink_state

        for i in range(self.tabs.count()):
            tab_widget = self.tabs.widget(i)
            has_red = False

            # Look for nested QTabWidget inside the tab
            sub_tab_widget = tab_widget.findChild(QTabWidget)
            if sub_tab_widget:
                for j in range(sub_tab_widget.count()):
                    sub_widget = sub_tab_widget.widget(j)
                    if isinstance(sub_widget, SystemStatusDisplay) and sub_widget.has_red():
                        has_red = True
                        break
            elif isinstance(tab_widget, SystemStatusDisplay):
                has_red = tab_widget.has_red()
                has_red = tab_widget.has_red()

            if has_red:
                color = QColor("red") if self.blink_state else QColor("white")
            else:
                color = QColor("white")

            tab_bar.setTabTextColor(i, color)

    def create_rock_yard_map_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container)

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            print("[ERROR] Image failed to load")
        else:
            print(f"[INFO] Loaded image: {pixmap.width()} x {pixmap.height()}")

        self.image_label = MapLabel(pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        measure_toggle = QPushButton("Measure Distance")
        measure_toggle.setCheckable(True)
        measure_toggle.setStyleSheet("font-size: 16px; background-color: navy; color: white; border-radius: 8px; padding: 8px;")
        measure_toggle.clicked.connect(lambda: self.image_label.toggle_measure_mode(measure_toggle.isChecked()))
        layout.addWidget(measure_toggle)


        layout.addWidget(self.image_label)
        # Clear Clicks Button
        clear_button = QPushButton("Clear")
        clear_button.setStyleSheet("font-size: 16px; background-color: red; color: white; border-radius: 8px; padding: 8px;")

        def clear_clicks():
            self.image_label.clear_clicks()
            print("[INFO] Click points cleared")

        clear_button.clicked.connect(clear_clicks)
        layout.addWidget(clear_button)


        container.setLayout(layout)
        return container


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    window.setMinimumSize(800, 600)
    window.setMaximumSize(1920, 1080) 
    sys.exit(app.exec())
