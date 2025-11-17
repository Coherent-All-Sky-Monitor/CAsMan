"""
Assembly data retrieval and statistics functionality.

This module handles querying assembly connection data and generating
statistics from the assembled database.
"""

import logging
import sqlite3
from typing import List, Optional, Tuple

from casman.database.connection import get_database_path

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
                SELECT a.part_number, a.connected_to, a.scan_time, a.part_type, a.polarization
                FROM assembly a
                INNER JOIN (
                    SELECT part_number, connected_to, MAX(scan_time) as max_time
                    FROM assembly
                    GROUP BY part_number, connected_to
                ) latest
                ON a.part_number = latest.part_number
                AND a.connected_to = latest.connected_to
                AND a.scan_time = latest.max_time
                WHERE a.connection_status = 'connected'
                ORDER BY a.scan_time
            """
            )
            return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error("Database error getting connections: %s", e)
        return []
