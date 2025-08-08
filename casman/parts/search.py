"""
Advanced search functionality for CAsMan parts.

This module provides enhanced search capabilities for finding parts
based on various criteria and patterns.
"""
import sqlite3
from typing import Any, Dict, List, Optional

from casman.database.connection import get_database_path

from .part import Part
from .validation import validate_part_type, validate_polarization


def search_parts(
    part_type: Optional[str] = None,
    polarization: Optional[str] = None,
    part_number_pattern: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    limit: Optional[int] = None,
    db_dir: Optional[str] = None
) -> List[Part]:
    """
    Advanced search for parts with multiple criteria.

    Parameters
    ----------
    part_type : Optional[str]
        Filter by part type (e.g., "ANTENNA")
    polarization : Optional[str]
        Filter by polarization (e.g., "P1")
    part_number_pattern : Optional[str]
        Filter by part number pattern (supports SQL LIKE syntax)
    created_after : Optional[str]
        Filter parts created after this date (YYYY-MM-DD format)
    created_before : Optional[str]
        Filter parts created before this date (YYYY-MM-DD format)
    limit : Optional[int]
        Maximum number of results to return
    db_dir : Optional[str]
        Custom database directory

    Returns
    -------
    List[Part]
        List of matching Part instances
    """
    # Build the query
    query = "SELECT id, part_number, part_type, polarization, date_created, date_modified FROM parts WHERE 1=1"
    params = []

    if part_type is not None:
        if not validate_part_type(part_type):
            raise ValueError(f"Invalid part type: {part_type}")
        query += " AND part_type = ?"
        params.append(part_type)

    if polarization is not None:
        if not validate_polarization(polarization):
            raise ValueError(f"Invalid polarization: {polarization}")
        query += " AND part_number LIKE ?"
        params.append(f"%-{polarization}-%")

    if part_number_pattern is not None:
        query += " AND part_number LIKE ?"
        params.append(part_number_pattern)

    if created_after is not None:
        query += " AND date_created >= ?"
        params.append(created_after)

    if created_before is not None:
        query += " AND date_created <= ?"
        params.append(created_before)

    query += " ORDER BY date_created DESC"

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    # Execute the query
    db_path = get_database_path("parts.db", db_dir)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    # Convert to Part instances
    parts = []
    for row in rows:
        try:
            parts.append(Part.from_database_row(row))
        except ValueError as e:
            # Skip invalid parts but log the issue
            print(f"Warning: Skipping invalid part in database: {e}")

    return parts


def get_all_parts(db_dir: Optional[str] = None) -> List[Part]:
    """
    Get all parts from the database.

    Parameters
    ----------
    db_dir : Optional[str]
        Custom database directory

    Returns
    -------
    List[Part]
        List of all Part instances
    """
    return search_parts(db_dir=db_dir)


def search_by_prefix(prefix: str, db_dir: Optional[str] = None) -> List[Part]:
    """
    Search for parts by prefix (e.g., "ANT", "LNA").

    Parameters
    ----------
    prefix : str
        The part prefix to search for
    db_dir : Optional[str]
        Custom database directory

    Returns
    -------
    List[Part]
        List of matching Part instances
    """
    return search_parts(part_number_pattern=f"{prefix}-%", db_dir=db_dir)


def get_part_statistics(db_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics about parts in the database.

    Parameters
    ----------
    db_dir : Optional[str]
        Custom database directory

    Returns
    -------
    Dict[str, Any]
        Dictionary containing part statistics
    """
    db_path = get_database_path("parts.db", db_dir)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Total parts
        cursor.execute("SELECT COUNT(*) FROM parts")
        total_parts = cursor.fetchone()[0]

        # Parts by type
        cursor.execute(
            "SELECT part_type, COUNT(*) FROM parts GROUP BY part_type")
        parts_by_type = dict(cursor.fetchall())

        # Parts by polarization
        cursor.execute("""
            SELECT
                CASE
                    WHEN part_number LIKE '%-P1-%' THEN 'P1'
                    WHEN part_number LIKE '%-P2-%' THEN 'P2'
                    WHEN part_number LIKE '%-PV-%' THEN 'PV'
                    ELSE 'Other'
                END as polarization,
                COUNT(*)
            FROM parts
            GROUP BY polarization
        """)
        parts_by_polarization = dict(cursor.fetchall())

        # Most recent part
        cursor.execute(
            "SELECT part_number, date_created FROM parts ORDER BY date_created DESC LIMIT 1")
        latest_part = cursor.fetchone()

    return {
        'total_parts': total_parts,
        'parts_by_type': parts_by_type,
        'parts_by_polarization': parts_by_polarization,
        'latest_part': {
            'part_number': latest_part[0] if latest_part else None,
            'date_created': latest_part[1] if latest_part else None
        }
    }


def find_part(
        part_number: str,
        db_dir: Optional[str] = None) -> Optional[Part]:
    """
    Find a specific part by part number.

    Parameters
    ----------
    part_number : str
        The exact part number to find
    db_dir : Optional[str]
        Custom database directory

    Returns
    -------
    Optional[Part]
        The Part instance if found, None otherwise
    """
    results = search_parts(
        part_number_pattern=part_number,
        limit=1,
        db_dir=db_dir)
    return results[0] if results else None


def get_recent_parts(
        count: int = 10,
        db_dir: Optional[str] = None) -> List[Part]:
    """
    Get the most recently created parts.

    Parameters
    ----------
    count : int
        Number of recent parts to return (default: 10)
    db_dir : Optional[str]
        Custom database directory

    Returns
    -------
    List[Part]
        List of recently created Part instances
    """
    return search_parts(limit=count, db_dir=db_dir)
