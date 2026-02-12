"""
Database initialization utilities for CAsMan.

This module provides functions to initialize and set up database tables
for both parts and assembly tracking.
"""

import os
import sqlite3
from typing import Optional

from .connection import get_database_path
from .antenna_positions import init_antenna_positions_table
from .snap_boards import init_snap_boards_table


def init_grid_positions_table(db_dir: Optional[str] = None) -> None:
    """Initialize the grid_positions table for storing coordinates of all grid positions.
    
    This table stores coordinates for ALL grid positions, independent of antenna assignments.
    
    Parameters
    ----------
    db_dir : str, optional
        Custom database directory for testing
    """
    if db_dir is not None:
        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS grid_positions (
            grid_code TEXT PRIMARY KEY,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            height REAL NOT NULL,
            coordinate_system TEXT,
            notes TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def init_parts_db(db_dir: Optional[str] = None) -> None:
    """
    Initialize the parts.db database and create necessary tables if they don't exist.

    Creates the database directory if it doesn't exist and sets up the parts table
    with columns for id, part_number, part_type, polarization, and timestamps.

    Parameters
    ----------
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    None
    """
    # Get the database file path
    if db_dir is not None:
        # If explicit directory provided, use it directly (for tests and custom
        # setups)
        db_path = os.path.join(db_dir, "parts.db")
    else:
        # If no directory provided, use config resolution (respecting
        # environment variables)
        db_path = get_database_path("parts.db", None)

    # Create database directory if it doesn't exist
    db_directory = os.path.dirname(db_path)
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS parts (
        id INTEGER PRIMARY KEY,
        part_number TEXT UNIQUE,
        part_type TEXT,
        polarization TEXT,
        date_created TEXT,
        date_modified TEXT
    )"""
    )

    # Check if polarization column exists, add it if missing (for schema
    # migration)
    c.execute("PRAGMA table_info(parts)")
    columns = [row[1] for row in c.fetchall()]
    if "polarization" not in columns:
        c.execute("ALTER TABLE parts ADD COLUMN polarization TEXT")

    # Check if date_created column exists, update old created_at/modified_at
    # columns
    if "date_created" not in columns and "created_at" in columns:
        # Rename old columns to new names
        c.execute("ALTER TABLE parts ADD COLUMN date_created TEXT")
        c.execute("ALTER TABLE parts ADD COLUMN date_modified TEXT")
        c.execute(
            "UPDATE parts SET date_created = created_at, date_modified = modified_at"
        )

    # Create part_notes table
    c.execute(
        """CREATE TABLE IF NOT EXISTS part_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        part_number TEXT NOT NULL,
        note TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (part_number) REFERENCES parts(part_number)
    )"""
    )

    conn.commit()
    conn.close()


def init_assembled_db(db_dir: Optional[str] = None) -> None:
    """
    Initialize the assembled_casm.db database and create necessary tables if they don't exist.

    Creates the database directory if it doesn't exist and sets up the assembly table
    with columns for tracking part connections and scan times.

    Parameters
    ----------
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    None
    """
    # Get the database file path
    if db_dir is not None:
        # If explicit directory provided, use it directly (for tests and custom
        # setups)
        db_path = os.path.join(db_dir, "assembled_casm.db")
    else:
        # If no directory provided, use config resolution (respecting
        # environment variables)
        db_path = get_database_path("assembled_casm.db", None)

    # Create database directory if it doesn't exist
    db_directory = os.path.dirname(db_path)
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)

    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS assembly (
            id INTEGER PRIMARY KEY,
            part_number TEXT,
            part_type TEXT,
            polarization TEXT,
            scan_time TEXT,
            connected_to TEXT,
            connected_to_type TEXT,
            connected_polarization TEXT,
            connected_scan_time TEXT,
            connection_status TEXT DEFAULT 'connected'
        )"""
        )

        # Migrate existing databases: add connection_status column if it doesn't exist
        c.execute("PRAGMA table_info(assembly)")
        columns = [row[1] for row in c.fetchall()]
        if "connection_status" not in columns:
            c.execute(
                """ALTER TABLE assembly
                ADD COLUMN connection_status TEXT DEFAULT 'connected'"""
            )
            # Update all existing records to 'connected'
            c.execute(
                """UPDATE assembly
                SET connection_status = 'connected'
                WHERE connection_status IS NULL"""
            )

        conn.commit()


def init_all_databases(db_dir: Optional[str] = None) -> None:
    """
    Initialize all databases.

    Calls init_parts_db(), init_assembled_db(), init_antenna_positions_table(),
    init_snap_boards_table(), and init_grid_positions_table() to set up all required
    database tables for the CAsMan system.

    Parameters
    ----------
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    None
    """
    init_parts_db(db_dir)
    init_assembled_db(db_dir)
    init_antenna_positions_table(db_dir)
    init_snap_boards_table(db_dir)
    init_grid_positions_table(db_dir)

def ensure_schema_migrations(db_dir: Optional[str] = None) -> None:
    """
    Ensure all required schema updates and migrations are applied.
    
    This function should be called on application startup to handle any schema
    migrations needed for new features. It ensures backward compatibility by
    adding missing tables/columns to existing databases without data loss.
    
    Migrations applied:
    - Adds part_notes table if it doesn't exist (for notes feature)
    
    Parameters
    ----------
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.
    
    Returns
    -------
    None
    """
    # Get paths for both databases
    if db_dir is not None:
        parts_db_path = os.path.join(db_dir, "parts.db")
    else:
        parts_db_path = get_database_path("parts.db", None)
    
    # Ensure parts.db has part_notes table
    if os.path.exists(parts_db_path):
        try:
            conn = sqlite3.connect(parts_db_path)
            c = conn.cursor()
            
            # Check if part_notes table exists
            c.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='part_notes'"
            )
            table_exists = c.fetchone() is not None
            
            if not table_exists:
                # Create part_notes table if it doesn't exist
                c.execute(
                    """CREATE TABLE IF NOT EXISTS part_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    part_number TEXT NOT NULL,
                    note TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (part_number) REFERENCES parts(part_number)
                )"""
                )
                conn.commit()
            
            conn.close()
        except sqlite3.Error as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during schema migration: {e}")