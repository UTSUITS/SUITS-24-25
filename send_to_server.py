#!/usr/bin/env python3
import socket
import struct 
import json
import time
import argparse 

# Loads server data from json file 
with open('server_info.json', 'r') as f:
   server_config = json.load(f) 

# Check if system is big-endian
def is_big_endian():
    return struct.pack("H", 1) == b"\x00\x01" 

# Convert values to big-endian if necessary
def to_big_endian(value):
    return struct.pack(">I", value) if not is_big_endian() else struct.pack("I", value) 

# Create a UDP socket and send the request
def send_udp_request(server_ip, server_port, request_time, command):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Build request packet (time, command)
    request_packet = to_big_endian(request_time) + to_big_endian(command)

    # Send UDP request
    udp_socket.sendto(request_packet, (server_ip, server_port))
    
    return udp_socket

# Receive and process the response from the server
def receive_response(udp_socket):
    response, server_address = udp_socket.recvfrom(1024)  # Buffer size 1024 bytes
    
    # Extract response data
    server_time, command = struct.unpack("II", response[:8])

    # Decode data (you can customize this as needed)
    output_data = response[8:]
    decoded_data = int.from_bytes(output_data, byteorder='big')  # 'big' or 'little' depending on endianness
    
    return server_time, command, decoded_data, server_address

# Main function to drive the script
def main():
    # Set up argparse to handle the command-line input for the desired command
    parser = argparse.ArgumentParser(description="Send a command to the server via UDP and receive a response.")
    parser.add_argument('command', type=int, help="The command to send to the server.")
    args = parser.parse_args()

    # REQUEST_TIME = current time
    request_time = int(time.time())

    # Send UDP request
    udp_socket = send_udp_request(server_config["SERVER_IP"], int(server_config["SERVER_PORT"]), request_time, args.command)

    # Receive and process the server's response
    server_time, command_received, decoded_data, server_address = receive_response(udp_socket)

    # Display the response data
    print(f"Receiving from {server_address}") 
    print(f"Command: {args.command}")
    print(f"Output: {decoded_data}")

    # Close the socket
    udp_socket.close()

if __name__ == "__main__":
    main()
