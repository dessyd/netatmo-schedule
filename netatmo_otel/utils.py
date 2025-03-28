import os
import json
from .config import DEFAULT_ENV_FILE


def update_env_file(key, value, env_file=DEFAULT_ENV_FILE):
    """Update a specific key in the .env file with a new value"""
    try:
        # Check if file exists, create it if it doesn't
        if not os.path.exists(env_file):
            with open(env_file, "w"):
                pass

        with open(env_file, "r") as file:
            lines = file.readlines()

        # Update the specific key
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break

        # If key doesn't exist, add it
        if not found:
            lines.append(f"{key}={value}\n")

        # Write the updated content back to the .env file
        with open(env_file, "w") as file:
            file.writelines(lines)
    except Exception as e:
        print(f"Warning: Could not update {key} in {env_file} file: {e}")


def save_state(filename, state):
    """Save state to a JSON file"""
    try:
        with open(filename, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Error saving state: {e}")


def load_state(filename):
    """Load state from a JSON file"""
    if not os.path.exists(filename):
        return {}

    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading state: {e}")
        return {}
