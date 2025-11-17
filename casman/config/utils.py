"""
Configuration utilities for CAsMan.

Provides utility functions for configuration management, path resolution,
and configuration merging.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union


def resolve_config_path(path: Union[str, Path]) -> Path:
    """
    Resolve a configuration file path, handling relative paths and environment variables.

    Parameters
    ----------
    path : Union[str, Path]
        Path to resolve (can contain environment variables).

    Returns
    -------
    Path
        Resolved absolute path.
    """
    path_str = str(path)

    # Expand environment variables
    expanded_path = os.path.expandvars(path_str)

    # Expand user home directory
    expanded_path = os.path.expanduser(expanded_path)

    # Convert to Path object
    resolved_path = Path(expanded_path)

    # If relative path, make it relative to project root
    if not resolved_path.is_absolute():
        project_root = Path(__file__).parent.parent.parent
        resolved_path = project_root / resolved_path

    return resolved_path


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries.

    Later configurations override earlier ones. Nested dictionaries are merged recursively.

    Parameters
    ----------
    *configs : Dict[str, Any]
        Configuration dictionaries to merge.

    Returns
    -------
    Dict[str, Any]
        Merged configuration dictionary.
    """
    result: Dict[str, Any] = {}

    for config in configs:
        if not isinstance(config, dict):
            continue

        _deep_merge(result, config)

    return result


def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    Recursively merge source dictionary into target dictionary.

    Parameters
    ----------
    target : Dict[str, Any]
        Target dictionary to merge into.
    source : Dict[str, Any]
        Source dictionary to merge from.
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


def flatten_config(
    config: Dict[str, Any], prefix: str = "", separator: str = "."
) -> Dict[str, Any]:
    """
    Flatten a nested configuration dictionary.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary to flatten.
    prefix : str, optional
        Prefix to add to keys.
    separator : str, optional
        Separator between nested keys.

    Returns
    -------
    Dict[str, Any]
        Flattened configuration dictionary.
    """
    flattened = {}

    for key, value in config.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key

        if isinstance(value, dict):
            flattened.update(flatten_config(value, new_key, separator))
        else:
            flattened[new_key] = value

    return flattened


def unflatten_config(flattened: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """
    Unflatten a configuration dictionary.

    Parameters
    ----------
    flattened : Dict[str, Any]
        Flattened configuration dictionary.
    separator : str, optional
        Separator between nested keys.

    Returns
    -------
    Dict[str, Any]
        Unflattened configuration dictionary.
    """
    result: Dict[str, Any] = {}

    for key, value in flattened.items():
        keys = key.split(separator)
        target = result

        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value

    return result


def get_config_diff(config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the difference between two configuration dictionaries.

    Parameters
    ----------
    config1 : Dict[str, Any]
        First configuration.
    config2 : Dict[str, Any]
        Second configuration.

    Returns
    -------
    Dict[str, Any]
        Dictionary showing differences (added, removed, changed).
    """
    flat1 = flatten_config(config1)
    flat2 = flatten_config(config2)

    all_keys = set(flat1.keys()) | set(flat2.keys())

    diff: Dict[str, Dict[str, Any]] = {"added": {}, "removed": {}, "changed": {}}

    for key in all_keys:
        if key not in flat1:
            diff["added"][key] = flat2[key]
        elif key not in flat2:
            diff["removed"][key] = flat1[key]
        elif flat1[key] != flat2[key]:
            diff["changed"][key] = {"old": flat1[key], "new": flat2[key]}

    return diff


def validate_config_paths(config: Dict[str, Any]) -> Dict[str, bool]:
    """
    Validate that file paths in configuration exist.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary.

    Returns
    -------
    Dict[str, bool]
        Dictionary mapping path keys to existence status.
    """
    path_keys = [
        "CASMAN_PARTS_DB",
        "CASMAN_ASSEMBLED_DB",
        "logging.file_path",
        "barcode.output_directory",
    ]

    results = {}

    for key in path_keys:
        value: Any = None
        if "." in key:
            # Handle nested keys
            keys = key.split(".")
            temp_value: Any = config
            for k in keys:
                if isinstance(temp_value, dict) and k in temp_value:
                    temp_value = temp_value[k]
                else:
                    temp_value = None
                    break
            value = temp_value
        else:
            value = config.get(key)

        if value is not None and isinstance(value, (str, Path)):
            try:
                path = resolve_config_path(value)
                results[key] = path.exists()
            except (OSError, ValueError):
                results[key] = False
        else:
            results[key] = False

    return results


def setup_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """Setup logging configuration from config.

    Parameters
    ----------
    config : Dict[str, Any], optional
        Configuration dictionary. If not provided, loads from default config.
    """
    import logging
    import logging.handlers

    if config is None:
        from casman.config.core import get_config as load_config
        level_str = load_config("logging.level", "INFO")
        log_format = load_config("logging.format",
                                 "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_path = load_config("logging.file_path", None)
        max_file_size_mb = load_config("logging.max_file_size_mb", 10)
        backup_count = load_config("logging.backup_count", 5)
    else:
        logging_config = config.get("logging", {})
        level_str = logging_config.get("level", "INFO")
        log_format = logging_config.get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_path = logging_config.get("file_path", None)
        max_file_size_mb = logging_config.get("max_file_size_mb", 10)
        backup_count = logging_config.get("backup_count", 5)

    # Convert level string to logging constant
    level = getattr(logging, level_str.upper(), logging.INFO)

    # Setup handlers
    handlers: list = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)

    # File handler with rotation if file_path specified
    if file_path:
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers,
        force=True  # Override any existing configuration
    )


def create_config_directories(config: Dict[str, Any]) -> None:
    """
    Create directories for paths specified in configuration.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary.
    """
    path_keys = ["logging.file_path", "barcode.output_directory"]

    for key in path_keys:
        value: Any = None
        if "." in key:
            # Handle nested keys
            keys = key.split(".")
            temp_value: Any = config
            for k in keys:
                if isinstance(temp_value, dict) and k in temp_value:
                    temp_value = temp_value[k]
                else:
                    temp_value = None
                    break
            value = temp_value
        else:
            value = config.get(key)

        if value is not None and isinstance(value, (str, Path)):
            try:
                path = resolve_config_path(value)

                # Create parent directory if it's a file path
                if key.endswith("file_path"):
                    path.parent.mkdir(parents=True, exist_ok=True)
                else:
                    path.mkdir(parents=True, exist_ok=True)
            except (OSError, ValueError) as e:
                print(f"Warning: Could not create directory for {key}: {e}")
