import os
import json
import logging
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
HEALTH_DATA_FILE = os.path.join(BASE_DIR, "health_data.json")
JOURNAL_DATA_FILE = os.path.join(BASE_DIR, "journal_data.json")
LIFE_GAME_FILE = os.path.join(os.path.dirname(BASE_DIR), "life_game.json")

def load_life_game_data():
    if os.path.exists(LIFE_GAME_FILE):
        try:
            with open(LIFE_GAME_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Load Life Game Data Error: {e}")
    return {}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Load Config Error: {e}")
    return {
        "music_path": None,
        "pomodoro": {
            "default": {"work_duration": 25, "rest_duration": 5},
            "morning_routine": {
                "enabled": True,
                "start_time": "05:00",
                "end_time": "10:00",
                "work_duration": 10,
                "rest_duration": 5
            }
        }
    }

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
        except Exception as e:
            logging.error(f"Load Health Data Error: {e}")
    return {}

def save_health_data(data):
    try:
        with open(HEALTH_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logging.error(f"Save Health Data Error: {e}")


def load_journal_data():
    if os.path.exists(JOURNAL_DATA_FILE):
        try:
            with open(JOURNAL_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Load Journal Data Error: {e}")
    return {}


def save_journal_data(data):
    try:
        with open(JOURNAL_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Save Journal Data Error: {e}")

def check_today_record_status():
    """Checks if there's any health data entry for today."""
    today_str = str(date.today())
    data = load_health_data()
    return " (已填)" if today_str in data else " (未填!)"
