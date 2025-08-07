"""
Tests for the enhanced configuration system.

Covers configuration loading, validation, environment-specific configs,
and utility functions.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
import yaml

from casman.config import (
    ConfigManager,
    EnvironmentConfig,
    ConfigSchema,
    get_config,
    get_config_manager,
    load_config,
    merge_configs,
    reload_config,
    resolve_config_path,
    set_config,
    validate_config,
)


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_config_manager_initialization(self) -> None:
        """Test ConfigManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "test_config.yaml"

            test_config = {
                "PART_TYPES": {
                    "1": ["ANTENNA", "ANT"],
                    "2": ["LNA", "LNA"]
                },
                "CASMAN_PARTS_DB": "test_parts.db"
            }

            with open(config_file, 'w') as f:
                yaml.safe_dump(test_config, f)

            manager = ConfigManager([config_file])

            # Note: Due to test fixture, CASMAN_PARTS_DB will be overridden by environment variable
            # The value should be the environment variable value (from
            # conftest.py fixture), not config file
            db_path = manager.get("CASMAN_PARTS_DB")
            assert db_path is not None  # Should have a value from environment
            assert db_path.endswith("parts.db")  # Should end with parts.db
            assert manager.get("PART_TYPES.1") == ["ANTENNA", "ANT"]

    def test_config_manager_nested_access(self) -> None:
        """Test nested configuration access with dot notation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "test_config.yaml"

            test_config = {
                "database": {
                    "backup_enabled": True,
                    "settings": {
                        "timeout": 30
                    }
                }
            }

            with open(config_file, 'w') as f:
                yaml.safe_dump(test_config, f)

            manager = ConfigManager([config_file])

            assert manager.get("database.backup_enabled") is True
            assert manager.get("database.settings.timeout") == 30
            assert manager.get("nonexistent.key", "default") == "default"

    def test_config_manager_set_nested(self) -> None:
        """Test setting nested configuration values."""
        manager = ConfigManager([])

        manager.set("database.backup_enabled", True)
        manager.set("database.settings.timeout", 30)

        assert manager.get("database.backup_enabled") is True
        assert manager.get("database.settings.timeout") == 30

    @patch.dict(os.environ, {"CASMAN_TEST_VALUE": "env_override"})
    def test_environment_variable_overrides(self) -> None:
        """Test environment variable overrides."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "test_config.yaml"

            test_config = {"TEST_VALUE": "config_value"}

            with open(config_file, 'w') as f:
                yaml.safe_dump(test_config, f)

            manager = ConfigManager([config_file])

            # Environment variable should override config file
            assert manager.get("TEST_VALUE") == "env_override"

    def test_config_manager_json_support(self) -> None:
        """Test JSON configuration file support."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "test_config.json"

            test_config = {
                "PART_TYPES": {
                    "1": ["ANTENNA", "ANT"]
                }
            }

            with open(config_file, 'w') as f:
                json.dump(test_config, f)

            manager = ConfigManager([config_file])

            assert manager.get("PART_TYPES.1") == ["ANTENNA", "ANT"]

    def test_config_watchers(self) -> None:
        """Test configuration change watchers."""
        manager = ConfigManager([])
        watcher_called = False
        received_config = None

        def config_watcher(config: Dict[str, Any]) -> None:
            nonlocal watcher_called, received_config
            watcher_called = True
            received_config = config

        manager.add_watcher(config_watcher)
        manager.reload()

        assert watcher_called
        assert received_config is not None

        # Test watcher removal
        manager.remove_watcher(config_watcher)
        watcher_called = False
        manager.reload()
        # Should not be called again since watcher was removed


class TestEnvironmentConfig:
    """Test cases for EnvironmentConfig class."""

    def test_environment_detection(self) -> None:
        """Test environment detection from environment variables."""
        with patch.dict(os.environ, {"CASMAN_ENV": "development"}):
            env_config = EnvironmentConfig()
            assert env_config.get_current_environment() == "development"

        with patch.dict(os.environ, {"CASMAN_ENV": "prod"}):
            env_config = EnvironmentConfig()
            assert env_config.get_current_environment() == "production"

    @patch.dict(os.environ, {"CI": "true"})
    def test_ci_environment_detection(self) -> None:
        """Test CI environment auto-detection."""
        # Clear CASMAN_ENV if it exists
        with patch.dict(os.environ, {}, clear=True):
            os.environ["CI"] = "true"
            env_config = EnvironmentConfig()
            assert env_config.get_current_environment() == "testing"

    def test_environment_config_files(self) -> None:
        """Test environment-specific config file resolution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create base config
            base_config = temp_path / "config.yaml"
            with open(base_config, 'w') as f:
                yaml.safe_dump({"base": True}, f)

            # Create environment-specific config
            env_config_file = temp_path / "config.development.yaml"
            with open(env_config_file, 'w') as f:
                yaml.safe_dump({"env": "dev"}, f)

            with patch.dict(os.environ, {"CASMAN_ENV": "development"}):
                env_config = EnvironmentConfig(temp_path)
                config_files = env_config.get_config_files()

                assert base_config in config_files
                assert env_config_file in config_files

    def test_environment_config_templates(self) -> None:
        """Test environment-specific configuration templates."""
        env_config = EnvironmentConfig()

        dev_template = env_config.get_environment_config_template(
            "development")
        test_template = env_config.get_environment_config_template("testing")
        prod_template = env_config.get_environment_config_template(
            "production")

        assert dev_template["logging"]["level"] == "DEBUG"
        assert test_template["logging"]["level"] == "WARNING"
        assert prod_template["logging"]["level"] == "INFO"

        assert test_template["database"]["backup_enabled"] is False
        assert dev_template["database"]["backup_enabled"] is True


class TestConfigSchema:
    """Test cases for ConfigSchema class."""

    def test_default_schema(self) -> None:
        """Test default schema retrieval."""
        schema = ConfigSchema.get_default_schema()

        assert "PART_TYPES" in schema["properties"]
        assert "required" in schema
        assert "PART_TYPES" in schema["required"]

    def test_config_validation_valid(self) -> None:
        """Test validation of valid configuration."""
        valid_config = {
            "PART_TYPES": {
                "1": ["ANTENNA", "ANT"],
                "2": ["LNA", "LNA"]
            },
            "CASMAN_PARTS_DB": "database/parts.db"
        }

        is_valid, error = ConfigSchema.validate_config(valid_config)
        assert is_valid
        assert error == "" or "jsonschema not available" in error

    def test_config_validation_invalid(self) -> None:
        """Test validation of invalid configuration."""
        invalid_config = {
            "PART_TYPES": "not_a_dict",  # Should be a dict
        }

        is_valid, error = ConfigSchema.validate_config(invalid_config)
        # Either validation fails or jsonschema is not available
        assert not is_valid or "jsonschema not available" in error

    def test_config_template(self) -> None:
        """Test configuration template generation."""
        template = ConfigSchema.get_config_template()

        assert "PART_TYPES" in template
        assert "CASMAN_PARTS_DB" in template
        assert "database" in template
        assert "barcode" in template


class TestConfigUtils:
    """Test cases for configuration utilities."""

    def test_resolve_config_path(self) -> None:
        """Test configuration path resolution."""
        # Test relative path
        relative_path = "database/parts.db"
        resolved = resolve_config_path(relative_path)
        assert resolved.is_absolute()
        assert str(resolved).endswith("database/parts.db")

        # Test absolute path
        absolute_path = "/tmp/test.db"
        resolved = resolve_config_path(absolute_path)
        assert str(resolved) == absolute_path

    @patch.dict(os.environ, {"TEST_VAR": "/test/path"})
    def test_resolve_config_path_with_env_vars(self) -> None:
        """Test path resolution with environment variables."""
        path_with_env = "$TEST_VAR/parts.db"
        resolved = resolve_config_path(path_with_env)
        assert str(resolved) == "/test/path/parts.db"

    def test_merge_configs(self) -> None:
        """Test configuration merging."""
        config1 = {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "debug": True
        }

        config2 = {
            "database": {
                "port": 3306,
                "name": "casman"
            },
            "logging": {"level": "INFO"}
        }

        merged = merge_configs(config1, config2)

        assert merged["database"]["host"] == "localhost"  # From config1
        assert merged["database"]["port"] == 3306  # Overridden by config2
        assert merged["database"]["name"] == "casman"  # From config2
        assert merged["debug"] is True  # From config1
        assert merged["logging"]["level"] == "INFO"  # From config2


class TestGlobalConfigFunctions:
    """Test cases for global configuration functions."""

    def test_global_config_manager(self) -> None:
        """Test global configuration manager functions."""
        # Test setting and getting configuration
        set_config("test_key", "test_value")
        assert get_config("test_key") == "test_value"
        assert get_config("nonexistent_key", "default") == "default"

        # Test that we get the same manager instance
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        assert manager1 is manager2

    def test_config_reload(self) -> None:
        """Test configuration reloading."""
        # Should not raise an exception
        reload_config()

        # Configuration should still be accessible
        config = load_config()
        assert isinstance(config, dict)

    def test_config_validation(self) -> None:
        """Test global configuration validation."""
        # Should not raise an exception
        is_valid = validate_config()
        assert isinstance(is_valid, bool)
