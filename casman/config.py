"""
config.py - LEGACY MODULE

Utility to load configuration from config.yaml and provide access to environment variables/settings.

This module is maintained for backward compatibility. New code should use
the enhanced configuration system in casman.config package.
"""

import os
from typing import Any, Dict, Optional

import yaml

_CONFIG_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(__file__)),
    "config.yaml")


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml.

    Returns:
        dict: The configuration dictionary loaded from YAML.
    """
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError("config.yaml must contain a top-level dictionary")
        return data


# Load configuration on module import (legacy behavior)
try:
    _CONFIG = load_config()
except Exception:
    _CONFIG = {}


def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a configuration value by key, falling back to environment variable, then default.

    Args:
        key (str): The config key (e.g., 'CASMAN_PARTS_DB').
        default (str | None): Default value if not found.

    Returns:
        str | None: Value from config.yaml, or os.environ, or default.
    """
    return os.environ.get(key, _CONFIG.get(key, default))
