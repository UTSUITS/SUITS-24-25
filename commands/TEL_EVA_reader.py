import json
import argparse
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def load_json(filename: str):
    """Loads JSON data from a file."""
    full_path = os.path.abspath(filename)
    print(f"DEBUG: Looking for file at {full_path}")

    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
        logging.info(f"JSON file '{filename}' loaded successfully.")
        return data
    except FileNotFoundError:
        logging.error(f"File '{filename}' not found at {full_path}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON file: {filename}")
        return None

def extract_telemetry_data(telemetry_data, eva_data):
    """Extracts telemetry data for EVA time, EVA1, EVA2, and EVA states."""
    if not telemetry_data or "telemetry" not in telemetry_data:
        logging.warning("No telemetry data found.")
        return {}

    telemetry = telemetry_data["telemetry"]
    eva = eva_data.get("eva", {})

    telemetry_dict = {
        58: ("Current EVA Time (hours)", telemetry.get("eva_time", "N/A")),
        **{num: (f"EVA1 - {key.replace('_', ' ').title()} (Float)", telemetry["eva1"].get(key, "N/A"))
           for num, key in zip(range(59, 81), telemetry["eva1"].keys())},
        **{num: (f"EVA2 - {key.replace('_', ' ').title()} (Float)", telemetry["eva2"].get(key, "N/A"))
           for num, key in zip(range(81, 103), telemetry["eva2"].keys())},
        103: ("EVA Started", eva.get("started", "N/A")),
        104: ("EVA Paused", eva.get("paused", "N/A")),
        105: ("EVA Completed", eva.get("completed", "N/A")),
        106: ("Total EVA Time (hours)", eva.get("total_time", "N/A")),
        107: ("UIA Started", eva["uia"].get("started", "N/A")),
        108: ("UIA Completed", eva["uia"].get("completed", "N/A")),
        109: ("UIA Time (hours)", eva["uia"].get("time", "N/A")),
        110: ("DCU Started", eva["dcu"].get("started", "N/A")),
        111: ("DCU Completed", eva["dcu"].get("completed", "N/A")),
        112: ("DCU Time (hours)", eva["dcu"].get("time", "N/A")),
        113: ("Rover Started", eva["rover"].get("started", "N/A")),
        114: ("Rover Completed", eva["rover"].get("completed", "N/A")),
        115: ("Rover Time (hours)", eva["rover"].get("time", "N/A")),
        116: ("SPEC Started", eva["spec"].get("started", "N/A")),
        117: ("SPEC Completed", eva["spec"].get("completed", "N/A")),
        118: ("SPEC Time (hours)", eva["spec"].get("time", "N/A"))
    }
    return telemetry_dict

def display_telemetry_options(telemetry_data):
    """Displays the available telemetry command numbers."""
    print("\nAvailable Telemetry Commands:")
    for key, (label, _) in telemetry_data.items():
        print(f"{key}. {label}")

def get_telemetry_by_number(telemetry_data, command_number):
    """Retrieves telemetry data by command number."""
    if command_number in telemetry_data:
        return telemetry_data[command_number]
    else:
        logging.error("Invalid command number. Please enter a valid number from the list.")
        return None

def main():
    parser = argparse.ArgumentParser(description="Telemetry Data Reader")
    parser.add_argument("telemetry_file", type=str, help="Path to the TELEMETRY JSON file")
    parser.add_argument("eva_file", type=str, help="Path to the EVA JSON file")
    parser.add_argument("--command_number", type=int, help="Command number to retrieve telemetry data", required=False)

    args = parser.parse_args()

    telemetry_data = load_json(args.telemetry_file)
    eva_data = load_json(args.eva_file)
    
    if not telemetry_data or not eva_data:
        return

    telemetry_dict = extract_telemetry_data(telemetry_data, eva_data)

    if args.command_number:
        result = get_telemetry_by_number(telemetry_dict, args.command_number)
        if result:
            print(f"\nTelemetry Data for Command {args.command_number}: {result[0]} → {result[1]}")
        else:
            print("\nInvalid command number. Please choose from the list below:")
            display_telemetry_options(telemetry_dict)
    else:
        display_telemetry_options(telemetry_dict)

if __name__ == "__main__":
    main()
