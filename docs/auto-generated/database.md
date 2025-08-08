# Database Package

Documentation for the `casman.database` package.

## Overview

Database package for CAsMan.

This package provides modular database functionality including connection management,
schema operations, data access utilities, and database migrations.

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
- `get_all_parts()` - Fetch all unique part numbers from the assembled_casm
- `get_last_update()` - Get the latest timestamp from the scan_time and connected_scan_time columns
- `get_assembly_records()` - Get all assembly records from the database
- `check_part_in_db()` - Check if a part number exists in the parts database and get its polarization
- `get_parts_by_criteria()` - Get parts from the database based on criteria

### connection

Database connection utilities for CAsMan.

This module provides utilities for database path resolution and
project root detection.

**Functions:**
- `find_project_root()` - Find the project root directory by looking for casman package or pyproject
- `get_database_path()` - Get the full path to a database file

### migrations

Database migration utilities for CAsMan.

This module provides database migration functionality to handle
schema updates and data migrations safely.

**Functions:**
- `get_table_info()` - Get information about table columns and structure
- `backup_database()` - Create a backup of the database before migration
- `check_database_integrity()` - Check database integrity using SQLite's built-in integrity check
- `get_schema_version()` - Get the current schema version of the database
- `set_schema_version()` - Set the schema version in the database
- `execute_migration()` - Execute a migration SQL statement and update version

**Classes:**
- `DatabaseMigrator` - Database migration manager for CAsMan databases

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

### get_all_parts

**Signature:** `get_all_parts(db_dir: Optional[str]) -> List[str]`

Fetch all unique part numbers from the assembled_casm.db database.

**Parameters:**

db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

List[str]
List of all unique part numbers found in the database.

---

### get_last_update

**Signature:** `get_last_update(db_dir: Optional[str]) -> Optional[str]`

Get the latest timestamp from the scan_time and connected_scan_time columns.

**Parameters:**

db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

Optional[str]
The latest timestamp value, or None if the table is empty.

---

### get_assembly_records

**Signature:** `get_assembly_records(db_dir: Optional[str]) -> List[Tuple[str, Optional[str], str, str]]`

Get all assembly records from the database.

**Parameters:**

db_dir : str, optional
Custom database directory.
If not provided, uses the project root's database directory.

**Returns:**

List[Tuple[str, Optional[str], str, str]]
List of assembly records as tuples of
(part_number, connected_to, scan_time, connected_scan_time).

---

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

This module provides utilities for database path resolution and
project root detection.

## Functions

### find_project_root

**Signature:** `find_project_root() -> str`

Find the project root directory by looking for casman package or pyproject.toml.

**Returns:**

str
Absolute path to the project root directory.

---

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

## Migrations Module Details

This module provides database migration functionality to handle
schema updates and data migrations safely.

## Functions

### get_table_info

**Signature:** `get_table_info(db_name: str, table_name: str, db_dir: Optional[str]) -> List[Dict]`

Get information about table columns and structure.

**Parameters:**

db_name : str
Name of the database file.
table_name : str
Name of the table to inspect.
db_dir : str, optional
Custom database directory.

**Returns:**

List[Dict]
List of column information dictionaries.

---

### backup_database

**Signature:** `backup_database(db_name: str, backup_suffix: str, db_dir: Optional[str]) -> str`

Create a backup of the database before migration.

**Parameters:**

db_name : str
Name of the database file.
backup_suffix : str, optional
Suffix to add to backup filename.
db_dir : str, optional
Custom database directory.

**Returns:**

str
Path to the backup file.

---

### check_database_integrity

**Signature:** `check_database_integrity(db_name: str, db_dir: Optional[str]) -> bool`

Check database integrity using SQLite's built-in integrity check.

**Parameters:**

db_name : str
Name of the database file.
db_dir : str, optional
Custom database directory.

**Returns:**

bool
True if database integrity is OK, False otherwise.

---

### get_schema_version

**Signature:** `get_schema_version() -> int`

Get the current schema version of the database.

**Returns:**

int
Current schema version, 0 if no version table exists.

---

### set_schema_version

**Signature:** `set_schema_version(version: int) -> None`

Set the schema version in the database.

**Parameters:**

version : int
Schema version to set.

---

### execute_migration

**Signature:** `execute_migration(sql: str, version: int) -> None`

Execute a migration SQL statement and update version.

**Parameters:**

sql : str
SQL statement to execute.
version : int
Version number to set after successful migration.

---

## Classes

### DatabaseMigrator

**Class:** `DatabaseMigrator`

Database migration manager for CAsMan databases.

Handles schema versioning and migration execution.

#### Methods

##### __init__

**Signature:** `__init__(db_name: str, db_dir: Optional[str])`

Initialize the migrator for a specific database.

**Parameters:**

db_name : str
Name of the database file.
db_dir : str, optional
Custom database directory.

---

##### get_schema_version

**Signature:** `get_schema_version() -> int`

Get the current schema version of the database.

**Returns:**

int
Current schema version, 0 if no version table exists.

---

##### set_schema_version

**Signature:** `set_schema_version(version: int) -> None`

Set the schema version in the database.

**Parameters:**

version : int
Schema version to set.

---

##### execute_migration

**Signature:** `execute_migration(sql: str, version: int) -> None`

Execute a migration SQL statement and update version.

**Parameters:**

sql : str
SQL statement to execute.
version : int
Version number to set after successful migration.

---

---
