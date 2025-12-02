# Antenna Module - Standalone Installation

This guide explains how to install and use just the antenna positioning module from CAsMan without the full toolkit.

## Overview

The `casman.antenna` module provides lightweight antenna array management with:

- **Antenna position loading** from CAsMan database
- **Grid position parsing** and validation
- **Geographic coordinates** (latitude, longitude, height)
- **SNAP port mappings** for polarizations
- **Baseline calculations** between antenna pairs (geodetic and grid-based)
- **Minimal dependencies** (no Flask, Pillow, or web frameworks)

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
array = AntennaArray.from_database('database/parts.db')

print(f"Loaded {len(array)} antennas")

# Get specific antenna
ant = array.get_antenna('ANT00001')
print(f"Antenna: {ant.antenna_number}")
print(f"Grid Position: {ant.grid_code}")
print(f"Coordinates: ({ant.latitude}, {ant.longitude})")
```

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

### AntennaArray Class

Main interface for working with antenna collections.

#### Methods

**`AntennaArray.from_database(db_path, array_id='C')`**
- Load array from CAsMan database
- `db_path`: Path to `parts.db` file
- `array_id`: Array identifier (default: 'C' for core)
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
- `east_col`: int - Zero-based east column index

#### Methods

- `has_coordinates()`: bool - Check if coordinates available
- `get_snap_ports()`: dict - Get SNAP port assignments by tracing assembly chains
- `format_chain_status(polarization='P1')`: str - Format assembly chain status for display

## Examples

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



## Database Requirements

The antenna module expects a CAsMan database (`parts.db`) with:

### Required Table: `antenna_positions`

```sql
CREATE TABLE antenna_positions (
    id INTEGER PRIMARY KEY,
    antenna_number TEXT UNIQUE,
    grid_code TEXT UNIQUE,
    array_id TEXT,
    row_offset INTEGER,
    east_col INTEGER,
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
```

This file should be in the project root or discoverable via `CASMAN_CONFIG` environment variable.

## Performance Notes

- **Database loading**: Typically < 100ms for ~250 antennas
- **Baseline computation**: ~1ms per pair with coordinates, faster with grid spacing
- **All baselines**: ~1-2 seconds for 250 antennas (31,125 baselines)
- **Memory usage**: ~1KB per antenna (minimal)

## Limitations

- Grid baseline calculation assumes uniform spacing (0.4m default) - use coordinates for real life
- Great circle distance formula (Haversine) is accurate for Earth-scale baselines but assumes spherical Earth
- SNAP mappings require separate database table


## See Also

- [Grid Coordinates Documentation](grid_coordinates.md)
- [CAsMan Full Documentation](README.md)
- [Database Schema](database.md)
