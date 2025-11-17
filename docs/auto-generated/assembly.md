# Assembly Package

Documentation for the `casman.assembly` package.

## Overview

Assembly management functionality for CAsMan.

This module provides functionality for recording and retrieving assembly connections,
building connection chains, and interactive assembly scanning.

## Modules

### chains

Assembly chain building and analysis functionality.

This module handles building connection chains from assembly data
and provides analysis functions for understanding assembly relationships.

**Functions:**
- `build_connection_chains()` - Build a dictionary mapping each part to its connected parts
- `print_assembly_chains()` - Print all assembly chains in a readable format

### connections

Assembly connection recording functionality.

This module handles the recording of assembly connections between parts
in the assembled database.

**Functions:**
- `record_assembly_connection()` - Record an assembly connection or disconnection in the database with explicit timestamps
- `record_assembly_disconnection()` - Record an assembly disconnection in the database

### interactive

Interactive assembly operations for CAsMan.

This module provides interactive command-line interfaces for scanning
and assembling parts.

**Functions:**
- `validate_connection_rules()` - Validate that the connection follows the defined chain rules
- `validate_chain_directionality()` - Validate that parts follow proper chain directionality rules
- `check_existing_connections()` - Check if a part already has existing connections to prevent duplicates/branches
- `check_target_connections()` - Check if the target part can accept a new connection
- `validate_part_in_database()` - Validate if a part exists in the parts database or SNAP mapping
- `validate_snap_part()` - Validate a SNAP part against the snap_feng_map
- `scan_and_assemble_interactive()` - Interactive scanning and assembly function
- `scan_and_disassemble_interactive()` - Interactive scanning and disassembly function
- `main()` - Main entry point for assembly scanning CLI

### data

Assembly data retrieval and statistics functionality.

This module handles querying assembly connection data and generating
statistics from the assembled database.

**Functions:**
- `get_assembly_connections()` - Get all assembly connections from the database

## __Init__ Module Details

This module provides functionality for recording and retrieving assembly connections,
building connection chains, and interactive assembly scanning.

## Functions

### main

**Signature:** `main()`

Main entry point for the casman-scan command. Launches the interactive assembly scanner.

---

## Chains Module Details

This module handles building connection chains from assembly data
and provides analysis functions for understanding assembly relationships.

## Functions

### build_connection_chains

**Signature:** `build_connection_chains(db_dir: Optional[str]) -> Dict[str, List[str]]`

Build a dictionary mapping each part to its connected parts.

**Returns:**

Dict[str, List[str]]
Dictionary where keys are part numbers and values are lists
of connected part numbers.

**Examples:**

```python
>>> chains = build_connection_chains()
>>> print(chains.get('ANTP1-00001', []))
['LNA-P1-00001']
```

---

### print_assembly_chains

**Signature:** `print_assembly_chains(db_dir: Optional[str]) -> None`

Print all assembly chains in a readable format.

**Parameters:**

db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.
This function builds connection chains and prints them in a tree-like
structure showing how parts are connected to each other.

**Examples:**

```python
>>> print_assembly_chains()
Assembly Chains:
================
ANTP1-00001 ---> LNA-P1-00001 ---> CX1-P1-00001
ANTP1-00002 ---> LNA-P1-00002
```

---

## Connections Module Details

This module handles the recording of assembly connections between parts
in the assembled database.

## Functions

### record_assembly_connection

**Signature:** `record_assembly_connection(part_number: str, part_type: str, polarization: str, scan_time: str, connected_to: str, connected_to_type: str, connected_polarization: str, connected_scan_time: str, db_dir: Optional[str], connection_status: str) -> bool`

Record an assembly connection or disconnection in the database with explicit timestamps.

**Parameters:**

part_number : str
The part number being scanned.
part_type : str
The type of the part being scanned.
polarization : str
The polarization of the part being scanned.
scan_time : str
The timestamp when the part was scanned (YYYY-MM-DD HH:MM:SS).
connected_to : str
The part number this part is connected to.
connected_to_type : str
The type of the connected part.
connected_polarization : str
The polarization of the connected part.
connected_scan_time : str
The timestamp when the connection was made (YYYY-MM-DD HH:MM:SS).
db_dir : Optional[str]
Custom database directory. If not provided, uses the project root's database directory.
connection_status : str, optional
Status of the connection: 'connected' or 'disconnected'. Defaults to 'connected'.

**Returns:**

bool
True if the connection was recorded successfully, False otherwise.

**Examples:**

```python
>>> success = record_assembly_connection(
...     "ANTP1-00001", "ANTENNA", "X", "2024-01-01 10:00:00",
...     "LNA-P1-00001", "LNA", "X", "2024-01-01 10:05:00"
... )
>>> print(success)
True
>>> success = record_assembly_connection(
...     "ANTP1-00001", "ANTENNA", "X", "2024-01-01 10:00:00",
...     "LNA-P1-00001", "LNA", "X", "2024-01-01 10:10:00",
...     connection_status="disconnected"
... )
```

---

### record_assembly_disconnection

**Signature:** `record_assembly_disconnection(part_number: str, part_type: str, polarization: str, scan_time: str, connected_to: str, connected_to_type: str, connected_polarization: str, connected_scan_time: str, db_dir: Optional[str]) -> bool`

Record an assembly disconnection in the database. This is a convenience wrapper around record_assembly_connection that sets the connection_status to 'disconnected'.

**Parameters:**

part_number : str
The part number being disconnected.
part_type : str
The type of the part being disconnected.
polarization : str
The polarization of the part being disconnected.
scan_time : str
The timestamp when the part was scanned (YYYY-MM-DD HH:MM:SS).
connected_to : str
The part number this part was connected to.
connected_to_type : str
The type of the connected part.
connected_polarization : str
The polarization of the connected part.
connected_scan_time : str
The timestamp when the disconnection was made (YYYY-MM-DD HH:MM:SS).
db_dir : Optional[str]
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

bool
True if the disconnection was recorded successfully, False otherwise.

**Examples:**

```python
>>> success = record_assembly_disconnection(
...     "ANTP1-00001", "ANTENNA", "X", "2024-01-01 10:00:00",
...     "LNA-P1-00001", "LNA", "X", "2024-01-01 10:10:00"
... )
>>> print(success)
True
```

---

## Interactive Module Details

This module provides interactive command-line interfaces for scanning
and assembling parts.

## Functions

### validate_connection_rules

**Signature:** `validate_connection_rules(first_part: str, first_type: str, connected_part: str, connected_type: str) -> tuple[bool, str]`

Validate that the connection follows the defined chain rules.

**Returns:**

tuple[bool, str]: (is_valid, error_message)

---

### validate_chain_directionality

**Signature:** `validate_chain_directionality(part_type: str, connection_direction: str) -> tuple[bool, str]`

Validate that parts follow proper chain directionality rules.

**Returns:**

tuple[bool, str]: (is_valid, error_message)

---

### check_existing_connections

**Signature:** `check_existing_connections(part_number: str) -> tuple[bool, str, list]`

Check if a part already has existing connections to prevent duplicates/branches.

**Returns:**

tuple[bool, str, list]: (can_connect, error_message, existing_connections)

---

### check_target_connections

**Signature:** `check_target_connections(connected_part: str) -> tuple[bool, str]`

Check if the target part can accept a new connection.

**Returns:**

tuple[bool, str]: (can_accept, error_message)

---

### validate_part_in_database

**Signature:** `validate_part_in_database(part_number: str) -> tuple[bool, str, str]`

Validate if a part exists in the parts database or SNAP mapping.

**Returns:**

tuple[bool, str, str]: (is_valid, part_type, polarization)

---

### validate_snap_part

**Signature:** `validate_snap_part(part_number: str) -> tuple[bool, str, str]`

Validate a SNAP part against the snap_feng_map.yaml file.

**Returns:**

tuple[bool, str, str]: (is_valid, part_type, polarization)

---

### scan_and_assemble_interactive

**Signature:** `scan_and_assemble_interactive() -> None`

Interactive scanning and assembly function. Provides a command-line interface for scanning parts and recording their connections. Continues until the user types 'quit'.

**Returns:**

None

**Examples:**

```python
>>> scan_and_assemble_interactive()  # doctest: +SKIP
Interactive Assembly Scanner
============================
Type 'quit' to exit.
Scan first part: ANTP1-00001
Scan connected part: LNA-P1-00001
Connection recorded: ANTP1-00001 -> LNA-P1-00001
Scan first part: quit
Goodbye!
```

---

### scan_and_disassemble_interactive

**Signature:** `scan_and_disassemble_interactive() -> None`

Interactive scanning and disassembly function. Provides a command-line interface for scanning parts and recording their disconnections. Continues until the user types 'quit'.

**Returns:**

None

**Examples:**

```python
>>> scan_and_disassemble_interactive()  # doctest: +SKIP
Interactive Disassembly Scanner
===============================
Type 'quit' to exit.
Scan first part: ANTP1-00001
Scan disconnected part: LNA-P1-00001
Disconnection recorded: ANTP1-00001 -X-> LNA-P1-00001
Scan first part: quit
Goodbye!
```

---

### main

**Signature:** `main() -> None`

Main entry point for assembly scanning CLI. Provides interactive interface for assembly management operations.

---

## Data Module Details

This module handles querying assembly connection data and generating
statistics from the assembled database.

## Functions

### get_assembly_connections

**Signature:** `get_assembly_connections(db_dir: Optional[str]) -> List[Tuple[str, Optional[str], str, Optional[str], Optional[str]]]`

Get all assembly connections from the database.

**Parameters:**

db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

List[Tuple[str, Optional[str], str, Optional[str], Optional[str]]]
List of (part_number, connected_to, scan_time, part_type, polarization) tuples.

**Examples:**

```python
>>> connections = get_assembly_connections()
>>> for part, connected, time, ptype, pol in connections:
...     print(f"{part} -> {connected} at {time}")
ANTP1-00001 -> LNA-P1-00001 at 2024-01-01 10:00:00
```

---
