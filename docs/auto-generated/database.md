# Database Package

Documentation for the `casman.database` package.

## Overview

Database package for CAsMan.

This package provides core database functionality including connection management,
initialization, and data access operations.

## Modules

### sync

Database backup and synchronization module for CAsMan.

Provides cloud backup/restore functionality with support for:
- Cloudflare R2 / AWS S3 backends
- Versioned backups with timestamps
- Zero data loss guarantees
- Offline-first operation with graceful degradation
- Multi-user safety with conflict detection

**Functions:**
- `to_dict()` - No docstring available
- `from_dict()` - No docstring available
- `from_config()` - Load sync configuration from config
- `backend()` - Lazy-load the storage backend
- `backup_database()` - Backup a database to cloud storage
- `list_backups()` - List available backups
- `restore_database()` - Restore a database from a backup
- `sync_from_remote()` - Sync a local database from the remote (download if newer)
- `check_needs_sync()` - Check if a local database needs to be synced from remote
- `maintain_storage_class()` - Perform maintenance to keep objects in Standard storage class
- `record_scan()` - Record a scan operation
- `reset_after_backup()` - Reset counters after a backup
- `should_backup()` - Check if a backup should be triggered based on scan count or time

**Classes:**
- `BackupMetadata` - Metadata for a database backup
- `SyncConfig` - Configuration for database synchronization
- `DatabaseSyncManager` - Manages database backup and synchronization
- `ScanTracker` - Tracks scan operations to trigger time/count-based backups

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

### quota

R2 Quota tracking to enforce Cloudflare free tier limits.

Tracks:
- Storage: 10 GB limit
- Class A operations (writes): 1 million/month limit
- Class B operations (reads): 10 million/month limit

**Functions:**
- `record_backup()` - Record a backup operation (Class A: PUT + metadata)
- `record_restore()` - Record a restore operation (Class B: GET)
- `record_list()` - Record a list operation (Class A: LIST)
- `record_sync_check()` - Record sync check operations (Class B: HEAD requests)
- `check_quota()` - Check if operation would exceed quota limits
- `get_usage_summary()` - Get current quota usage summary

**Classes:**
- `QuotaExceededError` - Raised when R2 quota limits are exceeded
- `QuotaTracker` - Track R2 API usage to prevent exceeding free tier limits

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

## Sync Module Details

Provides cloud backup/restore functionality with support for:
- Cloudflare R2 / AWS S3 backends
- Versioned backups with timestamps
- Zero data loss guarantees
- Offline-first operation with graceful degradation
- Multi-user safety with conflict detection

## Functions

### to_dict

**Signature:** `to_dict() -> dict`

No docstring available.

---

### from_dict

*@classmethod*

**Signature:** `from_dict(cls, data: dict) -> 'BackupMetadata'`

No docstring available.

---

### from_config

*@classmethod*

**Signature:** `from_config(cls) -> 'SyncConfig'`

Load sync configuration from config.yaml and environment.

---

### backend

*@property*

**Signature:** `backend()`

Lazy-load the storage backend.

---

### backup_database

**Signature:** `backup_database(db_path: str, db_name: str, operation: Optional[str], quiet: bool) -> Optional[BackupMetadata]`

Backup a database to cloud storage.

**Parameters:**

db_path : str
Path to the database file to backup.
db_name : str
Name of the database (e.g., 'parts.db').
operation : str, optional
Description of the operation that triggered this backup.
quiet : bool, default False
If True, suppress log messages.

**Returns:**

BackupMetadata or None
Metadata about the backup, or None if backup failed/disabled.

---

### list_backups

**Signature:** `list_backups(db_name: Optional[str]) -> List[Tuple[str, BackupMetadata]]`

List available backups.

**Parameters:**

db_name : str, optional
Filter backups for a specific database.

**Returns:**

List[Tuple[str, BackupMetadata]]
List of (backup_key, metadata) tuples, sorted by timestamp (newest first).

---

### restore_database

**Signature:** `restore_database(backup_key: str, dest_path: str, create_backup: bool) -> bool`

Restore a database from a backup.

**Parameters:**

backup_key : str
S3 key of the backup to restore.
dest_path : str
Destination path for the restored database.
create_backup : bool, default True
If True, backup the current database before restoring.

**Returns:**

bool
True if restore succeeded, False otherwise.

---

### sync_from_remote

**Signature:** `sync_from_remote(db_path: str, db_name: str, force: bool, quiet: bool) -> bool`

Sync a local database from the remote (download if newer).

**Parameters:**

db_path : str
Path to local database.
db_name : str
Name of the database.
force : bool, default False
Force download even if local is up to date.
quiet : bool, default False
Suppress log messages.

**Returns:**

bool
True if sync occurred, False otherwise.

---

### check_needs_sync

**Signature:** `check_needs_sync(db_path: str, db_name: str) -> bool`

Check if a local database needs to be synced from remote.

**Parameters:**

db_path : str
Path to local database.
db_name : str
Name of the database.

**Returns:**

bool
True if sync is needed, False otherwise.

---

### maintain_storage_class

**Signature:** `maintain_storage_class() -> Dict[str, any]`

Perform maintenance to keep objects in Standard storage class. Touches all backup objects by reading their metadata (HEAD request) to prevent automatic transition to Infrequent Access storage. Should be called at least once per month to ensure objects remain in the free tier eligible Standard storage class.

**Returns:**

dict
Summary of maintenance operation including objects touched.

---

### record_scan

**Signature:** `record_scan()`

Record a scan operation.

---

### reset_after_backup

**Signature:** `reset_after_backup()`

Reset counters after a backup.

---

### should_backup

**Signature:** `should_backup(config: SyncConfig) -> bool`

Check if a backup should be triggered based on scan count or time.

**Parameters:**

config : SyncConfig
Sync configuration with thresholds.

**Returns:**

bool
True if backup should be triggered.

---

## Classes

### BackupMetadata

*@dataclass*

**Class:** `BackupMetadata`

Metadata for a database backup.

#### Methods

##### to_dict

**Signature:** `to_dict() -> dict`

No docstring available.

---

##### from_dict

*@classmethod*

**Signature:** `from_dict(cls, data: dict) -> 'BackupMetadata'`

No docstring available.

---

---

### SyncConfig

*@dataclass*

**Class:** `SyncConfig`

Configuration for database synchronization.

#### Methods

##### from_config

*@classmethod*

**Signature:** `from_config(cls) -> 'SyncConfig'`

Load sync configuration from config.yaml and environment.

---

---

### DatabaseSyncManager

**Class:** `DatabaseSyncManager`

Manages database backup and synchronization.

#### Methods

##### __init__

**Signature:** `__init__(config: Optional[SyncConfig], db_dir: Optional[str])`

No docstring available.

---

##### backend

*@property*

**Signature:** `backend()`

Lazy-load the storage backend.

---

##### backup_database

**Signature:** `backup_database(db_path: str, db_name: str, operation: Optional[str], quiet: bool) -> Optional[BackupMetadata]`

Backup a database to cloud storage.

**Parameters:**

db_path : str
Path to the database file to backup.
db_name : str
Name of the database (e.g., 'parts.db').
operation : str, optional
Description of the operation that triggered this backup.
quiet : bool, default False
If True, suppress log messages.

**Returns:**

BackupMetadata or None
Metadata about the backup, or None if backup failed/disabled.

---

##### list_backups

**Signature:** `list_backups(db_name: Optional[str]) -> List[Tuple[str, BackupMetadata]]`

List available backups.

**Parameters:**

db_name : str, optional
Filter backups for a specific database.

**Returns:**

List[Tuple[str, BackupMetadata]]
List of (backup_key, metadata) tuples, sorted by timestamp (newest first).

---

##### restore_database

**Signature:** `restore_database(backup_key: str, dest_path: str, create_backup: bool) -> bool`

Restore a database from a backup.

**Parameters:**

backup_key : str
S3 key of the backup to restore.
dest_path : str
Destination path for the restored database.
create_backup : bool, default True
If True, backup the current database before restoring.

**Returns:**

bool
True if restore succeeded, False otherwise.

---

##### sync_from_remote

**Signature:** `sync_from_remote(db_path: str, db_name: str, force: bool, quiet: bool) -> bool`

Sync a local database from the remote (download if newer).

**Parameters:**

db_path : str
Path to local database.
db_name : str
Name of the database.
force : bool, default False
Force download even if local is up to date.
quiet : bool, default False
Suppress log messages.

**Returns:**

bool
True if sync occurred, False otherwise.

---

##### check_needs_sync

**Signature:** `check_needs_sync(db_path: str, db_name: str) -> bool`

Check if a local database needs to be synced from remote.

**Parameters:**

db_path : str
Path to local database.
db_name : str
Name of the database.

**Returns:**

bool
True if sync is needed, False otherwise.

---

##### maintain_storage_class

**Signature:** `maintain_storage_class() -> Dict[str, any]`

Perform maintenance to keep objects in Standard storage class. Touches all backup objects by reading their metadata (HEAD request) to prevent automatic transition to Infrequent Access storage. Should be called at least once per month to ensure objects remain in the free tier eligible Standard storage class.

**Returns:**

dict
Summary of maintenance operation including objects touched.

---

---

### ScanTracker

**Class:** `ScanTracker`

Tracks scan operations to trigger time/count-based backups.

#### Methods

##### __init__

**Signature:** `__init__(db_dir: Optional[str])`

No docstring available.

---

##### record_scan

**Signature:** `record_scan()`

Record a scan operation.

---

##### reset_after_backup

**Signature:** `reset_after_backup()`

Reset counters after a backup.

---

##### should_backup

**Signature:** `should_backup(config: SyncConfig) -> bool`

Check if a backup should be triggered based on scan count or time.

**Parameters:**

config : SyncConfig
Sync configuration with thresholds.

**Returns:**

bool
True if backup should be triggered.

---

---

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

**Signature:** `get_all_antenna_positions() -> List[dict]`

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

## Quota Module Details

Tracks:
- Storage: 10 GB limit
- Class A operations (writes): 1 million/month limit
- Class B operations (reads): 10 million/month limit

## Functions

### record_backup

**Signature:** `record_backup(size_bytes: int, num_files: int)`

Record a backup operation (Class A: PUT + metadata).

---

### record_restore

**Signature:** `record_restore()`

Record a restore operation (Class B: GET).

---

### record_list

**Signature:** `record_list(num_requests: int)`

Record a list operation (Class A: LIST).

---

### record_sync_check

**Signature:** `record_sync_check(num_files: int)`

Record sync check operations (Class B: HEAD requests).

---

### check_quota

**Signature:** `check_quota(quota_limits: dict, operation: str) -> bool`

Check if operation would exceed quota limits.

**Parameters:**

quota_limits : dict
Dictionary with quota limit configuration.
operation : str
Type of operation: 'backup', 'restore', 'list', 'sync'

**Returns:**

bool
True if operation is allowed, False otherwise.

**Raises:**

QuotaExceededError
If quota would be exceeded.

---

### get_usage_summary

**Signature:** `get_usage_summary(quota_limits: dict) -> dict`

Get current quota usage summary.

---

## Classes

### QuotaExceededError

**Class:** `QuotaExceededError(Exception)`

Raised when R2 quota limits are exceeded.

---

### QuotaTracker

**Class:** `QuotaTracker`

Track R2 API usage to prevent exceeding free tier limits.

#### Methods

##### __init__

**Signature:** `__init__(db_dir: Optional[str])`

No docstring available.

---

##### record_backup

**Signature:** `record_backup(size_bytes: int, num_files: int)`

Record a backup operation (Class A: PUT + metadata).

---

##### record_restore

**Signature:** `record_restore()`

Record a restore operation (Class B: GET).

---

##### record_list

**Signature:** `record_list(num_requests: int)`

Record a list operation (Class A: LIST).

---

##### record_sync_check

**Signature:** `record_sync_check(num_files: int)`

Record sync check operations (Class B: HEAD requests).

---

##### check_quota

**Signature:** `check_quota(quota_limits: dict, operation: str) -> bool`

Check if operation would exceed quota limits.

**Parameters:**

quota_limits : dict
Dictionary with quota limit configuration.
operation : str
Type of operation: 'backup', 'restore', 'list', 'sync'

**Returns:**

bool
True if operation is allowed, False otherwise.

**Raises:**

QuotaExceededError
If quota would be exceeded.

---

##### get_usage_summary

**Signature:** `get_usage_summary(quota_limits: dict) -> dict`

Get current quota usage summary.

---

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
