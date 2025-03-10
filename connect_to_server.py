#!/usr/bin/env python3
import socket
import struct
import time
import argparse 

start_time = time.perf_counter()

# defining ip and port numbers as arguments 
parser = argparse.ArgumentParser(description="Write JSON data to a file.") 
parser.add_argument("--ip", type=str, required=True, help="server's ip address.") 
parser.add_argument("--port", type=str, required=True, help="server's port number.") 
# parsing arguments defined above 
args = parser.parse_args()

# Create a UDP socket and send the request
def send_udp_request(server_ip, server_port, request_time, command):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Build request packet (time, command)
    request_packet = struct.pack("!II",request_time,command) # two unsigned ints each 4 bytes long packed in big-endian format

    # Send UDP request
    udp_socket.sendto(request_packet, (server_ip, server_port))
    
    return udp_socket

# Receive and process the response from the server
def receive_raw_response(udp_socket):
    response, server_address = udp_socket.recvfrom(1024)  # Buffer size 1024 bytes
    
    # Extract response data
    server_time, command = struct.unpack("II", response[:8])

    # Decode data (you can customize this as needed)
    output_data = response[8:]
    decoded_data = int.from_bytes(output_data, byteorder='big')  # 'big' or 'little' depending on endianness
    
    return server_time, command, decoded_data, server_address

# Main function to drive the script
def main():

    for command in range(1,119): # iterates from 1-118 to send to server
        # REQUEST_TIME = current time
        request_time = int(time.time())

        # Send UDP request
        udp_socket = send_udp_request(args.ip, int(args.port), request_time, command)

        # Receive and process the server's response
        server_time, command_received, decoded_data, server_address = receive_raw_response(udp_socket)

        # write to json file/ write to persistent database / write to data variable in script 

        # Display the response data
        print(f"Receiving from {server_address}")
        print(f"Server Time: {server_time}") 
        print(f"Command Sent: {command}")
        print(f"Command Received: {command_received}") 
        print(f"Output: {decoded_data}") 

    # Close the socket
    udp_socket.close()

if __name__ == "__main__":
    main()

# checks time the script took to execute 
end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(f"Execution Time: {elapsed_time:.6f} seconds")
