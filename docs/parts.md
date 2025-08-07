# Parts Package

CAsMan parts subpackage: unified API for part management.

This __init__.py exposes the main part management functions, classes, and types.

## Submodules

This package is organized into the following submodules:

### db

Database access utilities for CAsMan parts.

**Functions:**

- `read_parts()`

### generation

Part number and barcode generation utilities for CAsMan.

**Functions:**

- `get_last_part_number()`
- `generate_part_numbers()`

### interactive

Interactive CLI utilities for CAsMan parts management.

**Functions:**

- `display_parts_interactive()`
- `add_parts_interactive()`
- `main()`
- `h()`

### part

Part class and core part functionality for CAsMan.

This module provides the main Part class for representing individual parts
and their properties, along with related utility functions.

**Functions:**

- `create_part()`
- `to_dict()`
- `from_dict()`
- `from_database_row()`
- `is_valid()`
- `get_barcode_filename()`
- `update_modified_time()`

### search

Advanced search functionality for CAsMan parts.

This module provides enhanced search capabilities for finding parts
based on various criteria and patterns.

**Functions:**

- `search_parts()`
- `get_all_parts()`
- `search_by_prefix()`
- `get_part_statistics()`
- `find_part()`
- `get_recent_parts()`

### types

Part type configuration utilities for CAsMan.

**Functions:**

- `load_part_types()`

### validation

Part validation utilities for CAsMan.

This module provides validation functions for part numbers, part types,
and other part-related data integrity checks.

**Functions:**

- `validate_part_number()`
- `validate_part_type()`
- `validate_polarization()`
- `get_part_info()`
- `normalize_part_number()`
