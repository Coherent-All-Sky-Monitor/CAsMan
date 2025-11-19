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

    Only returns connections where the most recent status between any two parts
    (checking both directions) is 'connected'. This ensures disconnected pairs
    are properly filtered out even if only one direction was recorded.

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
            # Get latest status for each part pair (checking both directions)
            # Only include if most recent status is 'connected'
            cursor.execute(
                """
                WITH latest_connections AS (
                    SELECT 
                        CASE 
                            WHEN part_number < connected_to THEN part_number
                            ELSE connected_to
                        END as part_a,
                        CASE 
                            WHEN part_number < connected_to THEN connected_to
                            ELSE part_number
                        END as part_b,
                        MAX(scan_time) as latest_time
                    FROM assembly
                    WHERE part_number IS NOT NULL AND connected_to IS NOT NULL
                    GROUP BY part_a, part_b
                ),
                pair_status AS (
                    SELECT 
                        a.part_number,
                        a.connected_to,
                        a.scan_time,
                        a.part_type,
                        a.polarization,
                        a.connection_status
                    FROM assembly a
                    INNER JOIN latest_connections lc
                    ON (
                        (a.part_number = lc.part_a AND a.connected_to = lc.part_b) OR
                        (a.part_number = lc.part_b AND a.connected_to = lc.part_a)
                    )
                    AND a.scan_time = lc.latest_time
                )
                SELECT DISTINCT 
                    ps.part_number, 
                    ps.connected_to, 
                    ps.scan_time, 
                    ps.part_type, 
                    ps.polarization
                FROM pair_status ps
                WHERE ps.connection_status = 'connected'
                ORDER BY ps.scan_time
            """
            )
            return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error("Database error getting connections: %s", e)
        return []
