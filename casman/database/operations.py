"""
Database operations utilities for CAsMan.

This module provides functions for querying and retrieving data
from the CAsMan databases.
"""

import sqlite3
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
