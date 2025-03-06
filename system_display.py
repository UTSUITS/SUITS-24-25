import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer
import random
import time

class SystemWarningDisplay(QWidget):
    def __init__(self, fan_status, oxygen_status, pump_status):
        super().__init__()
        self.setWindowTitle("Wrist-Mounted System Display")
        self.setGeometry(100, 100, 400, 350)

        # Set the background color to black
        self.setStyleSheet("""
            QWidget {
                background-color: black;
            }
        """)

        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title label
        title = QLabel("⚠️ ERROR TRACKING ⚠️")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)

        # Top-right timestamp display
        self.timestamp_label = QLabel(self.get_current_time())
        self.timestamp_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.timestamp_label.setStyleSheet("color: white;")
        layout.addWidget(self.timestamp_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        # System warning buttons (instead of labels)
        self.fan_button = self.create_status_button("FAN ERROR", fan_status)
        self.oxygen_button = self.create_status_button("OXYGEN WARNING", oxygen_status)
        self.pump_button = self.create_status_button("PUMP ERROR", pump_status)

        # Add to layout
        layout.addWidget(self.fan_button)
        layout.addWidget(self.oxygen_button)
        layout.addWidget(self.pump_button)

        # Chatbox-like bottom section to display level info
        self.chat_box = QTextEdit()
        self.chat_box.setFixedHeight(100)
        self.chat_box.setReadOnly(True)
        self.chat_box.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                border-radius: 10px;
                padding: 10px;
                border: 2px solid #333;
            }
        """)
        layout.addWidget(self.chat_box)

        self.setLayout(layout)

        # Timer to update the timestamp every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timestamp)
        self.timer.start(1000)

    def create_status_button(self, title, status):
        """ Creates a pushable button with a rounded style for each system """
        button = QPushButton(f"⚠️ {title} ⚠️" if status == 1 else f"✅ No {title}")
        button.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        button.setFixedSize(300, 80)
        button.setStyleSheet(self.get_button_style(status))

        # Connect the button click event to show the status level (random numbers for now)
        button.clicked.connect(lambda: self.show_level(title))

        return button

    def get_button_style(self, status):
        """ Returns the button style based on the error or no error status """
        if status == 1:
            return """
                background-color: rgba(255, 68, 68, 0.8);  /* Red background with opacity for error */
                border-radius: 15px;
                padding: 10px;
                border: 2px solid #ff2222;
            """
        else:
            return """
                background-color: rgba(0, 255, 0, 0.8);  /* Green background with opacity for no error */
                border-radius: 15px;
                padding: 10px;
                border: 2px solid #006600;
            """
        
    def show_level(self, title):
        """ Show random values for oxygen, fan, or pump levels when the button is clicked """
        level = random.randint(0, 100)  # Generate a random level between 0 and 100
        timestamp = self.get_current_time()
        level_label = f"{timestamp} - {title} Level: {level}%"
        
        # Append the level information to the chat box (acting as the bottom box)
        self.chat_box.append(level_label)

    def update_timestamp(self):
        """ Update the timestamp label every second """
        self.timestamp_label.setText(self.get_current_time())

    def get_current_time(self):
        """ Returns the current time formatted as HH:MM:SS """
        return time.strftime("%H:%M:%S")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Example inputs (Modify these for testing)
    fan_status = 1   # 1 = Error, 0 = No Error
    oxygen_status = 0  # 1 = Warning, 0 = No Warning
    pump_status = 1  # 1 = Error, 0 = No Error

    display = SystemWarningDisplay(fan_status, oxygen_status, pump_status)
    display.show()
    sys.exit(app.exec())
