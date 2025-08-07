"""
Database migration utilities for CAsMan.

This module provides database migration functionality to handle
schema updates and data migrations safely.
"""

import sqlite3
from typing import Dict, List, Optional

from .connection import get_database_path


class DatabaseMigrator:
    """
    Database migration manager for CAsMan databases.

    Handles schema versioning and migration execution.
    """

    def __init__(self, db_name: str, db_dir: Optional[str] = None):
        """
        Initialize the migrator for a specific database.

        Parameters
        ----------
        db_name : str
            Name of the database file.
        db_dir : str, optional
            Custom database directory.
        """
        self.db_name = db_name
        self.db_dir = db_dir
        self.db_path = get_database_path(db_name, db_dir)

    def get_schema_version(self) -> int:
        """
        Get the current schema version of the database.

        Returns
        -------
        int
            Current schema version, 0 if no version table exists.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            c.execute(
                "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            result = c.fetchone()
            version = result[0] if result else 0
        except sqlite3.OperationalError:
            # schema_version table doesn't exist
            version = 0
        finally:
            conn.close()

        return version

    def set_schema_version(self, version: int) -> None:
        """
        Set the schema version in the database.

        Parameters
        ----------
        version : int
            Schema version to set.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Create schema_version table if it doesn't exist
        c.execute("""CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        # Insert new version
        c.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        conn.commit()
        conn.close()

    def execute_migration(self, sql: str, version: int) -> None:
        """
        Execute a migration SQL statement and update version.

        Parameters
        ----------
        sql : str
            SQL statement to execute.
        version : int
            Version number to set after successful migration.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            # Execute migration
            c.execute(sql)
            conn.commit()

            # Update schema version
            self.set_schema_version(version)

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Migration failed: {e}")
        finally:
            conn.close()


def get_table_info(
        db_name: str,
        table_name: str,
        db_dir: Optional[str] = None) -> List[Dict]:
    """
    Get information about table columns and structure.

    Parameters
    ----------
    db_name : str
        Name of the database file.
    table_name : str
        Name of the table to inspect.
    db_dir : str, optional
        Custom database directory.

    Returns
    -------
    List[Dict]
        List of column information dictionaries.
    """
    conn = sqlite3.connect(get_database_path(db_name, db_dir))
    c = conn.cursor()

    c.execute(f"PRAGMA table_info({table_name})")
    columns = c.fetchall()
    conn.close()

    # Convert to dictionary format
    column_info = []
    for col in columns:
        column_info.append({
            'cid': col[0],
            'name': col[1],
            'type': col[2],
            'notnull': bool(col[3]),
            'default_value': col[4],
            'pk': bool(col[5])
        })

    return column_info


def backup_database(db_name: str, backup_suffix: str = "backup",
                    db_dir: Optional[str] = None) -> str:
    """
    Create a backup of the database before migration.

    Parameters
    ----------
    db_name : str
        Name of the database file.
    backup_suffix : str, optional
        Suffix to add to backup filename.
    db_dir : str, optional
        Custom database directory.

    Returns
    -------
    str
        Path to the backup file.
    """
    import shutil
    from datetime import datetime

    db_path = get_database_path(db_name, db_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{db_name}.{backup_suffix}_{timestamp}"
    backup_path = get_database_path(backup_name, db_dir)

    shutil.copy2(db_path, backup_path)
    return backup_path


def check_database_integrity(db_name: str,
                             db_dir: Optional[str] = None) -> bool:
    """
    Check database integrity using SQLite's built-in integrity check.

    Parameters
    ----------
    db_name : str
        Name of the database file.
    db_dir : str, optional
        Custom database directory.

    Returns
    -------
    bool
        True if database integrity is OK, False otherwise.
    """
    conn = sqlite3.connect(get_database_path(db_name, db_dir))
    c = conn.cursor()

    c.execute("PRAGMA integrity_check")
    result = c.fetchone()
    conn.close()

    return result[0] == "ok"
