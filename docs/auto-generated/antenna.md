# Antenna Package

Documentation for the `casman.antenna` package.

## Overview

Antenna grid positioning package.

This package provides utilities for managing antenna positions within
grid-based array layouts, tracing connections to SNAP ports, and mapping
grid coordinates to correlator kernel indices.

## Modules

### sync

Lightweight database synchronization for casman-antenna package.

This module provides auto-sync functionality for antenna-only users
who install casman-antenna via pip. It automatically downloads the latest
databases from GitHub Releases on import.

**Functions:**
- `sync_databases()` - Synchronize databases from GitHub Releases
- `force_sync()` - Force download of databases from GitHub Releases

### grid

Antenna grid position utilities.

This module defines parsing, formatting, and validation helpers for antenna
position codes of the form:

    [A-Z][N/C/S][000-999]E[01-99]

Examples
--------
    CN002E03  -> Core array (C), 2 rows North of center, East column 3
    CS017E04  -> Core array (C), 17 rows South of center, East column 4
    CC000E01  -> Core array (C), Center row, East column 1

The format is intentionally expansive; while the core layout currently uses
only a 43 x 6 grid (rows N001..N021, C000, S001..S021 and E01..E06), the
specification reserves three digits for the north/south offset and two digits
for the east column to allow future expansion (e.g. additional arrays or
extended baselines).

Configuration
-------------
Grid boundaries for the core array are defined in ``config.yaml`` under the
``grid.core`` section:

```
grid:
  core:
    array_id: "C"
    north_rows: 21
    south_rows: 21
    east_columns: 6
    allow_expansion: true
```

If expansion is allowed, codes outside the core bounds remain syntactically
valid but should be treated as unassigned when rendering the core layout.

Internal Representation
-----------------------
Rows are converted to signed integer offsets relative to the center:

    N002 -> +2
    S017 -> -17
    C000 -> 0 (Center must always use offset 000)

East columns are one-based integers parsed from the two-digit field:

    E01 -> 1
    E06 -> 6

Data Model
----------
The :class:`AntennaGridPosition` dataclass stores both the canonical string
(`grid_code`) and normalized numeric fields for efficient storage and lookup.

Functions provided:
    - ``parse_grid_code(code)``: Validate and parse a grid code string.
    - ``format_grid_code(array_id, direction, offset, east_col)``: Build code.
    - ``direction_from_row(row_offset)``: Infer N/S/C from signed offset.
    - ``validate_components(array_id, direction, offset, east_col)``: Bounds check.

All functions raise ``ValueError`` on invalid inputs.

**Functions:**
- `load_core_layout()` - Load core array layout limits from configuration
- `load_array_layout()` - Load array layout limits from configuration for any grid
- `get_array_name_for_id()` - Look up the array name (config key) for a given array ID letter
- `direction_from_row()` - Infer direction code from signed row offset
- `format_grid_code()` - Compose a grid code from components
- `validate_components()` - Validate numeric components against configuration bounds
- `parse_grid_code()` - Parse and validate a grid code string
- `to_grid_code()` - Convert numeric offsets to a grid code

**Classes:**
- `AntennaGridPosition` - Normalized representation of an antenna grid position

### chain

Antenna chain utilities for tracing connections to SNAP ports.

This module provides functions to traverse connection chains from antennas
through the assembly to determine SNAP port assignments for both polarizations.

**Functions:**
- `get_snap_port_for_chain()` - Find SNAP port at end of connection chain
- `get_snap_ports_for_antenna()` - Get SNAP ports for both polarizations of an antenna
- `format_snap_port()` - Format SNAP port info as human-readable string
- `get_snap_port_mapping()` - Get complete mapping for a SNAP port including network and ADC info

### kernel_index

Kernel index mapping for antenna grid positions.

This module provides functions to convert between grid coordinates and kernel indices
used by the correlator. The kernel index is a 0-indexed linear mapping of antenna
positions in the grid, used for correlator processing.

For the core array with 43 rows (N021 to S021) and 6 columns (E01-E06):
- Kernel indices 0-255 map to a 43x6 grid (258 total positions)
- Mapping follows row-major order starting from CN021E01
- Only the first 256 positions are mapped (CS021E05 and CS021E06 are unmapped)

**Functions:**
- `grid_to_kernel_index()` - Convert grid coordinate to kernel index
- `kernel_index_to_grid()` - Convert kernel index to grid coordinate
- `get_array_index_map()` - Get complete kernel index mapping with antenna and SNAP port information
- `get_by_kernel_index()` - Get information for a specific kernel index
- `get_by_grid_code()` - Get information for a specific grid code
- `plot_positions()` - Plot grid positions with labeled axes

**Classes:**
- `KernelIndexArray` - Container for kernel index mapping arrays

### array

Lightweight antenna array position management.

This module provides a minimal-dependency interface for working with antenna
positions, coordinates, and baseline calculations. It can be installed
independently of the full CAsMan toolkit.

Classes
-------
AntennaPosition : Dataclass representing a single antenna with all metadata
AntennaArray : Collection of antennas with baseline computation methods

Example
-------
>>> from casman.antenna.array import AntennaArray
>>> array = AntennaArray.from_database('database/parts.db')
>>> ant1 = array.get_antenna('ANT00001')
>>> ant2 = array.get_antenna('ANT00002')
>>> baseline = array.compute_baseline(ant1, ant2)
>>> print(f"Baseline: {baseline:.2f} meters")

**Functions:**
- `sync_database()` - Download database from GitHub Releases
- `has_coordinates()` - Check if this antenna has geographic coordinates
- `get_snap_ports()` - Get SNAP port assignments by tracing assembly chains
- `format_chain_status()` - Format assembly chain status for display
- `grid_code()` - Get the grid code string (e
- `row_offset()` - Get signed row offset (-999 to +999)
- `east_col()` - Get zero-based east column index
- `from_database()` - Load antenna array from CAsMan database
- `get_antenna()` - Get antenna by part number
- `get_antenna_at_position()` - Get antenna at specific grid position
- `compute_baseline()` - Compute baseline distance between two antennas
- `compute_all_baselines()` - Compute all pairwise baselines
- `filter_by_coordinates()` - Filter antennas by coordinate availability

**Classes:**
- `AntennaPosition` - Complete antenna position information including coordinates and SNAP mapping
- `AntennaArray` - Collection of antenna positions with baseline computation capabilities

## Sync Module Details

This module provides auto-sync functionality for antenna-only users
who install casman-antenna via pip. It automatically downloads the latest
databases from GitHub Releases on import.

## Functions

### sync_databases

**Signature:** `sync_databases(quiet: bool) -> bool`

Synchronize databases from GitHub Releases. This function is called automatically when the antenna module is imported. It downloads the latest databases if they're not already up-to-date. On first failure (e.g., rate limit), subsequent calls will skip sync and use local databases to avoid repeated error messages.

**Returns:**

True if sync successful or local databases are up-to-date, False otherwise

---

### force_sync

**Signature:** `force_sync() -> bool`

Force download of databases from GitHub Releases. This function checks if the local database is current, displays status information, and only downloads if an update is available.

**Returns:**

True if sync successful or databases are up-to-date, False otherwise

---

## Grid Module Details

This module defines parsing, formatting, and validation helpers for antenna
position codes of the form:

    [A-Z][N/C/S][000-999]E[01-99]

Examples
--------
    CN002E03  -> Core array (C), 2 rows North of center, East column 3
    CS017E04  -> Core array (C), 17 rows South of center, East column 4
    CC000E01  -> Core array (C), Center row, East column 1

The format is intentionally expansive; while the core layout currently uses
only a 43 x 6 grid (rows N001..N021, C000, S001..S021 and E01..E06), the
specification reserves three digits for the north/south offset and two digits
for the east column to allow future expansion (e.g. additional arrays or
extended baselines).

Configuration
-------------
Grid boundaries for the core array are defined in ``config.yaml`` under the
``grid.core`` section:

```
grid:
  core:
    array_id: "C"
    north_rows: 21
    south_rows: 21
    east_columns: 6
    allow_expansion: true
```

If expansion is allowed, codes outside the core bounds remain syntactically
valid but should be treated as unassigned when rendering the core layout.

Internal Representation
-----------------------
Rows are converted to signed integer offsets relative to the center:

    N002 -> +2
    S017 -> -17
    C000 -> 0 (Center must always use offset 000)

East columns are one-based integers parsed from the two-digit field:

    E01 -> 1
    E06 -> 6

Data Model
----------
The :class:`AntennaGridPosition` dataclass stores both the canonical string
(`grid_code`) and normalized numeric fields for efficient storage and lookup.

Functions provided:
    - ``parse_grid_code(code)``: Validate and parse a grid code string.
    - ``format_grid_code(array_id, direction, offset, east_col)``: Build code.
    - ``direction_from_row(row_offset)``: Infer N/S/C from signed offset.
    - ``validate_components(array_id, direction, offset, east_col)``: Bounds check.

All functions raise ``ValueError`` on invalid inputs.

## Functions

### load_core_layout

**Signature:** `load_core_layout() -> Tuple[str, int, int, int, bool]`

Load core array layout limits from configuration.

**Returns:**

(array_id, north_rows, south_rows, east_columns, allow_expansion)
Tuple containing bounds for validation.

**Raises:**

KeyError
If required configuration keys are missing.

---

### load_array_layout

**Signature:** `load_array_layout(array_name: str) -> Tuple[str, int, int, int, bool]`

Load array layout limits from configuration for any grid.

**Parameters:**

array_name : str
Name of the array section in config (e.g., 'core', 'outriggers').

**Returns:**

(array_id, north_rows, south_rows, east_columns, allow_expansion)
Tuple containing bounds for validation.

**Raises:**

KeyError
If required configuration keys are missing.

**Examples:**

```python
>>> load_array_layout('core')
('C', 21, 21, 6, True)
>>> load_array_layout('outriggers')
('O', 10, 10, 4, False)
```

---

### get_array_name_for_id

**Signature:** `get_array_name_for_id(array_id: str) -> Optional[str]`

Look up the array name (config key) for a given array ID letter.

**Parameters:**

array_id : str
Single letter array identifier (e.g., 'C', 'O').

**Returns:**

str or None
Array name (e.g., 'core', 'outriggers') or None if not found.

**Examples:**

```python
>>> get_array_name_for_id('C')
'core'
>>> get_array_name_for_id('O')
'outriggers'
>>> get_array_name_for_id('Z')
None
```

---

### direction_from_row

**Signature:** `direction_from_row(row_offset: int) -> str`

Infer direction code from signed row offset.

**Parameters:**

row_offset : int
Signed offset (negative for south, positive for north, zero for center).

**Returns:**

str
'N', 'S', or 'C'.

---

### format_grid_code

**Signature:** `format_grid_code(array_id: str, direction: str, offset: int, east_col: int) -> str`

Compose a grid code from components.

**Parameters:**

array_id : str
Single uppercase letter designating the array.
direction : str
'N', 'S', or 'C'.
offset : int
Absolute offset (0-999). Must be 0 if direction == 'C'.
east_col : int
One-based east column (1-99).

**Returns:**

str
Formatted grid code (e.g. 'CN002E03').

**Raises:**

ValueError
If components are invalid.

---

### validate_components

**Signature:** `validate_components(array_id: str, row_offset: int, east_col: int) -> None`

Validate numeric components against configuration bounds.

**Parameters:**

array_id : str
Array identifier letter.
row_offset : int
Signed offset (-999..999). Specific array bounds may be narrower.
east_col : int
East column index (1-based).
enforce_bounds : bool, optional
If True, apply array-specific layout limits unless expansion is enabled.

**Raises:**

ValueError
On any validation failure.

---

### parse_grid_code

**Signature:** `parse_grid_code(code: str) -> AntennaGridPosition`

Parse and validate a grid code string.

**Parameters:**

code : str
Grid code string in the canonical format.
enforce_bounds : bool, optional
Apply array-specific layout limits; ignored if expansion enabled in config.

**Returns:**

AntennaGridPosition
Dataclass with normalized components.

**Raises:**

ValueError
If the code is syntactically or semantically invalid.

**Examples:**

```python
>>> parse_grid_code("CN002E03")
AntennaGridPosition(array_id='C', direction='N', offset=2, east_col=3, row_offset=2, grid_code='CN002E03')
>>> parse_grid_code("CS017E04").row_offset
-17
>>> parse_grid_code("CC000E01").grid_code
'CC000E01'
```

---

### to_grid_code

**Signature:** `to_grid_code(row_offset: int, east_col: int, array_id: Optional[str]) -> str`

Convert numeric offsets to a grid code.

**Parameters:**

row_offset : int
Signed relative offset (negative south, positive north, zero center).
east_col : int
One-based east column (1-99).
array_id : str, optional
Array identifier; defaults to core array from config if omitted.

**Returns:**

str
Canonical grid code string.

**Raises:**

ValueError
If components invalid or out of bounds.

---

## Classes

### AntennaGridPosition

*@dataclass(frozen=True)*

**Class:** `AntennaGridPosition`

Normalized representation of an antenna grid position.

Parameters
----------
array_id : str
    Leading uppercase letter designating the array (e.g. 'C').
direction : str
    One of 'N', 'S', or 'C'.
offset : int
    Absolute offset from center (0-999). Must be 0 when direction == 'C'.
east_col : int
    Zero-based east column index (0-99). Core layout uses 0-5.
row_offset : int
    Signed offset: positive for North, negative for South, zero for Center.
grid_code : str
    Canonical code string matching the specification.

Notes
-----
The ``offset`` field never stores sign; use ``row_offset`` for relative
positioning logic. ``grid_code`` is always the authoritative string form.

---

## Chain Module Details

This module provides functions to traverse connection chains from antennas
through the assembly to determine SNAP port assignments for both polarizations.

## Functions

### get_snap_port_for_chain

**Signature:** `get_snap_port_for_chain(part_number: str) -> Optional[dict]`

Find SNAP port at end of connection chain. Traverses the connection chain starting from the given part until reaching a SNAP board, then extracts chassis/slot/port information.

**Parameters:**

part_number : str
Starting part number (e.g. 'ANT00001P1', 'LNA00005P2').
db_dir : str, optional
Custom database directory for testing.

**Examples:**

```python
>>> get_snap_port_for_chain('ANT00001P1')
{'snap_part': 'SNAP1A05', 'chassis': 1, 'slot': 'A', 'port': 5, 'chain': [...]}
```

---

### get_snap_ports_for_antenna

**Signature:** `get_snap_ports_for_antenna(antenna_number: str) -> dict`

Get SNAP ports for both polarizations of an antenna.

**Parameters:**

antenna_number : str
Antenna base number with or without polarization suffix.
E.g. 'ANT00001', 'ANT00001P1', 'ANT00001P2'.
db_dir : str, optional
Custom database directory for testing.

**Returns:**

dict
SNAP port info for both polarizations:
{
'antenna': str,        # Base antenna number (ANT00001)
'p1': dict or None,    # SNAP info for P1 chain
'p2': dict or None     # SNAP info for P2 chain
}

**Examples:**

```python
>>> ports = get_snap_ports_for_antenna('ANT00001')
>>> ports['p1']['chassis']
1
>>> ports['p2']
None  # P2 chain not assembled yet
```

---

### format_snap_port

**Signature:** `format_snap_port(snap_info: dict) -> str`

Format SNAP port info as human-readable string.

**Parameters:**

snap_info : dict
SNAP port dictionary from get_snap_port_for_chain.

**Returns:**

str
Formatted string like "Chassis 1, Slot A, Port 5".

**Examples:**

```python
>>> info = {'chassis': 1, 'slot': 'A', 'port': 5}
>>> format_snap_port(info)
'Chassis 1, Slot A, Port 5'
```

---

### get_snap_port_mapping

**Signature:** `get_snap_port_mapping(chassis: int, slot: str, port: int) -> Optional[dict]`

Get complete mapping for a SNAP port including network and ADC info. Maps a SNAP hardware location to network configuration, packet routing, and ADC input information.

**Parameters:**

chassis : int
SNAP chassis number (1-4).
slot : str
SNAP slot letter (A-K).
port : int
SNAP port number (0-11).
db_dir : str, optional
Custom database directory for testing.

**Examples:**

```python
>>> mapping = get_snap_port_mapping(1, 'A', 5)
>>> mapping['ip_address']
'192.168.1.1'
>>> mapping['packet_index']
5
>>> mapping['antenna']
'ANT00001'
```

---

## Kernel_Index Module Details

This module provides functions to convert between grid coordinates and kernel indices
used by the correlator. The kernel index is a 0-indexed linear mapping of antenna
positions in the grid, used for correlator processing.

For the core array with 43 rows (N021 to S021) and 6 columns (E01-E06):
- Kernel indices 0-255 map to a 43x6 grid (258 total positions)
- Mapping follows row-major order starting from CN021E01
- Only the first 256 positions are mapped (CS021E05 and CS021E06 are unmapped)

## Constants

### HAS_MATPLOTLIB

**Value:** `False`

## Functions

### grid_to_kernel_index

**Signature:** `grid_to_kernel_index(grid_code: str, array_name: str) -> Optional[int]`

Convert grid coordinate to kernel index.

**Parameters:**

grid_code : str
Grid position code (e.g., 'CN021E01')
array_name : str, optional
Name of array in config (default: 'core')

**Returns:**

int or None
Kernel index (0-255) if position is mapped, None otherwise

**Examples:**

```python
>>> grid_to_kernel_index('CN021E01')
0
>>> grid_to_kernel_index('CN021E06')
5
>>> grid_to_kernel_index('CS021E04')
255
>>> grid_to_kernel_index('CS021E06')  # Not mapped
None
```

---

### kernel_index_to_grid

**Signature:** `kernel_index_to_grid(kernel_idx: int, array_name: str) -> Optional[str]`

Convert kernel index to grid coordinate.

**Parameters:**

kernel_idx : int
Kernel index (0-255)
array_name : str, optional
Name of array in config (default: 'core')

**Returns:**

str or None
Grid position code (e.g., 'CN021E01') if valid, None otherwise

**Examples:**

```python
>>> kernel_index_to_grid(0)
'CN021E01'
>>> kernel_index_to_grid(5)
'CN021E06'
>>> kernel_index_to_grid(255)
'CS021E04'
>>> kernel_index_to_grid(256)  # Out of range
None
```

---

### get_array_index_map

**Signature:** `get_array_index_map(array_name: str) -> 'KernelIndexArray'`

Get complete kernel index mapping with antenna and SNAP port information. This function creates 2D arrays mapping kernel indices to grid coordinates, antenna part numbers, and SNAP port assignments. Arrays are sized according to the array configuration: (north_rows + south_rows + 1) × east_columns.

**Parameters:**

array_name : str, optional
Name of array in config (default: 'core')
db_dir : str, optional
Custom database directory for testing

**Returns:**

KernelIndexArray
Object containing 2D numpy arrays:
- kernel_indices: int array, -1 for unmapped positions
- grid_codes: str array, empty string for invalid positions
- antenna_numbers: str array, empty string for unassigned positions
- snap_ports: object array of tuples (chassis, slot, port), None for unassigned
- snap_board_info: object array of dicts with SNAP board configuration
(ip_address, mac_address, serial_number, feng_id, packet_index, adc_input)
- coordinates: 3D float array of shape (n_rows, n_cols, 3) containing
[latitude, longitude, height] for all grid positions

**Examples:**

```python
>>> kernel_data = get_array_index_map()
>>> kernel_data.shape
(43, 6)
>>> kernel_data.kernel_indices[0, 0]  # CN021E01
0
>>> kernel_data.grid_codes[0, 0]
'CN021E01'
>>> info = kernel_data.get_by_kernel_index(0)
>>> info['grid_code']
'CN021E01'
>>> info['snap_board_info']['ip_address']
'192.168.1.1'
>>> info['snap_board_info']['packet_index']
5
```

---

### get_by_kernel_index

**Signature:** `get_by_kernel_index(kernel_idx: int) -> Optional[dict]`

Get information for a specific kernel index.

**Parameters:**

kernel_idx : int
Kernel index to query (0-255)

**Returns:**

dict or None
Dictionary with keys: 'grid_code', 'antenna_number', 'snap_port',
'snap_board_info', 'ns', 'ew'. Returns None if kernel_idx is out of
range or unmapped.
snap_board_info dict contains: 'ip_address', 'mac_address',
'serial_number', 'feng_id', 'packet_index', 'adc_input'

---

### get_by_grid_code

**Signature:** `get_by_grid_code(grid_code: str) -> Optional[dict]`

Get information for a specific grid code.

**Parameters:**

grid_code : str
Grid code to query (e.g., 'CN021E01')

**Returns:**

dict or None
Dictionary with keys: 'kernel_index', 'antenna_number', 'snap_port',
'snap_board_info', 'ns', 'ew'. Returns None if grid_code not found
or unmapped.
snap_board_info dict contains: 'ip_address', 'mac_address',
'serial_number', 'feng_id', 'packet_index', 'adc_input'

---

### plot_positions

**Signature:** `plot_positions(show: bool)`

Plot grid positions with labeled axes. Shows a scatter plot of all grid positions with coordinates. Labels major rows (S21, S10, C00, N10, N21) and all columns (E01-E06).

**Parameters:**

show : bool, optional
If True, display the plot immediately (default: True).
If False, return the figure and axes for further customization.

**Returns:**

tuple of (fig, ax) if show=False, None otherwise

**Examples:**

```python
>>> array_map = get_array_index_map()
>>> array_map.plot_positions()  # Display plot
>>> fig, ax = array_map.plot_positions(show=False)
>>> ax.set_title('Custom Title')
>>> plt.show()
```

---

## Classes

### KernelIndexArray

**Class:** `KernelIndexArray`

Container for kernel index mapping arrays.

Attributes
----------
kernel_indices : np.ndarray
    2D array of kernel indices, shape (n_rows, n_cols).
    -1 indicates unmapped positions.
grid_codes : np.ndarray
    2D array of grid code strings, shape (n_rows, n_cols).
    Empty string indicates unmapped positions.
antenna_numbers : np.ndarray
    2D array of antenna part numbers, shape (n_rows, n_cols).
    Empty string indicates unassigned positions.
snap_ports : np.ndarray
    2D array of SNAP port tuples (chassis, slot, port), shape (n_rows, n_cols).
    None indicates unassigned or unmapped positions.
snap_board_info : np.ndarray
    2D array of SNAP board configuration dicts, shape (n_rows, n_cols).
    Each dict contains: ip_address, mac_address, serial_number, feng_id, 
    packet_index, adc_input. None for unassigned positions.
coordinates : np.ndarray
    3D array of coordinates, shape (n_rows, n_cols, 3).
    Each position contains [latitude, longitude, height] in decimal degrees and meters.
    Loaded from grid_positions data in the database.
shape : tuple
    Shape of the arrays (n_rows, n_cols).

#### Methods

##### __init__

**Signature:** `__init__(kernel_indices: np.ndarray, grid_codes: np.ndarray, antenna_numbers: np.ndarray, snap_ports: np.ndarray, snap_board_info: Optional[np.ndarray], coordinates: Optional[np.ndarray])`

Initialize kernel index array container.

**Parameters:**

kernel_indices : np.ndarray
2D array of kernel indices
grid_codes : np.ndarray
2D array of grid code strings
antenna_numbers : np.ndarray
2D array of antenna part numbers
snap_ports : np.ndarray
2D array of SNAP port tuples
snap_board_info : np.ndarray, optional
2D array of SNAP board configuration dicts
coordinates : np.ndarray, optional
3D array of shape (n_rows, n_cols, 3) containing [lat, lon, height]

---

##### get_by_kernel_index

**Signature:** `get_by_kernel_index(kernel_idx: int) -> Optional[dict]`

Get information for a specific kernel index.

**Parameters:**

kernel_idx : int
Kernel index to query (0-255)

**Returns:**

dict or None
Dictionary with keys: 'grid_code', 'antenna_number', 'snap_port',
'snap_board_info', 'ns', 'ew'. Returns None if kernel_idx is out of
range or unmapped.
snap_board_info dict contains: 'ip_address', 'mac_address',
'serial_number', 'feng_id', 'packet_index', 'adc_input'

---

##### get_by_grid_code

**Signature:** `get_by_grid_code(grid_code: str) -> Optional[dict]`

Get information for a specific grid code.

**Parameters:**

grid_code : str
Grid code to query (e.g., 'CN021E01')

**Returns:**

dict or None
Dictionary with keys: 'kernel_index', 'antenna_number', 'snap_port',
'snap_board_info', 'ns', 'ew'. Returns None if grid_code not found
or unmapped.
snap_board_info dict contains: 'ip_address', 'mac_address',
'serial_number', 'feng_id', 'packet_index', 'adc_input'

---

##### __repr__

**Signature:** `__repr__() -> str`

String representation of kernel index array.

---

##### plot_positions

**Signature:** `plot_positions(show: bool)`

Plot grid positions with labeled axes. Shows a scatter plot of all grid positions with coordinates. Labels major rows (S21, S10, C00, N10, N21) and all columns (E01-E06).

**Parameters:**

show : bool, optional
If True, display the plot immediately (default: True).
If False, return the figure and axes for further customization.

**Returns:**

tuple of (fig, ax) if show=False, None otherwise

**Examples:**

```python
>>> array_map = get_array_index_map()
>>> array_map.plot_positions()  # Display plot
>>> fig, ax = array_map.plot_positions(show=False)
>>> ax.set_title('Custom Title')
>>> plt.show()
```

---

---

## Array Module Details

This module provides a minimal-dependency interface for working with antenna
positions, coordinates, and baseline calculations. It can be installed
independently of the full CAsMan toolkit.

Classes
-------
AntennaPosition : Dataclass representing a single antenna with all metadata
AntennaArray : Collection of antennas with baseline computation methods

Example
-------
>>> from casman.antenna.array import AntennaArray
>>> array = AntennaArray.from_database('database/parts.db')
>>> ant1 = array.get_antenna('ANT00001')
>>> ant2 = array.get_antenna('ANT00002')
>>> baseline = array.compute_baseline(ant1, ant2)
>>> print(f"Baseline: {baseline:.2f} meters")

## Functions

### sync_database

**Signature:** `sync_database(db_name: str, db_dir: Optional[str]) -> dict`

Download database from GitHub Releases. Uses the same GitHub Releases sync as the antenna module. Falls back to local copy if GitHub unavailable.

**Parameters:**

db_name : str, optional
Database filename to sync (default: 'parts.db')
db_dir : str, optional
Database directory (default: 'database/')

**Returns:**

dict
Sync result with keys:
- 'success': bool - Whether download completed
- 'synced': bool - Whether database was updated
- 'message': str - Human readable status

**Examples:**

```python
>>> from casman.antenna import sync_database, AntennaArray
>>>
>>> result = sync_database('parts.db')
>>> if result['success']:
...     array = AntennaArray.from_database('database/parts.db')
>>>
>>> # Or use sync_first parameter in from_database
>>> array = AntennaArray.from_database('database/parts.db', sync_first=True)
```

---

### has_coordinates

**Signature:** `has_coordinates() -> bool`

Check if this antenna has geographic coordinates.

---

### get_snap_ports

**Signature:** `get_snap_ports() -> dict`

Get SNAP port assignments by tracing assembly chains. Traces the analog signal chain from this antenna through LNA, COAX, and BACKBOARD to determine which SNAP board ports the antenna connects to.

**Returns:**

dict
SNAP port information for both polarizations:
{
'antenna': str,        # Base antenna number (ANT00001)
'p1': dict or None,    # SNAP info for P1 chain
'p2': dict or None     # SNAP info for P2 chain
}
Each polarization dict (if connected) contains:
{
'snap_part': str,      # e.g. 'SNAP1A05'
'chassis': int,        # 1-4
'slot': str,           # A-K
'port': int,           # 0-11
'chain': List[str]     # Full connection chain
}

**Examples:**

```python
>>> ant = array.get_antenna('ANT00001')
>>> ports = ant.get_snap_ports()
>>> if ports['p1']:
...     print(f"P1 connected to {ports['p1']['snap_part']}")
... else:
...     print("P1 chain not complete")
```

---

### format_chain_status

**Signature:** `format_chain_status(polarization: str) -> str`

Format assembly chain status for display. Shows the complete analog signal chain from antenna to SNAP port, or indicates where the chain is incomplete.

**Parameters:**

polarization : str, optional
Polarization to display ('P1' or 'P2'), default 'P1'

**Returns:**

str
Formatted chain status, either:
- "ANT00001P1 → LNA00001P1 → COAX1-001P1 → ... → SNAP1A05"
- "Chain not connected: ANT00001P1 → LNA00001P1 → [disconnected]"

**Examples:**

```python
>>> ant = array.get_antenna('ANT00001')
>>> print(ant.format_chain_status('P1'))
ANT00001P1 → LNA00005P1 → COAX1-023P1 → BACBOARD2-023P1 → SNAP2C04
>>> print(ant.format_chain_status('P2'))
Chain not connected: ANT00001P2 → [not assembled]
```

---

### grid_code

*@property*

**Signature:** `grid_code() -> str`

Get the grid code string (e.g., 'CN002E03').

---

### row_offset

*@property*

**Signature:** `row_offset() -> int`

Get signed row offset (-999 to +999).

---

### east_col

*@property*

**Signature:** `east_col() -> int`

Get zero-based east column index.

---

### from_database

*@classmethod*

**Signature:** `from_database(cls, db_path: str | Path, array_id: str, db_dir: Optional[str], sync_first: bool) -> AntennaArray`

Load antenna array from CAsMan database.

**Parameters:**

db_path : str or Path
Path to parts.db database file
array_id : str, optional
Array identifier to load (default: 'C' for core array)
db_dir : str, optional
Database directory for assembly chain lookups (default: use parent of db_path)
sync_first : bool, optional
If True, download database from GitHub Releases before loading (default: False)

**Returns:**

AntennaArray
Loaded antenna array object

**Raises:**

FileNotFoundError
If database file doesn't exist (and sync_first=False)
sqlite3.Error
If database query fails

**Examples:**

```python
>>> # Load from local database
>>> array = AntennaArray.from_database('database/parts.db')
>>>
>>> # Download from GitHub Releases first
>>> array = AntennaArray.from_database('database/parts.db', sync_first=True)
>>>
>>> # Load specific array
>>> array = AntennaArray.from_database('database/parts.db', array_id='C')
```

---

### get_antenna

**Signature:** `get_antenna(antenna_number: str) -> Optional[AntennaPosition]`

Get antenna by part number.

**Parameters:**

antenna_number : str
Antenna part number (e.g., 'ANT00001')

**Returns:**

AntennaPosition or None
Antenna position if found, None otherwise

---

### get_antenna_at_position

**Signature:** `get_antenna_at_position(grid_code: str) -> Optional[AntennaPosition]`

Get antenna at specific grid position.

**Parameters:**

grid_code : str
Grid position code (e.g., 'CN002E03')

**Returns:**

AntennaPosition or None
Antenna at position if found, None otherwise

---

### compute_baseline

**Signature:** `compute_baseline(ant1: AntennaPosition, ant2: AntennaPosition, use_coordinates: bool) -> float`

Compute baseline distance between two antennas.

**Parameters:**

ant1 : AntennaPosition
First antenna
ant2 : AntennaPosition
Second antenna
use_coordinates : bool, optional
If True and coordinates available, compute geodetic distance.
If False or coordinates unavailable, compute grid spacing distance.
Default: True

**Returns:**

float
Baseline distance in meters

**Examples:**

```python
>>> ant1 = array.get_antenna('ANT00001')
>>> ant2 = array.get_antenna('ANT00002')
>>> baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)
```

---

### compute_all_baselines

**Signature:** `compute_all_baselines(use_coordinates: bool, include_self: bool) -> List[Tuple[str, str, float]]`

Compute all pairwise baselines.

**Parameters:**

use_coordinates : bool, optional
Whether to use geographic coordinates (default: True)
include_self : bool, optional
Whether to include zero-length self-baselines (default: False)

**Returns:**

list of tuple
List of (ant1_number, ant2_number, baseline_meters) tuples

**Examples:**

```python
>>> baselines = array.compute_all_baselines()
>>> for ant1, ant2, dist in baselines[:5]:
...     print(f"{ant1} - {ant2}: {dist:.2f} m")
```

---

### filter_by_coordinates

**Signature:** `filter_by_coordinates(has_coords: bool) -> List[AntennaPosition]`

Filter antennas by coordinate availability.

**Parameters:**

has_coords : bool, optional
If True, return antennas with coordinates.
If False, return antennas without coordinates.
Default: True

**Returns:**

list of AntennaPosition
Filtered antenna list

---

## Classes

### AntennaPosition

*@dataclass*

**Class:** `AntennaPosition`

Complete antenna position information including coordinates and SNAP mapping.

Attributes
----------
antenna_number : str
    Base antenna number without polarization (e.g., 'ANT00001')
grid_position : AntennaGridPosition
    Parsed grid position object with row/column offsets
latitude : float, optional
    Latitude in decimal degrees (WGS84 or other coordinate system)
longitude : float, optional
    Longitude in decimal degrees
height : float, optional
    Height/elevation in meters above reference
coordinate_system : str, optional
    Coordinate system identifier (e.g., 'WGS84', 'local')
assigned_at : str, optional
    ISO timestamp of position assignment
notes : str, optional
    Field notes or comments
db_dir : str, optional
    Database directory path for chain lookups (internal use)

Methods
-------
has_coordinates() : bool
    Check if geographic coordinates are available
get_snap_ports() : dict
    Get SNAP port assignments for both polarizations by tracing assembly chains
format_chain_status(polarization='P1') : str
    Format the assembly chain status for display

#### Methods

##### has_coordinates

**Signature:** `has_coordinates() -> bool`

Check if this antenna has geographic coordinates.

---

##### get_snap_ports

**Signature:** `get_snap_ports() -> dict`

Get SNAP port assignments by tracing assembly chains. Traces the analog signal chain from this antenna through LNA, COAX, and BACKBOARD to determine which SNAP board ports the antenna connects to.

**Returns:**

dict
SNAP port information for both polarizations:
{
'antenna': str,        # Base antenna number (ANT00001)
'p1': dict or None,    # SNAP info for P1 chain
'p2': dict or None     # SNAP info for P2 chain
}
Each polarization dict (if connected) contains:
{
'snap_part': str,      # e.g. 'SNAP1A05'
'chassis': int,        # 1-4
'slot': str,           # A-K
'port': int,           # 0-11
'chain': List[str]     # Full connection chain
}

**Examples:**

```python
>>> ant = array.get_antenna('ANT00001')
>>> ports = ant.get_snap_ports()
>>> if ports['p1']:
...     print(f"P1 connected to {ports['p1']['snap_part']}")
... else:
...     print("P1 chain not complete")
```

---

##### format_chain_status

**Signature:** `format_chain_status(polarization: str) -> str`

Format assembly chain status for display. Shows the complete analog signal chain from antenna to SNAP port, or indicates where the chain is incomplete.

**Parameters:**

polarization : str, optional
Polarization to display ('P1' or 'P2'), default 'P1'

**Returns:**

str
Formatted chain status, either:
- "ANT00001P1 → LNA00001P1 → COAX1-001P1 → ... → SNAP1A05"
- "Chain not connected: ANT00001P1 → LNA00001P1 → [disconnected]"

**Examples:**

```python
>>> ant = array.get_antenna('ANT00001')
>>> print(ant.format_chain_status('P1'))
ANT00001P1 → LNA00005P1 → COAX1-023P1 → BACBOARD2-023P1 → SNAP2C04
>>> print(ant.format_chain_status('P2'))
Chain not connected: ANT00001P2 → [not assembled]
```

---

##### grid_code

*@property*

**Signature:** `grid_code() -> str`

Get the grid code string (e.g., 'CN002E03').

---

##### row_offset

*@property*

**Signature:** `row_offset() -> int`

Get signed row offset (-999 to +999).

---

##### east_col

*@property*

**Signature:** `east_col() -> int`

Get zero-based east column index.

---

---

### AntennaArray

**Class:** `AntennaArray`

Collection of antenna positions with baseline computation capabilities.

This class provides efficient access to antenna metadata and methods for
computing baselines between antenna pairs. It can load data from a CAsMan
database or be constructed programmatically.

Parameters
----------
antennas : list of AntennaPosition
    List of antenna position objects

Attributes
----------
antennas : list of AntennaPosition
    All loaded antenna positions

Methods
-------
from_database(db_path, array_id='C') : AntennaArray
    Load antenna array from CAsMan database
get_antenna(antenna_number) : AntennaPosition or None
    Retrieve antenna by part number
get_antenna_at_position(grid_code) : AntennaPosition or None
    Retrieve antenna by grid position
compute_baseline(ant1, ant2, use_coordinates=True) : float
    Compute baseline distance between two antennas
compute_all_baselines(use_coordinates=True) : list of tuple
    Compute all pairwise baselines
filter_by_coordinates(has_coords=True) : list of AntennaPosition
    Filter antennas based on coordinate availability

Examples
--------
>>> array = AntennaArray.from_database('database/parts.db')
>>> print(f"Loaded {len(array.antennas)} antennas")
>>>
>>> # Get specific antenna
>>> ant = array.get_antenna('ANT00001')
>>> print(f"{ant.antenna_number} at {ant.grid_code}")
>>>
>>> # Compute baseline
>>> ant1 = array.get_antenna('ANT00001')
>>> ant2 = array.get_antenna('ANT00002')
>>> baseline = array.compute_baseline(ant1, ant2)
>>> print(f"Baseline: {baseline:.2f} m")

#### Methods

##### __init__

**Signature:** `__init__(antennas: List[AntennaPosition])`

Initialize antenna array with list of positions.

**Parameters:**

antennas : list of AntennaPosition
Antenna position objects to include in array

---

##### from_database

*@classmethod*

**Signature:** `from_database(cls, db_path: str | Path, array_id: str, db_dir: Optional[str], sync_first: bool) -> AntennaArray`

Load antenna array from CAsMan database.

**Parameters:**

db_path : str or Path
Path to parts.db database file
array_id : str, optional
Array identifier to load (default: 'C' for core array)
db_dir : str, optional
Database directory for assembly chain lookups (default: use parent of db_path)
sync_first : bool, optional
If True, download database from GitHub Releases before loading (default: False)

**Returns:**

AntennaArray
Loaded antenna array object

**Raises:**

FileNotFoundError
If database file doesn't exist (and sync_first=False)
sqlite3.Error
If database query fails

**Examples:**

```python
>>> # Load from local database
>>> array = AntennaArray.from_database('database/parts.db')
>>>
>>> # Download from GitHub Releases first
>>> array = AntennaArray.from_database('database/parts.db', sync_first=True)
>>>
>>> # Load specific array
>>> array = AntennaArray.from_database('database/parts.db', array_id='C')
```

---

##### get_antenna

**Signature:** `get_antenna(antenna_number: str) -> Optional[AntennaPosition]`

Get antenna by part number.

**Parameters:**

antenna_number : str
Antenna part number (e.g., 'ANT00001')

**Returns:**

AntennaPosition or None
Antenna position if found, None otherwise

---

##### get_antenna_at_position

**Signature:** `get_antenna_at_position(grid_code: str) -> Optional[AntennaPosition]`

Get antenna at specific grid position.

**Parameters:**

grid_code : str
Grid position code (e.g., 'CN002E03')

**Returns:**

AntennaPosition or None
Antenna at position if found, None otherwise

---

##### compute_baseline

**Signature:** `compute_baseline(ant1: AntennaPosition, ant2: AntennaPosition, use_coordinates: bool) -> float`

Compute baseline distance between two antennas.

**Parameters:**

ant1 : AntennaPosition
First antenna
ant2 : AntennaPosition
Second antenna
use_coordinates : bool, optional
If True and coordinates available, compute geodetic distance.
If False or coordinates unavailable, compute grid spacing distance.
Default: True

**Returns:**

float
Baseline distance in meters

**Examples:**

```python
>>> ant1 = array.get_antenna('ANT00001')
>>> ant2 = array.get_antenna('ANT00002')
>>> baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)
```

---

##### compute_all_baselines

**Signature:** `compute_all_baselines(use_coordinates: bool, include_self: bool) -> List[Tuple[str, str, float]]`

Compute all pairwise baselines.

**Parameters:**

use_coordinates : bool, optional
Whether to use geographic coordinates (default: True)
include_self : bool, optional
Whether to include zero-length self-baselines (default: False)

**Returns:**

list of tuple
List of (ant1_number, ant2_number, baseline_meters) tuples

**Examples:**

```python
>>> baselines = array.compute_all_baselines()
>>> for ant1, ant2, dist in baselines[:5]:
...     print(f"{ant1} - {ant2}: {dist:.2f} m")
```

---

##### filter_by_coordinates

**Signature:** `filter_by_coordinates(has_coords: bool) -> List[AntennaPosition]`

Filter antennas by coordinate availability.

**Parameters:**

has_coords : bool, optional
If True, return antennas with coordinates.
If False, return antennas without coordinates.
Default: True

**Returns:**

list of AntennaPosition
Filtered antenna list

---

##### __repr__

**Signature:** `__repr__() -> str`

String representation.

---

---
