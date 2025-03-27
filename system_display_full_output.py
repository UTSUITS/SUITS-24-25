import sys
import json
import time
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit, QTabWidget, QHBoxLayout
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QTimer

# Load server data from JSON file
json_path = r"C:\Users\jerem\SUITS-24-25\output_results.json"
image_path = r"C:\Users\jerem\SUITS-24-25\rockYardMap-min.png"

class ErrorStateDisplay(QWidget):
    def __init__(self):
        super().__init__()

        self.error_states = {i: None for i in range(2, 8)}  # Initialize error states 2-7
        self.error_states.update({14: None, 15: None, 16: None})  # Add 14-16

        self.setWindowTitle("Wrist-Mounted System Display")
        self.setGeometry(100, 100, 1024, 600)
        self.setFixedSize(1024, 600)
        self.setStyleSheet("background-color: black;")

        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet("background-color: #333; color: white; font-size: 16px;")

        # Initialize tabs
        self.error_state_tab = QWidget()
        self.create_error_state_tab()

        self.dcu_state_tab = QWidget()
        self.create_dcu_state_tab()

        self.image_tab = QWidget()
        self.create_image_tab()

        self.tabs.addTab(self.error_state_tab, "Error States")
        self.tabs.addTab(self.dcu_state_tab, "DCU States")
        self.tabs.addTab(self.image_tab, "Rock Yard Map")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # Set up a timer to refresh data
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1000)

    def create_error_state_tab(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("⚠️ ERROR TRACKING ⚠️")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)

        self.buttons = {
            14: QPushButton("Fan Error State"),
            15: QPushButton("Oxygen Error State"),
            16: QPushButton("Pump Error State")
        }

        self.chat_box = QTextEdit()
        self.chat_box.setFixedHeight(250)
        self.chat_box.setReadOnly(True)
        self.chat_box.setStyleSheet("background-color: rgba(0, 0, 0, 0.8); color: white;")

        # Add buttons and connect them to the function to toggle error state
        for error_id, button in self.buttons.items():
            self.setup_button(button, "green")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, eid=error_id: self.toggle_error_state(eid))
            layout.addWidget(button)

        # Add the chatbox at the bottom
        layout.addStretch()  # Pushes chatbox to the bottom
        layout.addWidget(self.chat_box)
        self.error_state_tab.setLayout(layout)

    def create_dcu_state_tab(self):
        layout = QVBoxLayout()

        # Horizontal layout for left and right sections
        h_layout = QHBoxLayout()

        # Center the title between the left and right buttons
        title_layout = QHBoxLayout()
        title = QLabel("EVA1 DCU STATES / EVA2 DCU STATES")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        title_layout.addStretch()
        title_layout.addWidget(title)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # Left section for EVA 1 DCU buttons (2-7)
        left_layout = QVBoxLayout()
        self.dcu_buttons = {}
        dcu_labels_1 = {2: "BATTERY", 3: "OXYGEN", 4: "COMMS", 5: "FAN", 6: "PUMP", 7: "CO2"}

        for i in range(2, 8):
            button = QPushButton("Local")
            button.setCheckable(True)
            button.setStyleSheet("background-color: grey; color: white; font-size: 16px; padding: 10px;")
            self.dcu_buttons[i] = button
            left_layout.addWidget(button)

        # Right section for EVA 2 DCU buttons (8-13)
        right_layout = QVBoxLayout()
        dcu_labels_2 = {8: "BATTERY", 9: "OXYGEN", 10: "COMMS", 11: "FAN", 12: "PUMP", 13: "CO2"}

        for i in range(8, 14):
            button = QPushButton("Local")
            button.setCheckable(True)
            button.setStyleSheet("background-color: grey; color: white; font-size: 16px; padding: 10px;")
            self.dcu_buttons[i] = button
            right_layout.addWidget(button)

        # Add labels for both left and right layouts
        left_labels_layout = QVBoxLayout()
        for i in range(2, 8):
            label = QLabel(dcu_labels_1.get(i, "BATTERY"))
            label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: white;")
            left_labels_layout.addWidget(label)

        right_labels_layout = QVBoxLayout()
        for i in range(8, 14):
            label = QLabel(dcu_labels_2.get(i, "BATTERY"))
            label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: white;")
            right_labels_layout.addWidget(label)

        # Add labels and buttons to their respective sections
        h_layout.addLayout(left_labels_layout)
        h_layout.addLayout(left_layout)
        h_layout.addLayout(right_labels_layout)
        h_layout.addLayout(right_layout)

        layout.addLayout(h_layout)
        self.dcu_state_tab.setLayout(layout)

    def create_image_tab(self):
        layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pixmap = QPixmap(image_path)

        if not self.pixmap.isNull():
            self.image_label.setPixmap(self.pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.image_label.setText("Image failed to load.")

        layout.addWidget(self.image_label)
        self.image_tab.setLayout(layout)

    def setup_button(self, button, color):
        button.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        button.setFixedHeight(60)
        button.setStyleSheet(f"background-color: {color}; color: white; border-radius: 10px; padding: 10px;")

    def read_json(self):
        try:
            with open(json_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error reading JSON file: {json_path}")
            return None

    def refresh_data(self):
        data = self.read_json()
        if data:
            # Update error states (similarly to how you did it for DCU states)
            for error_id in self.error_states.keys():
                new_state = data.get(str(error_id), None)
                if new_state is not None and new_state != self.error_states[error_id]:
                    self.update_error_state(new_state, error_id)
        
            for dcu_id, button in self.dcu_buttons.items():
                dcu_state = data.get(str(dcu_id), False)
                button.setChecked(dcu_state)

                # Change text and color based on DCU state
                if dcu_id == 2:
                    button.setText("Local" if dcu_state else "UMB")
                elif dcu_id == 3:
                    button.setText("PRI" if dcu_state else "SEC")
                elif dcu_id == 4:
                    button.setText("COMMS" if dcu_state else "B")
                elif dcu_id == 5:
                    button.setText("PRI" if dcu_state else "SEC")
                elif dcu_id == 6:
                    button.setText("OPEN" if dcu_state else "CLOSE")
                elif dcu_id == 7:
                    button.setText("A" if dcu_state else "B")

                if dcu_id == 8:
                    button.setText("Local" if dcu_state else "UMB")
                elif dcu_id == 9:
                    button.setText("PRI" if dcu_state else "SEC")
                elif dcu_id == 10:
                    button.setText("COMMS" if dcu_state else "B")
                elif dcu_id == 11:
                    button.setText("PRI" if dcu_state else "SEC")
                elif dcu_id == 12:
                    button.setText("OPEN" if dcu_state else "CLOSE")
                elif dcu_id == 13:
                    button.setText("A" if dcu_state else "B")

                # Change color based on state
                if dcu_state:
                    button.setStyleSheet("background-color: green; color: white;")
                else:
                    button.setStyleSheet("background-color: grey; color: white;")

    def toggle_error_state(self, error_id):
        new_state = not self.error_states.get(error_id, False)
        self.update_error_state(new_state, error_id)

    def update_error_state(self, error_state, error_id):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        if error_id in [14, 15, 16]:
            button = self.buttons[error_id]
            message = {
                14: "Fan Error State",
                15: "Oxygen Error State",
                16: "Pump Error State"
            }[error_id]
            self.chat_box.append(f"[{timestamp}] {message} {'Detected' if error_state else 'Cleared'}!")
            button.setStyleSheet("background-color: red; color: white;" if error_state else "background-color: green; color: white;")
        self.error_states[error_id] = error_state

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    display = ErrorStateDisplay()
    display.show()
    sys.exit(app.exec())
