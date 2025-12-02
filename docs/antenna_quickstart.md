# CAsMan Antenna Module - Quick Start

## Overview

The CAsMan antenna module provides lightweight tools for analyzing antenna array configurations, computing baselines, and performing UV coverage analysis. It can be installed standalone without the full CAsMan web interface dependencies.

## Installation Options

### Option 1: Minimal Installation (Antenna Module Only)

**From GitHub (one-line install):**
```bash
pip install "git+https://github.com/Coherent-All-Sky-Monitor/CAsMan.git#egg=casman[antenna]"
```

**From local clone:**
```bash
git clone https://github.com/Coherent-All-Sky-Monitor/CAsMan.git
cd CAsMan
pip install -e ".[antenna]"
```

**Dependencies:** Only PyYAML (~5MB)

**Use cases:**
- Baseline calculations
- UV coverage analysis
- Antenna position management
- Scientific data analysis scripts

### Option 2: Full Installation

Install complete CAsMan with web interface:

```bash
pip install -e .
```

**Dependencies:** Flask, Pillow, PyYAML, and others (~50MB)

## Quick Start

### 1. Loading an Antenna Array

```python
from casman.antenna.array import AntennaArray

# Load from database
array = AntennaArray.from_database('database/parts.db', array_id='C')

print(f"Loaded {len(array)} antennas")
```

### 2. Computing Baselines

```python
# Get two antennas
ant1 = array.get_antenna('ANT00001')
ant2 = array.get_antenna('ANT00002')

# Compute geodetic baseline (Haversine formula)
distance = array.compute_baseline(ant1, ant2, use_coordinates=True)
print(f"Baseline: {distance:.2f} meters")

# Compute all pairwise baselines
baselines = array.compute_all_baselines(use_coordinates=True)
for ant1_num, ant2_num, dist in baselines:
    print(f"{ant1_num} <-> {ant2_num}: {dist:.2f}m")
```

### 3. Filtering and Analysis

```python
# Get only antennas with coordinates
with_coords = array.filter_by_coordinates(has_coords=True)
print(f"Antennas with coordinates: {len(with_coords)}")

# Check SNAP port assignments
ant = array.get_antenna('ANT00001')
ports = ant.get_snap_ports()
if ports['p1']:
    print(f"P1: {ant.format_chain_status('P1')}")
    print(f"Connected to {ports['p1']['snap_part']}")
else:
    print(f"P1: {ant.format_chain_status('P1')}")

# Find antenna by grid position
ant = array.get_antenna_at_position('CN001E00')
if ant:
    print(f"Found: {ant.antenna_number}")
```

### 4. Accessing Antenna Properties

```python
ant = array.get_antenna('ANT00001')

# Basic properties
print(f"Antenna: {ant.antenna_number}")
print(f"Grid position: {ant.grid_code}")
print(f"Row offset: {ant.row_offset}, Column: {ant.east_col}")

# Geographic coordinates
if ant.has_coordinates():
    print(f"Lat: {ant.latitude:.6f}°")
    print(f"Lon: {ant.longitude:.6f}°")
    print(f"Height: {ant.height:.2f}m")
    print(f"System: {ant.coordinate_system}")

```

## Examples

### Example 1: Baseline Statistics

```python
from casman.antenna.array import AntennaArray

array = AntennaArray.from_database('database/parts.db')
baselines = array.compute_all_baselines(use_coordinates=True)

distances = [dist for _, _, dist in baselines]
print(f"Min baseline: {min(distances):.2f}m")
print(f"Max baseline: {max(distances):.2f}m")
print(f"Avg baseline: {sum(distances)/len(distances):.2f}m")
```

### Example 2: UV Coverage Analysis

```python
# Compute UV coordinates for 21cm HI line
wavelength = 0.21  # meters

for ant1_num, ant2_num, dist in array.compute_all_baselines():
    ant1 = array.get_antenna(ant1_num)
    ant2 = array.get_antenna(ant2_num)
    
    if ant1.has_coordinates() and ant2.has_coordinates():
        # Simplified UV calculation (needs proper projection)
        ew_baseline = (ant2.longitude - ant1.longitude) * 111000
        ns_baseline = (ant2.latitude - ant1.latitude) * 111000
        
        u = ew_baseline / wavelength
        v = ns_baseline / wavelength
        
        print(f"Baseline {ant1_num}-{ant2_num}: u={u:.1f}, v={v:.1f} λ")
```

### Example 3: Export to CSV

```python
import csv

array = AntennaArray.from_database('database/parts.db')

with open('antenna_positions.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['antenna', 'grid_code', 'lat', 'lon', 'height'])
    
    for ant in array:
        writer.writerow([
            ant.antenna_number,
            ant.grid_code,
            ant.latitude or '',
            ant.longitude or '',
            ant.height or ''
        ])

print(f"Exported {len(array)} antennas")
```

### Example 4: Find Nearest Neighbors

```python
def find_nearest(array, target_num, n=5):
    """Find N nearest antennas to target."""
    target = array.get_antenna(target_num)
    
    neighbors = []
    for ant in array:
        if ant.antenna_number != target_num and ant.has_coordinates():
            dist = array.compute_baseline(target, ant, use_coordinates=True)
            neighbors.append((ant, dist))
    
    neighbors.sort(key=lambda x: x[1])
    return neighbors[:n]

# Example usage
array = AntennaArray.from_database('database/parts.db')
nearest = find_nearest(array, 'ANT00001', n=5)

for ant, dist in nearest:
    print(f"{ant.antenna_number}: {dist:.2f}m away")
```

## API Reference

### AntennaPosition

Dataclass representing a single antenna with all metadata.

**Attributes:**
- `antenna_number` (str): Unique antenna identifier
- `grid_position` (AntennaGridPosition): Parsed grid position object
- `latitude` (float | None): Latitude in degrees
- `longitude` (float | None): Longitude in degrees
- `height` (float | None): Height above reference in meters
- `coordinate_system` (str | None): Coordinate system name
- `assigned_at` (str | None): Assignment timestamp
- `notes` (str | None): Additional notes

**Properties:**
- `grid_code` (str): Full grid code string
- `row_offset` (int): North-south row offset
- `east_col` (int): East-west column index

**Methods:**
- `has_coordinates() -> bool`: Returns True if lat/lon/height are set
- `get_snap_ports() -> dict`: Get SNAP port assignments by tracing assembly chains
- `format_chain_status(polarization='P1') -> str`: Format assembly chain status for display

### AntennaArray

Collection of antenna positions with analysis methods.

**Class Methods:**
- `from_database(db_path, array_id='C') -> AntennaArray`
  - Load array from database file
  - `db_path`: Path to parts.db SQLite database
  - `array_id`: Array identifier (default 'C')

**Instance Methods:**

**Lookup:**
- `get_antenna(antenna_number: str) -> AntennaPosition | None`
  - Get antenna by number
- `get_antenna_at_position(grid_code: str) -> AntennaPosition | None`
  - Get antenna by grid position (case-insensitive)

**Baseline Calculations:**
- `compute_baseline(ant1, ant2, use_coordinates=True) -> float`
  - Compute baseline distance between two antennas
  - `use_coordinates=True`: Use Haversine formula with coordinates
  - `use_coordinates=False`: Use grid-based approximation
  - Returns distance in meters

- `compute_all_baselines(use_coordinates=True, include_self=False) -> list`
  - Compute all pairwise baselines
  - Returns list of tuples: `[(ant1_num, ant2_num, distance), ...]`

**Filtering:**
- `filter_by_coordinates(has_coords=True) -> list[AntennaPosition]`
  - Filter antennas by coordinate availability

**Container Methods:**
- `__len__()`: Number of antennas
- `__iter__()`: Iterate over all antennas
- `__repr__()`: String representation

## Baseline Calculation Methods

### Geodetic (Haversine Formula)

Used when `use_coordinates=True`:

```
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
c = 2 × atan2(√a, √(1-a))
d_horizontal = R × c
d_3d = √(d_horizontal² + Δheight²)
```

Where R = 6371000 meters (Earth radius)

**Accuracy:** ~0.5% for distances < 1000km

### Grid-Based Approximation

Used when `use_coordinates=False` or coordinates unavailable:

```
d = √((Δrow × spacing)² + (Δcol × spacing)²)
```

Where spacing = 14 meters (default HERA grid spacing)

**Accuracy:** Assumes flat grid, no height differences

## Loading Geographic Coordinates

Coordinates can be loaded from CSV using the CLI:

```bash
casman database load-coordinates --csv grid_positions.csv
```

CSV format:
```csv
grid_code,latitude,longitude,height,coordinate_system,notes
CN001E00,37.871899,-122.258477,10.5,WGS84,Survey point 1
CN001E01,37.871912,-122.258321,10.6,WGS84,Survey point 2
```

## Database Schema

The module reads from these tables:

**antenna_positions:**
- `antenna_number` (TEXT): Unique identifier
- `grid_code` (TEXT): Grid position code
- `array_id` (TEXT): Array identifier (C, N, S, etc.)
- `row_offset` (INTEGER): N-S row offset
- `east_col` (INTEGER): E-W column index
- `latitude` (REAL): Latitude in degrees
- `longitude` (REAL): Longitude in degrees
- `height` (REAL): Height in meters
- `coordinate_system` (TEXT): Coordinate system name
- `assigned_at` (TEXT): ISO timestamp
- `notes` (TEXT): Additional notes

## Performance Notes

- Database loading: ~10ms for 256 antennas
- Baseline computation: ~0.01ms per pair (geodetic)
- All baselines (256 antennas): ~300ms (32,640 pairs)
- Memory usage: ~50KB per antenna

## Common Patterns

### Pattern 1: Quality Control

```python
# Check data completeness
array = AntennaArray.from_database('database/parts.db')

total = len(array)
with_coords = len(array.filter_by_coordinates(has_coords=True))

print(f"Data completeness:")
print(f"  Coordinates: {100*with_coords/total:.1f}%")
```

### Pattern 2: Baseline Matrix

```python
import numpy as np

array = AntennaArray.from_database('database/parts.db')
antennas = [ant for ant in array if ant.has_coordinates()]

n = len(antennas)
matrix = np.zeros((n, n))

for i, ant1 in enumerate(antennas):
    for j, ant2 in enumerate(antennas):
        if i != j:
            matrix[i, j] = array.compute_baseline(ant1, ant2)

print(f"Baseline matrix: {n}×{n}")
print(f"Min: {matrix[matrix > 0].min():.2f}m")
print(f"Max: {matrix.max():.2f}m")
```

### Pattern 3: Spatial Clustering

```python
from collections import defaultdict

array = AntennaArray.from_database('database/parts.db')

# Group antennas by row
by_row = defaultdict(list)
for ant in array:
    by_row[ant.row_offset].append(ant)

for row, antennas in sorted(by_row.items()):
    print(f"Row {row:+2d}: {len(antennas)} antennas")
```

## Troubleshooting

**Import error: "No module named 'casman'"**
- Run `pip install -e .` or `pip install -e ".[antenna]"` from repo root

**Import error: "No module named 'yaml'"**
- Install PyYAML: `pip install PyYAML`
- Or use full requirements: `pip install -r requirements.txt`

**Database not found**
- Check path to `database/parts.db`
- Use absolute paths or Path objects

**No coordinates loaded**
- Load coordinates: `casman database load-coordinates --csv grid_positions.csv`
- Check CSV format matches specification

## See Also

- Full documentation: `docs/antenna_module.md`
- Coordinate management: `docs/grid_coordinates.md`
- Example scripts: `scripts/example_*.py`
- Web visualization: `casman visualize grid`

## Support

For issues or questions:
- Check existing test files: `tests/test_antenna_*.py`
- Review example scripts: `scripts/example_*.py`
- Consult API documentation: `docs/api_reference.md`
