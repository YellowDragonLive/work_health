"""Configuration and data persistence manager for Work Health.

Atomic JSON file I/O with schema migration for health data.
All public function signatures are stable — callers in window.py, ui_right.py,
monitor.py, main.py, and questions.py depend on them.
"""

import json
import logging
import os
import shutil
import threading
from datetime import date

# Path constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
HEALTH_DATA_FILE = os.path.join(BASE_DIR, "health_data.json")
JOURNAL_DATA_FILE = os.path.join(BASE_DIR, "journal_data.json")
LIFE_GAME_FILE = os.path.join(os.path.dirname(BASE_DIR), "life_game.json")

SCHEMA_VERSION = 1
"""Current schema version written into health_data and journal_data on save."""

_io_lock = threading.Lock()
"""Module-level lock serialising all file I/O."""


class JsonStore:
    """Encapsulates JSON file I/O with atomic writes and automatic backup.

    Every ``load()`` and ``save()`` acquires the module-level ``_io_lock``.
    """

    def __init__(self, filepath: str, default_factory=None):
        """*filepath*: absolute path. *default_factory*: zero-arg callable for default value."""
        self.filepath = filepath
        self.default_factory = default_factory

    def load(self):
        """Load parsed JSON, or the default on missing/corrupt file."""
        with _io_lock:
            if not os.path.exists(self.filepath):
                return self._default()
            try:
                with open(self.filepath, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except json.JSONDecodeError:
                logging.error("JSON decode error loading %s", self.filepath, exc_info=True)
                return self._default()
            except (OSError, PermissionError):
                logging.error("OS error loading %s", self.filepath, exc_info=True)
                return self._default()

    def save(self, data):
        """Persist *data* atomically via :meth:`_atomic_write`."""
        self._atomic_write(data)

    def _atomic_write(self, data):
        """Write to ``<filepath>.tmp``, backup old file to ``.bak``, then
        ``os.replace()`` the tmp file into place.  Holds ``_io_lock``."""
        with _io_lock:
            tmp_path = self.filepath + ".tmp"
            bak_path = self.filepath + ".bak"
            try:
                with open(tmp_path, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=4, ensure_ascii=False)
                if os.path.exists(self.filepath):
                    shutil.copy2(self.filepath, bak_path)
                os.replace(tmp_path, self.filepath)
            except (OSError, PermissionError):
                logging.error("Atomic write error for %s", self.filepath, exc_info=True)
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

    def _default(self):
        """Return the default value for this store."""
        if self.default_factory is not None:
            return self.default_factory()
        return {}


_life_game_store = JsonStore(LIFE_GAME_FILE, dict)

_config_store = JsonStore(
    CONFIG_FILE,
    lambda: {
        "music_path": None,
        "pomodoro": {
            "default": {"work_duration": 25, "rest_duration": 5},
            "morning_routine": {
                "enabled": True,
                "start_time": "05:00",
                "end_time": "10:00",
                "work_duration": 10,
                "rest_duration": 5,
            },
        },
    },
)

_health_data_store = JsonStore(HEALTH_DATA_FILE, dict)
_journal_data_store = JsonStore(JOURNAL_DATA_FILE, dict)

_NUMERIC_FIELDS = {"weight", "bp_high", "bp_low", "heart_rate"}


def _coerce_record(record: dict) -> dict:
    """Convert string numeric fields in *record* to float where possible."""
    out: dict = {}
    for k, v in record.items():
        if k in _NUMERIC_FIELDS:
            try:
                out[k] = float(v)
            except (ValueError, TypeError):
                out[k] = v
        else:
            out[k] = v
    return out


def migrate_health_data(data: dict) -> dict:
    """Normalise ``health_data.json`` to list-of-records format.

    - Flat dict entries (pre-2026-04) → wrapped in ``[dict]`` with numeric coercion.
    - List entries (2026-04+) → each record's numeric fields coerced to float.
    - Non-dict / non-list values pass through unchanged.
    """
    if not isinstance(data, dict):
        return data
    migrated: dict = {}
    for date_key, value in data.items():
        if isinstance(value, dict):
            migrated[date_key] = [_coerce_record(value)]
        elif isinstance(value, list):
            migrated[date_key] = [
                _coerce_record(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            migrated[date_key] = value
    return migrated


def load_life_game_data() -> dict:
    """Load life-game data from ``life_game.json``."""
    return _life_game_store.load()


def load_config() -> dict:
    """Load application configuration from ``config.json``."""
    return _config_store.load()


def save_config(config: dict) -> None:
    """Persist *config* to ``config.json`` atomically."""
    _config_store.save(config)


def load_health_data() -> dict:
    """Load health data, applying schema migration automatically.

    All date entries are guaranteed to use the list-of-records format.
    """
    return migrate_health_data(_health_data_store.load())


def save_health_data(data: dict) -> None:
    """Persist *data* to ``health_data.json`` atomically.

    A ``"version"`` key is added to the saved payload (caller's dict
    is not mutated).
    """
    to_save = dict(data)
    to_save["version"] = SCHEMA_VERSION
    _health_data_store.save(to_save)


def load_journal_data() -> dict:
    """Load journal data from ``journal_data.json``."""
    return _journal_data_store.load()


def save_journal_data(data: dict) -> None:
    """Persist *data* to ``journal_data.json`` atomically.

    A ``"version"`` key is added to the saved payload (caller's dict
    is not mutated).
    """
    to_save = dict(data)
    to_save["version"] = SCHEMA_VERSION
    _journal_data_store.save(to_save)


def check_today_record_status() -> str:
    """Check whether any health-data entry exists for today.

    Returns ``" (已填)"`` if today has at least one record, otherwise
    ``" (未填!)"``.
    """
    today_str = str(date.today())
    data = load_health_data()
    return " (已填)" if today_str in data else " (未填!)"
