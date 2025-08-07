"""
Assembly data retrieval and statistics functionality.

This module handles querying assembly connection data and generating
statistics from the assembled database.
"""

import logging
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from casman.database import get_database_path

logger = logging.getLogger(__name__)


def get_assembly_connections(
    db_dir: Optional[str] = None,
) -> List[Tuple[str, Optional[str], str, Optional[str], Optional[str]]]:
    """
    Get all assembly connections from the database.

    Parameters
    ----------
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    List[Tuple[str, Optional[str], str, Optional[str], Optional[str]]]
        List of (part_number, connected_to, scan_time, part_type, polarization) tuples.

    Examples
    --------
    >>> connections = get_assembly_connections()
    >>> for part, connected, time, ptype, pol in connections:
    ...     print(f"{part} -> {connected} at {time}")
    ANTP1-00001 -> LNA-P1-00001 at 2024-01-01 10:00:00
    """
    try:
        db_path = get_database_path("assembled_casm.db", db_dir)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT part_number, connected_to, scan_time, part_type, polarization
                FROM assembly
                ORDER BY scan_time
            """
            )
            return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error("Database error getting connections: %s", e)
        return []


def get_assembly_stats(db_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Get assembly statistics from the database.

    Parameters
    ----------
    db_dir : Optional[str]
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing assembly statistics with keys:
        - total_scans: Total number of assembly scans
        - unique_parts: Number of unique parts in assemblies
        - connected_parts: Number of parts with connections
        - latest_scan: Timestamp of the most recent scan

    Examples
    --------
    >>> stats = get_assembly_stats()
    >>> print(f"Total scans: {stats['total_scans']}")
    >>> print(f"Latest scan: {stats['latest_scan']}")
    Total scans: 42
    Latest scan: 2024-01-01 15:30:00
    """
    try:
        db_path = get_database_path("assembled_casm.db", db_dir)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get total scans
            cursor.execute("SELECT COUNT(*) FROM assembly")
            total_scans = cursor.fetchone()[0]

            # Get unique parts
            cursor.execute("SELECT COUNT(DISTINCT part_number) FROM assembly")
            unique_parts = cursor.fetchone()[0]

            # Get connected parts (parts that have non-null connected_to)
            cursor.execute(
                """
                SELECT COUNT(DISTINCT part_number)
                FROM assembly
                WHERE connected_to IS NOT NULL
            """
            )
            connected_parts = cursor.fetchone()[0]

            # Get latest scan time
            cursor.execute("SELECT MAX(scan_time) FROM assembly")
            latest_scan = cursor.fetchone()[0]

            return {
                "total_scans": total_scans,
                "unique_parts": unique_parts,
                "connected_parts": connected_parts,
                "latest_scan": latest_scan,
            }

    except sqlite3.Error as e:
        logger.error("Database error getting stats: %s", e)
        return {
            "total_scans": 0,
            "unique_parts": 0,
            "connected_parts": 0,
            "latest_scan": None,
        }
