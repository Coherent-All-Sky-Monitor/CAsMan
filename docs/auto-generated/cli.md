# Cli Package

Documentation for the `casman.cli` package.

## Overview

CAsMan CLI command handlers.

This module provides the command-line interface functionality organized into
focused submodules for different command categories.

## Modules

### barcode_commands

Barcode and visualization CLI commands for CAsMan.

**Functions:**
- `cmd_barcode()` - Command-line interface for barcode generation
- `cmd_visualize()` - Command-line interface for visualization

### assembly_commands

Assembly-related CLI commands for CAsMan.

**Functions:**
- `cmd_scan()` - Command-line interface for scanning and assembly

### visualization_commands

Visualization commands for CAsMan CLI.

Provides basic visualization functionality including ASCII chains and summaries.

**Functions:**
- `cmd_visualize()` - Command-line interface for visualization
- `cmd_visualize_chains()` - Show ASCII visualization chains

### web_commands

Web application commands for CAsMan CLI.

Provides commands to run the unified web application.

**Functions:**
- `cmd_web()` - Command-line interface for unified web application

### utils

CLI utilities for CAsMan.

**Functions:**
- `show_completion_help()` - Show shell completion setup instructions
- `show_version()` - Show version information
- `show_commands_list()` - Show list of available commands
- `show_help_with_completion()` - Show help message with completion hint
- `show_unknown_command_error()` - Show error for unknown command

### parts_commands

Parts-related CLI commands for CAsMan.

**Functions:**
- `cmd_parts()` - Command-line interface for parts management
- `row_line()` - No docstring available

### main

Main CLI entry point for CAsMan.

This module provides the main function that routes commands to appropriate
sub-command handlers.

**Functions:**
- `main()` - Main command-line interface

### database_commands

Database management commands for CAsMan CLI.

This module provides CLI commands for database operations including:
- Clearing databases with safety confirmations
- Printing database contents with formatted output

**Functions:**
- `cmd_database()` - Database management command handler
- `cmd_database_clear()` - Handle database clear subcommand
- `cmd_database_print()` - Handle database print subcommand
- `cmd_database_load_coordinates()` - Handle database load-coordinates subcommand
- `print_stop_sign()` - Print a full color enhanced ASCII stop sign to the terminal
- `clear_parts_db_local()` - Clear the parts database by deleting all records
- `clear_assembled_db_local()` - Clear all records from the assembled_casm
- `print_db_schema()` - Print all entries from each table in the SQLite database at db_path
- `abbr()` - No docstring available
- `h()` - No docstring available

## Barcode_Commands Module Details

## Functions

### cmd_barcode

**Signature:** `cmd_barcode() -> None`

Command-line interface for barcode generation. Generates barcode printpages for specified part types and number ranges.

**Parameters:**

None
Uses sys.argv for command-line argument parsing.
Requires --part-type, --end-number, and optional --start-number.

**Returns:**

None

---

### cmd_visualize

**Signature:** `cmd_visualize() -> None`

Command-line interface for visualization. Provides functionality to display ASCII chains and visualization summaries.

**Parameters:**

None
Uses sys.argv for command-line argument parsing.

**Returns:**

None

---

## Assembly_Commands Module Details

## Functions

### cmd_scan

**Signature:** `cmd_scan() -> None`

Command-line interface for scanning and assembly. Provides functionality for interactive scanning and assembly statistics.

**Parameters:**

None
Uses sys.argv for command-line argument parsing.

**Returns:**

None

---

## Visualization_Commands Module Details

Provides basic visualization functionality including ASCII chains and summaries.

## Functions

### cmd_visualize

**Signature:** `cmd_visualize() -> None`

Command-line interface for visualization. Provides functionality for ASCII chains and basic summaries.

**Parameters:**

None
Uses sys.argv for command-line argument parsing.

**Returns:**

None

---

### cmd_visualize_chains

**Signature:** `cmd_visualize_chains() -> None`

Show ASCII visualization chains.

---

## Web_Commands Module Details

Provides commands to run the unified web application.

## Functions

### cmd_web

**Signature:** `cmd_web() -> None`

Command-line interface for unified web application. Launches the web application with configuration options for enabling scanner and/or visualization interfaces.

**Parameters:**

None
Uses sys.argv for command-line argument parsing.

**Returns:**

None

---

## Utils Module Details

## Constants

### COLOR_ERROR

**Value:** `''`

### COLOR_RESET

**Value:** `''`

## Functions

### show_completion_help

**Signature:** `show_completion_help() -> None`

Show shell completion setup instructions.

---

### show_version

**Signature:** `show_version() -> None`

Show version information.

---

### show_commands_list

**Signature:** `show_commands_list(commands: dict) -> None`

Show list of available commands.

---

### show_help_with_completion

**Signature:** `show_help_with_completion(parser) -> None`

Show help message with completion hint.

---

### show_unknown_command_error

**Signature:** `show_unknown_command_error(command: str, parser) -> None`

Show error for unknown command.

---

## Parts_Commands Module Details

## Functions

### cmd_parts

**Signature:** `cmd_parts() -> None`

Command-line interface for parts management. Provides functionality to list and add parts through command-line arguments. Supports filtering by part type and polarization.

**Parameters:**

None
Uses sys.argv for command-line argument parsing.

**Returns:**

None

---

### row_line

**Signature:** `row_line(row)`

No docstring available.

---

## Main Module Details

This module provides the main function that routes commands to appropriate
sub-command handlers.

## Functions

### main

**Signature:** `main() -> None`

Main command-line interface. Entry point for the CAsMan command-line application. Routes commands to appropriate sub-command handlers.

**Parameters:**

None
Uses sys.argv for command-line argument parsing.

**Returns:**

None

---

## Database_Commands Module Details

This module provides CLI commands for database operations including:
- Clearing databases with safety confirmations
- Printing database contents with formatted output

## Functions

### cmd_database

**Signature:** `cmd_database() -> None`

Database management command handler. Provides sub-commands for database operations: - clear: Clear database contents with safety confirmations - print: Display database contents in formatted tables

---

### cmd_database_clear

**Signature:** `cmd_database_clear(parser: argparse.ArgumentParser, remaining_args: list) -> None`

Handle database clear subcommand.

**Parameters:**

parser : argparse.ArgumentParser
The parser for the clear subcommand
remaining_args : list
Remaining command line arguments

---

### cmd_database_print

**Signature:** `cmd_database_print(parser: argparse.ArgumentParser, remaining_args: list) -> None`

Handle database print subcommand.

**Parameters:**

parser : argparse.ArgumentParser
The parser for the print subcommand
remaining_args : list
Remaining command line arguments

---

### cmd_database_load_coordinates

**Signature:** `cmd_database_load_coordinates(parser: argparse.ArgumentParser, remaining_args: list) -> None`

Handle database load-coordinates subcommand.

**Parameters:**

parser : argparse.ArgumentParser
The parser for the load-coordinates subcommand
remaining_args : list
Remaining command line arguments

---

### print_stop_sign

**Signature:** `print_stop_sign() -> None`

Print a full color enhanced ASCII stop sign to the terminal.

---

### clear_parts_db_local

**Signature:** `clear_parts_db_local(db_dir: str) -> None`

Clear the parts database by deleting all records.

---

### clear_assembled_db_local

**Signature:** `clear_assembled_db_local() -> None`

Clear all records from the assembled_casm.db database after double confirmation.

---

### print_db_schema

**Signature:** `print_db_schema(db_path: str) -> None`

Print all entries from each table in the SQLite database at db_path.

---

### abbr

**Signature:** `abbr(s: str) -> str`

No docstring available.

---

### h

**Signature:** `h(char: str, width: int) -> str`

No docstring available.

---
