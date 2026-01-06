# CAsMan Antenna Module Documentation

Complete guide to the antenna positioning module for array management, baseline calculations, and interferometry applications.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Database Sync](#database-sync)
5. [Core Concepts](#core-concepts)
6. [API Reference](#api-reference)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The `casman.antenna` module provides lightweight antenna array management with minimal dependencies, perfect for data analysis, baseline computation, and interferometry applications.

### Features

- **Antenna position loading** from CAsMan database
- **Multi-array support** (core array, outriggers, custom arrays)
- **Grid position parsing** with validation (1-based indexing)
- **Kernel index mapping** for correlator processing (0-255)
- **Geographic coordinates** (latitude, longitude, height)
- **SNAP port mappings** for polarizations
- **Baseline calculations** (geodetic and grid-based)
- **Minimal dependencies** (PyYAML, NumPy optional)

### Use Cases

- Data analysis scripts
- Baseline computation pipelines
- UV coverage calculations
- Interferometry applications
- Remote/HPC environments without GUI dependencies

---

## Installation

### Option 1: Antenna Module Only (Recommended for Analysis)

**One-line install from GitHub:**

```bash
pip install "git+https://github.com/Coherent-All-Sky-Monitor/CAsMan.git#egg=casman[antenna]"
```

**From local clone:**

```bash
git clone https://github.com/Coherent-All-Sky-Monitor/CAsMan.git
cd CAsMan
pip install -e ".[antenna]"
```

**Dependencies:** PyYAML only (~5 MB)

### Option 2: Full CAsMan Installation

For the complete toolkit including web interfaces, CLI, and visualization:

```bash
cd CAsMan
pip install -e .
```

**Dependencies:** Flask, Pillow, PyYAML, and others (~50 MB)

### Option 3: Development Installation

```bash
pip install -e ".[dev]"
```

---

## Quick Start

### Basic Loading and Access

```python
from casman.antenna import AntennaArray

# Load antenna array from database
array = AntennaArray.from_database('database/parts.db')
print(f"Loaded {len(array)} antennas")

# Get specific antenna
ant = array.get_antenna('ANT00001')
print(f"Antenna: {ant.antenna_number}")
print(f"Grid Position: {ant.grid_code}")
print(f"Row: {ant.row_offset}, Column: {ant.east_col}")

# Get antenna by grid position
ant = array.get_antenna_at_position('CN021E03')
if ant:
    print(f"Found: {ant.antenna_number}")
```

### Geographic Coordinates

```python
# Check if antenna has coordinates
if ant.has_coordinates():
    print(f"Lat: {ant.latitude:.6f}°")
    print(f"Lon: {ant.longitude:.6f}°")
    print(f"Height: {ant.height:.2f}m")
    print(f"System: {ant.coordinate_system}")

# Filter antennas with coordinates
with_coords = array.filter_by_coordinates(has_coords=True)
print(f"{len(with_coords)} antennas have coordinates")
```

### Baseline Calculations

```python
# Get two antennas
ant1 = array.get_antenna('ANT00001')
ant2 = array.get_antenna('ANT00002')

# Compute geodetic baseline (Haversine formula)
distance = array.compute_baseline(ant1, ant2, use_coordinates=True)
print(f"Baseline: {distance:.2f} meters")

# Or use grid spacing (approximate)
distance_grid = array.compute_baseline(ant1, ant2, use_coordinates=False)
print(f"Grid baseline: {distance_grid:.2f} meters")

# Compute all pairwise baselines
baselines = array.compute_all_baselines(use_coordinates=True)
print(f"Total baselines: {len(baselines)}")

for ant1_num, ant2_num, dist in baselines[:10]:
    print(f"{ant1_num} - {ant2_num}: {dist:.3f} m")
```

### SNAP Port Assignments

```python
# Check SNAP port assignments (requires assembled_casm.db)
ant = array.get_antenna('ANT00001')
ports = ant.get_snap_ports()

if ports['p1']:
    print(f"P1 connected: {ant.format_chain_status('P1')}")
    print(f"SNAP: {ports['p1']['snap_part']}")
else:
    print(f"P1 not connected: {ant.format_chain_status('P1')}")
```

---

## Database Sync

### First Time Setup

If you don't have a local database yet, download it automatically:

```python
from casman.antenna import AntennaArray

# Download and load in one line (uses public URL from config.yaml)
array = AntennaArray.from_database('database/parts.db', sync_first=True)
print(f"Downloaded and loaded {len(array)} antennas")
```

### Manual Sync

```python
from casman.antenna import sync_database

# Option 1: Auto-download using pre-configured public URL (no credentials!)
result = sync_database('parts.db')
print(result['message'])

if result['success']:
    array = AntennaArray.from_database('database/parts.db')
    print(f"Loaded {len(array)} antennas")

# Option 2: Override with custom public URL
PUBLIC_URL = 'https://pub-xxxxx.r2.dev/backups/parts.db/latest_parts.db'
result = sync_database('parts.db', public_url=PUBLIC_URL)

# Option 3: Download both databases for complete data
sync_database('parts.db')              # Antenna positions
sync_database('assembled_casm.db')     # Assembly chains (for SNAP ports)
```

### Smart Sync Behavior

The sync system intelligently handles updates:

- **Database doesn't exist** → Downloads it
- **Database exists and remote is newer** → Downloads update
- **Database exists and is up-to-date** → Skips download
- **Download fails but local exists** → Uses local copy

**Configuration** (in `config.yaml`):

```yaml
r2:
  public_urls:
    parts_db: "https://pub-xxxxx.r2.dev/backups/parts.db/latest_parts.db"
    assembled_db: "https://pub-xxxxx.r2.dev/backups/assembled_casm.db/latest_assembled_casm.db"
```

**Note:** Public URLs require no credentials and are pre-configured by maintainers.

---

## Core Concepts

### Grid Position Format

Grid codes use the format: `{array_id}{direction}{row:03d}E{col:02d}`

- **Array ID**: `C` (core), `N` (north), `S` (south)
- **Direction**: `N` (positive rows) or `S` (negative rows)
- **Row**: 3-digit row offset (e.g., `002` for row +2)
- **Column**: 2-digit column index (1-based, e.g., `01` for first column)

Examples:
- `CN021E01` - Core array, North row +21, East column 1
- `CS021E06` - Core array, South row -21, East column 6
- `CC000E03` - Core array, Center row 0, East column 3

### Kernel Index Mapping

The core array maps 256 antenna positions to kernel indices (0-255) for correlator processing:

```python
from casman.antenna import grid_to_kernel_index, kernel_index_to_grid

# Convert grid code to kernel index
kernel_idx = grid_to_kernel_index('CN021E01')  # Returns 0
print(f"Kernel index: {kernel_idx}")

# Convert kernel index to grid code
grid_code = kernel_index_to_grid(0)  # Returns 'CN021E01'
print(f"Grid code: {grid_code}")
```

**Mapping details:**
- Row-major ordering starting from CN021E01 (index 0)
- Covers 43 rows × 6 columns = 258 positions
- Only 256 mapped (CS021E05 and CS021E06 unmapped)
- Only enabled for core array

### Baseline Calculation Methods

#### Geodetic (Haversine Formula)

Used when `use_coordinates=True`:

```
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
c = 2 × atan2(√a, √(1-a))
d_horizontal = R × c
d_3d = √(d_horizontal² + Δheight²)
```

Where R = 6,371,000 meters (Earth radius)

**Accuracy:** ~0.5% for distances < 1000 km

#### Grid-Based Approximation

Used when `use_coordinates=False` or coordinates unavailable:

```
d = √((Δrow × spacing)² + (Δcol × spacing)²)
```

Where spacing = 0.4 meters (default CASM grid spacing)

**Accuracy:** Assumes flat grid, no height differences

---

## API Reference

### Database Sync Function

**`sync_database(db_name='parts.db', db_dir=None, public_url=None)`**

Download/sync database from cloud storage.

**Parameters:**
- `db_name` (str): Database filename (default: 'parts.db')
- `db_dir` (str): Database directory (default: 'database/')
- `public_url` (str): Public URL for download (optional - uses config.yaml if not provided)

**Returns:** dict with keys:
- `success` (bool): Whether operation succeeded
- `synced` (bool): Whether database was updated
- `message` (str): Status message

**Priority:** explicit public_url → config.yaml public_url → R2 with credentials

### AntennaArray Class

Main interface for working with antenna collections.

#### Class Methods

**`from_database(db_path, array_id='C', sync_first=False, public_url=None)`**

Load array from CAsMan database.

**Parameters:**
- `db_path` (str): Path to `parts.db` file
- `array_id` (str): Array identifier (default: 'C' for core)
- `sync_first` (bool): If True, download database before loading (default: False)
- `public_url` (str): Public URL for credential-free download

**Returns:** `AntennaArray` object

#### Instance Methods

**Lookup:**

- **`get_antenna(antenna_number)`** → `AntennaPosition | None`
  - Get antenna by part number

- **`get_antenna_at_position(grid_code)`** → `AntennaPosition | None`
  - Get antenna at grid position (case-insensitive)

**Baseline Calculations:**

- **`compute_baseline(ant1, ant2, use_coordinates=True)`** → `float`
  - Compute distance between two antennas
  - `use_coordinates=True`: Use geodetic (Haversine) formula
  - `use_coordinates=False`: Use grid spacing approximation
  - Returns distance in meters

- **`compute_all_baselines(use_coordinates=True, include_self=False)`** → `list`
  - Compute all pairwise baselines
  - Returns list of `(ant1_number, ant2_number, distance)` tuples

**Filtering:**

- **`filter_by_coordinates(has_coords=True)`** → `list[AntennaPosition]`
  - Filter antennas by coordinate availability

**Container Methods:**

- `__len__()`: Number of antennas
- `__iter__()`: Iterate over all antennas
- `__repr__()`: String representation

### AntennaPosition Class

Represents a single antenna with all metadata.

#### Attributes

- `antenna_number` (str): Base antenna number (e.g., 'ANT00001')
- `grid_position` (AntennaGridPosition): Parsed grid position object
- `latitude` (float | None): Latitude in decimal degrees
- `longitude` (float | None): Longitude in decimal degrees
- `height` (float | None): Height in meters
- `coordinate_system` (str | None): Coordinate system ID
- `assigned_at` (str | None): ISO timestamp
- `notes` (str | None): Field notes

#### Properties

- `grid_code` (str): Grid code string (e.g., 'CN002E03')
- `row_offset` (int): Signed row offset
- `east_col` (int): 1-based east column index

#### Methods

- **`has_coordinates()`** → `bool`
  - Returns True if lat/lon/height are set

- **`get_snap_ports()`** → `dict`
  - Get SNAP port assignments by tracing assembly chains
  - Returns dict with 'p1' and 'p2' keys containing port info or None

- **`format_chain_status(polarization='P1')`** → `str`
  - Format assembly chain status for display
  - Returns human-readable connection chain

### Kernel Index Functions

**`grid_to_kernel_index(grid_code, array_name='core')`** → `int | None`

Convert grid coordinate to kernel index.

**Parameters:**
- `grid_code` (str): Grid position (e.g., 'CN021E01')
- `array_name` (str): Array name in config (default: 'core')

**Returns:** int (0-255) or None if unmapped

**`kernel_index_to_grid(kernel_idx, array_name='core')`** → `str | None`

Convert kernel index to grid coordinate.

**Parameters:**
- `kernel_idx` (int): Kernel index (0-255)
- `array_name` (str): Array name in config (default: 'core')

**Returns:** str (grid code) or None if invalid

**`get_antenna_kernel_idx(array_name='core', db_dir=None)`** → `KernelIndexArray`

Get complete kernel index mapping with antenna data.

**Returns:** `KernelIndexArray` object with 43×6 arrays:
- `kernel_indices`: int array (-1 for unmapped)
- `grid_codes`: str array
- `antenna_numbers`: str array
- `snap_ports`: tuple array (chassis, slot, port)

**Methods:**
- `get_by_kernel_index(kernel_idx)`: Query by kernel index
- `get_by_grid_code(grid_code)`: Query by grid code

---

## Examples

### Example 1: Download and Load Latest Database

```python
from casman.antenna import sync_database, AntennaArray

# Method 1: One-liner with auto-download
array = AntennaArray.from_database('database/parts.db', sync_first=True)
print(f"Loaded {len(array)} antennas")

# Method 2: Explicit sync then load
result = sync_database('parts.db')
if result['success']:
    print(f"✓ {result['message']}")
    array = AntennaArray.from_database('database/parts.db')
else:
    print(f"✗ Download failed: {result['message']}")

# Method 3: Download both databases for complete functionality
sync_database('parts.db')              # Antenna positions
sync_database('assembled_casm.db')     # Assembly chains

array = AntennaArray.from_database('database/parts.db')

# Now you can trace complete chains
ant = array.get_antenna('ANT00001')
chain_p1 = ant.format_chain_status('P1')
print(f"Chain: {chain_p1}")
```

### Example 2: Baseline Statistics

```python
from casman.antenna import AntennaArray

array = AntennaArray.from_database('database/parts.db')
baselines = array.compute_all_baselines(use_coordinates=True)

distances = [dist for _, _, dist in baselines]
print(f"Total baselines: {len(baselines)}")
print(f"Min baseline: {min(distances):.2f}m")
print(f"Max baseline: {max(distances):.2f}m")
print(f"Avg baseline: {sum(distances)/len(distances):.2f}m")
```

### Example 3: Baseline Matrix Computation

```python
from casman.antenna import AntennaArray
import numpy as np

array = AntennaArray.from_database('database/parts.db')

# Get antennas with coordinates
antennas = [ant for ant in array if ant.has_coordinates()]
n = len(antennas)

# Create baseline matrix
baseline_matrix = np.zeros((n, n))

for i, ant1 in enumerate(antennas):
    for j, ant2 in enumerate(antennas):
        if i != j:
            baseline_matrix[i, j] = array.compute_baseline(
                ant1, ant2, use_coordinates=True
            )

# Save results
np.save('baseline_matrix.npy', baseline_matrix)
antenna_numbers = [ant.antenna_number for ant in antennas]
np.save('antenna_order.npy', antenna_numbers)

print(f"Saved {n}×{n} baseline matrix")
print(f"Min: {baseline_matrix[baseline_matrix > 0].min():.2f}m")
print(f"Max: {baseline_matrix.max():.2f}m")
```

### Example 4: Kernel Index Mapping

```python
from casman.antenna import get_antenna_kernel_idx
import numpy as np

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

### Example 5: Data Quality Check

```python
from casman.antenna import AntennaArray

array = AntennaArray.from_database('database/parts.db')

# Check data completeness
total = len(array)
with_coords = len(array.filter_by_coordinates(has_coords=True))

print(f"Data completeness:")
print(f"  Total antennas: {total}")
print(f"  With coordinates: {with_coords} ({100*with_coords/total:.1f}%)")

# Check SNAP assignments (requires assembled_casm.db)
connected_p1 = 0
connected_p2 = 0

for ant in array:
    ports = ant.get_snap_ports()
    if ports['p1']:
        connected_p1 += 1
    if ports['p2']:
        connected_p2 += 1

print(f"  SNAP P1 connected: {connected_p1} ({100*connected_p1/total:.1f}%)")
print(f"  SNAP P2 connected: {connected_p2} ({100*connected_p2/total:.1f}%)")
```

### Example 6: Spatial Clustering

```python
from casman.antenna import AntennaArray
from collections import defaultdict

array = AntennaArray.from_database('database/parts.db')

# Group antennas by row
by_row = defaultdict(list)
for ant in array:
    by_row[ant.row_offset].append(ant)

print("Antenna distribution by row:")
for row in sorted(by_row.keys(), reverse=True):
    antennas = by_row[row]
    print(f"  Row {row:+3d}: {len(antennas):3d} antennas")
```

---

## Database Schema

The antenna module reads from the `parts.db` database:

### Table: `antenna_positions`

```sql
CREATE TABLE antenna_positions (
    id INTEGER PRIMARY KEY,
    antenna_number TEXT UNIQUE NOT NULL,
    grid_code TEXT UNIQUE NOT NULL,
    array_id TEXT NOT NULL,           -- 'C', 'N', 'S', etc.
    row_offset INTEGER NOT NULL,      -- Signed: -21 to +21 for core
    east_col INTEGER NOT NULL,        -- 1-based: 1-6 for core array
    assigned_at TEXT NOT NULL,
    notes TEXT,
    latitude REAL,
    longitude REAL,
    height REAL,
    coordinate_system TEXT
);
```

### Loading Geographic Coordinates

Coordinates can be loaded from CSV using the CLI:

```bash
casman database load-coordinates --csv grid_positions.csv
```

CSV format:
```csv
grid_code,latitude,longitude,height,coordinate_system,notes
CN021E00,37.871899,-122.258477,10.5,WGS84,Survey point 1
CN021E01,37.871912,-122.258321,10.6,WGS84,Survey point 2
```

---

## Configuration

The module uses `config.yaml` for grid layout and sync configuration:

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

**Note:** Configuration file should be in project root or discoverable via `CASMAN_CONFIG` environment variable.

---

## Troubleshooting

### Import Errors

**"No module named 'casman'"**
- Run `pip install -e .` or `pip install -e ".[antenna]"` from repo root

**"No module named 'yaml'"**
- Install PyYAML: `pip install PyYAML`
- Or use full requirements: `pip install -r requirements.txt`

### Database Issues

**Database not found**
- Use absolute paths or Path objects
- Check path to `database/parts.db`
- Try downloading: `sync_database('parts.db')`

**No coordinates loaded**
- Load coordinates: `casman database load-coordinates --csv grid_positions.csv`
- Check CSV format matches specification
- Verify antennas exist in database first

**Sync failed**
- Check internet connection
- Verify public URL in config.yaml
- Try explicit URL: `sync_database('parts.db', public_url='...')`

### Data Issues

**SNAP ports not found**
- Download assembled database: `sync_database('assembled_casm.db')`
- Check assembly chains exist in database
- Verify antenna is actually connected

**Baseline calculation returns None**
- Check both antennas exist: `array.get_antenna('ANT00001')`
- Verify coordinates loaded: `ant.has_coordinates()`
- Try grid-based: `compute_baseline(..., use_coordinates=False)`


---


### Quick Reference

**Installation:**
```bash
pip install "git+https://github.com/Coherent-All-Sky-Monitor/CAsMan.git#egg=casman[antenna]"
```

**Download and load:**
```python
from casman.antenna import AntennaArray
array = AntennaArray.from_database('database/parts.db', sync_first=True)
```

**Compute baselines:**
```python
baselines = array.compute_all_baselines(use_coordinates=True)
```

**Kernel index:**
```python
from casman.antenna import grid_to_kernel_index
kernel_idx = grid_to_kernel_index('CN021E01')  # Returns 0
```

### Related Documentation

- [Database Documentation](database.md) - Database schema and backup system
- [Grid Coordinates](grid_coordinates.md) - Geographic coordinate management
- [Main Documentation](main.md) - Getting started with CAsMan
- [Development Guide](development.md) - Developer documentation
