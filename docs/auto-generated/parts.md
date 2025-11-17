# Parts Package

Documentation for the `casman.parts` package.

## Overview

CAsMan parts subpackage: unified API for part management.

This __init__.py exposes the main part management functions, classes, and types.

## Modules

### db

Database access utilities for CAsMan parts.

**Functions:**
- `read_parts()` - Read parts from the database with optional filtering

### generation

Part number and barcode generation utilities for CAsMan.

**Functions:**
- `get_last_part_number()` - Get the last part number for a given part type
- `generate_part_numbers()` - Generate new part numbers for a given part type

### types

Part type configuration utilities for CAsMan.

**Functions:**
- `load_part_types()` - Load part types from config

### interactive

Interactive CLI utilities for CAsMan parts management.

**Functions:**
- `display_parts_interactive()` - Interactive function to display parts with user input
- `add_parts_interactive()` - Interactive function to add new parts
- `main()` - Main function for command-line usage
- `h()` - No docstring available

### search

Advanced search functionality for CAsMan parts.

This module provides enhanced search capabilities for finding parts
based on various criteria and patterns.

**Functions:**
- `search_parts()` - Advanced search for parts with multiple criteria
- `get_all_parts()` - Get all parts from the database
- `search_by_prefix()` - Search for parts by prefix (e
- `get_part_statistics()` - Get statistics about parts in the database
- `find_part()` - Find a specific part by part number
- `get_recent_parts()` - Get the most recently created parts

### part

Part class and core part functionality for CAsMan.

This module provides the main Part class for representing individual parts
and their properties, along with related utility functions.

**Functions:**
- `create_part()` - Convenience function to create a Part instance
- `to_dict()` - Convert part to dictionary representation
- `from_dict()` - Create Part instance from dictionary
- `from_database_row()` - Create Part instance from database row
- `is_valid()` - Check if the part is valid
- `get_barcode_filename()` - Get the expected barcode filename for this part
- `update_modified_time()` - Update the modified timestamp to current time

**Classes:**
- `Part` - Represents a CAsMan part with validation and utility methods

### validation

Part validation utilities for CAsMan.

This module provides validation functions for part numbers, part types,
and other part-related data integrity checks.

**Functions:**
- `validate_part_number()` - Validate a part number format
- `validate_part_type()` - Validate if a part type is supported
- `validate_polarization()` - Validate polarization format
- `get_part_info()` - Extract part information from a valid part number
- `normalize_part_number()` - Normalize a part number to standard format

## Db Module Details

## Functions

### read_parts

**Signature:** `read_parts(part_type: Optional[str], polarization: Optional[str], db_dir: Optional[str]) -> List[Tuple]`

Read parts from the database with optional filtering.

---

## Generation Module Details

## Functions

### get_last_part_number

**Signature:** `get_last_part_number(part_type: str, db_dir: Optional[str]) -> Optional[str]`

Get the last part number for a given part type.

---

### generate_part_numbers

**Signature:** `generate_part_numbers(part_type: str, count: int, polarization: str, db_dir: Optional[str]) -> List[str]`

Generate new part numbers for a given part type.

---

## Types Module Details

## Functions

### load_part_types

**Signature:** `load_part_types() -> Dict[int, Tuple[str, str]]`

Load part types from config.yaml, parsing keys as int and values as tuple.

**Returns:**

Dict[int, Tuple[str, str]]
Mapping from integer key to (full_name, abbreviation).

---

## Interactive Module Details

## Functions

### display_parts_interactive

**Signature:** `display_parts_interactive() -> None`

Interactive function to display parts with user input.

---

### add_parts_interactive

**Signature:** `add_parts_interactive() -> None`

Interactive function to add new parts.

---

### main

**Signature:** `main() -> None`

Main function for command-line usage.

---

### h

**Signature:** `h(char: str, width: int) -> str`

No docstring available.

---

## Search Module Details

This module provides enhanced search capabilities for finding parts
based on various criteria and patterns.

## Functions

### search_parts

**Signature:** `search_parts(part_type: Optional[str], polarization: Optional[str], part_number_pattern: Optional[str], created_after: Optional[str], created_before: Optional[str], limit: Optional[int], db_dir: Optional[str]) -> List[Part]`

Advanced search for parts with multiple criteria.

**Parameters:**

part_type : Optional[str]
Filter by part type (e.g., "ANTENNA")
polarization : Optional[str]
Filter by polarization (e.g., "P1")
part_number_pattern : Optional[str]
Filter by part number pattern (supports SQL LIKE syntax)
created_after : Optional[str]
Filter parts created after this date (YYYY-MM-DD format)
created_before : Optional[str]
Filter parts created before this date (YYYY-MM-DD format)
limit : Optional[int]
Maximum number of results to return
db_dir : Optional[str]
Custom database directory

**Returns:**

List[Part]
List of matching Part instances

---

### get_all_parts

**Signature:** `get_all_parts(db_dir: Optional[str]) -> List[Part]`

Get all parts from the database.

**Parameters:**

db_dir : Optional[str]
Custom database directory

**Returns:**

List[Part]
List of all Part instances

---

### search_by_prefix

**Signature:** `search_by_prefix(prefix: str, db_dir: Optional[str]) -> List[Part]`

Search for parts by prefix (e.g., "ANT", "LNA").

**Parameters:**

prefix : str
The part prefix to search for
db_dir : Optional[str]
Custom database directory

**Returns:**

List[Part]
List of matching Part instances

---

### get_part_statistics

**Signature:** `get_part_statistics(db_dir: Optional[str]) -> Dict[str, Any]`

Get statistics about parts in the database.

**Parameters:**

db_dir : Optional[str]
Custom database directory

**Returns:**

Dict[str, Any]
Dictionary containing part statistics

---

### find_part

**Signature:** `find_part(part_number: str, db_dir: Optional[str]) -> Optional[Part]`

Find a specific part by part number.

**Parameters:**

part_number : str
The exact part number to find
db_dir : Optional[str]
Custom database directory

**Returns:**

Optional[Part]
The Part instance if found, None otherwise

---

### get_recent_parts

**Signature:** `get_recent_parts(count: int, db_dir: Optional[str]) -> List[Part]`

Get the most recently created parts.

**Parameters:**

count : int
Number of recent parts to return (default: 10)
db_dir : Optional[str]
Custom database directory

**Returns:**

List[Part]
List of recently created Part instances

---

## Part Module Details

This module provides the main Part class for representing individual parts
and their properties, along with related utility functions.

## Functions

### create_part

**Signature:** `create_part(part_number: str, **kwargs) -> Part`

Convenience function to create a Part instance.

**Parameters:**

part_number : str
The part number
**kwargs
Additional Part constructor arguments

**Returns:**

Part
New Part instance

---

### to_dict

**Signature:** `to_dict() -> Dict[str, Any]`

Convert part to dictionary representation.

**Returns:**

Dict[str, Any]
Dictionary containing all part properties

---

### from_dict

*@classmethod*

**Signature:** `from_dict(cls, data: Dict[str, Any]) -> 'Part'`

Create Part instance from dictionary.

**Parameters:**

data : Dict[str, Any]
Dictionary containing part data

**Returns:**

Part
New Part instance

---

### from_database_row

*@classmethod*

**Signature:** `from_database_row(cls, row: tuple) -> 'Part'`

Create Part instance from database row. Assumes row format: (id, part_number, part_type, polarization, date_created, date_modified)

**Parameters:**

row : tuple
Database row tuple

**Returns:**

Part
New Part instance

---

### is_valid

**Signature:** `is_valid() -> bool`

Check if the part is valid.

**Returns:**

bool
True if all part properties are valid

---

### get_barcode_filename

**Signature:** `get_barcode_filename() -> str`

Get the expected barcode filename for this part.

**Returns:**

str
Barcode filename (e.g., "ANT00001P1.png")

---

### update_modified_time

**Signature:** `update_modified_time() -> None`

Update the modified timestamp to current time.

---

## Classes

### Part

**Class:** `Part`

Represents a CAsMan part with validation and utility methods.

This class encapsulates all properties and behaviors of a part,
including validation, formatting, and database representation.

#### Methods

##### __init__

**Signature:** `__init__(part_number: str, part_type: Optional[str], polarization: Optional[str], date_created: Optional[str], date_modified: Optional[str]) -> None`

Initialize a Part instance.

**Parameters:**

part_number : str
The part number (e.g., "ANT00001P1")
part_type : Optional[str]
The part type (e.g., "ANTENNA"). If None, extracted from part_number
polarization : Optional[str]
The polarization (e.g., "P1"). If None, extracted from part_number
date_created : Optional[str]
Creation timestamp. If None, uses current time
date_modified : Optional[str]
Modification timestamp. If None, uses current time

**Raises:**

ValueError
If the part number is invalid or incompatible with provided type/polarization

---

##### __str__

**Signature:** `__str__() -> str`

String representation of the part.

---

##### __repr__

**Signature:** `__repr__() -> str`

Detailed string representation of the part.

---

##### to_dict

**Signature:** `to_dict() -> Dict[str, Any]`

Convert part to dictionary representation.

**Returns:**

Dict[str, Any]
Dictionary containing all part properties

---

##### from_dict

*@classmethod*

**Signature:** `from_dict(cls, data: Dict[str, Any]) -> 'Part'`

Create Part instance from dictionary.

**Parameters:**

data : Dict[str, Any]
Dictionary containing part data

**Returns:**

Part
New Part instance

---

##### from_database_row

*@classmethod*

**Signature:** `from_database_row(cls, row: tuple) -> 'Part'`

Create Part instance from database row. Assumes row format: (id, part_number, part_type, polarization, date_created, date_modified)

**Parameters:**

row : tuple
Database row tuple

**Returns:**

Part
New Part instance

---

##### is_valid

**Signature:** `is_valid() -> bool`

Check if the part is valid.

**Returns:**

bool
True if all part properties are valid

---

##### get_barcode_filename

**Signature:** `get_barcode_filename() -> str`

Get the expected barcode filename for this part.

**Returns:**

str
Barcode filename (e.g., "ANT00001P1.png")

---

##### update_modified_time

**Signature:** `update_modified_time() -> None`

Update the modified timestamp to current time.

---

---

## Validation Module Details

This module provides validation functions for part numbers, part types,
and other part-related data integrity checks.

## Functions

### validate_part_number

**Signature:** `validate_part_number(part_number: str) -> bool`

Validate a part number format. Expected format: {PREFIX}{NUMBER}P{POLARIZATION}

**Parameters:**

part_number : str
The part number to validate

**Returns:**

bool
True if the part number is valid, False otherwise

**Examples:**

```python

```

---

### validate_part_type

**Signature:** `validate_part_type(part_type: str) -> bool`

Validate if a part type is supported.

**Parameters:**

part_type : str
The part type to validate

**Returns:**

bool
True if the part type is valid, False otherwise

---

### validate_polarization

**Signature:** `validate_polarization(polarization: str) -> bool`

Validate polarization format. Valid polarizations: P1, P2, PV (and potentially others)

**Parameters:**

polarization : str
The polarization to validate

**Returns:**

bool
True if the polarization is valid, False otherwise

---

### get_part_info

**Signature:** `get_part_info(part_number: str) -> Optional[Dict[str, str]]`

Extract part information from a valid part number.

**Parameters:**

part_number : str
The part number to parse

**Returns:**

Optional[Dict[str, str]]
Dictionary with part info (prefix, type, polarization, number) or None if invalid

---

### normalize_part_number

**Signature:** `normalize_part_number(part_number: str) -> Optional[str]`

Normalize a part number to standard format.

**Parameters:**

part_number : str
The part number to normalize

**Returns:**

Optional[str]
Normalized part number or None if invalid

---
