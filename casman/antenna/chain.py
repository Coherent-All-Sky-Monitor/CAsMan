"""Antenna chain utilities for tracing connections to SNAP ports.

This module provides functions to traverse connection chains from antennas
through the assembly to determine SNAP port assignments for both polarizations.
"""

import sqlite3
from typing import List, Optional

from casman.database.connection import get_database_path


def get_snap_port_for_chain(
    part_number: str, *, db_dir: Optional[str] = None
) -> Optional[dict]:
    """Find SNAP port at end of connection chain.

    Traverses the connection chain starting from the given part until reaching
    a SNAP board, then extracts chassis/slot/port information.

    Parameters
    ----------
    part_number : str
        Starting part number (e.g. 'ANT00001P1', 'LNA00005P2').
    db_dir : str, optional
        Custom database directory for testing.

    Returns
    -------
    dict or None
        SNAP port info if chain complete:
        {
            'snap_part': str,      # e.g. 'SNAP1A05'
            'chassis': int,        # 1-4
            'slot': str,           # A-K
            'port': int,           # 0-11
            'chain': List[str]     # Full chain from start to SNAP
        }
        Returns None if chain incomplete or doesn't reach SNAP.

    Examples
    --------
    >>> get_snap_port_for_chain('ANT00001P1')
    {'snap_part': 'SNAP1A05', 'chassis': 1, 'slot': 'A', 'port': 5, 'chain': [...]}
    """
    if db_dir is not None:
        import os

        db_path = os.path.join(db_dir, "assembled_casm.db")
    else:
        db_path = get_database_path("assembled_casm.db", None)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        current_part = part_number.upper()
        chain = [current_part]
        max_depth = 10  # Prevent infinite loops

        for _ in range(max_depth):
            # Find next connection where current part is the source
            # Use same logic as chains view - only get latest status for each pair
            cursor.execute(
                """
                WITH latest_connection AS (
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
                    WHERE (part_number = ? OR connected_to = ?)
                        AND part_number IS NOT NULL 
                        AND connected_to IS NOT NULL
                    GROUP BY part_a, part_b
                )
                SELECT a.connected_to, a.connected_to_type, a.connection_status
                FROM assembly a
                INNER JOIN latest_connection lc
                ON (
                    (a.part_number = lc.part_a AND a.connected_to = lc.part_b) OR
                    (a.part_number = lc.part_b AND a.connected_to = lc.part_a)
                )
                AND a.scan_time = lc.latest_time
                WHERE a.part_number = ? AND a.connection_status = 'connected'
                LIMIT 1
            """,
                (current_part, current_part, current_part),
            )

            row = cursor.fetchone()
            if not row:
                # No outgoing connection found
                break

            next_part = row["connected_to"]
            next_type = row["connected_to_type"]
            chain.append(next_part)

            # Check if we've reached a SNAP board
            if next_type == "SNAP" or next_part.startswith("SNAP"):
                # Parse SNAP format: SNAP[chassis][slot][port]
                # e.g. SNAP1A05 -> chassis=1, slot=A, port=5
                try:
                    snap_str = next_part[4:]  # Remove 'SNAP' prefix
                    chassis = int(snap_str[0])
                    slot = snap_str[1]
                    port = int(snap_str[2:])

                    return {
                        "snap_part": next_part,
                        "chassis": chassis,
                        "slot": slot,
                        "port": port,
                        "chain": chain,
                    }
                except (IndexError, ValueError):
                    # Malformed SNAP part number
                    break

            # Continue traversal
            current_part = next_part

    return None


def get_snap_ports_for_antenna(
    antenna_number: str, *, db_dir: Optional[str] = None
) -> dict:
    """Get SNAP ports for both polarizations of an antenna.

    Parameters
    ----------
    antenna_number : str
        Antenna base number with or without polarization suffix.
        E.g. 'ANT00001', 'ANT00001P1', 'ANT00001P2'.
    db_dir : str, optional
        Custom database directory for testing.

    Returns
    -------
    dict
        SNAP port info for both polarizations:
        {
            'antenna': str,        # Base antenna number (ANT00001)
            'p1': dict or None,    # SNAP info for P1 chain
            'p2': dict or None     # SNAP info for P2 chain
        }

    Examples
    --------
    >>> ports = get_snap_ports_for_antenna('ANT00001')
    >>> ports['p1']['chassis']
    1
    >>> ports['p2']
    None  # P2 chain not assembled yet
    """
    from casman.database.antenna_positions import strip_polarization

    antenna_base = strip_polarization(antenna_number)

    # Try both polarizations
    p1_port = get_snap_port_for_chain(f"{antenna_base}P1", db_dir=db_dir)
    p2_port = get_snap_port_for_chain(f"{antenna_base}P2", db_dir=db_dir)

    return {"antenna": antenna_base, "p1": p1_port, "p2": p2_port}


def format_snap_port(snap_info: dict) -> str:
    """Format SNAP port info as human-readable string.

    Parameters
    ----------
    snap_info : dict
        SNAP port dictionary from get_snap_port_for_chain.

    Returns
    -------
    str
        Formatted string like "Chassis 1, Slot A, Port 5".

    Examples
    --------
    >>> info = {'chassis': 1, 'slot': 'A', 'port': 5}
    >>> format_snap_port(info)
    'Chassis 1, Slot A, Port 5'
    """
    return f"Chassis {snap_info['chassis']}, Slot {snap_info['slot']}, Port {snap_info['port']}"


__all__ = [
    "get_snap_port_for_chain",
    "get_snap_ports_for_antenna",
    "format_snap_port",
]
