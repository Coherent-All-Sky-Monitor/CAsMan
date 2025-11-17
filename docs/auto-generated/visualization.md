# Visualization Package

Documentation for the `casman.visualization` package.

## Overview

Visualization package for CAsMan.

This package provides basic visualization capabilities including:
- ASCII chain displays
- Basic statistics and summaries

The package focuses on core functionality for assembly visualization.

## Modules

### core

Core visualization functions for CAsMan.

This module contains the legacy visualization functions that were previously
in the main visualization.py module.

**Functions:**
- `format_ascii_chains()` - Format assembly chains as ASCII text
- `get_duplicate_connections()` - Get information about duplicate connections in the database
- `get_chain_summary()` - Get summary statistics about assembly chains
- `main()` - Main function for command-line usage

## __Init__ Module Details

This package provides basic visualization capabilities including:
- ASCII chain displays
- Basic statistics and summaries

The package focuses on core functionality for assembly visualization.

## Functions

### main

**Signature:** `main() -> None`

Main entry point for visualization package.

---

## Core Module Details

This module contains the legacy visualization functions that were previously
in the main visualization.py module.

## Functions

### format_ascii_chains

**Signature:** `format_ascii_chains(db_dir: Optional[str]) -> str`

Format assembly chains as ASCII text.

**Parameters:**

db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

str
Formatted ASCII representation of assembly chains.

---

### get_duplicate_connections

**Signature:** `get_duplicate_connections(db_dir: Optional[str]) -> Dict[str, List[Tuple[str, str, str]]]`

Get information about duplicate connections in the database.

**Returns:**

Dict[str, List[Tuple[str, str, str]]]
Dictionary mapping part numbers to list of (connected_to, scan_time, connected_scan_time) tuples
for parts that appear multiple times in the database.

---

### get_chain_summary

**Signature:** `get_chain_summary(db_dir: Optional[str]) -> Dict[str, float]`

Get summary statistics about assembly chains.

**Parameters:**

db_dir : str, optional
Custom database directory. If not provided, uses the project root's database directory.

**Returns:**

Dict[str, float]
Dictionary containing chain statistics.

---

### main

**Signature:** `main() -> None`

Main function for command-line usage.

---
