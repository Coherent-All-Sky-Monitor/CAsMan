# CAsMan Database Documentation

Complete guide to CAsMan's database system, including schema, backup/sync, and maintenance.

## Table of Contents

1. [Overview](#overview)
2. [Database Schema](#database-schema)
<<<<<<< HEAD
3. [Database Synchronization](#database-synchronization)
4. [Implementation Details](#implementation-details)
=======

>>>>>>> 3af716335635dd47079f2f570bffe22cc46c5cd3

---

## Overview

CAsMan uses **SQLite** databases to manage parts inventory, assembly tracking, and antenna positions. The system includes:

- **Two main databases**: `parts.db` and `assembled_casm.db`
- **GitHub-based sync**: Download database releases from GitHub
- **Multi-user access**: Centralized database distribution via GitHub Releases
- **Offline-first**: Works without internet connection

### Database Files

1. **`parts.db`** - Parts inventory, antenna positions, and SNAP board configurations (~400 KB)
2. **`assembled_casm.db`** - Assembly tracking and connections (~10 MB)
3. **`grid_positions.csv`** - Geographic coordinates (CSV, not SQLite)
4. **`snap_boards.csv`** - SNAP board configurations with F-engine IDs (CSV, not SQLite)

### Database Location

Default location: `database/` in project root

Can be customized via:
- Environment variable: `CASMAN_DATABASE_DIR`
- Configuration file: `config.yaml`
- Command-line parameter in functions

---

## Database Schema

### Database 1: `parts.db`

Main inventory database for tracking individual parts and antenna grid positions.

#### Table: `parts`

Stores information about all individual parts in the system.

##### Schema

```sql
CREATE TABLE parts (
    id INTEGER PRIMARY KEY,
    part_number TEXT UNIQUE,
    part_type TEXT,
    polarization TEXT,
    date_created TEXT,
    date_modified TEXT
)
```

##### Column Descriptions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| `part_number` | TEXT | UNIQUE | Unique part identifier (e.g., `ANT00001P1`, `LNA00042P2`) |
| `part_type` | TEXT | - | Type of part: `ANTENNA`, `LNA`, `COAXSHORT`, `COAXLONG`, `BACBOARD`, `SNAP` |
| `polarization` | TEXT | - | Polarization: `P1` or `P2` for dual-pol parts, `NULL` for single parts |
| `date_created` | TEXT | - | ISO 8601 timestamp when part was first added |
| `date_modified` | TEXT | - | ISO 8601 timestamp of last modification |

##### Part Number Formats

- **Antenna**: `ANT{5-digit}P{1|2}` (e.g., `ANT00001P1`)
- **LNA**: `LNA{5-digit}P{1|2}` (e.g., `LNA00042P2`)
- **COAXSHORT**: `CXS{5-digit}P{1|2}` (e.g., `CXS00123P1`)
- **COAXLONG**: `CXL{5-digit}P{1|2}` (e.g., `CXL00456P2`)
- **BACBOARD**: `BAC{5-digit}P{1|2}` (e.g., `BAC00789P1`)
- **SNAP**: `SNAP{chassis:02d}{slot:02d}{port:02d}` (e.g., `SNAP010203`)

##### Example Data

```sql
INSERT INTO parts VALUES 
    (1, 'ANT00001P1', 'ANTENNA', 'P1', '2025-01-15T10:30:00Z', '2025-01-15T10:30:00Z'),
    (2, 'ANT00001P2', 'ANTENNA', 'P2', '2025-01-15T10:30:00Z', '2025-01-15T10:30:00Z'),
    (3, 'LNA00042P1', 'LNA', 'P1', '2025-01-16T14:20:00Z', '2025-01-16T14:20:00Z'),
    (4, 'SNAP010203', 'SNAP', NULL, '2025-01-17T09:15:00Z', '2025-01-17T09:15:00Z');
```

##### Common Queries

```sql
-- Get all antennas
SELECT * FROM parts WHERE part_type = 'ANTENNA';

-- Get parts by polarization
SELECT * FROM parts WHERE polarization = 'P1';

-- Find a specific part
SELECT * FROM parts WHERE part_number = 'ANT00001P1';

-- Count parts by type
SELECT part_type, COUNT(*) as count FROM parts GROUP BY part_type;

-- Get recently added parts (last 7 days)
SELECT * FROM parts 
WHERE date_created >= datetime('now', '-7 days')
ORDER BY date_created DESC;
```

#### Table: `antenna_positions`

Maps antenna base numbers to grid positions and optionally stores geographic coordinates.

##### Schema

```sql
CREATE TABLE antenna_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    antenna_number TEXT UNIQUE NOT NULL,
    array_id TEXT NOT NULL,
    row_offset INTEGER NOT NULL CHECK(row_offset BETWEEN -999 AND 999),
    east_col INTEGER NOT NULL CHECK(east_col BETWEEN 0 AND 99),
    grid_code TEXT UNIQUE NOT NULL,
    assigned_at TEXT NOT NULL,
    notes TEXT,
    latitude REAL,
    longitude REAL,
    height REAL,
    coordinate_system TEXT,
    UNIQUE(array_id, row_offset, east_col)
)
```

##### Column Descriptions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| `antenna_number` | TEXT | UNIQUE, NOT NULL | Base antenna number without polarization (e.g., `ANT00001`) |
| `array_id` | TEXT | NOT NULL | Array identifier: `C` (core), `N` (north), `S` (south) |
| `row_offset` | INTEGER | NOT NULL, -999 to 999 | North-south row offset from center (0 = center) |
| `east_col` | INTEGER | NOT NULL, 0 to 99 | East-west column index (0 = westernmost) |
| `grid_code` | TEXT | UNIQUE, NOT NULL | Canonical position string (e.g., `CN002E03`) |
| `assigned_at` | TEXT | NOT NULL | ISO 8601 timestamp of position assignment |
| `notes` | TEXT | - | Optional notes about the position or assignment |
| `latitude` | REAL | - | Latitude in decimal degrees (WGS84 or other system) |
| `longitude` | REAL | - | Longitude in decimal degrees (WGS84 or other system) |
| `height` | REAL | - | Height in meters above reference surface |
| `coordinate_system` | TEXT | - | Coordinate system name (e.g., `WGS84`, `local`) |

##### Grid Code Format

Format: `{array_id}{direction}{row:03d}E{col:02d}`

- **Array ID**: `C`, `N`, or `S`
- **Direction**: `N` (north/positive) or `S` (south/negative)
- **Row**: 3-digit row offset (e.g., `002` for row +2, `021` for row -21)
- **Column**: 2-digit column index (e.g., `01` for first column)

Examples:
- `CN002E03` - Core array, North row +2, East column 3
- `CS021E01` - Core array, South row -21, East column 1
- `CC000E01` - Core array, Center row 0, East column 1

##### Common Queries

```sql
-- Get position for specific antenna
SELECT * FROM antenna_positions WHERE antenna_number = 'ANT00001';

-- Get antenna at specific grid position
SELECT * FROM antenna_positions WHERE grid_code = 'CN002E03';

-- Get all positions with coordinates
SELECT * FROM antenna_positions 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Get positions in specific row
SELECT * FROM antenna_positions WHERE row_offset = 2;

-- Get all core array positions
SELECT * FROM antenna_positions WHERE array_id = 'C';
```

#### Table: `snap_boards`

Stores SNAP board configurations including serial numbers, network information, and F-engine IDs.

##### Schema

```sql
CREATE TABLE snap_boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chassis INTEGER NOT NULL CHECK(chassis BETWEEN 1 AND 4),
    slot TEXT NOT NULL CHECK(slot IN ('A','B','C','D','E','F','G','H','I','J','K')),
    serial_number TEXT UNIQUE NOT NULL,
    mac_address TEXT UNIQUE NOT NULL,
    ip_address TEXT UNIQUE NOT NULL,
    feng_id INTEGER UNIQUE NOT NULL CHECK(feng_id BETWEEN 0 AND 43),
    notes TEXT,
    date_added TEXT NOT NULL,
    date_modified TEXT,
    UNIQUE(chassis, slot)
)
```

##### Column Descriptions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| `chassis` | INTEGER | NOT NULL, 1-4 | Chassis number (1-4) |
| `slot` | TEXT | NOT NULL, A-K | Slot letter (A-K, 11 slots per chassis) |
| `serial_number` | TEXT | UNIQUE, NOT NULL | Board serial number (e.g., SN01) |
| `mac_address` | TEXT | UNIQUE, NOT NULL | Board MAC address |
| `ip_address` | TEXT | UNIQUE, NOT NULL | Board IP address |
| `feng_id` | INTEGER | UNIQUE, NOT NULL, 0-43 | F-engine ID for packet routing |
| `notes` | TEXT | - | Optional notes about the board |
| `date_added` | TEXT | NOT NULL | ISO 8601 timestamp when record was added |
| `date_modified` | TEXT | - | ISO 8601 timestamp of last modification |

##### Packet Index Calculation

Each SNAP port has a unique packet index calculated as:

```
packet_index = feng_id × 12 + port_number
```

**Examples:**
- SNAP1A (feng_id=0), port 5: packet_index = 0×12+5 = 5
- SNAP1A (feng_id=0), port 11: packet_index = 0×12+11 = 11
- SNAP2A (feng_id=11), port 0: packet_index = 11×12+0 = 132
- SNAP2A (feng_id=11), port 5: packet_index = 11×12+5 = 137
- SNAP4K (feng_id=43), port 11: packet_index = 43×12+11 = 527

##### Configuration Management

```bash
# Generate SNAP board CSV
python scripts/generate_snap_boards.py

# Load into database
casman database load-snap-boards
```

##### Common Queries

```sql
-- Get board info for specific chassis and slot
SELECT * FROM snap_boards WHERE chassis = 1 AND slot = 'A';

-- Get board by serial number
SELECT * FROM snap_boards WHERE serial_number = 'SN01';

-- Get board by F-engine ID
SELECT * FROM snap_boards WHERE feng_id = 11;

-- Calculate packet index for specific port
SELECT 
    chassis, slot, feng_id,
    (feng_id * 12 + 5) as packet_index_port5,
    (feng_id * 12 + 0) as packet_index_port0,
    (feng_id * 12 + 11) as packet_index_port11
FROM snap_boards;

-- Get all boards in chassis 2
SELECT * FROM snap_boards WHERE chassis = 2 ORDER BY slot;

-- Get network configuration summary
SELECT chassis, slot, serial_number, ip_address, feng_id 
FROM snap_boards 
ORDER BY chassis, slot;
```

### Database 2: `assembled_casm.db`

Tracks assembled connections between parts in the signal chain.

#### Table: `assembly`

Records connections between parts (e.g., Antenna → LNA → Coax → SNAP).

##### Schema

```sql
CREATE TABLE assembly (
    id INTEGER PRIMARY KEY,
    part_number TEXT,
    part_type TEXT,
    polarization TEXT,
    scan_time TEXT,
    connected_to TEXT,
    connected_to_type TEXT,
    connected_polarization TEXT,
    connected_scan_time TEXT,
    connection_status TEXT DEFAULT 'connected'
)
```

##### Valid Signal Chain

```
ANTENNA → LNA → COAXSHORT → COAXLONG → BACBOARD → SNAP
```

Each connection must follow this sequence. Polarizations must match (P1→P1, P2→P2).

##### Common Queries

```sql
-- Get all connections for a part
SELECT * FROM assembly WHERE part_number = 'ANT00001P1';

-- Find what a part is connected to
SELECT connected_to, connected_to_type 
FROM assembly 
WHERE part_number = 'ANT00001P1' AND connection_status = 'connected';

-- Get complete chain for an antenna
WITH RECURSIVE chain AS (
    SELECT * FROM assembly WHERE part_number = 'ANT00001P1'
    UNION ALL
    SELECT a.* FROM assembly a
    INNER JOIN chain c ON a.part_number = c.connected_to
    WHERE a.connection_status = 'connected'
)
SELECT * FROM chain;
```

### File: `grid_positions.csv`

CSV file for managing geographic coordinates of antenna grid positions.

Coordinates are stored in decimal degrees with up to 9 decimal places (WGS84). The generator in [scripts/generate_grid_coordinates.py](scripts/generate_grid_coordinates.py) writes [database/grid_positions.csv](database/grid_positions.csv) using fixed 9-decimal precision.

#### Format

```csv
grid_code,latitude,longitude,height,coordinate_system,notes
CN021E01,37.871899000,-122.258477000,10.5,WGS84,Survey point 1
CN021E02,37.871912000,-122.258321000,10.6,WGS84,Survey point 2
```

#### Usage

```bash
# Generate coordinates from survey reference point
python scripts/generate_grid_coordinates.py

# Visualize generated coordinates
python scripts/plot_grid_positions.py

# Load coordinates into database
casman database load-coordinates
```

### File: `snap_boards.csv`

CSV file for managing SNAP board configurations including serial numbers, network settings, and F-engine IDs.

#### Format

```csv
chassis,slot,sn,mac,ip,feng_id,notes
1,A,SN01,00:11:22:33:01:00,192.168.1.1,0,Generated on 2025-12-17
1,B,SN02,00:11:22:33:01:01,192.168.1.2,1,Generated on 2025-12-17
2,A,SN12,00:11:22:33:02:00,192.168.1.12,11,Generated on 2025-12-17
4,K,SN44,00:11:22:33:04:0A,192.168.1.44,43,Generated on 2025-12-17
```

#### Column Descriptions

| Column | Description | Example |
|--------|-------------|---------|
| `chassis` | Chassis number (1-4) | `1` |
| `slot` | Slot letter (A-K) | `A` |
| `sn` | Serial number | `SN01` |
| `mac` | MAC address | `00:11:22:33:01:00` |
| `ip` | IP address | `192.168.1.1` |
| `feng_id` | F-engine ID (0-43) | `0` |
| `notes` | Optional notes | `Generated on 2025-12-17` |

#### Configuration Details

- **Total boards**: 44 (4 chassis × 11 slots)
- **F-engine IDs**: 0-43 (sequential, one per board)
- **Packet index formula**: `feng_id × 12 + port_number`
- **Port range**: 0-11 (12 ports per board)
- **Total packet indices**: 0-527 (44 boards × 12 ports)

#### Packet Index Examples

| Board | F-engine ID | Port | Packet Index | Calculation |
|-------|-------------|------|--------------|-------------|
| SNAP1A | 0 | 0 | 0 | 0×12+0 |
| SNAP1A | 0 | 5 | 5 | 0×12+5 |
| SNAP1A | 0 | 11 | 11 | 0×12+11 |
| SNAP2A | 11 | 0 | 132 | 11×12+0 |
| SNAP2A | 11 | 5 | 137 | 11×12+5 |
| SNAP4K | 43 | 11 | 527 | 43×12+11 |

#### Usage

```bash
# Generate SNAP board CSV with dummy data
python scripts/generate_snap_boards.py

# Load configurations into database
casman database load-snap-boards

# Load from custom CSV
casman database load-snap-boards --csv custom_boards.csv
```

#### Visualization Integration

SNAP board information is displayed in all three web visualizations:

1. **Chains Visualization** - Shows SN, F-engine ID, packet index, MAC, IP inline for SNAP parts
2. **Core Grid Visualization** - Displays board info in antenna detail panel
3. **SNAP Ports Visualization** - Click any port to see modal with complete board configuration

---

<<<<<<< HEAD
## Database Synchronization

CAsMan provides database synchronization via **GitHub Releases**, enabling multi-user access to centralized database files without requiring cloud storage credentials.

### Features

- **Public Access**: Download database releases from GitHub without authentication
- **Version Control**: Tagged releases with semantic versioning
- **Multi-User Distribution**: Centralized database files accessible to all users
- **Offline-First**: Works without internet connection, sync when available
- **Simple Setup**: No cloud credentials required for client downloads

### Storage Locations

**Full CAsMan installation:**
- Downloads to project `database/` directory
- Automatic timestamped backups before overwriting
- Example: `database/assembled_casm.db.20260126-221500.bak`

**Standalone antenna module (pip install):**
- Downloads to XDG standard location: `~/.local/share/casman/databases/`
- Automatic backups on overwrite

### Quick Start

#### 1. Download Latest Database

```bash
# Download latest database from GitHub
casman database pull

# Force re-download even if up-to-date
casman database pull --force
```

This downloads the latest database release from GitHub to your project `database/` directory (full install) or `~/.local/share/casman/databases/` (standalone antenna module). Creates automatic timestamped backups before overwriting existing files.

#### 2. Restore from Backups (if needed)

```bash
# Restore both databases from latest backups
casman database restore --latest

# Restore only parts.db
casman database restore --latest --parts

# Restore only assembled_casm.db
casman database restore --latest --assembled
```

Backups are created automatically during pulls with names like `assembled_casm.db.20260126-221500.bak`.

#### 3. Check Sync Status

```bash
casman database status
```

Shows:
- Current GitHub Release version
- Local database status and sizes
- Download location
- Last sync check time

#### 4. Verify Setup

The `AntennaArray` class can automatically sync on initialization:

```python
from casman.antenna import AntennaArray

# Automatically downloads latest database if needed
array = AntennaArray.from_database(
    'database/parts.db',
    sync_first=True  # Downloads from GitHub if not present locally
)
```

**You're all set!** The database will be synced from GitHub Releases when needed. Automatic backups are created during each sync to protect your local data.

### Multi-User Workflow

#### For Database Administrators (Upload Access)

1. **Upload Updated Database**:
   ```bash
   casman database push
   ```
   - Requires GitHub authentication token
   - Creates new GitHub Release with database files
   - Tags release with timestamp

2. **Verify Upload**:
   ```bash
   casman database status
   ```

#### For Field Users (Download Access)

1. **Download Latest Database**:
   ```bash
   casman database pull
   ```
   - No authentication required
   - Downloads from public GitHub Release

2. **Use in Scripts**:
   ```python
   from casman.antenna import AntennaArray
   
   # Sync and load database
   array = AntennaArray.from_database(
       'database/parts.db',
       sync_first=True
   )
   ```

### CLI Commands Reference

| Command | Description | Authentication Required |
|---------|-------------|-------------------------|
| `casman database pull` | Download latest database from GitHub | No |
| `casman database push` | Upload database to GitHub Releases | Yes (GitHub token) |
| `casman database status` | Show sync status and GitHub Release info | No |

### Configuration

In `config.yaml`:

```yaml
database:
  sync:
    enabled: true
    backend: github
  github:
    repo: "username/CAsMan"
    token_env: "GITHUB_TOKEN"  # Environment variable for upload token
```

### GitHub Authentication (Upload Only)

For database administrators who need to upload:

1. **Create GitHub Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` scope

2. **Set Environment Variable**:
   ```bash
   export GITHUB_TOKEN="your-github-token"
   ```

3. **Upload Database**:
   ```bash
   casman database push
   ```

**Note**: Field users downloading databases do NOT need authentication.

---

## Download Location

Downloaded databases are stored in:
- **macOS/Linux**: `~/.local/share/casman/databases/`
- **Windows**: `%LOCALAPPDATA%\casman\databases\`

The `AntennaArray.from_database()` method with `sync_first=True` will:
1. Check if database exists locally
2. If not found, download from latest GitHub Release
3. Extract to the appropriate local directory
4. Load the database for use

---

## Implementation Details

### Core Components

#### 1. GitHub Sync Module (`casman/database/github_sync.py`)

**GitHubSyncManager**: Main class for database synchronization
- Download databases from GitHub Releases to local cache
- Upload databases to GitHub Releases (requires authentication)
- List available releases with metadata
- Checksum validation for integrity
- Public access downloads (no authentication required)

**Configuration Management**:
- Loads from config.yaml and environment variables
- Supports GitHub Releases backend only
- Configurable repository and authentication

#### 2. Database Download Integration

**AntennaArray** (`casman/antenna/array.py`):
- `sync_first=True` parameter downloads database before loading
- Uses GitHubSyncManager to fetch from GitHub Releases
- Extracts to `~/.local/share/casman/databases/`
- Falls back to local database if sync fails or offline

**Auto-sync on Install** (`casman/__init__.py`):
- Downloads database on first import if not present
- Silent failure if offline (works without database)

#### 3. CLI Commands

Complete command-line interface via `casman/cli/database_commands.py`:
- `casman database pull` - Download latest database from GitHub
- `casman database push` - Upload database to GitHub Releases (requires token)
- `casman database status` - Show current sync status and GitHub Release info

### Files Modified

**Modified Files:**
- `casman/database/github_sync.py` - GitHub sync implementation
- `casman/database/__init__.py` - Export GitHubSyncManager
- `casman/__init__.py` - Auto-sync on install
- `casman/cli/main.py` - Register database commands
- `casman/cli/database_commands.py` - CLI commands for sync
- `casman/antenna/array.py` - Database sync on load
- `config.yaml` - GitHub sync configuration
- `requirements.txt` - Added requests for GitHub API

### System Architecture

The sync system provides database distribution via GitHub Releases:

```
┌────────────────────────────────────┐
│  Local Databases                   │
│  - parts.db (~340 KB)              │
│  - assembled_casm.db (~10 MB)      │
│  - Located in project database/    │
└────────────────────────────────────┘
         ↕ Upload (requires GitHub token)
┌────────────────────────────────────┐
│  GitHub Releases                   │
│  - Public download access          │
│  - Versioned releases              │
│  - Tag-based organization          │
└────────────────────────────────────┘
         ↕ Download (public, no auth)
┌────────────────────────────────────┐
│  Field Sites / Remote Users        │
│  - ~/.local/share/casman/databases │
│  - Offline-capable                 │
└────────────────────────────────────┘
```

---

## Summary

CAsMan's database system provides:

- **Schema**: SQLite databases (parts.db, assembled_casm.db) with well-defined structure  
- **Sync**: GitHub Releases-based distribution for multi-user access  
- **Public Access**: Download databases without authentication  
- **Versioned**: Tagged releases with semantic versioning  
- **Offline**: Fully functional without internet connection  
- **Simple**: No cloud credentials required for client downloads  

### Quick Actions

**Setup** (1 minute):
```bash
casman database pull
```

**Daily Use**:
- Work normally with local databases
- `casman database pull` to get latest version when needed
- Databases auto-sync when using `AntennaArray.from_database(..., sync_first=True)`

**For Database Administrators**:
```bash
# Upload updated database
export GITHUB_TOKEN="your-token"
casman database push
```
=======
>>>>>>> 3af716335635dd47079f2f570bffe22cc46c5cd3
