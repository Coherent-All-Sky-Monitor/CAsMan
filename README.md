

# CAsMan - CASM Assembly Manager

A toolkit for managing and visualizing CASM (Coherent All-Sky Monitor) assembly processes. CAsMan provides scripts for part management, barcode generation, assembly tracking, and visualization.


```mermaid
graph TD
    A[ANTENNA (ANT)]
    B[LNA (LNA)]
    C[COAX1 (CX1)]
    D[COAX2 (CX2)]
    E[BACBOARD (BAC)]
    F[SNAP (SNAP)]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
```

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/Coherent-All-Sky-Monitor/CAsMan.git
cd CAsMan

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### With Development Dependencies

```bash
pip install -e ".[dev]"
```

## Quick Start

### Command Line Usage

```bash
# Main CLI interface
casman --help

# Part management
casman parts list
casman parts add

# Scanning and assembly
casman scan interactive

# Visualization
casman visualize chains
casman visualize summary

# Barcode generation
casman barcode printpages --part-type ANTENNA --start-number 1 --end-number 50
```

### Individual Tools

Each module can also be run independently:

```bash
# Part management
casman-parts

# Assembly scanning
casman-scan

# Visualization
casman-visualize

# Barcode generation
casman-barcode ANTENNA 1 50
```

## Package Structure

```
casman/
├── __init__.py           # Package initialization
├── cli.py               # Command-line interface entry point
├── cli/                 # CLI command modules
│   ├── __init__.py
│   ├── main.py         # Main CLI logic
│   ├── parts_commands.py
│   ├── assembly_commands.py
│   ├── barcode_commands.py
│   ├── visualization_commands.py
│   └── utils.py        # CLI utilities
├── assembly.py          # Assembly and scanning (legacy)
├── assembly/            # Assembly modules
│   ├── __init__.py
│   ├── chains.py       # Chain analysis and management
│   ├── connections.py  # Connection handling
│   ├── data.py         # Assembly data structures
│   └── interactive.py  # Interactive assembly tools
├── parts/               # Part management modules
│   ├── __init__.py
│   ├── db.py           # Database operations for parts
│   ├── generation.py   # Part number generation
│   ├── interactive.py  # Interactive part management
│   ├── part.py         # Part data structures
│   ├── search.py       # Part searching functionality
│   ├── types.py        # Part type definitions
│   └── validation.py   # Part validation
├── database/            # Database operations
│   ├── __init__.py
│   ├── connection.py   # Database connections
│   ├── initialization.py # Database setup
│   ├── migrations.py   # Database migrations
│   └── operations.py   # Database operations
├── visualization.py     # Visualization tools (legacy)
├── visualization/       # Visualization modules
│   ├── __init__.py
│   ├── core.py         # Core visualization functions
│   └── web.py          # Web visualization utilities
├── barcode_utils.py     # Barcode generation (legacy)
├── barcode/             # Barcode modules
│   ├── __init__.py
│   ├── generation.py   # Barcode generation
│   ├── operations.py   # Barcode operations
│   ├── printing.py     # Print page generation
│   └── validation.py   # Barcode validation
├── config.py            # Configuration handling (legacy)
└── config/              # Configuration modules
    ├── __init__.py
    ├── core.py         # Core configuration
    ├── environments.py # Environment management
    ├── schema.py       # Configuration schema
    └── utils.py        # Configuration utilities
```

## Configuration

CAsMan uses SQLite databases stored in the `database/` directory:

- `parts.db` - Part information and metadata
- `assembled_casm.db` - Assembly connections and scan history

Barcodes are generated in the `barcodes/` directory, organized by part type.

## Part Types

CAsMan supports multiple part types:

1. **ANTENNA** (ANT) - Antenna components
2. **LNA** (LNA) - Low Noise Amplifier components  
3. **COAX1** (CX1) - Coaxial cable components (first type)
4. **COAX2** (CX2) - Coaxial cable components (second type)
5. **BACBOARD** (BAC) - Backboard components
6. **SNAP** (SNAP) - SNAP components

Part numbers follow the format: `[ABBREVIATION]-P[POLARIZATION]-[NUMBER]` (e.g., `ANT-P1-00001`)

## Development

### Setting up Development Environment

```bash
# Clone and install in development mode
git clone https://github.com/Coherent-All-Sky-Monitor/CAsMan.git
cd CAsMan
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black casman/

# Linting
flake8 casman/

# Type checking
mypy casman/
```

### Running the CLI in Development

```bash
# Run commands directly from source
python -m casman.cli --help
```

### Adding New Features

1. **New CLI Commands**: Add to `casman/cli/` modules and update main.py
2. **Database Changes**: Update modules in `casman/database/`
3. **New Part Types**: Update `PART_TYPES` in part type definitions

## Migration from Scripts

This package replaces the individual scripts in the `scripts/` directory:

| Old Script | New Command | New Module |
|------------|-------------|------------|
| `gen_add_part_numbers.py` | `casman parts add` | `casman.parts` |
| `read_parts_db.py` | `casman parts list` | `casman.parts` |
| `scan_and_assemble.py` | `casman scan interactive` | `casman.assembly` |
| `visualize_analog_chains_term.py` | `casman visualize chains` | `casman.visualization` |
| `gen_barcode_printpages.py` | `casman barcode printpages` | `casman.barcode_utils` |

## Dependencies

### Core Dependencies

- **Pillow** - Image processing for barcode generation
- **python-barcode** - Barcode generation library

### Optional Dependencies

- **Flask** - Used by standalone web visualization scripts

### Development Dependencies

- **pytest** - Testing framework
- **black** - Code formatter
- **flake8** - Linting
- **mypy** - Type checking

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Format code (`black casman/`)
7. Commit your changes (`git commit -am 'Add new feature'`)
8. Push to the branch (`git push origin feature/new-feature`)
9. Create a Pull Request

## Support

For issues and questions:

- Create an issue on GitHub: https://github.com/Coherent-All-Sky-Monitor/CAsMan/issues
- Check the documentation in the repository

## Changelog

### Version 1.0.0

- Complete refactoring of script-based tools into installable package
- Comprehensive CLI with subcommands
- Improved database management with proper schemas
- Basic ASCII visualization functionality
- Comprehensive documentation and type hints
- Production-ready packaging with setup tools and project configuration

## Usage Examples

### List all parts
```sh
casman parts list
```

### Add new parts interactively
```sh
casman parts add
```

### Generate barcodes for a part type
```sh
casman barcode printpages --part-type ANTENNA --start-number 1 --end-number 10
```

### Record an assembly connection
```sh
casman assemble connect --part1 ANT-P1-00001 --part1-type ANTENNA --part2 LNA-P1-00001 --part2-type LNA --polarization P1
```

### Visualize assembly chains in ASCII
```sh
casman visualize chains
```
