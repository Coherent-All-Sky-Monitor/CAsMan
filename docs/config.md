# Config Package

Documentation for the `casman.config` package.

## Overview

Configuration system for CAsMan.

This package provides comprehensive configuration management with support for:

- YAML and JSON configuration files

- Environment variable overrides

- Schema validation

- Runtime configuration updates

- Environment-specific settings

## Modules

### utils

Configuration utilities for CAsMan.

Provides utility functions for configuration management, path resolution,
and configuration merging.

**Functions:**

- `resolve_config_path()` - Resolve a configuration file path, handling relative paths and environment variables

- `merge_configs()` - Merge multiple configuration dictionaries

- `flatten_config()` - Flatten a nested configuration dictionary

- `unflatten_config()` - Unflatten a configuration dictionary

- `get_config_diff()` - Get the difference between two configuration dictionaries

- `validate_config_paths()` - Validate that file paths in configuration exist

- `create_config_directories()` - Create directories for paths specified in configuration

### schema

Configuration schema definitions for CAsMan.

Provides JSON schema validation for configuration files.

**Functions:**

- `get_default_schema()` - Get the default CAsMan configuration schema

- `validate_config()` - Validate configuration against schema

- `get_config_template()` - Get a configuration template with default values

**Classes:**

- `ConfigSchema` - Configuration schema management class

### environments

Environment-specific configuration management for CAsMan.

Provides utilities for managing configuration across different environments
(development, testing, production).

**Functions:**

- `get_config_files()` - Get list of configuration files for current environment

- `get_environment_variables()` - Get environment variables relevant to CAsMan configuration

- `create_environment_config()` - Create an environment-specific configuration file

- `get_current_environment()` - Get the current environment name

- `set_environment()` - Set the current environment

- `get_environment_config_template()` - Get a configuration template for a specific environment

**Classes:**

- `EnvironmentConfig` - Environment-specific configuration manager

### core

Core configuration management functionality for CAsMan.

Provides the main ConfigManager class and primary configuration functions.

**Functions:**

- `get_config_manager()` - Get the global configuration manager instance

- `get_config()` - Get a configuration value from the global config manager

- `set_config()` - Set a configuration value in the global config manager

- `load_config()` - Load and return all configuration data

- `reload_config()` - Reload configuration from files

- `validate_config()` - Validate current configuration

- `reload()` - Reload configuration from all configured files

- `get()` - Get a configuration value

- `set()` - Set a configuration value

- `get_all()` - Get all configuration data

- `add_watcher()` - Add a callback to be notified when configuration changes

- `remove_watcher()` - Remove a configuration watcher

- `validate()` - Validate current configuration against a schema

- `merge_dicts()` - No docstring available

**Classes:**

- `ConfigManager` - Central configuration manager for CAsMan

## __Init__ Module Details

This package provides comprehensive configuration management with support for:

- YAML and JSON configuration files

- Environment variable overrides

- Schema validation

- Runtime configuration updates

- Environment-specific settings

## Functions

### load_config

**Signature:** `load_config() -> Dict[str, Any]`

Load configuration from config.yaml (legacy function).

**Returns:**

dict: The configuration dictionary loaded from YAML.

---

### get_config

**Signature:** `get_config(key: str, default: Optional[str]) -> Optional[str]`

Get a configuration value by key, checking environment variables first, then enhanced config, then config file (unified function).

**Returns:**

str | None: Value from environment variables, or runtime config, or config.yaml, or default.

---

## Utils Module Details

Provides utility functions for configuration management, path resolution,
and configuration merging.

## Functions

### resolve_config_path

**Signature:** `resolve_config_path(path: Union[str, Path]) -> Path`

Resolve a configuration file path, handling relative paths and environment variables.

**Parameters:**

path : Union[str, Path]
Path to resolve (can contain environment variables).

**Returns:**

Path
Resolved absolute path.

---

### merge_configs

**Signature:** `merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]`

Merge multiple configuration dictionaries. Later configurations override earlier ones. Nested dictionaries are merged recursively.

**Parameters:**

*configs : Dict[str, Any]
Configuration dictionaries to merge.

**Returns:**

Dict[str, Any]
Merged configuration dictionary.

---

### flatten_config

**Signature:** `flatten_config(config: Dict[str, Any], prefix: str, separator: str) -> Dict[str, Any]`

Flatten a nested configuration dictionary.

**Parameters:**

config : Dict[str, Any]
Configuration dictionary to flatten.
prefix : str, optional
Prefix to add to keys.
separator : str, optional
Separator between nested keys.

**Returns:**

Dict[str, Any]
Flattened configuration dictionary.

---

### unflatten_config

**Signature:** `unflatten_config(flattened: Dict[str, Any], separator: str) -> Dict[str, Any]`

Unflatten a configuration dictionary.

**Parameters:**

flattened : Dict[str, Any]
Flattened configuration dictionary.
separator : str, optional
Separator between nested keys.

**Returns:**

Dict[str, Any]
Unflattened configuration dictionary.

---

### get_config_diff

**Signature:** `get_config_diff(config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]`

Get the difference between two configuration dictionaries.

**Parameters:**

config1 : Dict[str, Any]
First configuration.
config2 : Dict[str, Any]
Second configuration.

**Returns:**

Dict[str, Any]
Dictionary showing differences (added, removed, changed).

---

### validate_config_paths

**Signature:** `validate_config_paths(config: Dict[str, Any]) -> Dict[str, bool]`

Validate that file paths in configuration exist.

**Parameters:**

config : Dict[str, Any]
Configuration dictionary.

**Returns:**

Dict[str, bool]
Dictionary mapping path keys to existence status.

---

### create_config_directories

**Signature:** `create_config_directories(config: Dict[str, Any]) -> None`

Create directories for paths specified in configuration.

**Parameters:**

config : Dict[str, Any]
Configuration dictionary.

---

## Schema Module Details

Provides JSON schema validation for configuration files.

## Functions

### get_default_schema

*@staticmethod*

**Signature:** `get_default_schema() -> Dict[str, Any]`

Get the default CAsMan configuration schema.

---

### validate_config

*@staticmethod*

**Signature:** `validate_config(config: Dict[str, Any], schema: Optional[Dict[str, Any]]) -> tuple[bool, str]`

Validate configuration against schema.

**Parameters:**

config : Dict[str, Any]
Configuration to validate.
schema : Dict[str, Any], optional
Schema to validate against. Uses default if None.

**Returns:**

tuple[bool, str]
(is_valid, error_message)

---

### get_config_template

*@staticmethod*

**Signature:** `get_config_template() -> Dict[str, Any]`

Get a configuration template with default values.

---

## Classes

### ConfigSchema

**Class:** `ConfigSchema`

Configuration schema management class.

#### Methods

##### get_default_schema

*@staticmethod*

**Signature:** `get_default_schema() -> Dict[str, Any]`

Get the default CAsMan configuration schema.

---

##### validate_config

*@staticmethod*

**Signature:** `validate_config(config: Dict[str, Any], schema: Optional[Dict[str, Any]]) -> tuple[bool, str]`

Validate configuration against schema.

**Parameters:**

config : Dict[str, Any]
Configuration to validate.
schema : Dict[str, Any], optional
Schema to validate against. Uses default if None.

**Returns:**

tuple[bool, str]
(is_valid, error_message)

---

##### get_config_template

*@staticmethod*

**Signature:** `get_config_template() -> Dict[str, Any]`

Get a configuration template with default values.

---

---

## Environments Module Details

Provides utilities for managing configuration across different environments
(development, testing, production).

## Functions

### get_config_files

**Signature:** `get_config_files() -> list[Path]`

Get list of configuration files for current environment.

**Returns:**

list[Path]
Ordered list of config files to load (base first, then environment-specific).

---

### get_environment_variables

**Signature:** `get_environment_variables() -> Dict[str, str]`

Get environment variables relevant to CAsMan configuration.

**Returns:**

Dict[str, str]
Dictionary of CAsMan-related environment variables.

---

### create_environment_config

**Signature:** `create_environment_config(environment: str, config_data: Dict[str, Any]) -> Path`

Create an environment-specific configuration file.

**Parameters:**

environment : str
Environment name (development, testing, production).
config_data : Dict[str, Any]
Configuration data to write.

**Returns:**

Path
Path to the created configuration file.

---

### get_current_environment

**Signature:** `get_current_environment() -> str`

Get the current environment name.

---

### set_environment

**Signature:** `set_environment(environment: str) -> None`

Set the current environment.

**Parameters:**

environment : str
Environment name to set.

---

### get_environment_config_template

**Signature:** `get_environment_config_template(environment: str) -> Dict[str, Any]`

Get a configuration template for a specific environment.

**Parameters:**

environment : str
Environment name.

**Returns:**

Dict[str, Any]
Environment-specific configuration template.

---

## Classes

### EnvironmentConfig

**Class:** `EnvironmentConfig`

Environment-specific configuration manager.

Supports loading different configuration files based on the current environment.

#### Methods

##### __init__

**Signature:** `__init__(base_config_dir: Optional[Path]) -> None`

Initialize environment configuration.

**Parameters:**

base_config_dir : Path, optional
Base directory containing configuration files.

---

##### get_config_files

**Signature:** `get_config_files() -> list[Path]`

Get list of configuration files for current environment.

**Returns:**

list[Path]
Ordered list of config files to load (base first, then environment-specific).

---

##### get_environment_variables

**Signature:** `get_environment_variables() -> Dict[str, str]`

Get environment variables relevant to CAsMan configuration.

**Returns:**

Dict[str, str]
Dictionary of CAsMan-related environment variables.

---

##### create_environment_config

**Signature:** `create_environment_config(environment: str, config_data: Dict[str, Any]) -> Path`

Create an environment-specific configuration file.

**Parameters:**

environment : str
Environment name (development, testing, production).
config_data : Dict[str, Any]
Configuration data to write.

**Returns:**

Path
Path to the created configuration file.

---

##### get_current_environment

**Signature:** `get_current_environment() -> str`

Get the current environment name.

---

##### set_environment

**Signature:** `set_environment(environment: str) -> None`

Set the current environment.

**Parameters:**

environment : str
Environment name to set.

---

##### get_environment_config_template

**Signature:** `get_environment_config_template(environment: str) -> Dict[str, Any]`

Get a configuration template for a specific environment.

**Parameters:**

environment : str
Environment name.

**Returns:**

Dict[str, Any]
Environment-specific configuration template.

---

---

## Core Module Details

Provides the main ConfigManager class and primary configuration functions.

## Functions

### get_config_manager

**Signature:** `get_config_manager() -> ConfigManager`

Get the global configuration manager instance.

---

### get_config

**Signature:** `get_config(key: str, default: Any) -> Any`

Get a configuration value from the global config manager.

**Parameters:**

key : str
Configuration key.
default : Any, optional
Default value if key is not found.

**Returns:**

Any
Configuration value or default.

---

### set_config

**Signature:** `set_config(key: str, value: Any) -> None`

Set a configuration value in the global config manager.

**Parameters:**

key : str
Configuration key.
value : Any
Value to set.

---

### load_config

**Signature:** `load_config() -> Dict[str, Any]`

Load and return all configuration data.

**Returns:**

Dict[str, Any]
Complete configuration dictionary.

---

### reload_config

**Signature:** `reload_config() -> None`

Reload configuration from files.

---

### validate_config

**Signature:** `validate_config(schema: Optional[Dict[str, Any]]) -> bool`

Validate current configuration.

**Parameters:**

schema : Dict[str, Any], optional
JSON schema to validate against.

**Returns:**

bool
True if configuration is valid.

---

### reload

**Signature:** `reload() -> None`

Reload configuration from all configured files.

---

### get

**Signature:** `get(key: str, default: Any) -> Any`

Get a configuration value.

**Parameters:**

key : str
Configuration key (supports dot notation for nested values).
default : Any, optional
Default value if key is not found.

**Returns:**

Any
Configuration value or default.

---

### set

**Signature:** `set(key: str, value: Any) -> None`

Set a configuration value.

**Parameters:**

key : str
Configuration key (supports dot notation for nested values).
value : Any
Value to set.

---

### get_all

**Signature:** `get_all() -> Dict[str, Any]`

Get all configuration data.

---

### add_watcher

**Signature:** `add_watcher(callback: Callable[[Dict[str, Any]], None]) -> None`

Add a callback to be notified when configuration changes.

**Parameters:**

callback : Callable[[Dict[str, Any]], None]
Function to call with updated config dict.

---

### remove_watcher

**Signature:** `remove_watcher(callback: Callable[[Dict[str, Any]], None]) -> None`

Remove a configuration watcher.

---

### validate

**Signature:** `validate(schema: Optional[Dict[str, Any]]) -> bool`

Validate current configuration against a schema.

**Parameters:**

schema : Dict[str, Any], optional
JSON schema to validate against.

**Returns:**

bool
True if configuration is valid.

---

### merge_dicts

**Signature:** `merge_dicts(target: Dict[str, Any], source: Dict[str, Any]) -> None`

No docstring available.

---

## Classes

### ConfigManager

**Class:** `ConfigManager`

Central configuration manager for CAsMan.

Supports YAML and JSON configuration files with environment variable overrides,
schema validation, and runtime updates.

#### Methods

##### __init__

**Signature:** `__init__(config_paths: Optional[List[Union[str, Path]]]) -> None`

Initialize the configuration manager.

**Parameters:**

config_paths : List[Union[str, Path]], optional
List of configuration file paths to load. If None, uses default paths.

---

##### reload

**Signature:** `reload() -> None`

Reload configuration from all configured files.

---

##### get

**Signature:** `get(key: str, default: Any) -> Any`

Get a configuration value.

**Parameters:**

key : str
Configuration key (supports dot notation for nested values).
default : Any, optional
Default value if key is not found.

**Returns:**

Any
Configuration value or default.

---

##### set

**Signature:** `set(key: str, value: Any) -> None`

Set a configuration value.

**Parameters:**

key : str
Configuration key (supports dot notation for nested values).
value : Any
Value to set.

---

##### get_all

**Signature:** `get_all() -> Dict[str, Any]`

Get all configuration data.

---

##### add_watcher

**Signature:** `add_watcher(callback: Callable[[Dict[str, Any]], None]) -> None`

Add a callback to be notified when configuration changes.

**Parameters:**

callback : Callable[[Dict[str, Any]], None]
Function to call with updated config dict.

---

##### remove_watcher

**Signature:** `remove_watcher(callback: Callable[[Dict[str, Any]], None]) -> None`

Remove a configuration watcher.

---

##### validate

**Signature:** `validate(schema: Optional[Dict[str, Any]]) -> bool`

Validate current configuration against a schema.

**Parameters:**

schema : Dict[str, Any], optional
JSON schema to validate against.

**Returns:**

bool
True if configuration is valid.

---

---
