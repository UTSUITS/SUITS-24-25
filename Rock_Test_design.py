from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar,
    QHBoxLayout, QGroupBox, QPushButton, QGraphicsOpacityEffect,
    QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush
import sys
import random
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Map of command IDs to element names
eva1_commands = {
    27: "SiO2", 28: "TiO2", 29: "Al2O3", 30: "FeO", 31: "MnO",
    32: "MgO", 33: "CaO", 34: "K2O", 35: "P2O3", 36: "Other"
}

eva2_commands = {
    38: "SiO2", 39: "TiO2", 40: "Al2O3", 41: "FeO", 42: "MnO",
    43: "MgO", 44: "CaO", 45: "K2O", 46: "P2O3", 47: "Other"
}

class RockImageProgress(QWidget):
    def __init__(self, label_text):
        super().__init__()
        self.setFixedSize(256, 200)  # Adjusted to fit on the right of progress bars
        self.label_text = label_text

        self.background = QPixmap("C:/Users/jerem/SUITS-24-25/Rock.png")
        if self.background.isNull():
            self.background = QPixmap(256, 200)
            self.background.fill(QColor("gray"))

        self.progress = 0

    def set_progress(self, percent):
        self.progress = percent
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        scaled_bg = self.background.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x_offset = (self.width() - scaled_bg.width()) // 2
        y_offset = (self.height() - scaled_bg.height()) // 2
        painter.drawPixmap(x_offset, y_offset, scaled_bg)

        mask_width = int((self.progress / 100.0) * scaled_bg.width())
        painter.setBrush(QBrush(QColor(0, 255, 0, 120)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(x_offset, y_offset, mask_width, scaled_bg.height())

        # Draw the EVA label
        painter.setPen(QColor("white"))
        painter.drawText(10, 20, self.label_text)
        painter.end()

class RockScanner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wrist-Mounted System Display")
        self.setGeometry(100, 100, 1024, 600)
        self.setFixedSize(1024, 600)
        self.setStyleSheet("""
            background-color: black;
            QLabel { font-size: 14px; color: white; }
            QProgressBar { height: 16px; border-radius: 8px; }
            QPushButton {
                font-size: 14px;
                padding: 6px;
                background-color: #333;
                color: white;
                border: 1px solid gray;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
                color: black;
            }
            QComboBox {
                font-size: 14px;
                padding: 4px;
                border: 1px solid gray;
                border-radius: 6px;
                background-color: #222;
                color: white;
            }
            QComboBox:hover {
                border: 1px solid #2ecc71;
                color: #2ecc71;
            }
        """)

        self.layout = QVBoxLayout(self)

        # Progress bars layout
        progress_layout = QVBoxLayout()

        self.eva1_scan_bar = QProgressBar()
        self.eva1_scan_bar.setRange(0, 100)
        self.eva1_scan_bar.setFormat("Scanning EVA 1: %p%")
        progress_layout.addWidget(self.eva1_scan_bar)

        self.eva2_scan_bar = QProgressBar()
        self.eva2_scan_bar.setRange(0, 100)
        self.eva2_scan_bar.setFormat("Scanning EVA 2: %p%")
        progress_layout.addWidget(self.eva2_scan_bar)

        # Start scan button
        self.start_button = QPushButton("Start New Scan")
        self.start_button.clicked.connect(self.fade_out_start_scan)
        progress_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Rock images and scan bars in horizontal layout
        layout = QHBoxLayout()

        self.eva1_bars = self.create_scan_group("EVA 1 Rock Composition", eva1_commands)
        self.eva2_bars = self.create_scan_group("EVA 2 Rock Composition", eva2_commands)

        # Initialize the rock images for EVA 1 and EVA 2
        self.eva1_image = RockImageProgress("EVA 1 Rock")
        self.eva2_image = RockImageProgress("EVA 2 Rock")

        layout.addLayout(progress_layout)
        layout.addWidget(self.eva1_image)
        layout.addWidget(self.eva2_image)

        self.layout.addLayout(layout)

        # Create the chart
        self.chart = Figure()
        self.canvas = FigureCanvas(self.chart)
        self.layout.addWidget(self.canvas)

        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.simulate_scan_progress)

        self.server_timer = QTimer()
        self.server_timer.timeout.connect(self.simulate_server_update)

        self.fade_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.fade_effect)

        self.start_scan()

    def create_scan_group(self, title, commands):
        group = QGroupBox(title)
        group.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; color: white; border: 1px solid gray; border-radius: 6px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }")
        vbox = QVBoxLayout()
        bars = {}

        for cmd_id, label in commands.items():
            hbox = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(True)
            bar.setFormat("%p%")
            hbox.addWidget(lbl)
            hbox.addWidget(bar)
            vbox.addLayout(hbox)
            bars[cmd_id] = bar

        group.setLayout(vbox)
        return {"group": group, "bars": bars}

    def update_from_server_data(self, server_data):
        eva1_values = {}
        for cmd_id, value in server_data.items():
            if cmd_id in self.eva1_bars["bars"]:
                self.eva1_bars["bars"][cmd_id].setValue(int(value))
                self.eva1_bars["bars"][cmd_id].setFormat(f"{value:.1f} %")
                eva1_values[eva1_commands[cmd_id]] = value
            elif cmd_id in self.eva2_bars["bars"]:
                self.eva2_bars["bars"][cmd_id].setValue(int(value))
                self.eva2_bars["bars"][cmd_id].setFormat(f"{value:.1f} %")

        self.draw_pie_chart(eva1_values)

    def draw_pie_chart(self, data):
        self.chart.clear()
        ax = self.chart.add_subplot(111)
        if data:
            labels = list(data.keys())
            sizes = list(data.values())
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', textprops={'color': 'white'})
            ax.set_title("EVA 1 Rock Composition", color='white')
            self.chart.set_facecolor("black")
            ax.set_facecolor("black")
        self.canvas.draw()

    def simulate_server_update(self):
        server_data = {cmd: random.uniform(0, 100) for cmd in list(eva1_commands.keys()) + list(eva2_commands.keys())}
        self.update_from_server_data(server_data)

    def start_scan(self):
        self.scan_progress = 0
        self.eva1_scan_bar.setValue(0)
        self.eva2_scan_bar.setValue(0)
        self.eva1_image.set_progress(0)
        self.eva2_image.set_progress(0)
        self.scan_timer.start(100)

    def fade_out_start_scan(self):
        self.animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.fade_in_start_scan)
        self.animation.start()

    def fade_in_start_scan(self):
        self.start_scan()
        self.animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def simulate_scan_progress(self):
        if self.scan_progress >= 100:
            self.scan_timer.stop()
            self.server_timer.start(1000)
        else:
            self.scan_progress += 1
            self.eva1_scan_bar.setValue(self.scan_progress)
            self.eva2_scan_bar.setValue(self.scan_progress)
            self.eva1_image.set_progress(self.scan_progress)
            self.eva2_image.set_progress(self.scan_progress)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    scanner = RockScanner()
    scanner.show()
    sys.exit(app.exec())
