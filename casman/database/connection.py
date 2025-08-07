"""
Database connection utilities for CAsMan.

This module provides utilities for database path resolution and
project root detection.
"""

import os
from typing import Optional

from casman.config import get_config


def find_project_root() -> str:
    """
    Find the project root directory by looking for casman package or pyproject.toml.

    Returns
    -------
    str
        Absolute path to the project root directory.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up directories until we find the project root
    while current_dir != os.path.dirname(
            current_dir):  # Stop at filesystem root
        # Check for project indicators
        if (os.path.exists(os.path.join(current_dir, "pyproject.toml")) or
            os.path.exists(os.path.join(current_dir, "casman")) and
                os.path.exists(os.path.join(current_dir, "database"))):
            return current_dir
        current_dir = os.path.dirname(current_dir)

    # Fallback to current working directory
    return os.getcwd()


def get_database_path(db_name: str, db_dir: Optional[str] = None) -> str:
    """
    Get the full path to a database file.

    Parameters
    ----------
    db_name : str
        Name of the database file.
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    str
        Full path to the database file.
    """

    """
    Returns
    -------
    str
        Full path to the database file.
    """
    # If db_dir is explicitly provided, use it directly (for tests and custom
    # setups)
    if db_dir is not None:
        return os.path.join(db_dir, db_name)

    # Use config loader for environment variable or config.yaml override
    if db_name == "parts.db":
        config_path = get_config("CASMAN_PARTS_DB")
        if config_path is not None:
            return str(config_path)
    elif db_name == "assembled_casm.db":
        config_path = get_config("CASMAN_ASSEMBLED_DB")
        if config_path is not None:
            return str(config_path)

    # Default to project root database directory
    project_root = find_project_root()
    db_dir = os.path.join(project_root, "database")

    return os.path.join(db_dir, db_name)
