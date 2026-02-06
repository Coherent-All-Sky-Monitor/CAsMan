"""Database operations for antenna grid positions.

This module provides CRUD operations for storing and retrieving antenna
positions within the grid layout. Positions are stored in the `parts.db`
database alongside other part metadata.

The antenna_positions table schema:
    - id: Auto-incrementing primary key
    - antenna_number: Base antenna number without polarization (ANT00001)
    - array_id: Array identifier letter ('C' for core)
    - row_offset: Signed row offset (-21 to +21, 0 = center)
    - east_col: East column index (0-5 for core)
    - grid_code: Canonical position string (e.g. 'CN002E03')
    - assigned_at: ISO timestamp of assignment
    - notes: Optional field notes
    - latitude: Latitude in decimal degrees (REAL)
    - longitude: Longitude in decimal degrees (REAL)
    - height: Height in meters above reference (REAL)
    - coordinate_system: Coordinate system identifier (e.g., 'WGS84', 'local')

Uniqueness constraints ensure:
    - Each antenna can only be assigned one position
    - Each grid position can only have one antenna
"""

from datetime import datetime, timezone
import sqlite3
from typing import List, Optional

from casman.antenna.grid import parse_grid_code, to_grid_code
from casman.database.connection import get_database_path


def init_antenna_positions_table(db_dir: Optional[str] = None) -> None:
    """Initialize the antenna_positions table in parts.db.

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
            CREATE TABLE IF NOT EXISTS antenna_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                antenna_number TEXT UNIQUE NOT NULL,
                array_id TEXT NOT NULL,
                row_offset INTEGER NOT NULL,
                east_col INTEGER NOT NULL,
                grid_code TEXT UNIQUE NOT NULL,
                assigned_at TEXT NOT NULL,
                notes TEXT,
                latitude REAL,
                longitude REAL,
                height REAL,
                coordinate_system TEXT,
                CHECK(row_offset >= -999 AND row_offset <= 999),
                CHECK(east_col >= 0 AND east_col <= 99),
                UNIQUE(array_id, row_offset, east_col)
            )
        """
        )

        # Check if coordinate columns exist (for migration)
        cursor.execute("PRAGMA table_info(antenna_positions)")
        columns = [row[1] for row in cursor.fetchall()]

        if "latitude" not in columns:
            cursor.execute("ALTER TABLE antenna_positions ADD COLUMN latitude REAL")
        if "longitude" not in columns:
            cursor.execute("ALTER TABLE antenna_positions ADD COLUMN longitude REAL")
        if "height" not in columns:
            cursor.execute("ALTER TABLE antenna_positions ADD COLUMN height REAL")
        if "coordinate_system" not in columns:
            cursor.execute(
                "ALTER TABLE antenna_positions ADD COLUMN coordinate_system TEXT"
            )

        conn.commit()


def strip_polarization(part_number: str) -> str:
    """Remove polarization suffix from part number.

    Parameters
    ----------
    part_number : str
        Part number, possibly with P1 or P2 suffix.

    Returns
    -------
    str
        Base part number without polarization.

    Examples
    --------
    >>> strip_polarization('ANT00001P1')
    'ANT00001'
    >>> strip_polarization('ANT00123')
    'ANT00123'
    """
    import re

    match = re.match(r"^(ANT\d{5})(?:P[12])?$", part_number.upper())
    if match:
        return match.group(1)
    return part_number


def assign_antenna_position(
    antenna_number: str,
    grid_code: str,
    *,
    notes: Optional[str] = None,
    allow_overwrite: bool = False,
    db_dir: Optional[str] = None,
) -> dict:
    """Assign an antenna to a grid position.

    Parameters
    ----------
    antenna_number : str
        Antenna part number (with or without polarization suffix).
        Polarization will be stripped automatically.
    grid_code : str
        Grid position code (e.g. 'CN002E03').
    notes : str, optional
        Optional field notes for the assignment.
    allow_overwrite : bool, default=False
        If True, allows reassigning antenna or position. If False, raises
        ValueError if either antenna or position already assigned.
    db_dir : str, optional
        Custom database directory for testing.

    Returns
    -------
    dict
        Success response with assigned position info:
        {'success': True, 'antenna': str, 'grid_code': str, 'message': str}

    Raises
    ------
    ValueError
        If grid_code invalid, antenna already assigned (unless overwrite),
        or position already occupied (unless overwrite).
    sqlite3.Error
        If database operations fail.

    Examples
    --------
    >>> assign_antenna_position('ANT00001P1', 'CN002E03')
    {'success': True, 'antenna': 'ANT00001', 'grid_code': 'CN002E03', ...}
    """
    # Strip polarization and validate
    antenna_base = strip_polarization(antenna_number)
    if not antenna_base.startswith("ANT"):
        raise ValueError(f"Invalid antenna number: {antenna_number}")

    # Parse and validate grid code
    try:
        position = parse_grid_code(grid_code)
    except ValueError as e:
        raise ValueError(f"Invalid grid code: {e}")

    # Get database connection
    if db_dir is not None:
        import os

        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Check if antenna already assigned
        cursor.execute(
            "SELECT grid_code FROM antenna_positions WHERE antenna_number = ?",
            (antenna_base,),
        )
        existing_antenna = cursor.fetchone()
        if existing_antenna and not allow_overwrite:
            raise ValueError(
                f"Antenna {antenna_base} already assigned to {existing_antenna[0]}. "
                "Use allow_overwrite=True to reassign."
            )

        # Check if position already occupied
        cursor.execute(
            "SELECT antenna_number FROM antenna_positions WHERE grid_code = ?",
            (position.grid_code,),
        )
        existing_position = cursor.fetchone()
        if (
            existing_position
            and existing_position[0] != antenna_base
            and not allow_overwrite
        ):
            raise ValueError(
                f"Position {position.grid_code} already occupied by {existing_position[0]}. "
                "Use allow_overwrite=True to reassign."
            )

        # Perform assignment (INSERT or REPLACE)
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if allow_overwrite:
            # Delete existing entries
            cursor.execute(
                "DELETE FROM antenna_positions WHERE antenna_number = ?",
                (antenna_base,),
            )
            cursor.execute(
                "DELETE FROM antenna_positions WHERE grid_code = ?",
                (position.grid_code,),
            )

        cursor.execute(
            """
            INSERT INTO antenna_positions
            (antenna_number, array_id, row_offset, east_col, grid_code, assigned_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                antenna_base,
                position.array_id,
                position.row_offset,
                position.east_col,
                position.grid_code,
                timestamp,
                notes,
            ),
        )
        conn.commit()

    return {
        "success": True,
        "antenna": antenna_base,
        "grid_code": position.grid_code,
        "message": f"Assigned {antenna_base} to {position.grid_code}",
    }


def get_antenna_position(
    antenna_number: str, *, db_dir: Optional[str] = None
) -> Optional[dict]:
    """Retrieve grid position for an antenna.

    Parameters
    ----------
    antenna_number : str
        Antenna part number (with or without polarization).
    db_dir : str, optional
        Custom database directory for testing.

    Returns
    -------
    dict or None
        Position info if assigned:
        {'antenna': str, 'grid_code': str, 'array_id': str, 'row_offset': int,
         'east_col': int, 'assigned_at': str, 'notes': str or None,
         'latitude': float or None, 'longitude': float or None, 'height': float or None,
         'coordinate_system': str or None}
        Returns None if antenna not assigned.

    Examples
    --------
    >>> get_antenna_position('ANT00001P1')
    {'antenna': 'ANT00001', 'grid_code': 'CN002E03', ...}
    """
    antenna_base = strip_polarization(antenna_number)

    if db_dir is not None:
        import os

        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT antenna_number, grid_code, array_id, row_offset, east_col, assigned_at, notes,
                   latitude, longitude, height, coordinate_system
            FROM antenna_positions
            WHERE antenna_number = ?
        """,
            (antenna_base,),
        )
        row = cursor.fetchone()

    if row:
        return dict(row)
    return None


def get_antenna_at_position(
    grid_code: str, *, db_dir: Optional[str] = None
) -> Optional[dict]:
    """Retrieve antenna assigned to a grid position.

    Parameters
    ----------
    grid_code : str
        Grid position code (e.g. 'CN002E03').
    db_dir : str, optional
        Custom database directory for testing.

    Returns
    -------
    dict or None
        Antenna info if position occupied:
        {'antenna': str, 'grid_code': str, 'array_id': str, 'row_offset': int,
         'east_col': int, 'assigned_at': str, 'notes': str or None}
        Returns None if position not assigned.

    Raises
    ------
    ValueError
        If grid_code is invalid.

    Examples
    --------
    >>> get_antenna_at_position('CN002E03')
    {'antenna': 'ANT00001', 'grid_code': 'CN002E03', ...}
    """
    # Validate grid code
    try:
        parse_grid_code(grid_code)
    except ValueError as e:
        raise ValueError(f"Invalid grid code: {e}")

    if db_dir is not None:
        import os

        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT antenna_number, grid_code, array_id, row_offset, east_col, assigned_at, notes
            FROM antenna_positions
            WHERE grid_code = ?
        """,
            (grid_code.upper(),),
        )
        row = cursor.fetchone()

    if row:
        return dict(row)
    return None


def get_all_antenna_positions(
    *, array_id: Optional[str] = None, db_dir: Optional[str] = None
) -> List[dict]:
    """Retrieve all antenna position assignments.

    Parameters
    ----------
    array_id : str, optional
        Filter by array identifier (e.g. 'C'). If None, returns all arrays.
    db_dir : str, optional
        Custom database directory for testing.

    Returns
    -------
    list of dict
        List of position assignments, each dict containing:
        {'antenna': str, 'grid_code': str, 'array_id': str, 'row_offset': int,
         'east_col': int, 'assigned_at': str, 'notes': str or None,
         'latitude': float or None, 'longitude': float or None, 'height': float or None,
         'coordinate_system': str or None}

    Examples
    --------
    >>> positions = get_all_antenna_positions(array_id='C')
    >>> len(positions)
    42
    """
    if db_dir is not None:
        import os

        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if array_id is not None:
            cursor.execute(
                """
                SELECT antenna_number, grid_code, array_id, row_offset, east_col, assigned_at, notes,
                       latitude, longitude, height, coordinate_system
                FROM antenna_positions
                WHERE array_id = ?
                ORDER BY row_offset DESC, east_col ASC
            """,
                (array_id,),
            )
        else:
            cursor.execute(
                """
                SELECT antenna_number, grid_code, array_id, row_offset, east_col, assigned_at, notes,
                       latitude, longitude, height, coordinate_system
                FROM antenna_positions
                ORDER BY array_id ASC, row_offset DESC, east_col ASC
            """
            )

        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def remove_antenna_position(
    antenna_number: str, *, db_dir: Optional[str] = None
) -> dict:
    """Remove antenna position assignment.

    Parameters
    ----------
    antenna_number : str
        Antenna part number (with or without polarization).
    db_dir : str, optional
        Custom database directory for testing.

    Returns
    -------
    dict
        {'success': True, 'message': str, 'removed': bool}
        removed=True if assignment existed and was deleted, False if not assigned.

    Examples
    --------
    >>> remove_antenna_position('ANT00001P1')
    {'success': True, 'removed': True, 'message': 'Removed ANT00001 from CN002E03'}
    """
    antenna_base = strip_polarization(antenna_number)

    if db_dir is not None:
        import os

        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Check current assignment
        cursor.execute(
            "SELECT grid_code FROM antenna_positions WHERE antenna_number = ?",
            (antenna_base,),
        )
        existing = cursor.fetchone()

        if existing:
            grid_code = existing[0]
            cursor.execute(
                "DELETE FROM antenna_positions WHERE antenna_number = ?",
                (antenna_base,),
            )
            conn.commit()
            
            return {
                "success": True,
                "removed": True,
                "message": f"Removed {antenna_base} from {grid_code}",
            }
        else:
            return {
                "success": True,
                "removed": False,
                "message": f"{antenna_base} was not assigned to any position",
            }


def load_grid_coordinates_from_csv(
    csv_path: Optional[str] = None, *, db_dir: Optional[str] = None
) -> dict:
    """Load grid position coordinates from CSV file.

    Updates the antenna_positions table with latitude, longitude, height, and
    coordinate_system for each grid position. Only updates positions that exist
    in the CSV file. Does not create antenna assignments.

    CSV format:
        grid_code,latitude,longitude,height,coordinate_system,notes
        CN002E03,37.8719,-122.2585,10.5,WGS84,North row 2

    Parameters
    ----------
    csv_path : str, optional
        Path to CSV file. If not provided, uses database/grid_positions.csv
    db_dir : str, optional
        Custom database directory for testing.

    Returns
    -------
    dict
        Summary with counts: {'updated': int, 'skipped': int, 'errors': list}

    Examples
    --------
    >>> result = load_grid_coordinates_from_csv()
    >>> print(f"Updated {result['updated']} positions")
    """
    import csv
    import os

    # Determine CSV path
    if csv_path is None:
        # Default to database/grid_positions.csv
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        csv_path = os.path.join(project_root, "database", "grid_positions.csv")

    if not os.path.exists(csv_path):
        return {
            "updated": 0,
            "skipped": 0,
            "errors": [f"CSV file not found: {csv_path}"],
        }

    # Get database path
    if db_dir is not None:
        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    updated = 0
    skipped = 0
    errors = []

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                grid_code = row.get("grid_code", "").strip().upper()
                if not grid_code:
                    skipped += 1
                    continue

                # Parse coordinate values (empty strings become None)
                lat = row.get("latitude", "").strip()
                lon = row.get("longitude", "").strip()
                height = row.get("height", "").strip()
                coord_sys = row.get("coordinate_system", "").strip()

                latitude = float(lat) if lat else None
                longitude = float(lon) if lon else None
                height_val = float(height) if height else None
                coord_system = coord_sys if coord_sys else None

                try:
                    # Check if values have changed before updating
                    cursor.execute(
                        """
                        SELECT latitude, longitude, height, coordinate_system
                        FROM antenna_positions
                        WHERE grid_code = ?
                        """,
                        (grid_code,)
                    )
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Compare values (handle None/NULL comparison)
                        if (existing[0] == latitude and 
                            existing[1] == longitude and 
                            existing[2] == height_val and 
                            existing[3] == coord_system):
                            skipped += 1
                            continue
                        
                        # Values differ, update
                        cursor.execute(
                            """
                            UPDATE antenna_positions
                            SET latitude = ?,
                                longitude = ?,
                                height = ?,
                                coordinate_system = ?
                            WHERE grid_code = ?
                            """,
                            (latitude, longitude, height_val, coord_system, grid_code),
                        )
                        updated += 1
                    else:
                        # Grid code not found in database
                        skipped += 1

                except Exception as e:
                    errors.append(f"{grid_code}: {str(e)}")
                    skipped += 1

        conn.commit()

    return {"updated": updated, "skipped": skipped, "errors": errors}


def load_grid_positions_from_csv(
    csv_path: Optional[str] = None, *, db_dir: Optional[str] = None
) -> dict:
    """Load grid position coordinates from CSV into grid_positions table.
    
    This loads coordinates for ALL grid positions into a separate table,
    independent of antenna assignments.
    
    CSV format:
        grid_code,latitude,longitude,height,coordinate_system,notes
        CN002E03,37.8719,-122.2585,10.5,WGS84,North row 2
    
    Parameters
    ----------
    csv_path : str, optional
        Path to CSV file. If not provided, uses database/grid_positions.csv
    db_dir : str, optional
        Custom database directory for testing.
    
    Returns
    -------
    dict
        Summary with counts: {'loaded': int, 'skipped': int, 'errors': list}
    """
    import csv
    import os
    
    # Determine CSV path
    if csv_path is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        csv_path = os.path.join(project_root, "database", "grid_positions.csv")
    
    if not os.path.exists(csv_path):
        return {
            "loaded": 0,
            "skipped": 0,
            "errors": [f"CSV file not found: {csv_path}"],
        }
    
    # Get database path
    if db_dir is not None:
        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)
    
    loaded = 0
    skipped = 0
    errors = []
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                grid_code = row.get("grid_code", "").strip().upper()
                if not grid_code:
                    skipped += 1
                    continue
                
                lat = row.get("latitude", "").strip()
                lon = row.get("longitude", "").strip()
                height = row.get("height", "").strip()
                coord_sys = row.get("coordinate_system", "").strip()
                notes = row.get("notes", "").strip()
                
                try:
                    latitude = float(lat) if lat else None
                    longitude = float(lon) if lon else None
                    height_val = float(height) if height else None
                    
                    if latitude is None or longitude is None or height_val is None:
                        skipped += 1
                        continue
                    
                    # Insert or replace
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO grid_positions
                        (grid_code, latitude, longitude, height, coordinate_system, notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (grid_code, latitude, longitude, height_val, coord_sys or None, notes or None),
                    )
                    loaded += 1
                except Exception as e:
                    errors.append(f"{grid_code}: {str(e)}")
                    skipped += 1
        
        conn.commit()
    
    return {"loaded": loaded, "skipped": skipped, "errors": errors}


__all__ = [
    "init_antenna_positions_table",
    "strip_polarization",
    "assign_antenna_position",
    "get_antenna_position",
    "get_antenna_at_position",
    "get_all_antenna_positions",
    "remove_antenna_position",
    "load_grid_coordinates_from_csv",
    "load_grid_positions_from_csv",
]
