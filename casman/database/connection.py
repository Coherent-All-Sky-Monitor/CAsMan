"""
Database connection utilities for CAsMan.

This module provides utilities for database path resolution.
Supports both local project databases and synced XDG user databases.
"""

import os
from pathlib import Path
from typing import Optional

from casman.config import get_config


def get_database_path(db_name: str, db_dir: Optional[str] = None) -> str:
    """
    Get the full path to a database file.

    Path resolution order:
    1. Explicit db_dir parameter (for tests/custom setups)
    2. Environment variables (CASMAN_PARTS_DB, CASMAN_ASSEMBLED_DB)
    3. config.yaml settings (CASMAN_PARTS_DB, CASMAN_ASSEMBLED_DB)
    4. XDG user data directory (~/.local/share/casman/databases/)
    5. Project root database directory (development)
    6. Fallback to cwd/database

    Parameters
    ----------
    db_name : str
        Name of the database file.
    db_dir : str, optional
        Custom database directory. If not provided, uses automatic resolution.

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

    # Check XDG user data directory (for synced databases)
    # This is used by pip-installed casman-antenna users
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        xdg_db_dir = Path(xdg_data_home) / "casman" / "databases"
    else:
        xdg_db_dir = Path.home() / ".local" / "share" / "casman" / "databases"

    xdg_db_path = xdg_db_dir / db_name
    if xdg_db_path.exists():
        return str(xdg_db_path)

    # Default to project root database directory (find by going up from __file__)
    # This is used for development/server installations
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
