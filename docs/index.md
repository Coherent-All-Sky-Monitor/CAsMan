# CAsMan Documentation

Welcome to the CAsMan (CASM Assembly Manager) documentation. This documentation is automatically generated from the source code and reflects the current modular architecture.

## Getting Started

- [Overview and Quick Start](README.md) - Start here for an introduction to CAsMan

- [Migration Guide](migration_guide.md) - **IMPORTANT**: Guide for upgrading from v1.x to v2.0

- [Development Guide](development.md) - Comprehensive guide for developers

- [API Reference](api_reference.md) - Quick reference for all modules and functions

## User Documentation

- [Command Line Interface](cli.md) - Learn about all available CLI commands

- [Examples and Tutorials](examples.md) - Comprehensive examples and step-by-step tutorials

- [Safety Features](safety_features.md) - Comprehensive safety and security features

- [Configuration](config.md) - Configuration management and settings

## API Documentation

- [API Index](api.md) - Complete list of all modules and functions

## Auto-Generated API Documentation

The following documentation is automatically generated from the source code:

- [Auto-Generated API Reference](auto-generated/api_reference.md) - Complete API reference from code analysis

- [Auto-Generated CLI Documentation](auto-generated/cli.md) - CLI commands extracted from code

- [Auto-Generated Assembly Package](auto-generated/assembly.md) - Assembly package API from source

- [Auto-Generated CLI Package](auto-generated/cli.md) - CLI package API from source  

- [Auto-Generated Config Package](auto-generated/config.md) - Config package API from source

- [Auto-Generated Database Package](auto-generated/database.md) - Database package API from source

- [Auto-Generated Parts Package](auto-generated/parts.md) - Parts package API from source

- [Auto-Generated Visualization Package](auto-generated/visualization.md) - Visualization package API from source

*Note: Auto-generated docs are created by running `python docs/generate_docs.py` and provide technical API details extracted directly from the source code.*

### Core Packages (Modularized v2.0)

CAsMan v2.0 uses a fully modular architecture with focused packages:

- [Assembly Package](assembly.md) - Assembly connection recording and management

- [CLI Package](cli.md) - Command-line interface with hierarchical commands

- [Parts Package](parts.md) - Part management and validation

- [Database Package](database.md) - Database operations and CLI management

- [Config Package](config.md) - Configuration handling and environments

- [Barcode Package](barcode_utils.md) - Barcode generation and validation

- [Visualization Package](visualization.md) - ASCII and web visualization

### Legacy Modules (Compatibility)

These modules maintain backward compatibility:

- [Database](database.md) - Database initialization and utilities

- [Barcode Utils](barcode_utils.md) - Barcode generation and printing  

- [Visualization](visualization.md) - ASCII chain visualization

- [Configuration](config.md) - Configuration management

## Architecture Overview

CAsMan v2.0 follows a **fully modular architecture** with clear separation of concerns:

### Package Structure

```text

casman/
├── assembly/            # Assembly management (NEW: fully modularized)
│   ├── chains.py       # Connection chain analysis
│   ├── connections.py  # Connection recording and validation
│   ├── data.py        # Assembly data structures
│   └── interactive.py # Interactive assembly tools
├── cli/               # Command-line interface (NEW: hierarchical commands)
│   ├── main.py        # Main CLI entry point
│   ├── assembly_commands.py   # Assembly/scanning commands
│   ├── database_commands.py   # Database management commands
│   ├── parts_commands.py      # Parts management commands
│   ├── barcode_commands.py    # Barcode generation commands
│   └── visualization_commands.py # Visualization commands
├── parts/             # Parts management (NEW: fully modularized)
│   ├── generation.py  # Part number generation
│   ├── interactive.py # Interactive part management
│   ├── validation.py  # Part validation and checking
│   └── search.py      # Part searching functionality
├── database/          # Database operations (NEW: modularized)
│   ├── connection.py  # Database connections and paths
│   ├── initialization.py # Database setup and schema
│   ├── operations.py  # Database queries and operations
│   └── migrations.py  # Schema migrations and updates
├── config/            # Configuration management (NEW: modularized)
│   ├── core.py        # Core configuration functions
│   ├── environments.py # Environment handling
│   └── schema.py      # Configuration validation
├── barcode/           # Barcode operations (NEW: modularized)
│   ├── generation.py  # Barcode creation
│   ├── operations.py  # Barcode processing
│   └── validation.py  # Barcode validation
└── visualization/     # Visualization tools (NEW: modularized)
    ├── core.py        # ASCII visualization
    └── web.py         # Web-based visualization

```python

### Key Benefits

- **🎯 Focused Modules**: Each package has a single responsibility

- **🔧 Better Maintainability**: Clear separation makes code easier to maintain

- **🧪 Enhanced Testing**: Modular structure enables comprehensive testing

- **📚 Clear Documentation**: Each module has dedicated documentation

- **🔄 Backward Compatibility**: Legacy imports continue to work

- **⚡ Performance**: Optimized imports and reduced dependencies

## Testing

All functionality is covered by comprehensive tests:

```bash

# Run all tests (59 tests total)
python -m pytest

# Test specific packages
python -m pytest tests/test_assembly.py -v  # Assembly package tests
python -m pytest tests/test_cli.py -v      # CLI package tests
python -m pytest tests/test_parts.py -v    # Parts package tests

```python

## Scripts

The project includes standalone scripts in the `scripts/` directory:

- `visualize_analog_chains_web.py` - Web-based visualization of assembly chains

## Development

This documentation includes both manually written guides and auto-generated API documentation.

### Manual Documentation

The main documentation (guides, tutorials, examples) is manually maintained for accuracy and clarity.

### Auto-Generated Documentation

To generate technical API documentation from source code:

```bash

python docs/generate_docs.py

```python

This creates auto-generated documentation in `docs/auto-generated/` with technical API details extracted from the source code.

## Project Structure

```text

CAsMan/
├── casman/                 # Main Python package
├── scripts/               # Standalone utility scripts
├── database/              # SQLite database files
├── barcodes/              # Generated barcode images
├── docs/                  # Documentation (this directory)
│   ├── auto-generated/    # Auto-generated API docs
│   └── *.md              # Manual documentation
├── tests/                 # Unit tests
└── config.yaml           # Project configuration

```python