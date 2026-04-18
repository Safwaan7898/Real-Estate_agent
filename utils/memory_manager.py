"""Persistent user preferences manager using JSON storage."""
import json
import os
from pathlib import Path
from typing import Any

PREFS_FILE = Path(__file__).parent.parent / "data" / "user_preferences.json"


def _load() -> dict:
    if PREFS_FILE.exists():
        try:
            return json.loads(PREFS_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save(data: dict) -> None:
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREFS_FILE.write_text(json.dumps(data, indent=2))


def save_preference(key: str, value: Any) -> str:
    """Save a single preference key-value pair."""
    prefs = _load()
    prefs[key] = value
    _save(prefs)
    return f"Saved: {key} = {value}"


def get_preferences() -> dict:
    """Return all saved preferences."""
    return _load()


def delete_preference(key: str) -> str:
    """Delete a preference by key."""
    prefs = _load()
    if key in prefs:
        del prefs[key]
        _save(prefs)
        return f"Deleted preference: {key}"
    return f"Key '{key}' not found."


def clear_preferences() -> str:
    """Clear all preferences."""
    _save({})
    return "All preferences cleared."
