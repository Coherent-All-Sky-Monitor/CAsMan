"""
Environment-specific configuration management for CAsMan.

Provides utilities for managing configuration across different environments
(development, testing, production).
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional


class EnvironmentConfig:
    """
    Environment-specific configuration manager.

    Supports loading different configuration files based on the current environment.
    """

    def __init__(self, base_config_dir: Optional[Path] = None) -> None:
        """
        Initialize environment configuration.

        Parameters
        ----------
        base_config_dir : Path, optional
            Base directory containing configuration files.
        """
        if base_config_dir is None:
            base_config_dir = Path(__file__).parent.parent.parent

        self.base_config_dir = base_config_dir
        self.current_environment = self._detect_environment()

    def _detect_environment(self) -> str:
        """
        Detect current environment from environment variables.

        Returns
        -------
        str
            Environment name (development, testing, production).
        """
        env = os.environ.get("CASMAN_ENV", "").lower()

        if env in ["dev", "development"]:
            return "development"
        elif env in ["test", "testing"]:
            return "testing"
        elif env in ["prod", "production"]:
            return "production"
        else:
            # Auto-detect based on other indicators
            if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
                return "testing"
            elif os.path.exists("/.dockerenv") or os.environ.get("CONTAINER"):
                return "production"
            else:
                return "development"

    def get_config_files(self) -> list[Path]:
        """
        Get list of configuration files for current environment.

        Returns
        -------
        list[Path]
            Ordered list of config files to load (base first, then environment-specific).
        """
        config_files = []

        # Base configuration files
        for filename in ["config.yaml", "config.yml", "config.json"]:
            config_path = self.base_config_dir / filename
            if config_path.exists():
                config_files.append(config_path)

        # Environment-specific configuration files
        env_patterns = [
            f"config.{self.current_environment}.yaml",
            f"config.{self.current_environment}.yml",
            f"config.{self.current_environment}.json",
            f"config-{self.current_environment}.yaml",
            f"config-{self.current_environment}.yml",
            f"config-{self.current_environment}.json",
        ]

        for pattern in env_patterns:
            config_path = self.base_config_dir / pattern
            if config_path.exists():
                config_files.append(config_path)

        return config_files

    def get_environment_variables(self) -> Dict[str, str]:
        """
        Get environment variables relevant to CAsMan configuration.

        Returns
        -------
        Dict[str, str]
            Dictionary of CAsMan-related environment variables.
        """
        casman_vars = {}

        for key, value in os.environ.items():
            if key.startswith(("CASMAN_", "DATABASE_", "BARCODE_")):
                casman_vars[key] = value

        return casman_vars

    def create_environment_config(
        self, environment: str, config_data: Dict[str, Any]
    ) -> Path:
        """
        Create an environment-specific configuration file.

        Parameters
        ----------
        environment : str
            Environment name (development, testing, production).
        config_data : Dict[str, Any]
            Configuration data to write.

        Returns
        -------
        Path
            Path to the created configuration file.
        """
        import yaml

        config_filename = f"config.{environment}.yaml"
        config_path = self.base_config_dir / config_filename

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f, default_flow_style=False, sort_keys=True)

        return config_path

    def get_current_environment(self) -> str:
        """Get the current environment name."""
        return self.current_environment

    def set_environment(self, environment: str) -> None:
        """
        Set the current environment.

        Parameters
        ----------
        environment : str
            Environment name to set.
        """
        self.current_environment = environment
        os.environ["CASMAN_ENV"] = environment

    def get_environment_config_template(self, environment: str) -> Dict[str, Any]:
        """
        Get a configuration template for a specific environment.

        Parameters
        ----------
        environment : str
            Environment name.

        Returns
        -------
        Dict[str, Any]
            Environment-specific configuration template.
        """
        base_template = {
            "database": {
                "backup_enabled": True,
                "integrity_check_enabled": True,
            },
            "logging": {
                "level": "INFO",
            },
        }

        if environment == "development":
            dev_config = base_template.copy()
            db_config = dev_config.get("database", {})
            if isinstance(db_config, dict):
                db_config.update(
                    {
                        "backup_interval_hours": 1,
                        "max_backups": 3,
                    }
                )
            dev_config.update(
                {
                    "logging": {
                        "level": "DEBUG",
                        "file_path": "logs/casman-dev.log",
                    },
                    "visualization": {
                        "web_port": 8080,
                        "auto_refresh": True,
                    },
                }
            )
            return dev_config

        elif environment == "testing":
            test_config = base_template.copy()
            db_config = test_config.get("database", {})
            if isinstance(db_config, dict):
                db_config.update(
                    {
                        "backup_enabled": False,
                        "integrity_check_enabled": False,
                    }
                )
            test_config.update(
                {
                    "logging": {
                        "level": "WARNING",
                        "file_path": "logs/casman-test.log",
                    },
                    "barcode": {
                        "output_directory": "test_barcodes",
                    },
                }
            )
            return test_config

        elif environment == "production":
            prod_config = base_template.copy()
            db_config = prod_config.get("database", {})
            if isinstance(db_config, dict):
                db_config.update(
                    {
                        "backup_interval_hours": 6,
                        "max_backups": 14,
                    }
                )
            prod_config.update(
                {
                    "logging": {
                        "level": "INFO",
                        "file_path": "/var/log/casman/casman.log",
                    },
                    "visualization": {
                        "web_port": 80,
                        "auto_refresh": False,
                    },
                }
            )
            return prod_config

        return base_template
