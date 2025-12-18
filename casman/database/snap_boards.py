"""Database operations for SNAP board configurations.

This module provides CRUD operations for storing and retrieving SNAP board
information including serial numbers, MAC addresses, and IP addresses.

The snap_boards table schema:
    - id: Auto-incrementing primary key
    - chassis: Chassis number (1-4)
    - slot: Slot letter (A-K)
    - serial_number: Board serial number (unique)
    - mac_address: MAC address (unique)
    - ip_address: IP address (unique)
    - feng_id: F-engine ID (0-43, unique)
    - notes: Optional field notes
    - date_added: ISO timestamp when record was added
    - date_modified: ISO timestamp when record was last modified

Uniqueness constraints ensure:
    - Each (chassis, slot) combination is unique
    - Each serial number is unique
    - Each MAC address is unique
    - Each IP address is unique
"""

import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from casman.database.connection import get_database_path


def init_snap_boards_table(db_dir: Optional[str] = None) -> None:
    """Initialize the snap_boards table in parts.db.

    Creates the table if it doesn't exist. Safe to call multiple times.

    Parameters
    ----------
    db_dir : str, optional
        Custom database directory. If not provided, uses configured path.

    Raises
    ------
    sqlite3.Error
        If database operations fail.
    """
    if db_dir is not None:
        import os
        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS snap_boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chassis INTEGER NOT NULL,
                slot TEXT NOT NULL,
                serial_number TEXT UNIQUE NOT NULL,
                mac_address TEXT UNIQUE NOT NULL,
                ip_address TEXT UNIQUE NOT NULL,
                feng_id INTEGER UNIQUE NOT NULL,
                notes TEXT,
                date_added TEXT NOT NULL,
                date_modified TEXT,
                CHECK(chassis >= 1 AND chassis <= 4),
                CHECK(slot IN ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K')),
                CHECK(feng_id >= 0 AND feng_id <= 43),
                UNIQUE(chassis, slot)
            )
        """
        )
        
        # Check if feng_id column exists (for migration)
        cursor.execute("PRAGMA table_info(snap_boards)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "feng_id" not in columns:
            cursor.execute("ALTER TABLE snap_boards ADD COLUMN feng_id INTEGER")
        
        conn.commit()


def load_snap_boards_from_csv(csv_path: Optional[str] = None) -> Dict[str, int]:
    """Load SNAP board configurations from CSV file into database.

    CSV format: chassis, slot, sn, mac, ip, feng_id, notes

    Parameters
    ----------
    csv_path : str, optional
        Path to CSV file. If not provided, uses database/snap_boards.csv

    Returns
    -------
    dict
        Statistics with 'loaded', 'updated', 'skipped', 'errors' counts

    Raises
    ------
    FileNotFoundError
        If CSV file doesn't exist
    ValueError
        If CSV format is invalid
    sqlite3.Error
        If database operations fail
    """
    # Determine CSV path
    if csv_path is None:
        project_root = Path(__file__).parent.parent.parent
        csv_path = project_root / "database" / "snap_boards.csv"
    else:
        csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Get database path
    db_path = get_database_path("parts.db", None)

    # Ensure table exists
    init_snap_boards_table()

    stats = {"loaded": 0, "updated": 0, "skipped": 0, "errors": 0}

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Collect all CSV data first
        csv_data = []
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Validate required fields
                    required = ["chassis", "slot", "sn", "mac", "ip", "feng_id"]
                    missing = [f for f in required if f not in row or not row[f]]
                    if missing:
                        print(f"  Row {row_num}: Missing fields {missing}")
                        stats["errors"] += 1
                        continue

                    chassis = int(row["chassis"])
                    slot = row["slot"].strip().upper()
                    sn = row["sn"].strip()
                    mac = row["mac"].strip()
                    ip = row["ip"].strip()
                    feng_id = int(row["feng_id"])
                    notes = row.get("notes", "").strip()
                    
                    csv_data.append((chassis, slot, sn, mac, ip, feng_id, notes))

                except (ValueError, KeyError) as e:
                    print(f"  Row {row_num}: Error - {e}")
                    stats["errors"] += 1
                    continue

        timestamp = datetime.now(timezone.utc).isoformat()

        # First pass: identify what to update vs insert
        to_update = []
        to_insert = []
        
        for chassis, slot, sn, mac, ip, feng_id, notes in csv_data:
            try:
                # Check if record exists
                cursor.execute(
                    """
                    SELECT id, serial_number, mac_address, ip_address, feng_id
                    FROM snap_boards
                    WHERE chassis = ? AND slot = ?
                    """,
                    (chassis, slot),
                )
                existing = cursor.fetchone()

                if existing:
                    # Check if data changed
                    if (
                        existing[1] == sn
                        and existing[2] == mac
                        and existing[3] == ip
                        and existing[4] == feng_id
                    ):
                        stats["skipped"] += 1
                        continue

                    to_update.append((chassis, slot, sn, mac, ip, feng_id, notes))
                else:
                    to_insert.append((chassis, slot, sn, mac, ip, feng_id, notes))

            except Exception as e:
                print(f"  Error checking {chassis}{slot}: {e}")
                stats["errors"] += 1

        # Second pass: delete all records that will be updated
        for chassis, slot, sn, mac, ip, feng_id, notes in to_update:
            try:
                cursor.execute(
                    "DELETE FROM snap_boards WHERE chassis = ? AND slot = ?",
                    (chassis, slot),
                )
            except Exception as e:
                print(f"  Error deleting {chassis}{slot}: {e}")
                stats["errors"] += 1

        # Third pass: insert all updated records
        for chassis, slot, sn, mac, ip, feng_id, notes in to_update:
            try:
                cursor.execute(
                    """
                    INSERT INTO snap_boards
                    (chassis, slot, serial_number, mac_address, ip_address,
                     feng_id, notes, date_added, date_modified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (chassis, slot, sn, mac, ip, feng_id, notes, timestamp, timestamp),
                )
                stats["updated"] += 1
            except sqlite3.IntegrityError as e:
                print(f"  Error updating {chassis}{slot}: {e}")
                stats["errors"] += 1

        # Fourth pass: insert new records
        for chassis, slot, sn, mac, ip, feng_id, notes in to_insert:
            try:
                cursor.execute(
                    """
                    INSERT INTO snap_boards
                    (chassis, slot, serial_number, mac_address, ip_address,
                     feng_id, notes, date_added)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (chassis, slot, sn, mac, ip, feng_id, notes, timestamp),
                )
                stats["loaded"] += 1
            except sqlite3.IntegrityError as e:
                print(f"  Error inserting {chassis}{slot}: {e}")
                stats["errors"] += 1

        conn.commit()

    return stats


def get_snap_board_info(
    chassis: int, slot: str, db_dir: Optional[str] = None
) -> Optional[Tuple[str, str, str, int]]:
    """Get SNAP board information for a specific chassis and slot.

    Parameters
    ----------
    chassis : int
        Chassis number (1-4)
    slot : str
        Slot letter (A-K)
    db_dir : str, optional
        Custom database directory

    Returns
    -------
    tuple or None
        (serial_number, mac_address, ip_address, feng_id) or None if not found
    """
    if db_dir is not None:
        import os
        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT serial_number, mac_address, ip_address, feng_id
            FROM snap_boards
            WHERE chassis = ? AND slot = ?
            """,
            (chassis, slot.upper()),
        )
        result = cursor.fetchone()

    return result


def get_all_snap_boards(
    db_dir: Optional[str] = None,
) -> List[Dict[str, any]]:
    """Get all SNAP board configurations.

    Parameters
    ----------
    db_dir : str, optional
        Custom database directory

    Returns
    -------
    list
        List of dicts with keys: chassis, slot, serial_number, mac_address, ip_address
    """
    if db_dir is not None:
        import os
        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT chassis, slot, serial_number, mac_address, ip_address, feng_id, notes
            FROM snap_boards
            ORDER BY chassis, slot
            """
        )
        rows = cursor.fetchall()

    boards = []
    for row in rows:
        boards.append(
            {
                "chassis": row[0],
                "slot": row[1],
                "serial_number": row[2],
                "mac_address": row[3],
                "ip_address": row[4],
                "feng_id": row[5],
                "notes": row[6],
            }
        )

    return boards
