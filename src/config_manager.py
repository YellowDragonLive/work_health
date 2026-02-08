import os
import json
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
HEALTH_DATA_FILE = os.path.join(BASE_DIR, "health_data.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"music_path": None, "work_duration": 25}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logging.error(f"Save Config Error: {e}")

def load_health_data():
    if os.path.exists(HEALTH_DATA_FILE):
        try:
            with open(HEALTH_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_health_data(data):
    try:
        with open(HEALTH_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logging.error(f"Save Health Data Error: {e}")
