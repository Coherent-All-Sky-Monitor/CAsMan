# Config Package

Documentation for the `casman.config` package.

## Overview

Configuration system for CAsMan.

Provides simple configuration management with:
- YAML configuration file loading
- Environment variable overrides

## __Init__ Module Details

Provides simple configuration management with:
- YAML configuration file loading
- Environment variable overrides

## Functions

### get_config

**Signature:** `get_config(key: str, default: Any) -> Any`

Get a configuration value by key, checking environment variables first, then config file. Supports dot notation for nested values (e.g., 'web_app.dev.port').

**Returns:**

Any: Value from environment variables, or config.yaml, or default.

---
