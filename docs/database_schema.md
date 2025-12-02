# CAsMan Database Schema Documentation

## Overview

CAsMan uses **SQLite** databases to manage parts inventory, assembly tracking, and antenna positions. The system consists of two main database files and one optional CSV-based coordinate management system.

### Database Files

1. **`parts.db`** - Parts inventory and antenna positions
2. **`assembled_casm.db`** - Assembly tracking and connections
3. **`grid_positions.csv`** - Geographic coordinates (CSV, not SQLite)

### Database Location

Default location: `database/` in project root

Can be customized via:
- Environment variable: `CASMAN_DATABASE_DIR`
- Configuration file: `config.yaml`
- Command-line parameter in functions

---

## Database 1: `parts.db`

Main inventory database for tracking individual parts and antenna grid positions.

### Table: `parts`

Stores information about all individual parts in the system.

#### Schema

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

#### Column Descriptions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| `part_number` | TEXT | UNIQUE | Unique part identifier (e.g., `ANT00001P1`, `LNA00042P2`) |
| `part_type` | TEXT | - | Type of part: `ANTENNA`, `LNA`, `COAXSHORT`, `COAXLONG`, `BACBOARD`, `SNAP` |
| `polarization` | TEXT | - | Polarization: `P1` or `P2` for dual-pol parts, `NULL` for single parts |
| `date_created` | TEXT | - | ISO 8601 timestamp when part was first added |
| `date_modified` | TEXT | - | ISO 8601 timestamp of last modification |

#### Part Number Formats

- **Antenna**: `ANT{5-digit}P{1|2}` (e.g., `ANT00001P1`)
- **LNA**: `LNA{5-digit}P{1|2}` (e.g., `LNA00042P2`)
- **COAXSHORT**: `CXS{5-digit}P{1|2}` (e.g., `CXS00123P1`)
- **COAXLONG**: `CXL{5-digit}P{1|2}` (e.g., `CXL00456P2`)
- **BACBOARD**: `BAC{5-digit}P{1|2}` (e.g., `BAC00789P1`)
- **SNAP**: `SNAP{chassis:02d}{slot:02d}{port:02d}` (e.g., `SNAP010203`)

#### Example Data

```sql
INSERT INTO parts VALUES 
    (1, 'ANT00001P1', 'ANTENNA', 'P1', '2025-01-15T10:30:00Z', '2025-01-15T10:30:00Z'),
    (2, 'ANT00001P2', 'ANTENNA', 'P2', '2025-01-15T10:30:00Z', '2025-01-15T10:30:00Z'),
    (3, 'LNA00042P1', 'LNA', 'P1', '2025-01-16T14:20:00Z', '2025-01-16T14:20:00Z'),
    (4, 'SNAP010203', 'SNAP', NULL, '2025-01-17T09:15:00Z', '2025-01-17T09:15:00Z');
```

#### Usage Notes

- Each physical antenna has 2 rows (P1 and P2 polarizations)
- SNAP parts have no polarization (single entry)
- Timestamps are in ISO 8601 format with 'Z' suffix (UTC)
- Part numbers must be unique across the entire table

#### Common Queries

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

---

### Table: `antenna_positions`

Maps antenna base numbers to grid positions and optionally stores geographic coordinates.

#### Schema

```sql
CREATE TABLE antenna_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    antenna_number TEXT UNIQUE NOT NULL,
    array_id TEXT NOT NULL,
    row_offset INTEGER NOT NULL,
    east_col INTEGER NOT NULL,
    grid_code TEXT UNIQUE NOT NULL,
    assigned_at TEXT NOT NULL,
    notes TEXT,
    latitude REAL,
    longitude REAL,
    height REAL,
    coordinate_system TEXT,
    CHECK(row_offset >= -999 AND row_offset <= 999),
    CHECK(east_col >= 0 AND east_col <= 99),
    UNIQUE(array_id, row_offset, east_col)
)
```

#### Column Descriptions

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

#### Grid Code Format

Format: `{array_id}{direction}{row:03d}E{col:02d}`

- **Array ID**: `C`, `N`, or `S`
- **Direction**: `N` (north/positive) or `S` (south/negative)
- **Row**: 3-digit row offset (e.g., `002` for row +2, `021` for row -21)
- **Column**: 2-digit column index (e.g., `00` for first column)

Examples:
- `CN002E03` - Core array, North row +2, East column 3
- `CS021E00` - Core array, South row -21, East column 0
- `CC000E01` - Core array, Center row 0, East column 1

#### Uniqueness Constraints

1. Each `antenna_number` can only have one position
2. Each `grid_code` can only have one antenna
3. Each `(array_id, row_offset, east_col)` combination is unique

#### Example Data

```sql
INSERT INTO antenna_positions VALUES
    (1, 'ANT00001', 'C', 2, 3, 'CN002E03', '2025-01-15T10:30:00Z', 
     'First deployment', 37.871899, -122.258477, 10.5, 'WGS84'),
    (2, 'ANT00002', 'C', 0, 0, 'CC000E00', '2025-01-15T11:00:00Z',
     'Center position', 37.871912, -122.258321, 10.6, 'WGS84'),
    (3, 'ANT00003', 'C', -1, 2, 'CS001E02', '2025-01-15T11:30:00Z',
     NULL, NULL, NULL, NULL, NULL);
```

#### Usage Notes

- `antenna_number` is stored **without** polarization suffix (just `ANT00001`, not `ANT00001P1`)
- Geographic coordinates are optional (can be `NULL`)
- Coordinates can be loaded from CSV using `casman database load-coordinates`
- Row offset is signed: positive = north, negative = south, 0 = center
- Column index is 0-based from westernmost position

#### Common Queries

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

-- Get positions sorted by row and column
SELECT * FROM antenna_positions 
ORDER BY array_id, row_offset DESC, east_col;

-- Count antennas with and without coordinates
SELECT 
    COUNT(*) as total,
    COUNT(latitude) as with_coords,
    COUNT(*) - COUNT(latitude) as without_coords
FROM antenna_positions;
```

---

## Database 2: `assembled_casm.db`

Tracks assembled connections between parts in the signal chain.

### Table: `assembly`

Records connections between parts (e.g., Antenna → LNA → Coax → SNAP).

#### Schema

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

#### Column Descriptions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-incrementing unique identifier |
| `part_number` | TEXT | - | Part number of the source component |
| `part_type` | TEXT | - | Type of source part |
| `polarization` | TEXT | - | Polarization of source part (`P1`, `P2`, or `NULL`) |
| `scan_time` | TEXT | - | ISO 8601 timestamp when source was scanned |
| `connected_to` | TEXT | - | Part number of the connected component |
| `connected_to_type` | TEXT | - | Type of connected part |
| `connected_polarization` | TEXT | - | Polarization of connected part |
| `connected_scan_time` | TEXT | - | Timestamp when connection was scanned |
| `connection_status` | TEXT | DEFAULT 'connected' | Status: `connected` or `disconnected` |

#### Valid Signal Chain Sequence

```
ANTENNA → LNA → COAXSHORT → COAXLONG → BACBOARD → SNAP
```

Each connection must follow this sequence. Polarizations must match (P1→P1, P2→P2).

#### Connection Status Values

- **`connected`** (default): Active connection
- **`disconnected`**: Connection has been broken/removed

#### Example Data

```sql
INSERT INTO assembly VALUES
    (1, 'ANT00001P1', 'ANTENNA', 'P1', '2025-01-20T08:00:00Z',
        'LNA00042P1', 'LNA', 'P1', '2025-01-20T08:01:00Z', 'connected'),
    (2, 'LNA00042P1', 'LNA', 'P1', '2025-01-20T08:01:00Z',
        'CXS00123P1', 'COAXSHORT', 'P1', '2025-01-20T08:02:00Z', 'connected'),
    (3, 'CXS00123P1', 'COAXSHORT', 'P1', '2025-01-20T08:02:00Z',
        'CXL00456P1', 'COAXLONG', 'P1', '2025-01-20T08:03:00Z', 'connected'),
    (4, 'CXL00456P1', 'COAXLONG', 'P1', '2025-01-20T08:03:00Z',
        'BAC00789P1', 'BACBOARD', 'P1', '2025-01-20T08:04:00Z', 'connected'),
    (5, 'BAC00789P1', 'BACBOARD', 'P1', '2025-01-20T08:04:00Z',
        'SNAP010203', 'SNAP', NULL, '2025-01-20T08:05:00Z', 'connected');
```

#### Usage Notes

- Each row represents a **directional connection**: A → B
- Reverse connection (B → A) is not automatically created
- For complete chain, multiple rows needed (one per connection)
- Polarizations must match except for SNAP (which has no polarization)
- `connection_status` allows marking disconnections without deleting history

#### Common Queries

```sql
-- Get all connections for a part
SELECT * FROM assembly WHERE part_number = 'ANT00001P1';

-- Find what a part is connected to
SELECT connected_to, connected_to_type 
FROM assembly 
WHERE part_number = 'ANT00001P1' AND connection_status = 'connected';

-- Find what is connected to a part
SELECT part_number, part_type 
FROM assembly 
WHERE connected_to = 'LNA00042P1' AND connection_status = 'connected';

-- Get complete chain for an antenna
WITH RECURSIVE chain AS (
    SELECT * FROM assembly WHERE part_number = 'ANT00001P1'
    UNION ALL
    SELECT a.* FROM assembly a
    JOIN chain c ON a.part_number = c.connected_to
    WHERE a.connection_status = 'connected'
)
SELECT * FROM chain;

-- Get all active connections
SELECT * FROM assembly WHERE connection_status = 'connected';

-- Get disconnected parts
SELECT * FROM assembly WHERE connection_status = 'disconnected';

-- Count connections by part type
SELECT part_type, COUNT(*) as count 
FROM assembly 
WHERE connection_status = 'connected'
GROUP BY part_type;

-- Find orphaned parts (not connected to anything)
SELECT p.part_number 
FROM parts p 
LEFT JOIN assembly a ON p.part_number = a.part_number 
WHERE a.part_number IS NULL AND p.part_type = 'ANTENNA';
```

---

## File 3: `grid_positions.csv`

CSV file for managing geographic coordinates of antenna grid positions.

### Format

```csv
grid_code,latitude,longitude,height,coordinate_system,notes
CN021E00,37.871899,-122.258477,10.5,WGS84,Survey point 1
CN021E01,37.871912,-122.258321,10.6,WGS84,Survey point 2
```

### Column Descriptions

| Column | Type | Description |
|--------|------|-------------|
| `grid_code` | TEXT | Grid position code (e.g., `CN002E03`) |
| `latitude` | REAL | Latitude in decimal degrees |
| `longitude` | REAL | Longitude in decimal degrees |
| `height` | REAL | Height in meters above reference |
| `coordinate_system` | TEXT | Coordinate system (e.g., `WGS84`, `local`) |
| `notes` | TEXT | Optional notes about the position |

### Loading Coordinates

Use the CLI command to load coordinates from CSV into the database:

```bash
casman database load-coordinates --csv database/grid_positions.csv
```

This populates the `latitude`, `longitude`, `height`, and `coordinate_system` columns in the `antenna_positions` table.

### Template

The repository includes a template CSV with all 258 core grid positions (rows -21 to +21, columns 0-5). Coordinates are initially empty and should be populated from survey data.

---

## Database Relationships

### Entity Relationship Diagram

```
┌─────────────────────┐
│      parts          │
│  (parts.db)         │
├─────────────────────┤
│ id (PK)             │
│ part_number (UNIQUE)│──┐
│ part_type           │  │
│ polarization        │  │
│ date_created        │  │
│ date_modified       │  │
└─────────────────────┘  │
                         │
                         │ Referenced by 
                         │
        ┌────────────────┴────────────────┐
        │                                  │
        ↓                                  ↓
┌──────────────────┐           ┌──────────────────┐
│ antenna_positions│           │    assembly      │
│   (parts.db)     │           │(assembled_casm.db)│
├──────────────────┤           ├──────────────────┤
│ id (PK)          │           │ id (PK)          │
│ antenna_number   │←─────┐    │ part_number      │
│   (UNIQUE)       │      │    │ connected_to     │
│ grid_code (UNIQUE)│      │    │ connection_status│
│ array_id         │      │    │ ...              │
│ row_offset       │      │    └──────────────────┘
│ east_col         │      │
│ latitude         │      └─── Base antenna number
│ longitude        │           (without P1/P2 suffix)
│ height           │
│ coordinate_system│
└──────────────────┘
```

### Relationship Notes

**Important**: SQLite does **not enforce foreign key constraints** by default in these databases. Referential integrity is maintained by the application layer.

1. **parts → antenna_positions**
   - `antenna_positions.antenna_number` should match base antenna numbers in `parts` (without P1/P2)
   - One entry in `antenna_positions` corresponds to two entries in `parts` (P1 and P2)

2. **parts → assembly**
   - `assembly.part_number` and `assembly.connected_to` should exist in `parts.part_number`
   - Not enforced by database - validated by application

---

## Database Initialization

### Automatic Initialization

Databases are automatically created when first needed by CAsMan CLI or API.

```python
from casman.database import init_all_databases

# Initialize all databases
init_all_databases()

# Or initialize individually
from casman.database import init_parts_db, init_assembled_db
from casman.database.antenna_positions import init_antenna_positions_table

init_parts_db()
init_assembled_db()
init_antenna_positions_table()
```

### Manual Initialization

```bash
# Using Python
python -c "from casman.database import init_all_databases; init_all_databases()"

# Or use CLI (creates databases automatically)
casman database print-parts
casman database print-assembled
```

---

## Schema Migrations

### Automatic Migrations

The initialization functions include automatic schema migrations:

1. **parts table**:
   - Adds `polarization` column if missing
   - Renames `created_at`/`modified_at` to `date_created`/`date_modified`

2. **assembly table**:
   - Adds `connection_status` column if missing (default: `'connected'`)

3. **antenna_positions table**:
   - Adds `latitude`, `longitude`, `height`, `coordinate_system` if missing

### Migration Safety

- All migrations use `ALTER TABLE ADD COLUMN` (safe, preserves data)
- No migrations drop columns or delete data
- Migrations are idempotent (safe to run multiple times)

---

## Database Maintenance

### Backup

```bash
# Backup databases
cp database/parts.db database/parts.db.backup
cp database/assembled_casm.db database/assembled_casm.db.backup

# Or use SQLite backup
sqlite3 database/parts.db ".backup database/parts_backup.db"
```

### Vacuum (Reclaim Space)

```bash
sqlite3 database/parts.db "VACUUM;"
sqlite3 database/assembled_casm.db "VACUUM;"
```

### Integrity Check

```bash
sqlite3 database/parts.db "PRAGMA integrity_check;"
sqlite3 database/assembled_casm.db "PRAGMA integrity_check;"
```

### Clear Databases

```bash
# Using CAsMan CLI
casman database clear-parts
casman database clear-assembled

# Or manually
rm database/parts.db database/assembled_casm.db
casman database print-parts  # Recreates empty database
```

---

## Common Workflows

### 1. Adding a New Part

```sql
-- Add antenna with both polarizations
INSERT INTO parts (part_number, part_type, polarization, date_created, date_modified)
VALUES 
    ('ANT00099P1', 'ANTENNA', 'P1', datetime('now'), datetime('now')),
    ('ANT00099P2', 'ANTENNA', 'P2', datetime('now'), datetime('now'));
```

### 2. Assigning Antenna to Grid Position

```sql
-- Assign antenna to position CN005E02
INSERT INTO antenna_positions 
    (antenna_number, array_id, row_offset, east_col, grid_code, assigned_at)
VALUES 
    ('ANT00099', 'C', 5, 2, 'CN005E02', datetime('now'));
```

### 3. Loading Geographic Coordinates

```bash
# Prepare CSV file
cat > coords.csv << EOF
grid_code,latitude,longitude,height,coordinate_system,notes
CN005E02,37.871950,-122.258200,10.8,WGS84,New survey
EOF

# Load into database
casman database load-coordinates --csv coords.csv
```

### 4. Connecting Parts in Assembly

```sql
-- Connect antenna to LNA
INSERT INTO assembly 
    (part_number, part_type, polarization, scan_time,
     connected_to, connected_to_type, connected_polarization, connected_scan_time,
     connection_status)
VALUES 
    ('ANT00099P1', 'ANTENNA', 'P1', datetime('now'),
     'LNA00123P1', 'LNA', 'P1', datetime('now'),
     'connected');
```

### 5. Disconnecting Parts

```sql
-- Mark connection as disconnected (preserves history)
UPDATE assembly 
SET connection_status = 'disconnected'
WHERE part_number = 'ANT00099P1' AND connected_to = 'LNA00123P1';
```

### 6. Finding Complete Signal Chain

```python
from casman.assembly import get_analog_chain

# Get complete chain for antenna
chain = get_analog_chain('ANT00001P1')
for part in chain:
    print(f"{part['part_number']} ({part['part_type']})")
```

---

## Performance Considerations

### Indexes

Currently, the databases use these indexes (automatically created by SQLite):

- `parts.part_number` (UNIQUE constraint creates index)
- `antenna_positions.antenna_number` (UNIQUE constraint creates index)
- `antenna_positions.grid_code` (UNIQUE constraint creates index)
- `assembly.id` (PRIMARY KEY creates index)

### Optimization Tips

1. **Add indexes for frequent queries**:
   ```sql
   CREATE INDEX idx_assembly_part ON assembly(part_number);
   CREATE INDEX idx_assembly_connected ON assembly(connected_to);
   CREATE INDEX idx_assembly_status ON assembly(connection_status);
   ```

2. **Use prepared statements** for repeated queries (CAsMan does this internally)

3. **Keep databases small**: Archive old disconnection records periodically

4. **Run ANALYZE** periodically to update query optimizer statistics:
   ```bash
   sqlite3 database/parts.db "ANALYZE;"
   ```

---

## Data Integrity Rules

### Application-Level Constraints

These rules are enforced by CAsMan code, not by database constraints:

1. **Part Number Uniqueness**: Each part_number must be unique across `parts` table
2. **Grid Position Uniqueness**: Each grid position can only have one antenna
3. **Antenna Uniqueness**: Each antenna can only be in one grid position
4. **Connection Sequence**: Must follow ANTENNA→LNA→COAXSHORT→COAXLONG→BACBOARD→SNAP
5. **Polarization Matching**: Connected parts must have matching polarizations (except SNAP)
6. **Part Existence**: Parts in `assembly` should exist in `parts` table
7. **Timestamp Format**: All timestamps must be ISO 8601 format

### Validation

Run integrity checks using:

```bash
# Check for orphaned assembly records
sqlite3 database/assembled_casm.db << EOF
SELECT DISTINCT part_number FROM assembly
WHERE part_number NOT IN (SELECT part_number FROM parts);
EOF

# Check for duplicate grid positions
sqlite3 database/parts.db << EOF
SELECT grid_code, COUNT(*) 
FROM antenna_positions 
GROUP BY grid_code 
HAVING COUNT(*) > 1;
EOF
```

---

## Troubleshooting

### Database Locked

**Problem**: `sqlite3.OperationalError: database is locked`

**Solution**:
- Close all connections to the database
- Check for hung processes: `ps aux | grep sqlite`
- Wait a few seconds and retry
- Use WAL mode: `sqlite3 database/parts.db "PRAGMA journal_mode=WAL;"`

### Schema Mismatch

**Problem**: Missing columns or tables

**Solution**:
```python
from casman.database import init_all_databases
init_all_databases()  # Runs automatic migrations
```

### Coordinate Loading Fails

**Problem**: CSV coordinates not loading

**Solution**:
- Check CSV format matches specification
- Ensure grid_code matches entries in `antenna_positions`
- Verify no header row issues
- Check for UTF-8 encoding

### Connection Sequence Violation

**Problem**: Cannot connect parts in wrong order

**Solution**:
- Check valid sequence: ANT→LNA→CXS→CXL→BAC→SNAP
- Verify polarization matching
- Use CLI scanner for guided assembly

---

## API Reference

### Python API for Database Access

```python
# Initialize databases
from casman.database import init_parts_db, init_assembled_db
from casman.database.antenna_positions import init_antenna_positions_table

# Get database paths
from casman.database.connection import get_database_path
parts_db = get_database_path("parts.db")

# Antenna positions
from casman.database.antenna_positions import (
    assign_antenna_position,
    get_antenna_position,
    get_all_antenna_positions,
    unassign_antenna_position,
    load_grid_coordinates_from_csv
)

# Parts operations
from casman.parts import add_part, get_part, part_exists

# Assembly operations
from casman.assembly import record_connection, get_analog_chain
```

See full API documentation in `docs/api_reference.md`.

---

## Version History

### Schema Versions

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Initial | Basic `parts` and `assembly` tables |
| 1.1 | 2024-11 | Added `polarization` column to `parts` |
| 1.2 | 2024-12 | Added `antenna_positions` table |
| 1.3 | 2025-01 | Added `connection_status` to `assembly` |
| 1.4 | 2025-01 | Added geographic coordinates to `antenna_positions` |
| 1.5 | Current | Added geographic coordinates to `antenna_positions` |

---

## See Also

- [Database API Reference](api_reference.md#database)
- [Grid Coordinates Documentation](grid_coordinates.md)
- [Antenna Module Documentation](antenna_module.md)
- [CLI Database Commands](cli.md#database-commands)
