"""
Core configuration management functionality for CAsMan.

Provides the main ConfigManager class and primary configuration functions.
"""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml


class ConfigManager:
    """
    Central configuration manager for CAsMan.

    Supports YAML and JSON configuration files with environment variable overrides,
    schema validation, and runtime updates.
    """

    def __init__(self, config_paths: Optional[List[Union[str, Path]]] = None) -> None:
        """
        Initialize the configuration manager.

        Parameters
        ----------
        config_paths : List[Union[str, Path]], optional
            List of configuration file paths to load. If None, uses default paths.
        """
        self._config: Dict[str, Any] = {}
        self._config_paths: List[Path] = []
        self._watchers: List[Callable[[Dict[str, Any]], None]] = []

        if config_paths is None:
            config_paths = self._get_default_config_paths()

        self._config_paths = [Path(p) for p in config_paths]
        self.reload()

    def _get_default_config_paths(self) -> List[Path]:
        """Get default configuration file paths."""
        base_dir = Path(__file__).parent.parent.parent
        return [
            base_dir / "config.yaml",
            base_dir / "config.json",
        ]

    def reload(self) -> None:
        """Reload configuration from all configured files."""
        self._config = {}

        for config_path in self._config_paths:
            if config_path.exists():
                try:
                    config_data = self._load_file(config_path)
                    self._merge_config(config_data)
                except (
                    FileNotFoundError,
                    yaml.YAMLError,
                    json.JSONDecodeError,
                    ValueError,
                ) as e:
                    print(f"Warning: Failed to load config from {config_path}: {e}")

        # Apply environment variable overrides
        self._apply_env_overrides()

        # Notify watchers
        for watcher in self._watchers:
            try:
                watcher(self._config)
            except (TypeError, AttributeError) as e:
                print(f"Warning: Config watcher failed: {e}")

    def _load_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from a file."""
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            elif file_path.suffix.lower() == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {file_path.suffix}")

        if not isinstance(data, dict):
            raise ValueError(
                f"Config file must contain a top-level dictionary: {file_path}"
            )

        return data

    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """Merge new configuration data into existing config."""

        def merge_dicts(target: Dict[str, Any], source: Dict[str, Any]) -> None:
            for key, value in source.items():
                if (
                    key in target
                    and isinstance(target[key], dict)
                    and isinstance(value, dict)
                ):
                    merge_dicts(target[key], value)
                else:
                    target[key] = value

        merge_dicts(self._config, new_config)

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        env_prefix = "CASMAN_"

        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # Store both the full key and the key without prefix for
                # flexibility
                self._config[key] = value  # Full key (e.g., "CASMAN_PARTS_DB")
                config_key = key[len(env_prefix):]
                # Key without prefix (e.g., "PARTS_DB")
                self._config[config_key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Parameters
        ----------
        key : str
            Configuration key (supports dot notation for nested values).
        default : Any, optional
            Default value if key is not found.

        Returns
        -------
        Any
            Configuration value or default.
        """
        if "." in key:
            return self._get_nested(key, default)

        return self._config.get(key, default)

    def _get_nested(self, key: str, default: Any = None) -> Any:
        """Get a nested configuration value using dot notation."""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Parameters
        ----------
        key : str
            Configuration key (supports dot notation for nested values).
        value : Any
            Value to set.
        """
        if "." in key:
            self._set_nested(key, value)
        else:
            self._config[key] = value

    def _set_nested(self, key: str, value: Any) -> None:
        """Set a nested configuration value using dot notation."""
        keys = key.split(".")
        target = self._config

        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            elif not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration data."""
        return self._config.copy()

    def add_watcher(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback to be notified when configuration changes.

        Parameters
        ----------
        callback : Callable[[Dict[str, Any]], None]
            Function to call with updated config dict.
        """
        self._watchers.append(callback)

    def remove_watcher(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a configuration watcher."""
        if callback in self._watchers:
            self._watchers.remove(callback)

    def validate(self, schema: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate current configuration against a schema.

        Parameters
        ----------
        schema : Dict[str, Any], optional
            JSON schema to validate against.

        Returns
        -------
        bool
            True if configuration is valid.
        """
        if schema is None:
            return True

        try:
            # Try importing jsonschema for validation
            import jsonschema  # type: ignore

            jsonschema.validate(self._config, schema)
            return True
        except ImportError:
            print("Warning: jsonschema not available for validation")
            return True
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value from the global config manager.

    Parameters
    ----------
    key : str
        Configuration key.
    default : Any, optional
        Default value if key is not found.

    Returns
    -------
    Any
        Configuration value or default.
    """
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any) -> None:
    """
    Set a configuration value in the global config manager.

    Parameters
    ----------
    key : str
        Configuration key.
    value : Any
        Value to set.
    """
    get_config_manager().set(key, value)


def load_config() -> Dict[str, Any]:
    """
    Load and return all configuration data.

    Returns
    -------
    Dict[str, Any]
        Complete configuration dictionary.
    """
    return get_config_manager().get_all()


def reload_config() -> None:
    """Reload configuration from files."""
    get_config_manager().reload()


def validate_config(schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate current configuration.

    Parameters
    ----------
    schema : Dict[str, Any], optional
        JSON schema to validate against.

    Returns
    -------
    bool
        True if configuration is valid.
    """
    return get_config_manager().validate(schema)
