

# CAsMan - CASM Assembly Manager

A comprehensive toolkit for managing and visualizing CASM (Coherent All-Sky Monitor) assembly processes. CAsMan provides CLI tools for part management, barcode generation, assembly tracking with connection validation, and interactive visualization.

## Assembly Chain Validation

CAsMan enforces strict assembly chain rules to ensure proper CASM assembly:

```mermaid

graph TD
    A["ANTENNA (ANT)"]
    B["LNA (LNA)"]
    C["COAXSHORT (CXS)"]
    D["COAXLONG (CXL)"]
    E["BACBOARD (BAC)"]
    F["SNAP (SNAP)"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    
    style A fill:#e1f5fe
    style F fill:#f3e5f5

```

### Connection Rules

- **Sequence Enforcement**: Parts must connect in order: `ANT → LNA → COAXSHORT → COAXLONG → BACBOARD → SNAP`

- **Directionality**: ANTENNA parts can only be sources, SNAP parts can only be targets

- **No Duplicates**: Each part can have only one outgoing and one incoming connection

- **Part Validation**: All parts validated against database and SNAP mapping files

## Installation

### Quick Install Options

**Minimal install (Antenna module only):**
```bash
pip install "casman[antenna] @ git+https://github.com/Coherent-All-Sky-Monitor/CAsMan.git"
```
- For data analysis, baseline calculations, etc. 
  
**Full install (All features):**
```bash
pip install "git+https://github.com/Coherent-All-Sky-Monitor/CAsMan.git"
```

### From Source with Virtual Environment (Recommended for Development)

```bash

# Clone the repository
git clone https://github.com/Coherent-All-Sky-Monitor/CAsMan.git
cd CAsMan

# Create and activate a virtual environment
python -m venv .venv

# On macOS/Linux:
source .venv/bin/activate

# On Windows:

# .venv\Scripts\activate

# Install in development mode
pip install -e .

# Or install antenna module only
pip install -e ".[antenna]"

```

### With Development Dependencies

```bash

# After activating your virtual environment
pip install -e ".[dev]"

```

### Alternative: Direct Installation

```bash

# If you prefer not to use a virtual environment
pip install git+https://github.com/Coherent-All-Sky-Monitor/CAsMan.git

```

## Quick Start

**Note**: If you installed using a virtual environment, make sure to activate it before using CAsMan:

```bash

# On macOS/Linux:
source .venv/bin/activate

# On Windows:

# .venv\Scripts\activate

```

### Command Line Usage

```bash

# Main CLI interface with comprehensive help
casman --help

# List available commands
casman --list-commands

# Part management
casman parts list                    # List all parts in database
casman parts add                     # Interactive part addition (can add single type or all types)

# Interactive scanning with connection validation
casman scan connect                  # Full interactive scanning and assembly workflow
casman scan connection               # Basic connection scanning
casman scan disconnect               # Full interactive disconnection workflow
casman scan disconnection            # Basic disconnection scanning

# Database management
casman database clear                # Clear database contents with safety confirmations
casman database clear --parts        # Clear only parts database
casman database clear --assembled    # Clear only assembly database
casman database print               # Display formatted database contents

# Visualization with duplicate detection
casman visualize chains              # ASCII chain visualization

# Web interfaces
casman web                           # Launch unified web app (scanner + visualization)
casman web --mode prod               # Launch production server with Gunicorn
casman web --scanner-only            # Launch scanner interface only (port 5000)
casman web --visualize-only          # Launch visualization interface only (port 5000)

# Barcode generation
casman barcode printpages --part-type ANTENNA --start-number 1 --end-number 100

# Database synchronization (GitHub Releases)
casman database pull                 # Download latest database from GitHub
casman database push                 # Upload database to GitHub (requires token)
casman database status               # Show sync status and GitHub Release info
casman database restore --latest     # Restore from latest timestamped backups

```

### Database Synchronization

CAsMan uses GitHub Releases for database distribution, enabling multi-user access without cloud credentials:

```bash
# Download latest database (no authentication required)
# Downloads directly to project database/ directory with automatic backups
casman database pull

# Force re-download even if up-to-date
casman database pull --force

# Restore from latest timestamped backups
casman database restore --latest              # Restore both DBs
casman database restore --latest --parts      # Restore only parts.db
casman database restore --latest --assembled  # Restore only assembled_casm.db

# Check sync status
casman database status

# Upload database (requires GitHub token - administrators only)
export GITHUB_TOKEN="your-github-token"
casman database push
```

**Features:**
- Public download access (no credentials needed)
- Downloads to project `database/` directory (full install) or XDG location (standalone antenna module)
- Automatic timestamped backups before overwriting databases
- Version control via GitHub Releases
- Offline-capable operation
- Restore from backups with `casman database restore`
- Auto-sync on load with `AntennaArray.from_database(..., sync_first=True)`

See [Database Documentation](docs/database.md) for complete setup guide and features.

### Database Management

The database commands provide safe operations with double confirmation for destructive actions:

```bash
casman database clear                # Clear both databases (with warnings)
casman database clear --parts        # Clear only parts database
casman database clear --assembled    # Clear only assembly database
casman database print                # Display assembly database in tables
```

### Part Management

Interactive part creation with automatic numbering and barcode generation:

```bash
casman parts add    # Choose part type (ANTENNA, LNA, COAXSHORT, COAXLONG, BACBOARD) or ALL
```

**Available part types:**
- ANTENNA (ANT), LNA (LNA), COAXSHORT (CXS), COAXLONG (CXL), BACBOARD (BAC)
- Option to add all types at once
- Specify quantity and polarization (1 or 2)
- Automatic part numbering and barcode generation

### SNAP Board Configuration

Manage SNAP board configurations including F-engine IDs and packet indices:

```bash
# Generate SNAP board CSV with 44 boards
python scripts/generate_snap_boards.py

# Load SNAP board configurations into database
casman database load-snap-boards

# Load with custom CSV
casman database load-snap-boards --csv custom_boards.csv
```

**SNAP Board Configuration:**
- 4 chassis × 11 slots (A-K) = 44 SNAP boards
- Each board has: Serial Number, MAC Address, IP Address, F-engine ID (0-43)
- Each port's packet index = `feng_id × 12 + port_number`
- Example: SNAP1A (feng_id=0) port 5 → packet_index = 5
- Example: SNAP2A (feng_id=11) port 5 → packet_index = 137

**Visualizations display:**
- Serial numbers and network configuration
- F-engine ID and calculated packet index for each port
- Board info shown in chains, core grid, and SNAP ports pages

### Interactive Scanning

The `casman scan connect` command provides comprehensive validation:

- Real-time part validation against database
- SNAP part format validation (SNAP<chassis><slot><port>)
- Connection sequence enforcement (ANT→LNA→COAXSHORT→COAXLONG→BACBOARD→SNAP)
- Duplicate connection prevention
- Chain directionality rules (ANTENNA sources only, SNAP targets only)

```bash
casman scan connect       # Full interactive workflow
casman scan connection    # Basic connection scanning
```

## Key Features

### Disconnect Tracking

Track part disconnections with full historical records. The database maintains both connection and disconnection events with automatic migration support.

**Usage:**
```bash
casman scan disconnect    # Record part disconnections
```

**Database Schema:**
- Automatic `connection_status` column migration
- Records marked as 'connected' or 'disconnected'
- Visualizations filter to show only connected parts
- Allows part reconnection after disconnection

**API:**
```python
from casman.assembly.connections import record_assembly_disconnection

# Record a disconnection
record_assembly_disconnection(
    part_number, part_type, polarization, scan_time,
    connected_to, connected_to_type, connected_polarization,
    connected_scan_time, db_dir=None
)
```

### Part Notes

Add timestamped notes to any part for documentation, maintenance tracking, or issue reporting.

**Usage:**
```bash
# View part history including notes via web interface
casman web
# Navigate to Part History and enter part number
```

**Features:**
- Add notes to any part via web interface
- View all notes with timestamps in Part History view
- Auto-generated notes during Replace Part workflow
- Notes stored in `part_notes` table with automatic schema migration

**API:**
```python
from casman.database.operations import add_part_note, get_part_notes

# Add a note to a part
add_part_note("ANT00001P1", "Replaced due to signal degradation")

# Get all notes for a part (returns list of (note, timestamp) tuples)
notes = get_part_notes("ANT00001P1")
for note, timestamp in notes:
    print(f"{timestamp}: {note}")
```

### Web Application

A web server serving both scanner and visualization interfaces with flexible configuration.

- Scanner interface for connecting/disconnecting parts
- Antenna grid position assignment workflow
- Visualization interface for viewing assembled chains
- Interactive 43×6 antenna grid display with SNAP port tracing
- Interactive part history access via clickable part numbers
- Version number displayed on all pages
  
**Configuration (`config.yaml`):**
```yaml
web_app:
  enable_scanner: true
  enable_visualization: true
  dev:
    port: 5000
    host: "0.0.0.0"
  production:
    port: 8000
    workers: 4

# Antenna grid layout configuration (expandable format)
grid:
  core:
    array_id: "C"           # Core array identifier
    north_rows: 21          # Rows north of center (N001-N021)
    south_rows: 21          # Rows south of center (S001-S021)
    east_columns: 6         # East columns (E01-E06)
    allow_expansion: true   # Allow grid codes beyond core bounds
```

**Deployment:**
```bash
# Development mode
casman web

# Production mode with Gunicorn
casman web --mode prod

# Scanner-only for commissioning/repairs
casman web --scanner-only

# Visualization-only for monitoring
casman web --visualize-only
```

**Web Interface Features:**

1. **Clickable Part History**: Click any part number in the visualization pages to view its complete connection history and notes
   - Analog Chains view: Click any part box to see its history
   - Core Grid view: Click part names in the P1/P2 chain displays
   - Direct URL access: `/scanner?part=<part_number>&action=history`

2. **Version Display**: Current CAsMan version displayed at the bottom of all web pages

3. **Dark/Light Mode**: All interfaces support theme toggling with preference persistence

4. **Interactive Navigation**: Seamless cross-page navigation between visualizations and scanner interface

### Antenna Grid Position Assignment

CAsMan provides a complete system for assigning antennas to physical grid positions, tracing connections to SNAP boards, and mapping positions to correlator kernel indices.

**Grid Format:** `[A-Z][N/C/S][000-999]E[01-99]`

- **Array ID** (A-Z): Single letter identifying the array (C = core, A/O/etc = outriggers)
- **Direction** (N/C/S): North, Center, or South of array center
- **Offset** (000-999): Row offset (C must use 000, N/S must use 001-999)
- **East Column** (01-99): 1-based east column index

**Examples:**
- `CN002E03` - Core array, North row 2, East column 3
- `CC000E01` - Core array, Center row, East column 1  
- `CS021E04` - Core array, South row 21, East column 4
- `AN015E02` - Outrigger array A, North row 15, East column 2
- `OS008E06` - Outrigger array O, South row 8, East column 6

**Multi-Array Support:**
CAsMan supports multiple independent antenna arrays configured in `config.yaml`:
- **Core Array**: Primary 43×6 grid (21 north + center + 21 south rows, 6 columns)
- **Outrigger Arrays**: Multiple optional secondary arrays with independent dimensions
  - Configured as a list in `config.yaml` under `grid.outriggers`
  - Each outrigger has its own array_id (e.g., A, O, B, D)
  - Independent grid dimensions and expansion settings
  - Accessed as "outrigger_A", "outrigger_O" etc. in web interface
- Array-specific validation and visualization
- Dynamic web interface adapts to configured arrays

**Kernel Index Mapping:**
The core array includes kernel index mapping for correlator processing:
- Maps 256 antenna positions to kernel indices 0-255
- Row-major ordering starting from CN021E01 (index 0)
- CS021E05 and CS021E06 are unmapped (exceed 256-antenna limit)
- Functions: `grid_to_kernel_index()`, `kernel_index_to_grid()`, `get_antenna_kernel_idx()`
- Returns 43×6 arrays of kernel indices, grid codes, antenna numbers, and SNAP ports

**Scanner Workflow:**
1. Select "Assign Antenna Position" action
2. Choose array from dropdown (core, outrigger_A, outrigger_O, etc.)
3. Choose input method (barcode scan or manual entry)
4. Enter antenna number (with or without P1/P2 suffix)
5. Select grid position using direction, offset, and column dropdowns
6. System validates antenna exists and checks position availability
7. Assign position with optional overwrite for corrections

**Visualization:**
- Visit `/visualize/grid` for interactive 43×6 grid display
- Search by antenna number, grid code, or kernel index
- View assigned positions with color highlighting
- Display SNAP port connections for both P1 and P2 polarizations
- Shows kernel index for each mapped position
- Full analog chain tracing from antenna to SNAP board

**Database Schema:**
```sql
CREATE TABLE antenna_positions (
    antenna_number TEXT UNIQUE NOT NULL,  -- Base antenna (no P1/P2)
    array_id TEXT NOT NULL,                -- 'C' for core, 'A'/'O'/etc for outriggers
    row_offset INTEGER NOT NULL,           -- -999 to +999 (signed)
    east_col INTEGER NOT NULL,             -- 1-99 (1-based)
    grid_code TEXT UNIQUE NOT NULL,        -- Canonical format
    assigned_at TEXT NOT NULL,             -- ISO timestamp
    notes TEXT
);
```

### Version Management

Automated version number management across all project files with git integration.

**Usage:**
```bash
# Show current version
python version_manager.py --show

# Increment version (patch/minor/major)
python version_manager.py --increment minor

# Set specific version
python version_manager.py --set 1.2.3

# Full release workflow
python version_manager.py --increment minor --commit --tag
```

**Files Updated:**
- `pyproject.toml` - Project version
- `casman/__init__.py` - Package version
- `casman/cli/utils.py` - CLI version display

**Semantic Versioning:**
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes and improvements

## Package Structure

```text

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
│   └── printing.py     # Print page generation
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

- **parts.db** - Parts inventory, antenna positions, and SNAP board configurations
- **assembled_casm.db** - Assembly tracking and connection chains
- **grid_positions.csv** - Geographic coordinates for antenna positions
- **snap_boards.csv** - SNAP board configurations (serial numbers, network info, F-engine IDs)

- `parts.db` - Part information and metadata

- `assembled_casm.db` - Assembly connections and scan history

Barcodes are generated in the `barcodes/` directory, organized by part type.

## Part Types

CAsMan supports multiple part types:

1. **ANTENNA** (ANT) - Antenna components
2. **LNA** (LNA) - Low Noise Amplifier components  
3. **COAXSHORT** (CXS) - Coaxial cable components (first type)
4. **COAXLONG** (CXL) - Coaxial cable components (second type)
5. **BACBOARD** (BAC) - Backboard components
6. **SNAP** (SNAP) - SNAP components

Part numbers follow the format: `[ABBREVIATION][NUMBER]P[POLARIZATION]` (e.g., `ANT00001P1`)

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

## Dependencies

### Core Dependencies

- **Pillow** - Image processing for barcode generation

- **python-barcode** - Barcode generation library

### Optional Dependencies

- **Flask** - Used by standalone web visualization scripts

### Development Dependencies

- **pytest** - Testing framework

- **coverage** - Code coverage analysis  

- **black** - Code formatter

- **flake8** - Linting

- **mypy** - Type checking

### Code Quality Tools

CAsMan includes automated tools for maintaining code quality:

```bash

# Quick coverage check with threshold validation
./coverage_check.sh

# Git pre-commit hook (optional) - updates docs before commits
bash .git/hooks/pre-commit

```

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

- Create an issue on [GitHub Issues](https://github.com/Coherent-All-Sky-Monitor/CAsMan/issues)

- Check the documentation in the repository



## Grid Position Coordinates

CAsMan supports tracking latitude, longitude, and height for antenna grid positions. Coordinates are managed via CSV file for easy editing and version control.

```bash
# Load geographic coordinates from CSV
casman database load-coordinates                    # Load from database/grid_positions.csv
casman database load-coordinates --csv survey.csv   # Load from custom CSV file
```

See [Grid Coordinates Documentation](docs/grid_coordinates.md) for details.

---

## Testing

### Running Tests

```bash

# Run all tests
pytest

# Run with coverage
coverage run -m pytest
coverage report --include="casman/*"

# Run specific test modules
pytest tests/test_parts.py -v
pytest tests/test_cli.py -v

# Quick coverage check script
./coverage_check.sh

```
