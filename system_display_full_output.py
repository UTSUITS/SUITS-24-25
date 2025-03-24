import sys
import json
import time
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

# Load server data from JSON file
json_path = r"C:\Users\jerem\SUITS-24-25\output_results.json"

class ErrorStateDisplay(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize error states to track changes
        self.error_state_14 = None
        self.error_state_15 = None
        self.error_state_16 = None

        # Set fixed window size to match the 1024x600 touchscreen
        self.setWindowTitle("Wrist-Mounted System Display")
        self.setGeometry(100, 100, 1024, 600)
        self.setFixedSize(1024, 600)
        self.setStyleSheet("background-color: black;")
        layout = QVBoxLayout()
        layout.setSpacing(10)

        title = QLabel("⚠️ ERROR TRACKING ⚠️")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)

        # Buttons for commands
        self.button_14 = QPushButton("Fan Error")
        self.button_15 = QPushButton("Oxygen Error")
        self.button_16 = QPushButton("Pump Error")

        # Chatbox placed at the bottom
        self.chat_box = QTextEdit()
        self.chat_box.setFixedHeight(250)  # Adjusted to fit within 1024x600 screen
        self.chat_box.setReadOnly(True)
        self.chat_box.setStyleSheet("background-color: rgba(0, 0, 0, 0.8); color: white; border-radius: 10px; padding: 10px; border: 2px solid #333;")

        # Buttons on top of the chatbox
        self.setup_button(self.button_14, "green")
        self.setup_button(self.button_15, "green")
        self.setup_button(self.button_16, "green")

        layout.addWidget(self.button_14)
        layout.addWidget(self.button_15)
        layout.addWidget(self.button_16)
        layout.addWidget(self.chat_box)  # Chatbox is now below the buttons

        self.setLayout(layout)

        # Set up a timer to refresh data every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(10)  # Refresh every 1 second

    def setup_button(self, button, color):
        button.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        button.setFixedHeight(60)  # Adjusted for better touch interaction
        button.setStyleSheet(f"background-color: {color}; color: white; border-radius: 10px; padding: 10px;")

    def read_json(self):
        """Reads the JSON file and returns the data."""
        try:
            with open(json_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error reading JSON file: {json_path}")
            return None

    def refresh_data(self):
        """Updates the error state based on the JSON data."""
        data = self.read_json()

        if data:
            fan_error = data.get("14", None)
            oxygen_error = data.get("15", None)
            pump_error = data.get("16", None)

            # Check and update the error state for each error condition
            if fan_error is not None and fan_error != self.error_state_14:
                self.update_error_state(fan_error, 14)
            if oxygen_error is not None and oxygen_error != self.error_state_15:
                self.update_error_state(oxygen_error, 15)
            if pump_error is not None and pump_error != self.error_state_16:
                self.update_error_state(pump_error, 16)

    def update_error_state(self, error_state, error_id):
        """Updates the error state and displays message."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        if error_id == 14:
            if error_state == 1 and self.error_state_14 != 1:
                self.chat_box.append(f"[{timestamp}] Fan Error Detected!")
                self.error_state_14 = 1
            elif error_state == 0 and self.error_state_14 != 0:
                self.chat_box.append(f"[{timestamp}] Fan Error Cleared!")
                self.error_state_14 = 0
            self.update_button_status(self.button_14, error_state)

        elif error_id == 15:
            if error_state == 1 and self.error_state_15 != 1:
                self.chat_box.append(f"[{timestamp}] Oxygen Error Detected!")
                self.error_state_15 = 1
            elif error_state == 0 and self.error_state_15 != 0:
                self.chat_box.append(f"[{timestamp}] Oxygen Error Cleared!")
                self.error_state_15 = 0
            self.update_button_status(self.button_15, error_state)

        elif error_id == 16:
            if error_state == 1 and self.error_state_16 != 1:
                self.chat_box.append(f"[{timestamp}] Pump Error Detected!")
                self.error_state_16 = 1
            elif error_state == 0 and self.error_state_16 != 0:
                self.chat_box.append(f"[{timestamp}] Pump Error Cleared!")
                self.error_state_16 = 0
            self.update_button_status(self.button_16, error_state)

    def update_button_status(self, button, error_state):
        """Updates the button color based on the error state."""
        if error_state == 1:
            button.setStyleSheet("background-color: red; color: white; border-radius: 10px; padding: 10px;")
        else:
            button.setStyleSheet("background-color: green; color: white; border-radius: 10px; padding: 10px;")

    def closeEvent(self, event):
        """Handles the close event."""
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    display = ErrorStateDisplay()
    display.show()
    sys.exit(app.exec())
