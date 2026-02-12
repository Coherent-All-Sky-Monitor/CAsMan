"""
Database operations utilities for CAsMan.

This module provides functions for querying and retrieving data
from the CAsMan databases.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple

from .connection import get_database_path


def check_part_in_db(
    part_number: str, part_type: str, db_dir: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Check if a part number exists in the parts database and get its polarization.

    Parameters
    ----------
    part_number : str
        The part number to check.
    part_type : str
        The expected part type.
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    Tuple[bool, Optional[str]]
        (exists, polarization) where exists is True if part is found,
        and polarization is the part's polarization if found.
    """
    conn = sqlite3.connect(get_database_path("parts.db", db_dir))
    c = conn.cursor()
    c.execute(
        "SELECT polarization FROM parts WHERE part_number = ? AND part_type = ?",
        (part_number, part_type),
    )
    result = c.fetchone()
    conn.close()

    if result:
        return True, result[0]
    return False, None


def get_parts_by_criteria(
    part_type: Optional[str] = None,
    polarization: Optional[str] = None,
    db_dir: Optional[str] = None,
) -> List[Tuple[int, str, str, str, str, str]]:
    """
    Get parts from the database based on criteria.

    Parameters
    ----------
    part_type : Optional[str]
        Filter by part type.
    polarization : Optional[str]
        Filter by polarization.
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    List[Tuple[int, str, str, str, str, str]]
        List of part records as tuples of \
            (id, part_number, part_type, polarization, date_created, date_modified).
    """
    conn = sqlite3.connect(get_database_path("parts.db", db_dir))
    c = conn.cursor()

    query = "SELECT id, part_number, part_type, \
        polarization, date_created, date_modified FROM parts"
    params = []
    conditions = []

    if part_type:
        conditions.append("part_type = ?")
        params.append(part_type)

    if polarization:
        conditions.append("polarization = ?")
        params.append(polarization)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY date_created DESC"

    c.execute(query, params)
    parts = c.fetchall()
    conn.close()

    return parts


def add_part_note(
    part_number: str, note: str, db_dir: Optional[str] = None
) -> bool:
    """
    Add a note to a part in the parts database.

    Parameters
    ----------
    part_number : str
        The part number to add a note to.
    note : str
        The note text to add.
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    bool
        True if note was added successfully, False otherwise.
    """
    try:
        conn = sqlite3.connect(get_database_path("parts.db", db_dir))
        c = conn.cursor()
        
        # Verify part exists
        c.execute("SELECT part_number FROM parts WHERE part_number = ?", (part_number,))
        if not c.fetchone():
            conn.close()
            return False
        
        # Add note with timestamp
        timestamp = datetime.now().isoformat()
        c.execute(
            "INSERT INTO part_notes (part_number, note, timestamp) VALUES (?, ?, ?)",
            (part_number, note, timestamp),
        )
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False


def get_part_notes(
    part_number: str, db_dir: Optional[str] = None
) -> List[Tuple[str, str]]:
    """
    Get all notes for a part from the parts database.

    Parameters
    ----------
    part_number : str
        The part number to get notes for.
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    List[Tuple[str, str]]
        List of (note, timestamp) tuples, ordered by timestamp (newest first).
    """
    conn = sqlite3.connect(get_database_path("parts.db", db_dir))
    c = conn.cursor()
    
    c.execute(
        "SELECT note, timestamp FROM part_notes WHERE part_number = ? ORDER BY timestamp DESC",
        (part_number,),
    )
    notes = c.fetchall()
    conn.close()
    
    return notes
