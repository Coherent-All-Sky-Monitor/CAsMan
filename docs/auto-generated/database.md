# Database Package

Documentation for the `casman.database` package.

## Overview

Database package for CAsMan.

This package provides core database functionality including connection management,
initialization, and data access operations.

## Modules

### antenna_positions

Database operations for antenna grid positions.

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

**Functions:**
- `init_antenna_positions_table()` - Initialize the antenna_positions table in parts
- `strip_polarization()` - Remove polarization suffix from part number
- `assign_antenna_position()` - Assign an antenna to a grid position
- `get_antenna_position()` - Retrieve grid position for an antenna
- `get_antenna_at_position()` - Retrieve antenna assigned to a grid position
- `get_all_antenna_positions()` - Retrieve all antenna position assignments
- `remove_antenna_position()` - Remove antenna position assignment
- `load_grid_coordinates_from_csv()` - Load grid position coordinates from CSV file

### initialization

Database initialization utilities for CAsMan.

This module provides functions to initialize and set up database tables
for both parts and assembly tracking.

**Functions:**
- `init_parts_db()` - Initialize the parts
- `init_assembled_db()` - Initialize the assembled_casm
- `init_all_databases()` - Initialize all databases

### operations

Database operations utilities for CAsMan.

This module provides functions for querying and retrieving data
from the CAsMan databases.

**Functions:**
- `check_part_in_db()` - Check if a part number exists in the parts database and get its polarization
- `get_parts_by_criteria()` - Get parts from the database based on criteria

### connection

Database connection utilities for CAsMan.

This module provides utilities for database path resolution.

**Functions:**
- `get_database_path()` - Get the full path to a database file

## Antenna_Positions Module Details

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

## Functions

### init_antenna_positions_table

**Signature:** `init_antenna_positions_table(db_dir: Optional[str]) -> None`

Initialize the antenna_positions table in parts.db. Creates the table if it doesn't exist. Safe to call multiple times.

**Parameters:**

db_dir : str, optional
Custom database directory. If not provided, uses configured path.

**Raises:**

sqlite3.Error
If database operations fail.

---

### strip_polarization

**Signature:** `strip_polarization(part_number: str) -> str`

Remove polarization suffix from part number.

**Parameters:**

part_number : str
Part number, possibly with P1 or P2 suffix.

**Returns:**

str
Base part number without polarization.

**Examples:**

```python
>>> strip_polarization('ANT00001P1')
'ANT00001'
>>> strip_polarization('ANT00123')
'ANT00123'
```

---

### assign_antenna_position

**Signature:** `assign_antenna_position(antenna_number: str, grid_code: str) -> dict`

Assign an antenna to a grid position.

**Parameters:**

antenna_number : str
Antenna part number (with or without polarization suffix).
Polarization will be stripped automatically.
grid_code : str
Grid position code (e.g. 'CN002E03').

**Returns:**

dict
Success response with assigned position info:
{'success': True, 'antenna': str, 'grid_code': str, 'message': str}

**Raises:**

ValueError
If grid_code invalid, antenna already assigned (unless overwrite),
or position already occupied (unless overwrite).
sqlite3.Error
If database operations fail.

**Examples:**

```python
>>> assign_antenna_position('ANT00001P1', 'CN002E03')
{'success': True, 'antenna': 'ANT00001', 'grid_code': 'CN002E03', ...}
```

---

### get_antenna_position

**Signature:** `get_antenna_position(antenna_number: str) -> Optional[dict]`

Retrieve grid position for an antenna.

**Parameters:**

antenna_number : str
Antenna part number (with or without polarization).
db_dir : str, optional
Custom database directory for testing.

**Returns:**



**Examples:**

```python
>>> get_antenna_position('ANT00001P1')
{'antenna': 'ANT00001', 'grid_code': 'CN002E03', ...}
```

---

### get_antenna_at_position

**Signature:** `get_antenna_at_position(grid_code: str) -> Optional[dict]`

Retrieve antenna assigned to a grid position.

**Parameters:**

grid_code : str
Grid position code (e.g. 'CN002E03').
db_dir : str, optional
Custom database directory for testing.

**Returns:**



**Raises:**

ValueError
If grid_code is invalid.

**Examples:**

```python
>>> get_antenna_at_position('CN002E03')
{'antenna': 'ANT00001', 'grid_code': 'CN002E03', ...}
```

---

### get_all_antenna_positions

**Signature:** `get_all_antenna_positions() -> list[dict]`

Retrieve all antenna position assignments.

**Parameters:**

array_id : str, optional
Filter by array identifier (e.g. 'C'). If None, returns all arrays.
db_dir : str, optional
Custom database directory for testing.

**Returns:**

list of dict
List of position assignments, each dict containing:
{'antenna': str, 'grid_code': str, 'array_id': str, 'row_offset': int,
'east_col': int, 'assigned_at': str, 'notes': str or None,
'latitude': float or None, 'longitude': float or None, 'height': float or None,
'coordinate_system': str or None}

**Examples:**

```python
>>> positions = get_all_antenna_positions(array_id='C')
>>> len(positions)
42
```

---

### remove_antenna_position

**Signature:** `remove_antenna_position(antenna_number: str) -> dict`

Remove antenna position assignment.

**Parameters:**

antenna_number : str
Antenna part number (with or without polarization).
db_dir : str, optional
Custom database directory for testing.

**Returns:**

dict
{'success': True, 'message': str, 'removed': bool}
removed=True if assignment existed and was deleted, False if not assigned.

**Examples:**

```python
>>> remove_antenna_position('ANT00001P1')
{'success': True, 'removed': True, 'message': 'Removed ANT00001 from CN002E03'}
```

---

### load_grid_coordinates_from_csv

**Signature:** `load_grid_coordinates_from_csv(csv_path: Optional[str]) -> dict`

Load grid position coordinates from CSV file. Updates the antenna_positions table with latitude, longitude, height, and coordinate_system for each grid position. Only updates positions that exist in the CSV file. Does not create antenna assignments. CSV format: grid_code,latitude,longitude,height,coordinate_system,notes CN002E03,37.8719,-122.2585,10.5,WGS84,North row 2

**Parameters:**

csv_path : str, optional
Path to CSV file. If not provided, uses database/grid_positions.csv
db_dir : str, optional
Custom database directory for testing.

**Returns:**

dict
Summary with counts: {'updated': int, 'skipped': int, 'errors': list}

**Examples:**

```python
>>> result = load_grid_coordinates_from_csv()
>>> print(f"Updated {result['updated']} positions")
```

---

## Initialization Module Details

This module provides functions to initialize and set up database tables
for both parts and assembly tracking.

## Functions

### init_parts_db

**Signature:** `init_parts_db(db_dir: Optional[str]) -> None`

Initialize the parts.db database and create necessary tables if they don't exist. Creates the database directory if it doesn't exist and sets up the parts table with columns for id, part_number, part_type, polarization, and timestamps.

**Parameters:**

db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

None

---

### init_assembled_db

**Signature:** `init_assembled_db(db_dir: Optional[str]) -> None`

Initialize the assembled_casm.db database and create necessary tables if they don't exist. Creates the database directory if it doesn't exist and sets up the assembly table with columns for tracking part connections and scan times.

**Parameters:**

db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

None

---

### init_all_databases

**Signature:** `init_all_databases(db_dir: Optional[str]) -> None`

Initialize all databases. Calls init_parts_db(), init_assembled_db(), and init_antenna_positions_table() to set up all required database tables for the CAsMan system.

**Parameters:**

db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

None

---

## Operations Module Details

This module provides functions for querying and retrieving data
from the CAsMan databases.

## Functions

### check_part_in_db

**Signature:** `check_part_in_db(part_number: str, part_type: str, db_dir: Optional[str]) -> Tuple[bool, Optional[str]]`

Check if a part number exists in the parts database and get its polarization.

**Parameters:**

part_number : str
The part number to check.
part_type : str
The expected part type.
db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

Tuple[bool, Optional[str]]
(exists, polarization) where exists is True if part is found,
and polarization is the part's polarization if found.

---

### get_parts_by_criteria

**Signature:** `get_parts_by_criteria(part_type: Optional[str], polarization: Optional[str], db_dir: Optional[str]) -> List[Tuple[int, str, str, str, str, str]]`

Get parts from the database based on criteria.

**Parameters:**

part_type : Optional[str]
Filter by part type.
polarization : Optional[str]
Filter by polarization.
db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

List[Tuple[int, str, str, str, str, str]]
List of part records as tuples of             (id, part_number, part_type, polarization, date_created, date_modified).

---

## Connection Module Details

This module provides utilities for database path resolution.

## Functions

### get_database_path

**Signature:** `get_database_path(db_name: str, db_dir: Optional[str]) -> str`

Get the full path to a database file.

**Parameters:**

db_name : str
Name of the database file.
db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

str
Full path to the database file.

---
