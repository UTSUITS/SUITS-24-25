import socket
import time
from PyQt5.QtCore import QThread, pyqtSignal

class ServerRequestThread(QThread):
    response_received = pyqtSignal(str, str, str, str)  # Signal includes timestamp

    def __init__(self, command, server_ip, server_port):
        super().__init__()
        self.command = command
        self.server_ip = server_ip
        self.server_port = server_port
        self._running = True

    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Send UDP packet
                timestamp = self.get_current_time()  # Get the timestamp when the request is sent
                print(f"{timestamp} - Sent request for command {self.command} to {self.server_ip}:{self.server_port}")  # Log the timestamp and request in terminal
                s.sendto(self.command.encode(), (self.server_ip, self.server_port))
                
                # Receive response
                response, _ = s.recvfrom(1024)  # buffer size is 1024 bytes
                
                # Try decoding the response with UTF-8, fallback if necessary
                try:
                    response = response.decode("utf-8").strip()
                except UnicodeDecodeError:
                    response = f"Invalid UTF-8 data received: {response.hex()}"
                
                if self._running:
                    # Extract the "Output" value after the word "Output:"
                    if "Output:" in response:
                        output_value = response.split("Output:")[-1].strip()  # Extract after "Output:"
                        self.response_received.emit(output_value, self.command, response, timestamp)
                    else:
                        self.response_received.emit("Disconnected", self.command, "No output received", timestamp)
        except Exception as e:
            print(f"Error connecting to server: {e}")
            if self._running:
                self.response_received.emit("Disconnected", self.command, str(e), self.get_current_time())

    def stop(self):
        self._running = False
        self.wait()  # Wait for the thread to finish

    def get_current_time(self):
        return time.strftime("%H:%M:%S")

# Example usage in PyQt5 application
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Server Request Client")
        self.setGeometry(100, 100, 600, 400)
        
        # Setup a label to display responses
        self.label = QLabel(self)
        self.label.setGeometry(10, 10, 580, 380)
        
        # Example command, IP, and Port
        self.command = "some_command"
        self.server_ip = "10.8.17.189"
        self.server_port = 14141
        
        # Setup thread to communicate with server
        self.request_thread = ServerRequestThread(self.command, self.server_ip, self.server_port)
        self.request_thread.response_received.connect(self.update_label)
        
        # Start the thread
        self.request_thread.start()
        
        # Timer to stop after 10 seconds (for example)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.stop_thread)
        self.timer.start(10000)  # Stop after 10 seconds

    def update_label(self, output, command, response, timestamp):
        # Update the label with the latest response
        self.label.setText(f"Timestamp: {timestamp}\nCommand: {command}\nResponse: {response}\nOutput: {output}")
        
    def stop_thread(self):
        self.request_thread.stop()

# Main application loop
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
