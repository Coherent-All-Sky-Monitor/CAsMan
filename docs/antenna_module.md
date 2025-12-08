# Antenna Module - Standalone Installation

This guide explains how to install and use just the antenna positioning module from CAsMan without the full toolkit.

## Overview

The `casman.antenna` module provides lightweight antenna array management with:

- **Antenna position loading** from CAsMan database
- **Multi-array support** (core array, outriggers, custom arrays)
- **Grid position parsing** and validation (1-based indexing)
- **Kernel index mapping** for correlator processing (0-255)
- **Geographic coordinates** (latitude, longitude, height)
- **SNAP port mappings** for polarizations
- **Baseline calculations** between antenna pairs (geodetic and grid-based)
- **Minimal dependencies** (PyYAML, NumPy for kernel index operations)

Perfect for:
- Data analysis scripts
- Baseline computation pipelines
- UV coverage calculations
- Interferometry applications
- Remote/HPC environments without GUI dependencies

## Installation Options

### Option 1: Install Antenna Module Only (Minimal Dependencies)

**One-line install directly from GitHub (recommended):**

```bash
pip install "git+https://github.com/Coherent-All-Sky-Monitor/CAsMan.git#egg=casman[antenna]"
```

**Or install from local clone:**

```bash
# Clone repository
git clone https://github.com/Coherent-All-Sky-Monitor/CAsMan.git
cd CAsMan

# Install with antenna extras
pip install -e ".[antenna]"
```

**Dependencies:** Only PyYAML (for config loading)

### Option 2: Install Full CAsMan

For the complete toolkit including web interfaces, CLI, and visualization:

```bash
pip install -e .
```

### Option 3: Install with Development Tools

```bash
# Development tools
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```python
from casman.antenna import AntennaArray

# Load antenna array from database
# (If you don't have the database yet, see next section to download it)
array = AntennaArray.from_database('database/parts.db')

print(f"Loaded {len(array)} antennas")

# Get specific antenna
ant = array.get_antenna('ANT00001')
print(f"Antenna: {ant.antenna_number}")
print(f"Grid Position: {ant.grid_code}")
print(f"Coordinates: ({ant.latitude}, {ant.longitude})")

# Get kernel index for grid position (core array only)
from casman.antenna import grid_to_kernel_index
kernel_idx = grid_to_kernel_index(ant.grid_code)
if kernel_idx is not None:
    print(f"Kernel Index: {kernel_idx}")
```

### First Time Setup (Download Database)

If you don't have a local database yet, download it first:

```python
from casman.antenna import AntennaArray

# Download and load in one line (uses public URL from config.yaml)
array = AntennaArray.from_database('database/parts.db', sync_first=True)
print(f"Downloaded and loaded {len(array)} antennas")

# Or do it separately
from casman.antenna import sync_database
result = sync_database('parts.db')
if result['success']:
    array = AntennaArray.from_database('database/parts.db')
```

**Smart Sync Behavior:**
- If database doesn't exist → Downloads it
- If database exists and remote is newer → Downloads update
- If database exists and is up to date → Skips download
- If download fails but local exists → Uses local copy

**That's it!** No credentials needed - public URL is pre-configured in `config.yaml`.

### Download Latest Database (No Credentials Required)

Download the latest database automatically:

```python
from casman.antenna import sync_database, AntennaArray

# Option 1: Auto-download using config.yaml (easiest - no credentials needed)
# Public URL is pre-configured in config.yaml
result = sync_database('parts.db')
print(result['message'])
if result['success']:
    array = AntennaArray.from_database('database/parts.db')

# Option 2: One-liner auto-download on load
array = AntennaArray.from_database('database/parts.db', sync_first=True)
# Uses public URL from config.yaml automatically!

# Option 3: Override with specific public URL
PUBLIC_URL = 'https://pub-xxxxx.r2.dev/backups/parts.db/latest_parts.db'
array = AntennaArray.from_database(
    'database/parts.db',
    sync_first=True,
    public_url=PUBLIC_URL
)

# Option 4: Use R2 with credentials (for maintainers only)
# See: Database Backup Quick Start guide
result = sync_database('parts.db')  # Falls back to R2 auth if no public URL
```

**Configuration:**

Public URLs are configured in `config.yaml`:
```yaml
r2:
  public_urls:
    parts_db: "https://pub-xxxxx.r2.dev/backups/parts.db/latest_parts.db"
    assembled_db: "https://pub-xxxxx.r2.dev/backups/assembled_casm.db/latest_assembled_casm.db"
```

**Note:** 
- Public URL download requires **no credentials**
- URLs are pre-configured by project maintainers
- Just install and call `sync_database()` - it works automatically!
- Or override with custom `public_url` parameter if needed

### Compute Baselines

```python
# Get two antennas
ant1 = array.get_antenna('ANT00001')
ant2 = array.get_antenna('ANT00002')

# Compute baseline using geographic coordinates
baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)
print(f"Baseline: {baseline:.2f} meters")

# Or use grid spacing (approximate)
baseline_grid = array.compute_baseline(ant1, ant2, use_coordinates=False)
print(f"Grid baseline: {baseline_grid:.2f} meters")
```

### Compute All Baselines

```python
# Compute all pairwise baselines
baselines = array.compute_all_baselines(use_coordinates=True)

print(f"Total baselines: {len(baselines)}")

# Show first 10
for ant1, ant2, dist in baselines[:10]:
    print(f"{ant1} - {ant2}: {dist:.3f} m")
```

### Filter by Criteria

```python
# Get only antennas with geographic coordinates
with_coords = array.filter_by_coordinates(has_coords=True)
print(f"{len(with_coords)} antennas have coordinates")

# Check SNAP port assignments by tracing assembly chains
ant = array.get_antenna('ANT00001')
ports = ant.get_snap_ports()
if ports['p1']:
    print(f"P1 connected: {ant.format_chain_status('P1')}")
else:
    print(f"P1 not connected: {ant.format_chain_status('P1')}")

# Get antenna at specific grid position
ant = array.get_antenna_at_position('CN021E03')
if ant:
    print(f"Found: {ant.antenna_number} at {ant.grid_code}")
```

## API Reference

### Database Sync Function

**`sync_database(db_name='parts.db', db_dir=None, public_url=None)`**
- Download/sync database from cloud storage
- `db_name`: Database filename (default: 'parts.db')
- `db_dir`: Database directory (default: 'database/')
- `public_url`: Public URL for download (optional - uses config.yaml if not provided)
- Returns: dict with 'success', 'synced', 'message' keys
- **No credentials needed** - uses public URL from config.yaml automatically
- Priority: explicit public_url → config.yaml public_url → R2 with credentials

### AntennaArray Class

Main interface for working with antenna collections.

#### Methods

**`AntennaArray.from_database(db_path, array_id='C', sync_first=False, public_url=None)`**
- Load array from CAsMan database
- `db_path`: Path to `parts.db` file
- `array_id`: Array identifier (default: 'C' for core)
- `sync_first`: If True, download database before loading (default: False)
- `public_url`: Public URL for credential-free download
- Returns: `AntennaArray` object

**`get_antenna(antenna_number)`**
- Get antenna by part number
- Returns: `AntennaPosition` or `None`

**`get_antenna_at_position(grid_code)`**
- Get antenna at grid position
- Returns: `AntennaPosition` or `None`

**`compute_baseline(ant1, ant2, use_coordinates=True)`**
- Compute distance between two antennas
- `use_coordinates`: Use geodetic (True) or grid spacing (False)
- Returns: distance in meters (float)

**`compute_all_baselines(use_coordinates=True, include_self=False)`**
- Compute all pairwise baselines
- Returns: list of `(ant1_number, ant2_number, distance)` tuples

**`filter_by_coordinates(has_coords=True)`**
- Filter antennas by coordinate availability
- Returns: list of `AntennaPosition`

### Kernel Index Functions

Functions for mapping between grid coordinates and correlator kernel indices.

**`grid_to_kernel_index(grid_code, array_name='core')`**
- Convert grid coordinate to kernel index
- `grid_code`: Grid position (e.g., 'CN021E01')
- `array_name`: Array name in config (default: 'core')
- Returns: int (0-255) or None if unmapped
- Example: `grid_to_kernel_index('CN021E01')` returns 0

**`kernel_index_to_grid(kernel_idx, array_name='core')`**
- Convert kernel index to grid coordinate
- `kernel_idx`: Kernel index (0-255)
- `array_name`: Array name in config (default: 'core')
- Returns: str (grid code) or None if invalid
- Example: `kernel_index_to_grid(0)` returns 'CN021E01'

**`get_antenna_kernel_idx(array_name='core', db_dir=None)`**
- Get complete kernel index mapping with antenna data
- Returns: `KernelIndexArray` object with 43×6 arrays:
  - `kernel_indices`: int array (-1 for unmapped)
  - `grid_codes`: str array
  - `antenna_numbers`: str array
  - `snap_ports`: tuple array (chassis, slot, port)
- Methods:
  - `get_by_kernel_index(kernel_idx)`: Query by kernel index
  - `get_by_grid_code(grid_code)`: Query by grid code

### AntennaPosition Class

Represents a single antenna with all metadata.

#### Attributes

- `antenna_number`: str - Base antenna number (e.g., 'ANT00001')
- `grid_position`: AntennaGridPosition - Parsed grid position object
- `latitude`: float or None - Latitude in decimal degrees
- `longitude`: float or None - Longitude in decimal degrees
- `height`: float or None - Height in meters
- `coordinate_system`: str or None - Coordinate system ID
- `assigned_at`: str or None - ISO timestamp
- `notes`: str or None - Field notes

#### Properties

- `grid_code`: str - Grid code string (e.g., 'CN002E03')
- `row_offset`: int - Signed row offset
- `east_col`: int - 1-based east column index (1-6 for core array)

#### Methods

- `has_coordinates()`: bool - Check if coordinates available
- `get_snap_ports()`: dict - Get SNAP port assignments by tracing assembly chains
- `format_chain_status(polarization='P1')`: str - Format assembly chain status for display

## Examples

### Download and Load Latest Database

```python
from casman.antenna import sync_database, AntennaArray

# Method 1: Auto-download using pre-configured URLs (easiest!)
print("Downloading latest database...")
result = sync_database('parts.db')  # Uses config.yaml public URL

if result['success']:
    print(f"✓ {result['message']}")
    array = AntennaArray.from_database('database/parts.db')
    print(f"Loaded {len(array.antennas)} antennas")
else:
    print(f"✗ Download failed: {result['message']}")

# Method 2: One-liner auto-download on load
array = AntennaArray.from_database('database/parts.db', sync_first=True)
# Automatically uses public URL from config.yaml!

# Method 3: Download both databases for complete data
sync_database('parts.db')              # Antenna positions (from config)
sync_database('assembled_casm.db')     # Assembly chains (from config)

array = AntennaArray.from_database('database/parts.db')

# Now you can trace complete chains with downloaded data
ant = array.get_antenna('ANT00001')
chain_p1 = ant.format_chain_status('P1')
print(f"Chain: {chain_p1}")

# Method 4: Override with custom public URL
CUSTOM_URL = 'https://custom-server.com/latest_parts.db'
result = sync_database('parts.db', public_url=CUSTOM_URL)

# Method 5: Use R2 with credentials (maintainers only)
# Requires R2 credentials configured - see Database Backup Quick Start
# Falls back to this if public URL not in config
result = sync_database('parts.db')
```

### Baseline Matrix Computation

```python
from casman.antenna import AntennaArray
import numpy as np

array = AntennaArray.from_database('database/parts.db')

# Get sorted antenna list
antennas = sorted(array.antennas, key=lambda a: a.antenna_number)
n = len(antennas)

# Create baseline matrix
baseline_matrix = np.zeros((n, n))

for i, ant1 in enumerate(antennas):
    for j, ant2 in enumerate(antennas):
        if i != j:
            baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)
            baseline_matrix[i, j] = baseline

# Save to numpy file
np.save('baseline_matrix.npy', baseline_matrix)

# Also save antenna order
antenna_numbers = [ant.antenna_number for ant in antennas]
np.save('antenna_order.npy', antenna_numbers)

print(f"Saved {n}×{n} baseline matrix")
```

### Kernel Index Mapping

```python
from casman.antenna import (
    grid_to_kernel_index,
    kernel_index_to_grid,
    get_antenna_kernel_idx
)

# Convert between grid codes and kernel indices
kernel_idx = grid_to_kernel_index('CN021E01')  # Returns 0
grid_code = kernel_index_to_grid(0)  # Returns 'CN021E01'

# Get complete mapping with antenna assignments
kernel_data = get_antenna_kernel_idx()

print(f"Array shape: {kernel_data.shape}")  # (43, 6)
print(f"Mapped positions: {np.sum(kernel_data.kernel_indices >= 0)}")  # 256

# Query by kernel index
info = kernel_data.get_by_kernel_index(0)
print(f"Kernel 0: {info['grid_code']}, {info['antenna_number']}")

# Query by grid code
info = kernel_data.get_by_grid_code('CN021E01')
print(f"Grid CN021E01: kernel index {info['kernel_index']}")

# Create antenna-to-kernel-index mapping
antenna_to_kernel = {}
for row in range(43):
    for col in range(6):
        ant_num = kernel_data.antenna_numbers[row, col]
        kernel_idx = kernel_data.kernel_indices[row, col]
        if ant_num and kernel_idx >= 0:
            antenna_to_kernel[ant_num] = kernel_idx

print(f"Mapped {len(antenna_to_kernel)} antennas to kernel indices")
```

### Multi-Array Support

```python
from casman.antenna import load_array_layout, get_array_name_for_id

# Load different array configurations
core_layout = load_array_layout('core')
print(f"Core: {core_layout[1]} N rows, {core_layout[3]} E cols")

# Get array name from ID
array_name = get_array_name_for_id('C')  # Returns 'core'
array_name = get_array_name_for_id('O')  # Returns 'outriggers' if configured

# Validate positions for specific arrays
from casman.antenna import validate_components

# This enforces bounds for the specified array
is_valid = validate_components(
    array_id='C',
    direction='N',
    offset=21,
    east_col=6,
    enforce_bounds=True,
    array_name='core'
)
```

## Database Requirements

The antenna module expects a CAsMan database (`parts.db`) with:

### Required Table: `antenna_positions`

```sql
CREATE TABLE antenna_positions (
    id INTEGER PRIMARY KEY,
    antenna_number TEXT UNIQUE,
    grid_code TEXT UNIQUE,
    array_id TEXT,           -- 'C' for core, 'O' for outriggers, etc.
    row_offset INTEGER,       -- Signed: -21 to +21 for core
    east_col INTEGER,         -- 1-based: 1-6 for core array
    assigned_at TEXT,
    notes TEXT,
    latitude REAL,
    longitude REAL,
    height REAL,
    coordinate_system TEXT
);
```

## Configuration

The module uses `config.yaml` for grid layout configuration:

```yaml
grid:
  core:
    array_id: "C"
    north_rows: 21
    south_rows: 21
    east_columns: 6
    allow_expansion: true
    
    # Kernel index mapping (core array only)
    kernel_index:
      enabled: true
      max_index: 255        # 256 antennas (0-255)
      start_row: 21         # CN021
      start_column: 1       # E01
  
  # Optional: Additional arrays
  outriggers:
    array_id: "O"
    north_rows: 10
    south_rows: 10
    east_columns: 4
    allow_expansion: false
```

This file should be in the project root or discoverable via `CASMAN_CONFIG` environment variable.

**Note:** Kernel index mapping is only enabled for the core array and maps 256 positions (kernel indices 0-255) using row-major ordering starting from CN021E01. Positions CS021E05 and CS021E06 are unmapped as they exceed the 256-antenna limit.

## See Also

- [Grid Coordinates Documentation](grid_coordinates.md)
- [CAsMan Full Documentation](README.md)
- [Database Schema](database.md)
