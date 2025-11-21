# Database Package

Documentation for the `casman.database` package.

## Overview

Database package for CAsMan.

This package provides core database functionality including connection management,
initialization, and data access operations.

## Modules

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

Initialize all databases. Calls both init_parts_db() and init_assembled_db() to set up all required database tables for the CAsMan system.

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
