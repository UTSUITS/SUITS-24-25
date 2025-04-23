## Code V6, modified 04/22/2025

# Libraries used
import socket
import struct
import time
import logging
import redis 

import sys
import json
import time
from PyQt6.QtWidgets import (
    QSizePolicy,
    QApplication, QWidget, QLabel, QProgressBar, QVBoxLayout, QTextEdit,
    QHBoxLayout, QPushButton, QTabWidget, QFrame, QGraphicsDropShadowEffect

)

from PyQt6.QtWidgets import QProgressBar
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush
from PyQt6.QtCore import Qt, QTimer, QSize, QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QSlider
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from threading import Thread, Lock

rd=redis.Redis(host='localhost', port=6379,db=0)

# Load telemetry range data from a JSON file and store in a map
#json_path = r"C:\\output_results.json"
image_path = r"/home/utsuits/Documents/SUITS-24-25/rockYardMap-min.png"
Telemetry_path = r"/home/utsuits/Documents/SUITS-24-25/EVA_Telemetry_Commands_Capacity_Ranges.json"

try:
    with open(Telemetry_path, 'r') as f:
        telemetry_ranges = json.load(f)
    TELEMETRY_RANGE_MAP = {entry["Command_Num"]: (entry["Min"], entry["Max"]) for entry in telemetry_ranges}
except Exception as e:
    print(f"[ERROR] Could not load telemetry ranges: {e}")
    TELEMETRY_RANGE_MAP = {}

# Maps telemetry command numbers to their display units
UNIT_MAP = {
    59: "sec",  64: "sec",
    60: "%",    61: "%",    62: "psi", 63: "psi",
    65: "BPM",  66: "L/min",
    67: "L/min",
    68: "psi",  69: "psi",  70: "psi", 71: "psi",
    72: "RPM",  73: "RPM",
    74: "psi",  75: "%",    76: "%",
    77: "°F",   78: "mL",
    79: "psi",  80: "psi",
    81: "sec",  82: "%",    83: "%",   84: "psi", 85: "psi",
    86: "sec",  87: "BPM",  88: "L/min",
    89: "L/min", 90: "psi", 91: "psi", 92: "psi", 93: "psi",
    94: "RPM",  95: "RPM",  96: "psi",
    97: "%",    98: "%",    99: "°F", 100: "mL", 101: "psi", 102: "psi"
}

# Configure logging to file
logging.basicConfig(
    filename="server_commands.log",
    level=logging.INFO,
    format="%(asctime)s - Command %(command)d - Value: %(value)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Create a custom logger for server polling
logger = logging.getLogger("server_logger")

class ToggleSwitch(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setEnabled(False)
        self.setFixedSize(80, 40)
        self._color = "red"
        self.setStyleSheet("background: transparent; border: none;")
        #self.clicked.connect(self.on_click)

    # Custom toggle switch button that reflects telemetry state (red/green)
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

# Circular LED-style indicator with optional blinking effect
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

    # Alternate visibility when blinking is active
    def toggle_blink(self):
        if self.blink:
            self.blink_state = not self.blink_state
            self.setVisible(self.blink_state)

    # Update the LED fill based on current color state
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

# Display the widgets in the command window
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

        # Create title labe;
        title = QLabel(self.title_text)
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white;")
        self.layout.addWidget(title)

        # Build row layouts for buttons/sliders (4 per row)
        buttons_per_row = 4  # Adjusted layout alignment for toggle buttons
        row_layouts = []
        for _ in range((len(keys_labels) + buttons_per_row - 1) // buttons_per_row):
            row = QHBoxLayout()
            row.setSpacing(40)
            row_layouts.append(row)

        # Create widget (slider or toggle/LED) for each telemetry key
        for idx, (key, label_text) in enumerate(keys_labels):
            if (key in range(59, 103) or self.title_text.startswith("🧪")) and not use_leds:
                min_val, max_val = TELEMETRY_RANGE_MAP.get(key, (0, 100))
                unit = UNIT_MAP.get(key, "")
                widget = GradientSlider(min_val, max_val, scale=1, unit=unit)
            else:
                widget = LEDIndicator(label_text) if use_leds else ToggleSwitch()
            self.widgets[key] = widget
            widget_box = self.create_labeled_widget(key, label_text, widget)
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

        # Timer for polling data and refreshing display
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1000)

    # Creates vertical layout with a label and the widget below it
    def create_labeled_widget(self, key, label_text, widget):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(label)

        layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)

        return container

    # Reads from JSON file (normally overridden by live UDP in actual use)
    def read_json(self):
        try:
            with open(json_path, 'r') as file:
                return json.load(file)
        except Exception:
            return None

    # Called by timer to refresh telemetry values and update UI
    def refresh_data(self):
        data = self.read_json()
        if data:
            for key, label in self.keys_labels:
                value = data.get(str(key))
                if value is not None and value != self.error_states[key]:
                    self.update_status(key, label, value)
            if self.notify_parent:
                self.notify_parent.check_tab_statuses()

    # Updates the color or value of the corresponding widget
    def update_status(self, key, label, value):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        widget = self.widgets[key]

        if isinstance(widget, GradientSlider):
            widget.set_actual_value(float(value))
            self.slider_states[key] = (int(value) == 0)
            self.chat_box.append(f"[{timestamp}] {label}: {value}")
            return

        if self.use_leds:
            if value == 1:
                widget.set_color("green")
                self.log_to_chat(f"[{timestamp}] {label} Error Detected!")
             #   self.chat_box.append(f"[{timestamp}] {label} Error Detected!")
            elif value == 0:
                widget.set_color("red")
                self.chat_box.append(f"[{timestamp}] {label} :- OK")
            else:
                widget.set_color("gray")
                self.chat_box.append(f"[{timestamp}] {label} Unknown State")
        else:
            # Always follow telemetry data for non-LEDs
            if value == 1:
                widget.set_color("green")
                self.chat_box.append(f"[{timestamp}] -> {label} Sensor On ✅")
                self.manual_resets[key] = True
            elif value == 0:
                widget.set_color("red")
                self.log_to_chat(f"[{timestamp}] -> {label} Sensor Off ⛔")
               # self.chat_box.append(f"[{timestamp}] -> {label} Sensor Off ⛔")
                self.manual_resets[key] = False

        self.error_states[key] = value
        print(f"[DEBUG] Key: {key}, Value: {value}, Manual Reset: {self.manual_resets[key]}")

    # Checks if any widget is in a red/error state
    def has_red(self):
        for key, widget in self.widgets.items():
            if isinstance(widget, LEDIndicator) and widget.color == "red":
                return True
            elif isinstance(widget, ToggleSwitch) and widget._color == "red":
                return True
            elif isinstance(widget, GradientSlider) and self.slider_states.get(key, False):
                return True
        return False

    # Clears the state for a manually reset widget and logs the action
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

    # Appends message to chatbox with red highlight if error
    def log_to_chat(self, message):
        # Max scroll value (at bottom)
        max_scroll = self.chat_box.verticalScrollBar().maximum()
        current_scroll = self.chat_box.verticalScrollBar().value()

        if current_scroll >= max_scroll:
            # User is at bottom — auto-clear if too long
            if self.chat_box.document().blockCount() > 12:  # adjust threshold as needed
                self.chat_box.clear()

        ## Modified code 20250409
        if "Off" in message or "⛔" in message:
            self.chat_box.setTextColor(QColor("red"))
        else:
            self.chat_box.setTextColor(QColor("white"))

        self.chat_box.append(message)
        self.chat_box.setTextColor(QColor("white"))  # Reset to default


class GradientSlider(QWidget):
    def __init__(self, min_val=0, max_val=100, scale=1, unit="", parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.scale = scale
        self.unit = unit

        # Create horizontal slider (disabled for display only)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(int(min_val * scale), int(max_val * scale))
        self.slider.setEnabled(False)
        self.slider.setFixedSize(200, 30)

        # Set slider with gradient coloring (red → yellow → green)
        self.slider.setStyleSheet("""
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

        # Label for showing value next to the slider
        self.value_label = QLabel("")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("color: lightgreen; font-size: 14px;")

        # Min/max labels under the slider
        self.min_label = QLabel(f"{min_val}")
        self.max_label = QLabel(f"{max_val}")
        self.min_label.setStyleSheet("color: gray; font-size: 10px;")
        self.max_label.setStyleSheet("color: gray; font-size: 10px;")

        # Min/Max layout directly under slider with tight vertical spacing
        minmax_layout = QHBoxLayout()
        minmax_layout.setContentsMargins(5, 0, 5, 0)  # Tighten up
        minmax_layout.setSpacing(0)
        minmax_layout.addWidget(self.min_label, alignment=Qt.AlignmentFlag.AlignLeft)
        minmax_layout.addWidget(self.max_label, alignment=Qt.AlignmentFlag.AlignRight)

        # Combine all layout parts vertically
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)  # Pull min/max closer to slider
        layout.addWidget(self.slider, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(minmax_layout)
        layout.addWidget(self.value_label)

    # Clamp value and update slider position and label
    def set_actual_value(self, value):
        value = max(self.min_val, min(self.max_val, value))
        self.slider.setValue(int(value * self.scale))

        if value == int(value):
            display = f"{int(value)} {self.unit}"
        else:
            display = f"{value:.2f} {self.unit}"

        self.value_label.setText(display)
        self.setToolTip(display)

class PieChartWidget(QWidget):
    def __init__(self, values, labels, title, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: black;")
        self.values = values
        self.labels = labels
        self.analysis_running = False

        layout = QVBoxLayout(self)

        # Initialize Matplotlib figure
        self.fig = Figure(figsize=(7, 5.5), facecolor="black")
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # Label above the pie chart that blinks while analyzing
        self.blink_label = QLabel("Analyzing Rock Composition")
        self.blink_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.blink_label.setStyleSheet("color: yellow; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.blink_label)

        # Create Progress bar under the chart and animated it
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid gray;
                border-radius: 8px;
                text-align: center;
                color: black;
                font-weight: bold;
                background-color: #222;
            }
            QProgressBar::chunk {
                background-color: #f1c40f;   
                width: 20px;
            }
        """)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        # Timers for blinking and progress bar animation
        self.blink_state = True
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_blink)

        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_value = 0
        self.pending_values = self.values.copy()

        # Initial chart rendering
        self.draw_pie(show_labels=True)

    # Makes the analysis label blink
    def toggle_blink(self):
        self.blink_state = not self.blink_state
        self.blink_label.setVisible(self.blink_state)

    # Starts progress bar animation and updates chart after it completes if new_values
    def start_analysis(self, new_values):
        if new_values != self.values and not self.analysis_running:
            self.pending_values = new_values
            self.progress_value = 0
            self.progress.setValue(0)
            self.analysis_running = True

            self.blink_label.setText("Analyzing Rock Composition")
            self.blink_label.setStyleSheet("color: yellow; font-size: 16px; font-weight: bold;")
            self.blink_label.setVisible(True)

            self.blink_timer.start(500)
            self.progress_timer.start(20)
            self.draw_pie(show_labels=False)

    # Called repeatedly by timer to increment progress
    def update_progress(self):
        if self.progress_value < 100:
            self.progress_value += 1
            self.progress.setValue(self.progress_value)

        if self.progress_value >= 100 and self.analysis_running:
            self.progress_timer.stop()
            self.blink_timer.stop()
            self.analysis_running = False

            self.blink_label.setText("Rock Composition Analysis Complete !")
            self.blink_label.setStyleSheet("color: Lightgreen; font-size: 16px; font-weight: bold;")
            self.blink_label.setVisible(True)

            self.values = self.pending_values.copy()
            self.draw_pie(show_labels=True)

    # Renders the pie chart with or without value labels
    def draw_pie(self, show_labels=True):
        self.ax.clear()
        display_values = [v if v > 0 else 0.001 for v in self.values]
        total = sum(display_values)

        wedges, _ = self.ax.pie(
            display_values,
            startangle=90,
            radius=1.0,
            wedgeprops=dict(width=1.0)
        )

        left_labels = []
        right_labels = []

        if show_labels:
            for i, wedge in enumerate(wedges):
                angle = (wedge.theta2 + wedge.theta1) / 2
                theta_rad = np.deg2rad(angle)
                x = np.cos(theta_rad)
                y = np.sin(theta_rad)
                value = self.values[i]

                if value > total * 0.05:
                    self.ax.text(x * 0.6, y * 0.6, f"{value:.2f}", ha='center', va='center',
                                 fontsize=10, color='white')
                else:
                    label_data = {"value": f"{value:.2f}", "x": x, "y": y}
                    (right_labels if x >= 0 else left_labels).append(label_data)

            self.place_side_labels(left_labels, "left")
            self.place_side_labels(right_labels, "right")

        self.ax.legend(
            wedges,
            [f"{label} ({self.values[i]:.2f})" for i, label in enumerate(self.labels)],
            loc='upper center',
            bbox_to_anchor=(0.5, 1.20),  # ✅ moves legend higher
            ncol=5,
            labelcolor='white',
            fontsize=10,
            frameon=False
        )

        self.ax.set_title("")
        self.ax.set_facecolor("black")
        self.fig.subplots_adjust(top=0.85)
        self.canvas.draw()

    # Draws value annotations on left/right sides outside the pie
    def place_side_labels(self, labels, side):
        labels.sort(key=lambda d: d["y"])
        spacing = 0.15
        start_y = -spacing * (len(labels) - 1) / 2

        for idx, item in enumerate(labels):
            label_y = start_y + idx * spacing
            label_x = 1.4 if side == "right" else -1.4
            anchor_x = item["x"] * 0.9
            anchor_y = item["y"] * 0.9
            ha = "left" if side == "right" else "right"

            self.ax.annotate(
                item["value"],
                xy=(anchor_x, anchor_y),
                xytext=(label_x, label_y),
                ha=ha, va="center",
                fontsize=9,
                color="white",
                arrowprops=dict(arrowstyle='-', lw=1, color='gray')
            )

class PieChartDisplay(QWidget):
    def __init__(self, title_text, keys_labels):
        super().__init__()
        self.title_text = title_text
        self.keys_labels = keys_labels
        self.labels = [label for _, label in keys_labels]
        self.values = [0.0 for _ in keys_labels]
        self.key_to_index = {key: i for i, (key, _) in enumerate(keys_labels)}

        self.layout = QVBoxLayout(self)

        # Add the section title
        title = QLabel(title_text)
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white;")
        self.layout.addWidget(title)

        # Create and add the pie chart widget
        clean_title = title_text.replace("🧪", "").strip()
        self.chart = PieChartWidget(self.values, self.labels, clean_title)
        self.layout.addWidget(self.chart)

        # Timer to poll new data values and update the pie chart
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_values)
        self.timer.start(1000)

    # Reads the latest telemetry values and updates the pie chart if any value changed
    def update_values(self):
        data = SystemStatusDisplay.read_json(self)
        new_values = [0.0 for _ in self.values]
        changed = False

        for key, idx in self.key_to_index.items():
            raw_val = data.get(str(key))
            if raw_val is not None:
                try:
                    new_val = float(raw_val)
                    new_values[idx] = new_val
                    if abs(new_val - self.values[idx]) > 1e-3:  # 🧠 small threshold to detect change
                        changed = True
                except:
                    pass

        if changed:
            self.chart.start_analysis(new_values)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set window title and fixed size
        self.setWindowTitle("Wrist-Mounted System Display")
        self.setGeometry(100, 100, 1024, 600)
        self.setFixedSize(1100, 600)
        self.setStyleSheet("background-color: black;")

        # Main layout and tab widget
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # Initialize various instance variables
        self.tab_labels = []
        self.blink_state = True
        self.displays = []

        # Define all tab names and associated telemetry keys
        tab_definitions = [
            ("EVA1 DCU", [(2, "Battery"), (3, "Oxygen"), (4, "Comm"), (5, "Fan"), (6, "Pump"), (7, "CO2")]),
            ("EVA2 DCU", [(8, "Battery"), (9, "Oxygen"), (10, "Comm"), (11, "Fan"), (12, "Pump"), (13, "CO2")]),
            ("Error Tracking", [(14, "Fan"), (15, "Oxygen"), (16, "Pump")], True),
            ("EVA1 IMU", [(17, "PosX"), (18, "PosY"), (19, "Heading")]),
            ("EVA2 IMU", [(20, "PosX"), (21, "PosY"), (22, "Heading")]),
            ("ROVER", [(20, "PosX"), (21, "PosY"), (22, "QR_ID")]),
            ("EVA1 SPEC", [(27, "SiO2"), (28, "TiO2"), (29, "Al2O3"), (309, "FeO"), (31, "MnO"),
                           (32, "MgO"), (33, "CaO"), (34, "K2O"), (35, "P2O3"), (36, "Other")]),
            ("EVA2 SPEC", [(38, "SiO2"), (39, "TiO2"), (40, "Al2O3"), (41, "FeO"), (42, "MnO"),
                           (43, "MgO"), (44, "CaO"), (45, "K2O"), (46, "P2O3"), (47, "Other")]),
            ("UIA", [(48, "EVA1 Power"), (49, "EVA1 Oxy"), (50, "EVA1 Water Supply"), (51, "EVA1 Water Waste"),
                     (52, "EVA2 Power"), (53, "EVA2 Oxy"), (54, "EVA2 Water Supply"), (55, "EVA2 Water Waste"),
                     (56, "Oxy Vent"), (57, "Depress")])
        ]

        # Loop through all tab definitions and create appropriate tabs
        for name, keys, *use_leds in tab_definitions:
            use_led = use_leds[0] if use_leds else False

            ##Added code - V3 20250409
            # Lock EVA1 IMU, EVA2 IMU, and ROVER tabs for now
            if name in ["EVA1 IMU", "EVA2 IMU", "ROVER"]:
                access_denied = QLabel("🚫 Access Denied")
                access_denied.setAlignment(Qt.AlignmentFlag.AlignCenter)
                access_denied.setStyleSheet("color: red; font-size: 28px; font-weight: bold;")
                self.tabs.addTab(access_denied, name)
                self.tab_labels.append(name)
                continue

            # Make EVA1 SPEC and EVA2 SPEC use DonutChart - modified 20250414
            if name in ["EVA1 SPEC", "EVA2 SPEC"]:
                display = PieChartDisplay(f"🧪 {name} 🧪", keys)
                self.displays.append(display)
                self.tabs.addTab(display, name)
                self.tab_labels.append(name)
                continue

            # Map tab names to emoji icons
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

            # Use generic system status display for remaining tabs
            display = SystemStatusDisplay(f"{icon} {name} {icon}", keys, use_leds=use_led, notify_parent=self)
            self.displays.append(display)
            self.tabs.addTab(display, name)
            self.tab_labels.append(name)

        # Add custom telemetry tab for EVA1
        eva_telemetry_tab = self.create_eva_telemetry_tab()
        self.tabs.addTab(eva_telemetry_tab, "EVA1 TELEMETRY")
        self.tab_labels.append("EVA1 TELEMETRY")

        # Add custom telemetry tab for EVA2
        eva2_telemetry_tab = self.create_eva2_telemetry_tab()
        self.tabs.addTab(eva2_telemetry_tab, "EVA2 TELEMETRY")
        self.tab_labels.append("EVA2 TELEMETRY")

        # Add EVA state indicator tab
        eva_states_tab = self.create_eva_states_tab()
        self.tabs.addTab(eva_states_tab, "EVA States")
        self.tab_labels.append("EVA States")

        # Add map display tab
        rock_yard_map_tab = self.create_rock_yard_map_tab()
        self.tabs.addTab(rock_yard_map_tab, "Rock Yard Map")
        self.tab_labels.append("Rock Yard Map")

        # Finalize layout
        self.layout.addWidget(self.tabs)

        # Timer to update blinking tab states periodically
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.update_blinking_tabs)
        self.blink_timer.start(300)

    # Container widget for EVA telemetry sub-tabs
    def create_eva_telemetry_tab(self):
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Sub-tabs widget with custom styles
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

        # First telemetry sub-tab
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

        # Second telemetry sub-tab
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

        # Third telemetry sub-tab
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

        # Add sub-tabs to main telemetry layout
        layout.addWidget(sub_tabs)
        return container

    # Create main container widget and layout for EVA2 telemetry tab
    def create_eva2_telemetry_tab(self):
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Create sub-tabs widget for organizing telemetry data
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

        # First telemetry sub-tab for EVA2
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

        # Second telemetry sub-tab for EVA2
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

        # Third telemetry sub-tab for EVA2
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

        # Add all sub-tabs to main layout
        layout.addWidget(sub_tabs)
        return container

    # Create container and layout for EVA state tracking tab
    def create_eva_states_tab(self):
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Sub-tabs for organizing state displays
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

        # First EVA states sub-tab (DCU/UIA related states)
        state1 = SystemStatusDisplay("📡 EVA STATES - 1 📡", [
            (103, "EVA-Started"), (104, "EVA-Paused"), (105, "EVA-Completed"),
            (106, "EVA-Total_time"), (107, "UIA-Started"), (108, "UIA-completed"),
            (109, "UIA-Time"), (110, "DCU-Started")
        ])
        sub_tabs.addTab(state1, "EVA STATES-1")
        self.displays.append(state1)
        self.tab_labels.append("EVA STATES-1")

        # Second EVA states sub-tab (Rover and Spec activity states)
        state2 = SystemStatusDisplay("📡 EVA STATES - 2 📡", [
            (111, "DCU-completed"), (112, "DCU-Time"), (113, "Rover-Started"),
            (114, "Rover-completed"), (115, "Rover-Time"), (116, "Spec-Started"),
            (117, "Spec-completed"), (118, "Spec-Time")
        ])
        sub_tabs.addTab(state2, "EVA STATES-2")
        self.displays.append(state2)
        self.tab_labels.append("EVA STATES-2")

        # Add state tracking sub-tabs to layout
        layout.addWidget(sub_tabs)
        return container

    # Placeholder method to check tab statuses - consider removing in final code
    def check_tab_statuses(self):
        pass

    # Blink tab text red/white if error (e.g., a red LED) is present, else keep text white
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
            # Check top-level tab for red LED
            elif isinstance(tab_widget, SystemStatusDisplay):
                has_red = tab_widget.has_red()
                has_red = tab_widget.has_red()

            # If red status detected, alternate tab text color
            if has_red:
                color = QColor("red") if self.blink_state else QColor("white")
            else:
                color = QColor("white")

            # Apply the color to the tab label
            tab_bar.setTabTextColor(i, color)

    # Create tab with rock yard image map - no functionality as of yet
    def create_rock_yard_map_tab(self):
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(image_path)

        # Load and scale the image if available
        if not pixmap.isNull():
            image_label.setPixmap(pixmap.scaled(900, 550, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            # Display error message if image fails to load
            image_label.setText("⚠️ Rock Yard Map failed to load.")
            print(f"[WARNING] Failed to load rock yard map: {image_path}")

        layout.addWidget(image_label)
        return container

# Shared dictionary for data
shared_results = {}

# Thread-safe lock
results_lock = Lock()

# Polls Redis for the most recent complete second's data
def redis_polling_loop():
    while True:
        try:
            current_epoch = int(time.time())
            data = rd.get(str(current_epoch))

            # If no data is present yet, try one second behind
            if data is None:
                data = rd.get(str(current_epoch - 1))

            if data is not None:
                parsed = json.loads(data)

                # Replace None with 0 for display safety (optional)
                cleaned = {int(k): (v if v is not None else 0) for k, v in parsed.items()}

                # Update the global shared_results dictionary safely
                with results_lock:
                    shared_results.clear()
                    shared_results.update(cleaned)

        except Exception as e:
            print(f"[REDIS ERROR] Failed to get data: {e}")

        time.sleep(1)

# Override read_json to pull from Redis-fueled shared_results
def read_from_redis(self):
    with results_lock:
        return {str(k): v for k, v in shared_results.items()}

# Bind new read function to your display class
SystemStatusDisplay.read_json = read_from_redis

# Main driver program
if __name__ == "__main__":
    redis_thread = Thread(target=redis_polling_loop, daemon=True)
    redis_thread.start() 

    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())

