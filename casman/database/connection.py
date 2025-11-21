"""
Database connection utilities for CAsMan.

This module provides utilities for database path resolution.
"""

import os
from typing import Optional

from casman.config import get_config


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

    # Default to project root database directory (find by going up from __file__)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
        if (
            os.path.exists(os.path.join(current_dir, "pyproject.toml"))
            or os.path.exists(os.path.join(current_dir, "casman"))
            and os.path.exists(os.path.join(current_dir, "database"))
        ):
            db_dir = os.path.join(current_dir, "database")
            return os.path.join(db_dir, db_name)
        current_dir = os.path.dirname(current_dir)

    # Fallback to cwd/database
    db_dir = os.path.join(os.getcwd(), "database")
    return os.path.join(db_dir, db_name)
