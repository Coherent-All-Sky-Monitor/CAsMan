# Database Package

Database package for CAsMan.

This package provides modular database functionality including connection management,
schema operations, data access utilities, and database migrations.

## Submodules

This package is organized into the following submodules:

### connection

Database connection utilities for CAsMan.

This module provides utilities for database path resolution and
project root detection.

**Functions:**

- `find_project_root()`
- `get_database_path()`

### initialization

Database initialization utilities for CAsMan.

This module provides functions to initialize and set up database tables
for both parts and assembly tracking.

**Functions:**

- `init_parts_db()`
- `init_assembled_db()`
- `init_all_databases()`

### migrations

Database migration utilities for CAsMan.

This module provides database migration functionality to handle
schema updates and data migrations safely.

**Functions:**

- `get_table_info()`
- `backup_database()`
- `check_database_integrity()`
- `get_schema_version()`
- `set_schema_version()`
- `execute_migration()`

### operations

Database operations utilities for CAsMan.

This module provides functions for querying and retrieving data
from the CAsMan databases.

**Functions:**

- `get_all_parts()`
- `get_last_update()`
- `get_assembly_records()`
- `check_part_in_db()`
- `get_parts_by_criteria()`
