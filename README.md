[![CI](https://github.com/Coherent-All-Sky-Monitor/CAsMan/actions/workflows/ci.yml/badge.svg)](https://github.com/Coherent-All-Sky-Monitor/CAsMan/actions/workflows/ci.yml)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/Coherent-All-Sky-Monitor/CAsMan/branch/main/graph/badge.svg)](https://codecov.io/gh/Coherent-All-Sky-Monitor/CAsMan)

# CAsMan - CASM Assembly Manager

A toolkit for managing and visualizing CASM (Coherent All-Sky Monitor) assembly processes. CAsMan provides scripts and a web interface for part management, barcode generation, assembly tracking, and visualization.


```mermaid
graph TD
    A[ANTENNA (ANT)]
    B[LNA (LNA)]
    C[COAX1 (COX1)]
    D[COAX2 (COX2)]
    E[BACBOARD (BAC)]

    A --> B
    B --> C
    C --> D
    D --> E
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

### Web Interface

Start the web application:

```bash
casman web
# or
casman-web
```

Then open your browser to `http://localhost:5000`

### Command Line Usage

```bash
# Main CLI interface
casman --help

# Part management
casman parts list
casman parts add

# Scanning and assembly
casman scan interactive
casman scan stats

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

## Web Interface

The web interface provides:

- **Dashboard**: Overview of parts, scans, and assembly chains
- **Parts Management**: Browse, filter, and add new parts
- **Scanning Interface**: Web-based barcode scanning for assembly
- **Visualization**: Interactive graphs and ASCII chain display
- **REST API**: JSON API for integration with other tools

### API Endpoints

- `GET /api/parts` - List parts with optional filtering
- `POST /api/scan` - Scan a part for assembly
- `GET /api/visualization-data` - Get data for interactive visualization
- `GET /api/stats` - Get assembly and part statistics

## Package Structure

```
casman/
├── __init__.py           # Package initialization
├── cli.py               # Command-line interface
├── web_app.py           # Flask web application
├── database.py          # Database management
├── parts.py             # Part management
├── assembly.py          # Assembly and scanning
├── visualization.py     # Visualization tools
├── barcode_utils.py     # Barcode generation
├── templates/           # HTML templates for web interface
│   ├── base.html
│   ├── dashboard.html
│   ├── parts.html
│   ├── add_parts.html
│   ├── scan.html
│   ├── visualization.html
│   └── error.html
└── static/
    └── fonts/           # Fonts for barcode generation
```

## Configuration

CAsMan uses SQLite databases stored in the `database/` directory:

- `parts.db` - Part information and metadata
- `assembled_casm.db` - Assembly connections and scan history

Barcodes are generated in the `barcodes/` directory, organized by part type.

## Part Types

CAsMan supports three main part types:

1. **ANTENNA** (ANT) - Antenna components
2. **LNA** (LNA) - Low Noise Amplifier components
3. **BACBOARD** (BAC) - Backboard components

Part numbers follow the format: `[TYPE]P1-[NUMBER]` (e.g., `ANTP1-00001`)

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

### Running the Web Application in Development

```bash
# With debug mode enabled
casman web --debug --host 0.0.0.0 --port 5000
```

### Adding New Features

1. **New CLI Commands**: Add to `cli.py` and create corresponding functions
2. **Web Routes**: Add to `web_app.py` with appropriate templates
3. **Database Changes**: Update `database.py` with new table schemas
4. **New Part Types**: Update `PART_TYPES` in `parts.py`

## Migration from Scripts

This package replaces the individual scripts in the `scripts/` directory:

| Old Script | New Command | New Module |
|------------|-------------|------------|
| `gen_add_part_numbers.py` | `casman parts add` | `casman.parts` |
| `read_parts_db.py` | `casman parts list` | `casman.parts` |
| `scan_and_assemble.py` | `casman scan interactive` | `casman.assembly` |
| `visualize_analog_chains_term.py` | `casman visualize chains` | `casman.visualization` |
| `visualize_analog_chains_web.py` | `casman web` | `casman.web_app` |
| `gen_barcode_printpages.py` | `casman barcode printpages` | `casman.barcode_utils` |
| `print_connections_database.py` | `casman visualize chains` | `casman.visualization` |

## Dependencies

### Core Dependencies

- **Flask** - Web framework for the web interface
- **Pillow** - Image processing for barcode generation
- **python-barcode** - Barcode generation library

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
- New Flask web interface with modern Bootstrap UI
- Comprehensive CLI with subcommands
- Improved database management with proper schemas
- Interactive visualization with vis.js
- REST API for integration
- Comprehensive documentation and type hints
- Production-ready packaging with setuptools and pyproject.toml

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
