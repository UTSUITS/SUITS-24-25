# Telemetry and EVA Data Reader

## Overview
This script reads telemetry and EVA data from JSON files and allows users to retrieve specific data points using command numbers. It supports:
- Telemetry Data Extraction (Commands 58-102)
- EVA Status Data Extraction (Commands 103-118)
- Command-based Querying for Specific Telemetry/EVA States

## Repository Structure
```
├── TEL_EVA_reader.py        # Python script to read telemetry & EVA data
├── Completed_TELEMETRY.json   # JSON file with telemetry data (can put file path into call on terminal)
└── Completed_EVA.json         # JSON file with EVA status data (can put file path into call on terminal)
```

## Requirements
Ensure you have Python 3.10.11 (what Dom used) installed.

### Install Required Packages
```bash
pip install argparse json logging
```

## How to Use
### 1. View All Available Commands
```bash
structure: python3 reader_file telemetry_data_file eva_data_file --command command_number
example 1:
python3 EVA_display_dom.py public\json_data\teams\2\Completed_TELEMETRY.json public\json_data\teams\2\Completed_EVA.json --command 103
example 2:
python3 TEL_EVA_reader.py Completed_TELEMETRY.json Completed_EVA.json
```
✅ Example Output:
```
Available Telemetry Commands:
58. Current EVA Time (hours)
59. EVA1 - Battery Time Left (Float)
...
103. EVA Started
104. EVA Paused
105. EVA Completed
...
118. SPEC Time (hours)
```

### 2. Retrieve Data for a Specific Command
```bash
python3 TEL_EVA_reader.py Completed_TELEMETRY.json Completed_EVA.json --command_number 106
```
✅ Example Output:
```
Telemetry Data for Command 106: Total EVA Time (hours) → 2
```

## Command Number Reference
| Command Number | Description |
|--------------------|----------------|
| 58 | Current EVA Time (hours) |
| 59-80 | EVA1 Telemetry Data |
| 81-102 | EVA2 Telemetry Data |
| 103 | EVA Started |
| 104 | EVA Paused |
| 105 | EVA Completed |
| 106 | Total EVA Time (hours) |
| 107-118 | EVA System States (UIA, DCU, Rover, SPEC) |

## Debugging
If the script cannot find the JSON files:
```bash
ls Completed_TELEMETRY.json Completed_EVA.json
```
If the script fails with a file not found error, provide the full path:
```bash
python3 telemetry_reader.py /path/to/Completed_TELEMETRY.json /path/to/Completed_EVA.json
```

## Notes
- Data is loaded from `Completed_TELEMETRY.json` and `Completed_EVA.json`.
- The script filters telemetry and EVA data and maps them to command numbers.
- Logs errors if files are missing or commands are invalid.

---
📌 Now you can efficiently retrieve telemetry and EVA status data using command numbers! 🚀

