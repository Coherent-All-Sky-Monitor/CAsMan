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
    4. XDG user data directory (~/.local/share/casman/databases/) - preferred for casman.antenna
    5. Project root database directory (only for full CAsMan project with setup.py)

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

    # If db_dir is explicitly provided, use it directly (for tests and custom setups)
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

    # Default to XDG user data directory for casman.antenna usage
    # This is the primary location for synced databases
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        xdg_db_dir = Path(xdg_data_home) / "casman" / "databases"
    else:
        xdg_db_dir = Path.home() / ".local" / "share" / "casman" / "databases"

    xdg_db_path = xdg_db_dir / db_name
    if xdg_db_path.exists():
        return str(xdg_db_path)
    
    # If running full CAsMan project with setup.py, also check project database
    # This allows development/server installations to use local database/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
        setup_py = os.path.join(current_dir, "setup.py")
        project_db = os.path.join(current_dir, "database", db_name)
        
        # Only use project database if setup.py exists (indicates full project installation)
        if os.path.exists(setup_py) and os.path.exists(project_db):
            return project_db
        
        current_dir = os.path.dirname(current_dir)

    # Always fallback to XDG path (sync_databases will populate it)
    # BUT: if we're in the full project (has pyproject.toml with casman project),
    # use project database instead for web app and server usage
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
        pyproject_path = os.path.join(current_dir, "pyproject.toml")
        project_db = os.path.join(current_dir, "database", db_name)
        
        # Use project database if we're in a full CAsMan project directory
        if os.path.exists(pyproject_path) and os.path.exists(project_db):
            # Check if this is a CAsMan project (has casman/ directory)
            if os.path.exists(os.path.join(current_dir, "casman")):
                return project_db
        
        current_dir = os.path.dirname(current_dir)

    # For pip-installed casman.antenna, always use XDG path
    return str(xdg_db_path)
