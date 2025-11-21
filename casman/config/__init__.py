"""Configuration system for CAsMan.

Provides simple configuration management with:
- YAML configuration file loading
- Environment variable overrides
"""

import os
from pathlib import Path
from typing import Any

import yaml

# Configuration variables
_CONFIG_PATH = os.path.join(Path(__file__).parent.parent.parent, "config.yaml")


# Load configuration on module import (legacy behavior)
try:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError("config.yaml must contain a top-level dictionary")
        _CONFIG = data
except Exception:
    _CONFIG = {}


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value by key, checking environment variables first, then config file.

    Supports dot notation for nested values (e.g., 'web_app.dev.port').

    Args:
        key (str): The config key (e.g., 'CASMAN_PARTS_DB' or 'web_app.dev.port').
        default (Any): Default value if not found.

    Returns:
        Any: Value from environment variables, or config.yaml, or default.
    """
    # First check environment variables directly (for test isolation and runtime overrides)
    if key in os.environ:
        return os.environ[key]

    # Support dot notation for nested config values
    if "." in key:
        keys = key.split(".")
        value = _CONFIG
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    # Fall back to config file for simple keys
    return _CONFIG.get(key, default)


__all__ = [
    "get_config",
]
