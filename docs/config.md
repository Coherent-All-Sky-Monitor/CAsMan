# Config Module

config.py - LEGACY MODULE

Utility to load configuration from config.yaml and provide access to environment variables/settings.

This module is maintained for backward compatibility. New code should use
the enhanced configuration system in casman.config package.

## Functions

### load_config

**Signature:** `load_config()`

Load configuration from config.yaml. Returns: dict: The configuration dictionary loaded from YAML.

---

### get_config

**Signature:** `get_config(key, default)`

Get a configuration value by key, falling back to environment variable, then default. Args: key (str): The config key (e.g., 'CASMAN_PARTS_DB'). default (str | None): Default value if not found. Returns: str | None: Value from config.yaml, or os.environ, or default.

---
