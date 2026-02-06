"""
Assembly connection recording functionality.

This module handles the recording of assembly connections between parts
in the assembled database.
"""

import logging
import sqlite3
from typing import Optional

from casman.database.connection import get_database_path
from casman.database.initialization import init_assembled_db

logger = logging.getLogger(__name__)


def record_assembly_connection(
    part_number: str,
    part_type: str,
    polarization: str,
    scan_time: str,
    connected_to: str,
    connected_to_type: str,
    connected_polarization: str,
    connected_scan_time: str,
    db_dir: Optional[str] = None,
    connection_status: str = "connected",
) -> bool:
    """
    Record an assembly connection or disconnection in the database with explicit timestamps.

    Parameters
    ----------
    part_number : str
        The part number being scanned.
    part_type : str
        The type of the part being scanned.
    polarization : str
        The polarization of the part being scanned.
    scan_time : str
        The timestamp when the part was scanned (YYYY-MM-DD HH:MM:SS).
    connected_to : str
        The part number this part is connected to.
    connected_to_type : str
        The type of the connected part.
    connected_polarization : str
        The polarization of the connected part.
    connected_scan_time : str
        The timestamp when the connection was made (YYYY-MM-DD HH:MM:SS).
    db_dir : Optional[str]
        Custom database directory. If not provided, uses the project root's database directory.
    connection_status : str, optional
        Status of the connection: 'connected' or 'disconnected'. Defaults to 'connected'.

    Returns
    -------
    bool
        True if the connection was recorded successfully, False otherwise.

    Notes
    -----
    This function explicitly takes all connection parameters with timestamps,
    making it suitable for both live scanning and batch recording operations.
    The connection_status parameter allows tracking both connections and disconnections.

    Examples
    --------
    >>> success = record_assembly_connection(
    ...     "ANTP1-00001", "ANTENNA", "X", "2024-01-01 10:00:00",
    ...     "LNA-P1-00001", "LNA", "X", "2024-01-01 10:05:00"
    ... )
    >>> print(success)
    True
    >>> success = record_assembly_connection(
    ...     "ANTP1-00001", "ANTENNA", "X", "2024-01-01 10:00:00",
    ...     "LNA-P1-00001", "LNA", "X", "2024-01-01 10:10:00",
    ...     connection_status="disconnected"
    ... )
    """
    try:
        init_assembled_db(db_dir)
        db_path = get_database_path("assembled_casm.db", db_dir)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Insert the assembly connection record
            cursor.execute(
                """
                INSERT INTO assembly
                (part_number, part_type, polarization, scan_time,
                 connected_to, connected_to_type, connected_polarization, connected_scan_time,
                 connection_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    part_number,
                    part_type,
                    polarization,
                    scan_time,
                    connected_to,
                    connected_to_type,
                    connected_polarization,
                    connected_scan_time,
                    connection_status,
                ),
            )

            conn.commit()
            logger.info(
                "Recorded assembly %s: %s -> %s",
                connection_status,
                part_number,
                connected_to,
            )
            
        return True

    except sqlite3.Error as e:
        logger.error("Database error recording assembly %s: %s", part_number, e)
        return False
    except (ValueError, TypeError) as e:
        logger.error("Error recording assembly %s: %s", part_number, e)
        return False


def record_assembly_disconnection(
    part_number: str,
    part_type: str,
    polarization: str,
    scan_time: str,
    connected_to: str,
    connected_to_type: str,
    connected_polarization: str,
    connected_scan_time: str,
    db_dir: Optional[str] = None,
) -> bool:
    """
    Record an assembly disconnection in the database.

    This is a convenience wrapper around record_assembly_connection that sets
    the connection_status to 'disconnected'.

    Parameters
    ----------
    part_number : str
        The part number being disconnected.
    part_type : str
        The type of the part being disconnected.
    polarization : str
        The polarization of the part being disconnected.
    scan_time : str
        The timestamp when the part was scanned (YYYY-MM-DD HH:MM:SS).
    connected_to : str
        The part number this part was connected to.
    connected_to_type : str
        The type of the connected part.
    connected_polarization : str
        The polarization of the connected part.
    connected_scan_time : str
        The timestamp when the disconnection was made (YYYY-MM-DD HH:MM:SS).
    db_dir : Optional[str]
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    bool
        True if the disconnection was recorded successfully, False otherwise.

    Examples
    --------
    >>> success = record_assembly_disconnection(
    ...     "ANTP1-00001", "ANTENNA", "X", "2024-01-01 10:00:00",
    ...     "LNA-P1-00001", "LNA", "X", "2024-01-01 10:10:00"
    ... )
    >>> print(success)
    True
    """
    return record_assembly_connection(
        part_number,
        part_type,
        polarization,
        scan_time,
        connected_to,
        connected_to_type,
        connected_polarization,
        connected_scan_time,
        db_dir,
        connection_status="disconnected",
    )
