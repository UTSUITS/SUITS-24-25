#!/usr/bin/env python3
import socket
import struct
import time
import redis 
import argparse
import threading
import json 
from flask import Flask, jsonify

# # defining ip and port numbers as arguments 
# parser = argparse.ArgumentParser(description="Write JSON data to a file.") 
# parser.add_argument("--ip", type=str, required=False, help="server's ip address.")

# # parsing arguments defined above 
# args = parser.parse_args()

# rd=redis.Redis(host='redis-db', port=6379,db=0)
rd=redis.Redis(host='localhost', port=6379,db=0)

app = Flask(__name__)

float_outputs = set(range(17, 23)) | set(range(27, 37)) | set(range(38, 48)) | set(range(58,103)) | {106,109,112,115,118}

# Create a UDP socket and send the request
def send_udp_request(server_ip, server_port, request_time, command, team_num):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    if team_num is None: 
        # Build request packet (time, command)
        request_packet = struct.pack("!II",request_time,int(command)) # two unsigned ints each 4 bytes long packed in big-endian format
    else:
        request_packet = struct.pack("!IIf",request_time,command,float(team_num)) # two unsigned int and a 4 byte floating-point number 

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

    return server_time, command, output_data, server_address

# Collects data every second and stores it to Redis 
def collect_data():
    
    team_num = 0

    while True: 
        results = {}
        request_time = int(time.time()) 

        for command in range(1,119): # iterates from 1-118 to send to server 
            if command >= 58: 
                # Send UDP request
                udp_socket = send_udp_request('172.18.0.1', 14141, request_time, command,team_num)
                # Receive and process the server's response
                server_time, command_received, output_data, server_address = receive_raw_response(udp_socket) 
                if command in float_outputs: 
                    decoded_data = struct.unpack(">f", output_data)[0]  # Big-endian float
                else: 
                    decoded_data = struct.unpack(">I", output_data)[0] & 0xFF # decoded_data is a tuple so just extract first entry 
            else: 
                udp_socket = send_udp_request('172.18.0.1', 14141, request_time, command,None) 
                # Receive and process the server's response
                server_time, command_received, output_data, server_address = receive_raw_response(udp_socket) 
                if command in float_outputs:
                    decoded_data = struct.unpack(">f", output_data)[0] # Unsigned int 
                else: 
                    decoded_data = struct.unpack(">I", output_data)[0] & 0xFF

            # write to json file/ write to persistent database / write to data variable in script 
            results[command] = decoded_data 
            # Close the socket
            udp_socket.close()
        rd.set(str(request_time),json.dumps(results))
        time.sleep(1) # sleeps for one second 

threading.Thread(target=collect_data, daemon=True).start()

@app.route('/get_data',methods=['GET'])
def get_data(): 
    all_keys = [int(key.decode('utf-8')) for key in rd.keys()] 
    
    if not all_keys:
        return jsonify({"error": "No data available"}), 404

    # Find the closest timestamp
    closest_time = min(all_keys, key=lambda x: abs(int(x) - time.time()))
    closest_data = rd.get(closest_time)
    print(type(closest_data))

    closest_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(closest_time))

    return {"closest_epoch": closest_time, "data": json.loads(closest_data)}

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0',port=5000)
