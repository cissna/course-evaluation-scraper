import json
import os

def load_json_file(filepath: str) -> dict:
    """Safely loads a JSON file, creating it if it doesn't exist."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {} # Return empty dict if file is empty or corrupt

def save_json_file(filepath: str, data: dict):
    """Saves a dictionary to a JSON file with pretty printing."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)