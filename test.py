import socket
import struct

# Server Address and Port
SERVER_IP = "172.20.99.167"  # Change this to the actual server IP
SERVER_PORT = 14141        # Change this to the correct UDP port

# UDP Request Constants
COMMAND_GET_LIDAR = 7   # Example: GET LIDAR Data
REQUEST_TIME = 0          # Can be set to 0 if not used
DATA_PLACEHOLDER = b'\x00\x00\x00\x00'  # 4 bytes of empty data

# Function to check if system is big-endian
def is_big_endian():
    return struct.pack("H", 1) == b"\x00\x01"

# Convert values to big-endian if necessary
def to_big_endian(value):
    return struct.pack(">I", value) if not is_big_endian() else struct.pack("I", value)

# Create UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Build request packet (time, command, data)
request_packet = to_big_endian(REQUEST_TIME) + to_big_endian(COMMAND_GET_LIDAR) + DATA_PLACEHOLDER

# Send UDP Request
udp_socket.sendto(request_packet, (SERVER_IP, SERVER_PORT))

# Receive Response
response, server_address = udp_socket.recvfrom(1024)  # Buffer size 1024 bytes

# Extract Response Data
server_time, command, response_data = struct.unpack(">I I 4s", response[:12])

# Convert data to float
value_float = struct.unpack(">f", response_data)[0]

print(f"Server Time: {server_time}")
print(f"Command: {command}")
print(str(value_float))

# Close the socket
udp_socket.close()
