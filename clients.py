"""Seed client data loader.

Loads targets from JSON configuration files (default: configs/social_capital.json).
"""

import os
import json
from typing import List, Dict, Any

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "configs", "social_capital.json")


def load_targets(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load investigation configuration and target data from JSON file."""
    if not os.path.exists(config_path):
        # Fallback if relative path from cwd was passed
        if os.path.exists(os.path.join(os.getcwd(), config_path)):
            config_path = os.path.join(os.getcwd(), config_path)
        else:
            raise FileNotFoundError(f"Configuration file not found at '{config_path}'")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def get_clients(config_path: str = DEFAULT_CONFIG_PATH) -> List[Dict[str, Any]]:
    """Return a list of targets from the given config file."""
    data = load_targets(config_path)
    return [dict(t) for t in data.get("targets", [])]


# Backwards compatibility for existing imports
try:
    CLIENTS: List[Dict[str, Any]] = get_clients()
except Exception:
    CLIENTS: List[Dict[str, Any]] = []
