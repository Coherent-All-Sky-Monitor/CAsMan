# Grid Position Coordinates

This document describes how to manage geographic coordinates (latitude, longitude, height) for antenna grid positions.

## Overview

The `antenna_positions` table in `parts.db` includes optional coordinate columns:
- `latitude` (REAL): Latitude in decimal degrees
- `longitude` (REAL): Longitude in decimal degrees  
- `height` (REAL): Height in meters above reference
- `coordinate_system` (TEXT): Coordinate system identifier (e.g., 'WGS84', 'local')

Coordinates are managed via CSV file (`database/grid_positions.csv`) for easy editing and version control.

## CSV Format

The CSV file has the following columns:

```csv
grid_code,latitude,longitude,height,coordinate_system,notes
CN021E01,37.8719,-122.2585,10.5,WGS84,North row 21 east 1
CN021E02,37.8720,-122.2583,10.6,WGS84,North row 21 east 2
```

- **grid_code**: Grid position identifier (e.g., 'CN021E01') - Note: uses 1-based indexing for east columns
- **latitude**: Decimal degrees (e.g., 37.8719)
- **longitude**: Decimal degrees (e.g., -122.2585)
- **height**: Height in meters (e.g., 10.5)
- **coordinate_system**: System identifier (e.g., 'WGS84', 'local')
- **notes**: Optional description

Empty coordinate values are skipped during loading.

## Usage

### 1. Edit Coordinates

Edit `database/grid_positions.csv` in a text editor or spreadsheet application:

```bash
# With text editor
nano database/grid_positions.csv

# Or import to spreadsheet (Excel, Google Sheets, LibreOffice Calc)
# Then export as CSV when done
```

**Template:** A template with all 258 core array positions (CN021E01 through CS021E06) is provided in `database/grid_positions.csv`. Note that the core array uses 1-based indexing for east columns (E01-E06).

### 2. Load Coordinates

After editing the CSV, load coordinates into the database:

```bash
# Load from default CSV (database/grid_positions.csv)
casman database load-coordinates

# Load from custom CSV
casman database load-coordinates --csv my_survey.csv
```

The command will report:
- Number of positions updated
- Number of positions skipped (no data or not in database)
- Any errors encountered

Example output:
```
Loading grid coordinates from CSV...
==================================================

✓ Updated: 3 position(s)
  Skipped: 0 position(s)

✓ Coordinate data loaded successfully
```

### 3. Verify Coordinates

Query the database to verify coordinates were loaded:

```bash
sqlite3 database/parts.db "SELECT antenna_number, grid_code, latitude, longitude, height FROM antenna_positions WHERE latitude IS NOT NULL;"
```

## Workflow

1. **Field Survey**: Measure coordinates with GPS equipment or total station
2. **Data Entry**: Enter coordinates into `database/grid_positions.csv`
3. **Version Control**: Commit CSV changes with `git commit`
4. **Load**: Run `casman database load-coordinates` to update database
5. **Deploy**: Updated coordinates are now available in the application

## Important Notes

- **Updates Only**: The loader only updates existing antenna position records. It does not create new antenna assignments.
- **Grid Position Must Exist**: An antenna must be assigned to a grid position before coordinates can be loaded for that position.
- **Overwrites Data**: Loading coordinates will overwrite existing coordinate values for that grid position.
- **CSV-Based**: No web UI for coordinate entry - all changes happen via CSV file editing.
- **Version Controlled**: CSV file should be committed to git for change tracking.

## Example: Adding Coordinates

1. Assign an antenna to a position (if not already assigned):
   ```bash
   # Via scanner web interface at http://localhost:5001/scanner
   # Scan antenna ANT00001 and assign to CN021E00
   ```

2. Add coordinates to CSV:
   ```csv
   grid_code,latitude,longitude,height,coordinate_system,notes
   CN021E00,37.871899,-122.258477,10.5,WGS84,North row 21 east 0
   ```

3. Load coordinates:
   ```bash
   casman database load-coordinates
   ```

4. Verify:
   ```bash
   sqlite3 database/parts.db "SELECT * FROM antenna_positions WHERE grid_code='CN021E00';"
   ```

## Coordinate Systems

Common coordinate system identifiers:
- **WGS84**: World Geodetic System 1984 (GPS standard)
- **NAD83**: North American Datum 1983
- **local**: Local survey coordinates (relative to site reference)
- **ITRF**: International Terrestrial Reference Frame

Choose a coordinate system appropriate for your site and measurement equipment.

## API Access

Coordinates are automatically included in position queries:

```python
from casman.database.antenna_positions import get_antenna_position

pos = get_antenna_position('ANT00001')
if pos:
    print(f"Latitude: {pos.get('latitude')}")
    print(f"Longitude: {pos.get('longitude')}")
    print(f"Height: {pos.get('height')}")
    print(f"System: {pos.get('coordinate_system')}")
```

All position retrieval functions return coordinate data when available:
- `get_antenna_position(antenna_number)` - Returns dict with coordinates
- `get_antenna_at_position(grid_code)` - Returns dict with coordinates  
- `get_all_antenna_positions(array_id='C')` - Returns list of dicts with coordinates

## Troubleshooting

**No positions updated:**
- Verify CSV has valid coordinate data (not empty)
- Check grid_code values match database records
- Ensure antennas are assigned to grid positions first

**CSV file not found:**
- Default path is `database/grid_positions.csv`
- Use `--csv` flag to specify different file
- Check working directory is project root

**Coordinate values incorrect:**
- Verify decimal degrees format (not degrees/minutes/seconds)
- Check sign convention (North/East positive, South/West negative)
- Ensure height units are meters
