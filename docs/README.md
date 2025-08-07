# CAsMan - CASM Assembly Manager

CAsMan is a comprehensive Python package for managing Coherent All-Sky Monitor (CASM) assembly operations. It provides tools for part management, barcode generation, assembly tracking, and visualization.

## Features

- **Part Management**: Track and manage electronic parts with barcode identification
- **Assembly Tracking**: Record connections between parts with timestamps
- **Visualization**: ASCII and web-based visualization of assembly chains
- **Barcode Generation**: Create and print barcodes for part identification
- **Database Management**: SQLite-based storage for parts and assembly data
- **Command Line Interface**: Comprehensive CLI tools for all operations

## Quick Start

1. **Install the package:**
   ```bash
   pip install -e .
   ```

2. **Initialize databases:**
   ```bash
   casman parts list  # This will create necessary databases
   ```

3. **Add parts:**
   ```bash
   casman parts add
   ```

4. **Generate barcodes:**
   ```bash
   casman barcode printpages --part-type ANTENNA --start-number 1 --end-number 10
   ```

5. **Record assembly connections:**
   ```bash
   casman assemble connect --part1 ANT-P1-00001 --part1-type ANTENNA --part2 LNA-P1-00001 --part2-type LNA --polarization P1
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
  - `visualize_analog_chains_web.py`: Web-based chain visualization
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
