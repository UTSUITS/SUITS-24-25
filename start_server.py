#!/usr/bin/env python3
import json
import re
import subprocess
import argparse

def extract_ip_port(output):
    """
    Extracts the IP address and port from server output using regex.
    """

    # Update the regex pattern to be more flexible with whitespace or line breaks
    match = re.search(r"Launching\s*Server\s*at\s*IP:\s*([\d\.]+):(\d+)", output)
    if match:
        return match.group(1), match.group(2)
    else: 
        raise ValueError("Could not find IP and Port in the given output")

def write_json_file(filename, data): 
    """ 
    Writes the given data to a JSON file.
    :param filename: Name of the JSON file.
    :param data: Dictionary to be written to the file.
    """ 
    try:
        with open(filename, 'w', encoding='utf-8') as file: 
            json.dump(data, file, indent=4)
        print(f"Data successfully written to {filename}")
    except Exception as e:
        print(f"Error writing JSON file: {e}")

def main():
    # Start the server first, then run this script, you might need to do chmod +x path/to/server
    # We will hardcode the server path when running it in raspberry pi 
    parser = argparse.ArgumentParser(description="Extract IP and Port from server output and save to JSON.")
    parser.add_argument("server_path", type=str, help="Path to the server executable (e.g., /path/to/server)")
    args = parser.parse_args()
    
    # Start the subprocess and capture output in real-time
    process = subprocess.Popen(args.server_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) # AI used

    # Iterate through the output lines to find the relevant info
    stdout, stderr = process.communicate()  # Capture the output

    # Extract IP and Port
    try:
        data = extract_ip_port(stdout)
        server_data = {
        "SERVER_IP": data[0], 
        "SERVER_PORT": data[1]
        }
        write_json_file("server_info.json", server_data) 
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
