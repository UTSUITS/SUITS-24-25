#!/usr/bin/env python3
import json 
import argparse 

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
    parser = argparse.ArgumentParser(description="Write JSON data to a file.") 
    parser.add_argument("--ip", type=str, required=True, help="server's ip address.") 
    parser.add_argument("--port", type=str, required=True, help="server's port number.") 
    # parser.add_argument("--get_data", type=str, required=True, help="command number to get data.") 
    
    args = parser.parse_args()

    data = {
        "SERVER_IP": args.ip, 
        "SERVER_PORT": args.port
    }

    write_json_file("server_info.json", data) 

if __name__ == "__main__":
    main()
