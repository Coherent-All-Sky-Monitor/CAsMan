# CAsMan Database Documentation

Complete guide to CAsMan's database system, including schema, backup/sync, and maintenance.

## Table of Contents

1. [Overview](#overview)
2. [Database Schema](#database-schema)
3. [Backup & Synchronization](#backup--synchronization)
4. [R2 Storage Class Maintenance](#r2-storage-class-maintenance)
5. [R2 Quota Enforcement](#r2-quota-enforcement)
6. [Implementation Details](#implementation-details)

---

## Overview

CAsMan uses **SQLite** databases to manage parts inventory, assembly tracking, and antenna positions. The system includes:

- **Two main databases**: `parts.db` and `assembled_casm.db`
- **Cloud backup system**: Cloudflare R2 or AWS S3
- **Automatic backups**: Triggered on critical operations
- **Multi-user sync**: Version-controlled cloud storage
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
- **Column**: 2-digit column index (e.g., `00` for first column)

Examples:
- `CN002E03` - Core array, North row +2, East column 3
- `CS021E00` - Core array, South row -21, East column 0
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

#### Format

```csv
grid_code,latitude,longitude,height,coordinate_system,notes
CN021E00,37.871899,-122.258477,10.5,WGS84,Survey point 1
CN021E01,37.871912,-122.258321,10.6,WGS84,Survey point 2
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

## Backup & Synchronization

CAsMan provides a robust cloud-based database backup and synchronization system designed for zero data loss and multi-user collaboration.

### Features

- **Automatic Backups**: Triggered on part generation and assembly operations
- **Versioned Storage**: Keep multiple backup versions with timestamps
- **Cloud Storage**: Cloudflare R2 (recommended) or AWS S3
- **Zero Data Loss**: Critical operations automatically backed up
- **Multi-User Safe**: Timestamp-based versioning prevents conflicts
- **Offline-First**: Graceful degradation when offline

### Quick Start

#### 1. Install Dependencies

```bash
pip install boto3
```

#### 2. Create Cloudflare R2 Bucket

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com) → **R2 Object Storage**
2. Click **Create bucket** → Name it `casman-databases`
3. Go to **Manage R2 API Tokens** → **Create API Token**
4. Set permissions: **Object Read & Write** for `casman-databases`
5. Save the credentials

#### 3. Configure Credentials

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# CAsMan R2 Backup
export R2_ACCOUNT_ID="your-account-id-here"
export R2_ACCESS_KEY_ID="your-access-key-here"
export R2_SECRET_ACCESS_KEY="your-secret-key-here"
```

Reload your shell:

```bash
source ~/.zshrc
```

#### 4. Verify Setup

```bash
casman sync status
```

Should show:

```
Backend Status:
  ✓ R2 backend initialized
```

#### 5. Create First Backup

```bash
casman sync backup
```

**You're all set!** Backups will now happen automatically. Use `casman sync status` to check your configuration.

### Automatic Backups

Backups are triggered automatically:

1. **After Part Generation**: Every time you generate parts
   ```bash
   casman parts add ANTENNA 10 1  # → Auto backup
   ```

2. **After Assembly Operations**: Every 10 operations OR every 24 hours (whichever comes first)
   - Connect/disconnect parts
   - Assign/remove antenna positions
   - Scanning operations

**Configuration** (`config.yaml`):

```yaml
database:
  sync:
    enabled: true
    backend: r2
    keep_versions: 10
    backup_on_scan_count: 10    # Backup every 10 operations
    backup_on_hours: 24.0        # OR after 24 hours since last backup
```

### Multi-User Workflow

1. **Person A** generates parts:
   ```bash
   casman parts add ANTENNA 50 1
   # → Automatic backup to R2
   ```

2. **Person B** (at different site) syncs:
   ```bash
   casman sync sync
   # → Downloads latest parts
   ```

3. **Person B** performs assembly work:
   ```bash
   casman scan connection
   # → Automatic backup after 10 operations
   ```

4. **Person A** syncs:
   ```bash
   casman sync sync
   # → Gets latest assembly data
   ```

### Restore from Backup

```bash
# 1. List available backups
casman sync list

# 2. Restore specific backup
casman sync restore backups/parts.db/20241208_143022_parts.db
```

**Safety Features:**
- Creates a safety backup of current database before restoring
- Validates database integrity after download
- Atomic operation (no partial restores)

### CLI Commands Reference

| Command | Description | When to Use |
|---------|-------------|-------------|
| `casman sync backup` | Manual backup of all databases | Before risky operations |
| `casman sync backup --parts` | Backup only parts.db | Selective backup |
| `casman sync backup --assembled` | Backup only assembled_casm.db | Selective backup |
| `casman sync list` | List all available backups | Before restoring |
| `casman sync restore <key>` | Restore from specific backup | After data loss |
| `casman sync sync` | Download latest from remote | Start of work session |
| `casman sync sync --force` | Force download even if up-to-date | Troubleshooting |
| `casman sync status` | Show configuration and quota | Regular monitoring |
| `casman sync maintain` | Keep backups in Standard storage | Monthly (automated) |

### Cost Estimation (Cloudflare R2)

For 2 databases × 10 versions = 20 MB total:

- **Storage**: ~$0.0003/month ($0.015/GB/month)
- **Writes**: 100 backups/month = $0.00045
- **Reads**: Unlimited FREE
- **Egress**: Unlimited FREE

**Total: ~$0.01/year** 🎉

---

## R2 Storage Class Maintenance

### Why This Matters

Cloudflare R2 may automatically move inactive backups to **Infrequent Access storage**, which is NOT free tier eligible:

| Feature | Standard (Free Tier) | Infrequent Access (Paid) |
|---------|---------------------|-------------------------|
| Storage | 10 GB free | $0.01/GB/month |
| Class A ops | 1M/month free | $9.00/million |
| Class B ops | 10M/month free | $0.90/million |
| Retrieval | FREE | $0.01/GB |
| Minimum duration | None | 30 days |

**Without maintenance**, you'll lose free tier benefits and incur unexpected costs.

### How to Maintain Free Tier

Run this command **at least once per month**:

```bash
casman sync maintain
```

This "touches" all backup objects to keep them active in Standard storage.

**What it does:**
- Lists all backups (1 Class A operation)
- Performs HEAD request on each backup (1 Class B per file)
- Updates "last accessed" timestamp
- Cost: $0.00 (uses ~0.001% of free tier quota)

### Automation

#### Using Cron (Recommended)

```bash
# Edit crontab
crontab -e

# Add this line (weekly on Sunday at 2am)
0 2 * * 0 /path/to/casman sync maintain >> /var/log/casman-maintain.log 2>&1
```

#### Using Systemd Timer

Create `/etc/systemd/system/casman-maintain.service`:

```ini
[Unit]
Description=CAsMan R2 Storage Maintenance
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=casman
WorkingDirectory=/home/casman
ExecStart=/usr/local/bin/casman sync maintain
StandardOutput=append:/var/log/casman-maintain.log
StandardError=append:/var/log/casman-maintain.log
```

Create `/etc/systemd/system/casman-maintain.timer`:

```ini
[Unit]
Description=CAsMan R2 Storage Maintenance Timer
Requires=casman-maintain.service

[Timer]
OnCalendar=weekly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable casman-maintain.timer
sudo systemctl start casman-maintain.timer
```

### Frequency Recommendations

- **Minimum (Required)**: Once per month
- **Recommended**: Once per week
- **Optimal**: Twice per week

---

## R2 Quota Enforcement

CAsMan enforces Cloudflare R2 free tier limits to ensure you **NEVER exceed** the free tier quotas.

### Free Tier Limits & Operation Types

| Resource | Limit | Monthly Reset | Operations |
|----------|-------|---------------|------------|
| **Storage** | 10 GB | No (cumulative) | N/A |
| **Class A (Writes)** | 1,000,000 | Yes | Upload, List, Delete |
| **Class B (Reads)** | 10,000,000 | Yes | Download, HEAD requests, Sync |

### How Enforcement Works

CAsMan uses two protection thresholds:

- **80% (Warning)**: Logs warnings, operations continue, shows ⚠ in status
- **95% (Blocking)**: Blocks operations, raises `QuotaExceededError`, shows ✗ in status

This prevents accidental overages while giving you time to adjust backup frequency.

### Check Quota Status

```bash
casman sync status
```

Output:

```
R2 Free Tier Quota Usage:
  Storage:              ✓ 2.34 / 10 GB (23.4%)
  Class A Ops (writes): ⚠ 850,000 / 1,000,000 (85.0%)
  Class B Ops (reads):  ✓ 1,234,567 / 10,000,000 (12.3%)
  Backups this month:   850
  Restores this month:  12
```

### What Happens at 95% Threshold

```bash
$ casman sync backup parts.db
Error: R2 quota limit reached: 95.3% of Class A operations used.
Operation 'backup' blocked to prevent exceeding free tier limits.
Storage: 3.45/10 GB, Class A: 953,000/1,000,000, Class B: 234,567/10,000,000
```

### Best Practices

- **Monitor regularly**: `casman sync status`
- **Reduce backup frequency** if hitting limits: Increase `backup_on_scan_count` to 20-50
- **Reduce retention** if storage fills up: Decrease `keep_versions` to 5-7
- **Run monthly maintenance**: `casman sync maintain` keeps backups in free tier

### Expected Usage Patterns

#### Small Shop (1-2 users)
- **Storage**: ~500 MB (50 backups × 10 MB each)
- **Class A ops**: ~1,500/month (50 backups + lists)
- **Class B ops**: ~500/month (occasional restores)
- **Result**: ✓ Well within limits

#### Medium Shop (5-10 users)
- **Storage**: ~2 GB (200 backups × 10 MB each)
- **Class A ops**: ~6,000/month (200 backups + lists)
- **Class B ops**: ~2,000/month (occasional restores/syncs)
- **Result**: ✓ Comfortably within limits

#### Large Shop (20+ users)
- **Storage**: ~5 GB (500 backups × 10 MB each)
- **Class A ops**: ~15,000/month (500 backups + lists)
- **Class B ops**: ~5,000/month (frequent syncs)
- **Result**: ✓ Still well below limits

### Troubleshooting

**Quota Exceeded Error**
- Wait until next month for automatic reset
- Check usage: `casman sync status`
- Reduce backup frequency: Increase `backup_on_scan_count` in config
- Delete old backups if storage is full

**Storage Backend Not Available**
- Install boto3: `pip install boto3`
- Check credentials: `echo $R2_ACCOUNT_ID`
- Verify status: `casman sync status`

**Sync Failed**
- Check internet connection
- Verify R2 credentials haven't expired
- Work offline, sync later

**Quota Tracker Not Resetting**
- Automatic reset on first operation of new month
- Run any operation: `casman sync list`

---

## Implementation Details

### Core Components

#### 1. Core Sync Module (`casman/database/sync.py`)

**DatabaseSyncManager**: Main class for backup/restore operations
- Upload databases to R2/S3 with versioning
- Download and restore from backups
- List available backups with metadata
- Checksum validation for integrity
- Automatic cleanup of old versions
- Storage class maintenance (HEAD requests to prevent Infrequent Access transition)

**SyncConfig**: Configuration management
- Loads from config.yaml and environment variables
- Supports R2 and S3 backends
- Configurable backup triggers and retention

**ScanTracker**: Tracks operations
- Records operation count since last backup
- Triggers backups based on count or time
- Persists state in `.scan_tracker.json`

**QuotaTracker**: Enforces R2 free tier limits
- Tracks storage, Class A, and Class B operations
- Warning threshold at 80%, blocking at 95%
- Automatic monthly reset for operation counters
- Persists state in `.r2_quota_tracker.json`

#### 2. Automatic Backup Triggers

**Parts Generation** (`casman/parts/generation.py`):
- Backups created after every part generation batch
- Zero data loss guarantee for new parts

**Assembly Operations** (`casman/assembly/connections.py`, `casman/database/antenna_positions.py`):
- Tracks every operation (connect, disconnect, assign, remove)
- Triggers backup after N operations OR N hours
- Configurable thresholds (default: 10 operations or 24 hours)

#### 3. CLI Commands

Complete command-line interface via `casman/cli/sync_commands.py`:
- `casman sync backup` - Manual backup
- `casman sync restore <key>` - Restore from backup
- `casman sync list` - List available backups
- `casman sync sync` - Download latest versions
- `casman sync status` - Show configuration and quota status
- `casman sync maintain` - Keep backups in Standard storage class

### Files Created/Modified

**New Files:**
- `casman/database/sync.py` - Core sync module (800+ lines)
- `casman/cli/sync_commands.py` - CLI commands (500+ lines)
- `database/.scan_tracker.json` - Operation tracking (auto-created)
- `database/.r2_quota_tracker.json` - Quota tracking (auto-created)

**Modified Files:**
- `config.yaml` - Added sync configuration
- `casman/database/__init__.py` - Export sync classes
- `casman/__init__.py` - Auto-sync on install
- `casman/cli/main.py` - Register sync commands
- `casman/parts/generation.py` - Auto backup trigger
- `casman/assembly/connections.py` - Operation tracking + auto backup
- `casman/database/antenna_positions.py` - Operation tracking + auto backup
- `requirements.txt` - Added boto3

### System Architecture

The backup system provides automatic synchronization between local databases and cloud storage:

```
┌────────────────────────────────────┐
│  Local Databases                   │
│  - parts.db (~340 KB)              │
│  - assembled_casm.db (~10 MB)      │
│  - Operation tracking              │
│  - Quota tracking                  │
└────────────────────────────────────┘
         ↕ Automatic/Manual Sync
┌────────────────────────────────────┐
│  Cloudflare R2 (Free Tier)         │
│  - 10 versions per database        │
│  - Timestamp-based versioning      │
│  - Quota enforcement (95% block)   │
│  - Standard storage maintenance    │
└────────────────────────────────────┘
         ↕ Multi-user access
┌────────────────────────────────────┐
│  Field Sites / Remote Users        │
│  - Sync latest versions            │
│  - Offline-capable                 │
└────────────────────────────────────┘
```

---

## Summary

CAsMan's database system provides:

✅ **Schema**: SQLite databases (parts.db, assembled_casm.db) with well-defined structure  
✅ **Backup**: Automatic backups after part generation and every 10 operations  
✅ **Sync**: Multi-user cloud storage with timestamp-based versioning  
✅ **Cost**: ~$0.01/year using Cloudflare R2 free tier  
✅ **Protection**: Quota enforcement (95% threshold) prevents overages  
✅ **Maintenance**: Monthly `casman sync maintain` keeps backups free  
✅ **Offline**: Fully functional without internet connection  

### Quick Actions

**Setup** (5 minutes):
1. `pip install boto3`
2. Set R2 credentials in `~/.zshrc`
3. `casman sync backup`

**Daily Use**:
- Work normally - backups happen automatically
- `casman sync sync` before/after work sessions
- `casman sync status` to monitor quota

**Monthly Maintenance**:
```bash
crontab -e
# Add: 0 2 * * 0 /path/to/casman sync maintain
```
