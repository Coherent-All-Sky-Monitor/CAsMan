# CAsMan - CASM Assembly Manager

CAsMan is a comprehensive Python package for managing Coherent All-Sky Monitor (CASM) assembly operations. It provides tools for part management, barcode generation, assembly tracking, and visualization.

## Features

- **Part Management**: Track and manage electronic parts with barcode identification
- **Assembly Tracking**: Record connections between parts with timestamps
- **Visualization**: ASCII visualization of assembly chains
- **Barcode Generation**: Create and print barcodes for part identification
- **Database Management**: SQLite-based storage for parts and assembly data
- **Command Line Interface**: Comprehensive CLI tools for all operations

## Quick Start

### Installation

1. **Set up virtual environment (recommended):**
   ```bash
   # Create and activate virtual environment
   python -m venv .venv
   
   # On macOS/Linux:
   source .venv/bin/activate
   
   # On Windows:
   # .venv\Scripts\activate
   ```

2. **Install the package:**
   ```bash
   pip install -e .
   ```

### Basic Usage

1. **Initialize databases:**
   ```bash
   casman parts list  # This will create necessary databases
   ```

2. **Add parts:**
   ```bash
   casman parts add
   ```

4. **Generate barcodes:**
   ```bash
   casman barcode printpages --part-type ANTENNA --start-number 1 --end-number 10
   ```

5. **Interactive assembly scanning:**
   ```bash
   casman scan connection
   ```

6. **Visualize assembly chains:**
   ```bash
   casman visualize chains
   ```

## Project Structure

- `casman/`: Main Python package
  - `assembly.py`: Assembly connection recording and management
  - `barcode_utils.py`: Barcode generation and printing utilities
  - `cli.py`: Command-line interface implementation
  - `config.py`: Configuration management
  - `database.py`: Database initialization and utilities
  - `parts.py`: Part management functions
  - `visualization.py`: ASCII chain visualization
- `scripts/`: Standalone utility scripts
- `database/`: SQLite database files
- `barcodes/`: Generated barcode images
- `tests/`: Unit tests

## Configuration

Configuration is managed through `config.yaml` in the project root. Key settings include:

- Database paths
- Part types and abbreviations
- SNAP/FENG mappings
- Default polarizations

## Database Schema

### Parts Database (`parts.db`)
- `parts` table: Stores part information including number, type, polarization, and timestamps

### Assembly Database (`assembled_casm.db`)
- `assembly` table: Records connections between parts with scan timestamps

## Development

To set up for development:

1. Clone the repository
2. Install in development mode: `pip install -e .`
3. Run tests: `python -m pytest tests/`
4. Generate documentation: `python docs/generate_docs.py`

## License

This project is part of the Coherent All-Sky Monitor project.
