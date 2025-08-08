"""
Configuration system for CAsMan.

This package provides comprehensive configuration management with support for:
- YAML and JSON configuration files
- Environment variable overrides
- Schema validation
- Runtime configuration updates
- Environment-specific settings
"""

# Import enhanced configuration system
from .core import (
    ConfigManager,
    get_config as get_config_enhanced,
    get_config_manager,
    load_config as load_config_enhanced,
    reload_config,
    set_config,
    validate_config,
)
from .environments import EnvironmentConfig
from .schema import ConfigSchema
from .utils import merge_configs, resolve_config_path

# Import legacy configuration functions for backward compatibility
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Legacy configuration variables and functions
_CONFIG_PATH = os.path.join(Path(__file__).parent.parent.parent, "config.yaml")


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml (legacy function).

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
    Get a configuration value by key, checking environment variables first, then enhanced config, then config file (unified function).

    Args:
        key (str): The config key (e.g., 'CASMAN_PARTS_DB').
        default (str | None): Default value if not found.

    Returns:
        str | None: Value from environment variables, or runtime config, or config.yaml, or default.
    """
    # First check environment variables directly (for test isolation and
    # runtime overrides)
    if key in os.environ:
        return os.environ[key]

    # Then try the enhanced configuration system (for runtime set values)
    try:
        enhanced_value = get_config_enhanced(key, None)
        if enhanced_value is not None:
            return enhanced_value
    except (AttributeError, KeyError, TypeError):
        pass

    # Fall back to config file
    return _CONFIG.get(key, default)


__all__ = [
    # Enhanced configuration system
    "ConfigManager",
    "EnvironmentConfig",
    "ConfigSchema",
    "get_config_enhanced",
    "get_config_manager",
    "load_config_enhanced",
    "merge_configs",
    "reload_config",
    "resolve_config_path",
    "set_config",
    "validate_config",
    # Legacy functions (backward compatibility)
    "get_config",
    "load_config",
]
