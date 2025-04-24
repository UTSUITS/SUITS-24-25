#!/usr/bin/env python3
import socket
import struct
import time
import redis 
import threading
import json 
from flask import Flask, request
import logging 

with open('/home/utsuits/ip_address.txt', 'r') as file:
    lines = file.readlines()
    ip_address = lines[0].strip() if len(lines) > 0 else None
    team_num = lines[1].strip() if len(lines) > 1 else None

rd=redis.Redis(host='localhost', port=6379,db=0)

app = Flask(__name__)

float_outputs = set(range(17, 23)) | set(range(27, 37)) | set(range(38, 48)) | set(range(58,103)) | {106,109,112,115,118}

# Builds the raw UDP packet for a command
def build_udp_message(request_time, command, team_num):
    if team_num is None:
        return struct.pack("!II", request_time, int(command))
    else:
        return struct.pack("!IIf", request_time, command, float(team_num))

# Parses raw UDP response into structured values
def parse_udp_response(data):
    server_time, command = struct.unpack("!II", data[:8])
    output_data = data[8:]
    return server_time, command, output_data

def collect_data():

    while True:
        request_time = int(time.time())
        results = {}
        start_time = time.time()

        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.settimeout(0.2)  # Adjust if needed
            server = (ip_address, 14141) 

            # Send all 118 requests
            for command in range(1, 119):
                try:
                    if command >= 58:
                        message = build_udp_message(request_time, command, team_num)
                    else:
                        message = build_udp_message(request_time, command, None)
                    
                    udp_socket.sendto(message, server)
                except Exception as e:
                    print(f"⚠️ Failed to send command {command}: {e}")

            # Receive responses
            received_commands = set()
            max_attempts = 150  # cap to avoid infinite loop

            while len(received_commands) < 118 and max_attempts > 0:
                try:
                    data, addr = udp_socket.recvfrom(1024)
                    server_time, command_received, output_data = parse_udp_response(data)

                    if command_received not in received_commands:
                        if command_received in float_outputs:
                            decoded = struct.unpack(">f", output_data)[0]
                        else:
                            decoded = struct.unpack(">I", output_data)[0] & 0xFF

                        results[command_received] = decoded
                        received_commands.add(command_received)
                except socket.timeout:
                    pass  # continue trying until max_attempts
                except Exception as e:
                    print(f"⚠️ Error receiving/parsing response: {e}")
                finally:
                    max_attempts -= 1

            # Fill missing commands with None
            for command in range(1, 119):
                if command not in results:
                    results[command] = None

            rd.set(str(request_time), json.dumps(results))
            udp_socket.close()

        except Exception as e:
            print("⚠️ Lost connection to UDP server or other issue:", e)
            print("⏳ Attempting to reconnect...")
            time.sleep(2)

        elapsed = time.time() - start_time
        print(f"⏱️ Collect cycle took: {elapsed:.3f}s")
        time.sleep(max(0, 1.0 - elapsed))

threading.Thread(target=collect_data, daemon=True).start() 

@app.route('/now', methods=['GET'])
def get_now():
    target_epoch = int(time.time())  # current epoch timestamp (rounded to second)
    start_time = time.time()

    while True:
        data = rd.get(str(target_epoch))  # Redis keys are strings
        if data is not None:
            break
        time.sleep(0.01)  # Poll every 10 ms (adjust if needed)

    wait_time = round(time.time() - start_time, 3)  # in seconds, rounded to ms

    formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(target_epoch))

    return {
        "closest_epoch": formatted_time,
        "waited_seconds": wait_time,
        "data": json.loads(data)
    } 

@app.route('/logs/<int:epochs>', methods=['GET'])
def get_logs(epochs): 
    # /logs/<int:epochs>?command=int 
    command = request.args.get('command', None) # default is all of them 
    # Validate the command parameter if it was provided
    if command is not None:
        try: 
            command = int(command) 
            if not 1 <= command <= 118:
                return "Command must be between 1 and 118\n", 400
        except ValueError: 
            logging.error("Invalid command parameter; command must be an integer \n")
            return "Invalid command parameter; command must be an integer \n", 400
    
    results = []
    current_time = int(time.time())  # current epoch timestamp (rounded to second) 
    # time.sleep(1) # sleeps a second to get current log 
    stop_time = current_time - epochs 
    keys = rd.keys() 

    # filtering the list to get elements in date range
    keys = [k for k in keys if stop_time <= int(k) <= current_time] 

    for item in keys: 
        data = rd.get(item)  # Redis keys are strings 
        parsed_data = json.loads(data)
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(item))) 
        # If command is provided, only add matching entries
        if command is None or str(command) in parsed_data:
            if command is not None:
                filtered_data = {str(command): parsed_data[str(command)]}
            else:
                filtered_data = parsed_data

            results.append({
                "epoch": formatted_time,
                "data": filtered_data
            })

    sorted_data = sorted(results, key=lambda item: item['epoch']) # list of dictionaries 
    
    return sorted_data

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0',port=5000) 
