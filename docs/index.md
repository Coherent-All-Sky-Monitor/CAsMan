# CAsMan Documentation

Welcome to the CAsMan (CASM Assembly Manager) documentation. This documentation is automatically generated from the source code and reflects the current modular architecture.

## Getting Started

- [Overview and Quick Start](README.md) - Start here for an introduction to CAsMan
- [Development Guide](development.md) - Comprehensive guide for developers
- [API Reference](api_reference.md) - Quick reference for all modules and functions

## User Documentation

- [Command Line Interface](cli.md) - Learn about all available CLI commands
- [Configuration](config.md) - Configuration management and settings

## API Documentation

- [API Index](api.md) - Complete list of all modules and functions

### Core Packages (Modularized)

CAsMan now uses a modular architecture with focused packages:

- [Assembly Package](assembly.md) - Assembly connection recording and management (modularized)
- [CLI Package](cli.md) - Command-line interface (modularized)
- [Parts Package](parts.md) - Part management and validation (modularized)

### Core Modules

- [Database](database.md) - Database initialization and utilities
- [Barcode Utils](barcode_utils.md) - Barcode generation and printing
- [Visualization](visualization.md) - ASCII chain visualization
- [Configuration](config.md) - Configuration management

## Architecture Overview

CAsMan follows a **modular architecture** with clear separation of concerns:

### Package Structure
```
casman/
├── assembly/         # Assembly management (NEW: modularized package)
├── cli/             # Command-line interface (NEW: modularized package)
├── parts/           # Parts management (NEW: modularized package)
├── barcode_utils.py # Barcode utilities
├── config.py        # Configuration
├── database.py      # Database operations
└── visualization.py # Visualization
```

### Key Benefits
- **Focused Modules**: Each package has a single responsibility
- **Backward Compatibility**: Existing imports continue to work
- **Enhanced Maintainability**: Easier to develop and test
- **Clear Organization**: Logical grouping of related functionality

## Testing

All functionality is covered by comprehensive tests:

```bash
# Run all tests (59 tests total)
python -m pytest

# Test specific packages
python -m pytest tests/test_assembly.py -v  # Assembly package tests
python -m pytest tests/test_cli.py -v      # CLI package tests
python -m pytest tests/test_parts.py -v    # Parts package tests
```

## Scripts

The project includes standalone scripts in the `scripts/` directory:

- `visualize_analog_chains_web.py` - Web-based visualization of assembly chains

## Development

This documentation is automatically updated on every push to the main branch via GitHub Actions. To generate documentation locally:

```bash
python docs/generate_docs.py
```

## Project Structure

```
CAsMan/
├── casman/                 # Main Python package
├── scripts/               # Standalone utility scripts
├── database/              # SQLite database files
├── barcodes/              # Generated barcode images
├── docs/                  # Documentation (this directory)
├── tests/                 # Unit tests
└── config.yaml           # Project configuration
```
