# CAsMan API Reference

This document provides a comprehensive reference for all CAsMan modules and functions.

## Package Overview

CAsMan is organized into focused, modular packages:

### Core Packages

| Package | Purpose | Type |
|---------|---------|------|
| `casman.assembly` | Assembly management and connection tracking | Package |
| `casman.cli` | Command-line interface | Package |
| `casman.parts` | Part management and validation | Package |

### Core Modules  

| Module | Purpose | Type |
|--------|---------|------|
| `casman.barcode_utils` | Barcode generation and printing | Module |
| `casman.config` | Configuration management | Module |
| `casman.database` | Database operations | Module |
| `casman.visualization` | ASCII visualization | Module |

## Quick Import Guide

### Assembly Operations
```python
from casman.assembly import (
    record_assembly_connection,   # Record new connections
    get_assembly_connections,     # Retrieve connection data
    get_assembly_stats,          # Get assembly statistics
    build_connection_chains,     # Build connection chains
    print_assembly_chains,       # Display chains
    scan_and_assemble_interactive # Interactive assembly
)
```

### CLI Usage
```python
from casman.cli import main as cli_main
# Or use command line: python -m casman.cli
```

### Parts Management
```python
from casman.parts import (
    Part,                    # Part class
    PartNumber,             # Part number management
    validate_part_number,   # Part validation
    get_all_parts,         # Retrieve all parts
    search_parts           # Search functionality
)
```

### Utilities
```python
from casman.barcode_utils import generate_barcode_page, print_barcodes
from casman.config import load_config, get_database_path
from casman.database import init_parts_db, init_assembled_db
from casman.visualization import print_ascii_chains
```

## Module Details

### casman.assembly Package

**Purpose**: Comprehensive assembly management functionality

**Submodules**:
- `connections`: Recording assembly connections
- `data`: Data retrieval and statistics  
- `chains`: Connection chain analysis
- `interactive`: Interactive assembly operations

**Key Functions**:
- `record_assembly_connection()`: Record new assembly connections
- `get_assembly_connections()`: Retrieve all connections
- `get_assembly_stats()`: Get assembly statistics
- `build_connection_chains()`: Build connection chains from data
- `print_assembly_chains()`: Display connection chains
- `scan_and_assemble_interactive()`: Interactive assembly scanning

### casman.cli Package

**Purpose**: Modular command-line interface

**Submodules**:
- `main`: Main CLI entry point and argument parsing
- `parts_commands`: Parts management commands
- `assembly_commands`: Assembly operation commands
- `barcode_commands`: Barcode generation commands  
- `visualization_commands`: Visualization commands
- `utils`: Common CLI utilities

**Key Functions**:
- `main()`: Main CLI entry point
- Various command functions for each operation type

### casman.parts Package

**Purpose**: Part management and validation

**Submodules**:
- `part`: Part class definition and core functionality
- `part_number`: Part number parsing and management
- `validation`: Part validation logic and rules

**Key Functions**:
- `Part()`: Main part class
- `PartNumber()`: Part number management class
- `validate_part_number()`: Validate part numbers
- `get_all_parts()`: Retrieve all parts from database
- `search_parts()`: Search parts by criteria

### casman.barcode_utils Module

**Purpose**: Barcode generation and printing utilities

**Key Functions**:
- `generate_barcode_page()`: Generate barcode print pages
- `print_barcodes()`: Print barcodes to files
- `generate_part_barcode()`: Generate individual part barcodes

### casman.config Module

**Purpose**: Configuration management and settings

**Key Functions**:
- `load_config()`: Load configuration from file
- `get_database_path()`: Get database file paths
- `get_config_value()`: Retrieve configuration values

### casman.database Module

**Purpose**: Database initialization and management

**Key Functions**:
- `init_parts_db()`: Initialize parts database
- `init_assembled_db()`: Initialize assembly database
- `get_database_path()`: Get database file paths
- `backup_database()`: Create database backups

### casman.visualization Module

**Purpose**: ASCII visualization of assembly chains

**Key Functions**:
- `print_ascii_chains()`: Display connection chains as ASCII
- `format_chain_display()`: Format chains for display
- `visualize_connections()`: Visualize assembly connections

## Usage Examples

### Recording Assembly Connections

```python
from casman.assembly import record_assembly_connection

# Record a connection between parts
success = record_assembly_connection(
    part_number="ANT-P1-00001",
    part_type="ANTENNA", 
    polarization="P1",
    scan_time="2024-01-01 10:00:00",
    connected_to="LNA-P1-00001",
    connected_to_type="LNA",
    connected_polarization="P1", 
    connected_scan_time="2024-01-01 09:59:00"
)
```

### Retrieving Assembly Data

```python
from casman.assembly import get_assembly_connections, get_assembly_stats

# Get all connections
connections = get_assembly_connections()

# Get assembly statistics
stats = get_assembly_stats()
print(f"Total scans: {stats['total_scans']}")
print(f"Unique parts: {stats['unique_parts']}")
```

### Building Connection Chains

```python
from casman.assembly import build_connection_chains, print_assembly_chains

# Build chains from connection data
chains = build_connection_chains()

# Display chains
print_assembly_chains()
```

### Part Management

```python
from casman.parts import Part, validate_part_number, get_all_parts

# Create a new part
part = Part("ANT-P1-00001", "ANTENNA", "P1")

# Validate part number
is_valid = validate_part_number("ANT-P1-00001")

# Get all parts
all_parts = get_all_parts()
```

### CLI Usage

```bash
# Assembly operations
python -m casman.cli assembly scan --interactive
python -m casman.cli assembly stats
python -m casman.cli assembly chains

# Parts operations  
python -m casman.cli parts add ANT-P1-00001 ANTENNA P1
python -m casman.cli parts list
python -m casman.cli parts search --type ANTENNA

# Barcode operations
python -m casman.cli barcode generate --type ANTENNA --count 5
python -m casman.cli barcode print --output-dir ./barcodes

# Visualization
python -m casman.cli visualize chains --format ascii
```

### Configuration

```python
from casman.config import load_config, get_database_path

# Load configuration
config = load_config()

# Get database paths
parts_db = get_database_path("parts.db")
assembled_db = get_database_path("assembled_casm.db")
```

## Error Handling

All functions include proper error handling:

```python
from casman.assembly import record_assembly_connection

try:
    success = record_assembly_connection(...)
    if not success:
        print("Failed to record connection")
except Exception as e:
    print(f"Error: {e}")
```

## Type Information

All functions include comprehensive type annotations:

```python
from typing import List, Dict, Optional, Tuple

def get_assembly_connections(db_dir: Optional[str] = None) -> List[Tuple[str, ...]]:
    """Get all assembly connections from database."""
    pass

def get_assembly_stats(db_dir: Optional[str] = None) -> Dict[str, Any]:
    """Get assembly statistics.""" 
    pass
```

## Testing

All modules include comprehensive test coverage:

```bash
# Test specific modules
python -m pytest tests/test_assembly.py -v
python -m pytest tests/test_cli.py -v
python -m pytest tests/test_parts.py -v

# Test all modules
python -m pytest
```

For detailed function documentation, see the individual module documentation files.
