<<<<<<< HEAD
import sys
import socket
import struct
import json
import time
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

# Load server data from JSON file
with open(r"C:\Users\jerem\SUITS-24-25\server_info.json", 'r') as f:
    server_config = json.load(f)

def is_big_endian():
    return struct.pack("H", 1) == b"\x00\x01"

def to_big_endian(value):
    return struct.pack(">I", value) if not is_big_endian() else struct.pack("I", value)

def send_udp_request(server_ip, server_port, request_time, command):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    request_packet = to_big_endian(request_time) + to_big_endian(command)
    udp_socket.sendto(request_packet, (server_ip, server_port))
    return udp_socket

def receive_response(udp_socket):
    response, server_address = udp_socket.recvfrom(1024)
    server_time, command = struct.unpack("II", response[:8])
    output_data = response[8:]
    decoded_data = int.from_bytes(output_data, byteorder='big')
    return server_time, command, decoded_data, server_address

class ServerRequestThread(QThread):
    response_received = pyqtSignal(str, int)

    def __init__(self, server_ip, server_port, command, display):
        super().__init__()
        self.server_ip = server_ip.strip()
        self.server_port = server_port
        self.command = command
        self.display = display
        self._running = True
        self.request_time = int(time.time())

    def run(self):
        try:
            udp_socket = send_udp_request(self.server_ip, self.server_port, self.request_time, self.command)
            server_time, command_received, decoded_data, server_address = receive_response(udp_socket)
            response = f"Receiving from {server_address}\nCommand: {self.command}\nOutput: {decoded_data}"
            self.response_received.emit(response, decoded_data)
            udp_socket.close()
        except Exception as e:
            self.response_received.emit(str(e), -1)

    def update_request_time(self):
        self.request_time = int(time.time())
        self.start()

class SystemWarningDisplay(QWidget):
    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port

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

        # Create threads for each command
        self.server_thread_14 = ServerRequestThread(self.server_ip, self.server_port, 14, self)
        self.server_thread_15 = ServerRequestThread(self.server_ip, self.server_port, 15, self)
        self.server_thread_16 = ServerRequestThread(self.server_ip, self.server_port, 16, self)

        # Connect signals for each thread to update button status
        self.server_thread_14.response_received.connect(self.update_button_status_14)
        self.server_thread_15.response_received.connect(self.update_button_status_15)
        self.server_thread_16.response_received.connect(self.update_button_status_16)

        # Start the threads for each command
        self.server_thread_14.start()
        self.server_thread_15.start()
        self.server_thread_16.start()

        # Set up a timer to refresh data every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1)  # Refresh every 1 second

    def setup_button(self, button, color):
        button.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        button.setFixedHeight(60)  # Adjusted for better touch interaction
        button.setStyleSheet(f"background-color: {color}; color: white; border-radius: 10px; padding: 10px;")

    def update_button_status_14(self, response, decoded_data):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.server_thread_14.request_time))
        if decoded_data == 1 and self.error_state_14 != 1:
            self.chat_box.append(f"[{timestamp}] Fan Error Detected!")
            self.error_state_14 = 1
        elif decoded_data == 0 and self.error_state_14 != 0:
            self.chat_box.append(f"[{timestamp}] Fan Error Cleared!")
            self.error_state_14 = 0
        self.update_button_status(self.button_14, decoded_data)

    def update_button_status_15(self, response, decoded_data):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.server_thread_15.request_time))
        if decoded_data == 1 and self.error_state_15 != 1:
            self.chat_box.append(f"[{timestamp}] Oxygen Error Detected!")
            self.error_state_15 = 1
        elif decoded_data == 0 and self.error_state_15 != 0:
            self.chat_box.append(f"[{timestamp}] Oxygen Error Cleared!")
            self.error_state_15 = 0
        self.update_button_status(self.button_15, decoded_data)

    def update_button_status_16(self, response, decoded_data):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.server_thread_16.request_time))
        if decoded_data == 1 and self.error_state_16 != 1:
            self.chat_box.append(f"[{timestamp}] Pump Error Detected!")
            self.error_state_16 = 1
        elif decoded_data == 0 and self.error_state_16 != 0:
            self.chat_box.append(f"[{timestamp}] Pump Error Cleared!")
            self.error_state_16 = 0
        self.update_button_status(self.button_16, decoded_data)

    def update_button_status(self, button, decoded_data):
        if decoded_data == 1:
            button.setStyleSheet("background-color: red; color: white; border-radius: 10px; padding: 10px;")
        else:
            button.setStyleSheet("background-color: green; color: white; border-radius: 10px; padding: 10px;")

    def send_command(self, command):
        if command == 14:
            self.server_thread_14 = ServerRequestThread(self.server_ip, self.server_port, 14, self)
            self.server_thread_14.start()
        elif command == 15:
            self.server_thread_15 = ServerRequestThread(self.server_ip, self.server_port, 15, self)
            self.server_thread_15.start()
        elif command == 16:
            self.server_thread_16 = ServerRequestThread(self.server_ip, self.server_port, 16, self)
            self.server_thread_16.start()

    def refresh_data(self):
        self.server_thread_14.update_request_time()
        self.server_thread_15.update_request_time()
        self.server_thread_16.update_request_time()

    def closeEvent(self, event):
        self.server_thread_14.quit()
        self.server_thread_15.quit()
        self.server_thread_16.quit()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    server_ip = server_config["SERVER_IP"]
    server_port = int(server_config["SERVER_PORT"])
    display = SystemWarningDisplay(server_ip, server_port)
    display.show()
    sys.exit(app.exec())
=======
import sys
import socket
import struct
import json
import time
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

# Load server data from JSON file
with open(r"C:\Users\jerem\SUITS-24-25\server_info.json", 'r') as f:
    server_config = json.load(f)

def is_big_endian():
    return struct.pack("H", 1) == b"\x00\x01"

def to_big_endian(value):
    return struct.pack(">I", value) if not is_big_endian() else struct.pack("I", value)

def send_udp_request(server_ip, server_port, request_time, command):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    request_packet = to_big_endian(request_time) + to_big_endian(command)
    udp_socket.sendto(request_packet, (server_ip, server_port))
    return udp_socket

def receive_response(udp_socket):
    response, server_address = udp_socket.recvfrom(1024)
    server_time, command = struct.unpack("II", response[:8])
    output_data = response[8:]
    decoded_data = int.from_bytes(output_data, byteorder='big')
    return server_time, command, decoded_data, server_address

class ServerRequestThread(QThread):
    response_received = pyqtSignal(str, int)

    def __init__(self, server_ip, server_port, command, display):
        super().__init__()
        self.server_ip = server_ip.strip()
        self.server_port = server_port
        self.command = command
        self.display = display
        self._running = True
        self.request_time = int(time.time())

    def run(self):
        try:
            udp_socket = send_udp_request(self.server_ip, self.server_port, self.request_time, self.command)
            server_time, command_received, decoded_data, server_address = receive_response(udp_socket)
            response = f"Receiving from {server_address}\nCommand: {self.command}\nOutput: {decoded_data}"
            self.response_received.emit(response, decoded_data)
            udp_socket.close()
        except Exception as e:
            self.response_received.emit(str(e), -1)

    def update_request_time(self):
        self.request_time = int(time.time())
        self.start()

class SystemWarningDisplay(QWidget):
    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port

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

        # Create threads for each command
        self.server_thread_14 = ServerRequestThread(self.server_ip, self.server_port, 14, self)
        self.server_thread_15 = ServerRequestThread(self.server_ip, self.server_port, 15, self)
        self.server_thread_16 = ServerRequestThread(self.server_ip, self.server_port, 16, self)

        # Connect signals for each thread to update button status
        self.server_thread_14.response_received.connect(self.update_button_status_14)
        self.server_thread_15.response_received.connect(self.update_button_status_15)
        self.server_thread_16.response_received.connect(self.update_button_status_16)

        # Start the threads for each command
        self.server_thread_14.start()
        self.server_thread_15.start()
        self.server_thread_16.start()

        # Set up a timer to refresh data every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1)  # Refresh every 1 second

    def setup_button(self, button, color):
        button.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        button.setFixedHeight(60)  # Adjusted for better touch interaction
        button.setStyleSheet(f"background-color: {color}; color: white; border-radius: 10px; padding: 10px;")

    def update_button_status_14(self, response, decoded_data):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.server_thread_14.request_time))
        if decoded_data == 1 and self.error_state_14 != 1:
            self.chat_box.append(f"[{timestamp}] Fan Error Detected!")
            self.error_state_14 = 1
        elif decoded_data == 0 and self.error_state_14 != 0:
            self.chat_box.append(f"[{timestamp}] Fan Error Cleared!")
            self.error_state_14 = 0
        self.update_button_status(self.button_14, decoded_data)

    def update_button_status_15(self, response, decoded_data):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.server_thread_15.request_time))
        if decoded_data == 1 and self.error_state_15 != 1:
            self.chat_box.append(f"[{timestamp}] Oxygen Error Detected!")
            self.error_state_15 = 1
        elif decoded_data == 0 and self.error_state_15 != 0:
            self.chat_box.append(f"[{timestamp}] Oxygen Error Cleared!")
            self.error_state_15 = 0
        self.update_button_status(self.button_15, decoded_data)

    def update_button_status_16(self, response, decoded_data):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.server_thread_16.request_time))
        if decoded_data == 1 and self.error_state_16 != 1:
            self.chat_box.append(f"[{timestamp}] Pump Error Detected!")
            self.error_state_16 = 1
        elif decoded_data == 0 and self.error_state_16 != 0:
            self.chat_box.append(f"[{timestamp}] Pump Error Cleared!")
            self.error_state_16 = 0
        self.update_button_status(self.button_16, decoded_data)

    def update_button_status(self, button, decoded_data):
        if decoded_data == 1:
            button.setStyleSheet("background-color: red; color: white; border-radius: 10px; padding: 10px;")
        else:
            button.setStyleSheet("background-color: green; color: white; border-radius: 10px; padding: 10px;")

    def send_command(self, command):
        if command == 14:
            self.server_thread_14 = ServerRequestThread(self.server_ip, self.server_port, 14, self)
            self.server_thread_14.start()
        elif command == 15:
            self.server_thread_15 = ServerRequestThread(self.server_ip, self.server_port, 15, self)
            self.server_thread_15.start()
        elif command == 16:
            self.server_thread_16 = ServerRequestThread(self.server_ip, self.server_port, 16, self)
            self.server_thread_16.start()

    def refresh_data(self):
        self.server_thread_14.update_request_time()
        self.server_thread_15.update_request_time()
        self.server_thread_16.update_request_time()

    def closeEvent(self, event):
        self.server_thread_14.quit()
        self.server_thread_15.quit()
        self.server_thread_16.quit()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    server_ip = server_config["SERVER_IP"]
    server_port = int(server_config["SERVER_PORT"])
    display = SystemWarningDisplay(server_ip, server_port)
    display.show()
    sys.exit(app.exec())
>>>>>>> origin/main
