# Disconnect Feature Implementation

## Overview
This feature adds the ability to track part disconnections in CAsMan, creating historical records of both connections and disconnections in the database.

## Changes Made

### 1. Database Schema Update
**File: `casman/database/initialization.py`**
- Added `connection_status` column to the `assembly` table with default value `'connected'`
- Implemented automatic migration for existing databases to add the column
- Updates all existing records to have `connection_status = 'connected'`

### 2. Connection Recording Functions
**File: `casman/assembly/connections.py`**
- Updated `record_assembly_connection()` to accept optional `connection_status` parameter (defaults to `'connected'`)
- Created new `record_assembly_disconnection()` function that wraps `record_assembly_connection()` with `connection_status='disconnected'`
- Both functions now record entries with the appropriate status

### 3. Interactive Scanning Functions
**File: `casman/assembly/interactive.py`**
- Created new `scan_and_disassemble_interactive()` function
- Mirrors the structure of `scan_and_assemble_interactive()` but for disconnections
- Validates both parts exist in database before recording disconnection
- Updated existing validation queries to filter by `connection_status='connected'`

### 4. CLI Commands
**File: `casman/cli/assembly_commands.py`**
- Added `disconnect` action to `casman scan` command
- Updated help text to include disconnect option
- Routes disconnect action to `scan_and_disassemble_interactive()`

### 5. Visualization Filtering
Updated SQL queries in multiple files to only show parts with `connection_status='connected'`:

**Files Modified:**
- `casman/assembly/interactive.py` - Connection validation queries
- `casman/assembly/data.py` - Assembly statistics and connection queries
- `casman/database/operations.py` - Part queries and last update queries
- `casman/visualization/core.py` - Duplicate connection detection

## Usage

### Recording a Disconnection
```bash
casman scan disconnect
```

This will launch an interactive scanner that:
1. Prompts you to scan the first part
2. Validates it exists in the database
3. Prompts you to scan the disconnected part
4. Validates the disconnected part exists
5. Records the disconnection with status `'disconnected'`

### Example Session
```
Interactive Disassembly Scanner
================================
Type 'quit' to exit.

Scan first part: ANT00001P1
✅ Valid part: ANT00001P1 (ANTENNA, P1)
Scan disconnected part: LNA00001P1
✅ Valid part: LNA00001P1 (LNA, P1)
✅ Disconnection recorded: ANT00001P1 -X-> LNA00001P1

Scan first part: quit
Goodbye!
```

## Database Schema

### Assembly Table Structure
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| part_number | TEXT | Part being scanned |
| part_type | TEXT | Type of part (ANTENNA, LNA, etc.) |
| polarization | TEXT | Polarization (P1, P2, etc.) |
| scan_time | TEXT | Timestamp of scan |
| connected_to | TEXT | Part it connects/disconnects to |
| connected_to_type | TEXT | Type of connected part |
| connected_polarization | TEXT | Polarization of connected part |
| connected_scan_time | TEXT | Timestamp of connection/disconnection |
| **connection_status** | TEXT | **'connected' or 'disconnected' (NEW)** |

## Behavior Changes

### Visualizations
All visualization functions now filter to only show parts with `connection_status='connected'`:
- `casman visualize chains` - Only shows connected parts
- `casman visualize web` - Only renders connected chains
- Assembly statistics - Counts only connected parts



### Validation
Connection validation checks (for duplicates and branches) now only consider parts with `connection_status='connected'`, allowing parts to be reconnected after being disconnected.

## Testing

### Verification Tests
```python
# Test 1: Database migration adds column
from casman.database.initialization import init_assembled_db
import sqlite3
from casman.database.connection import get_database_path

init_assembled_db('test_db')
db_path = get_database_path('assembled_casm.db', 'test_db')
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('PRAGMA table_info(assembly)')
columns = [row[1] for row in c.fetchall()]
assert 'connection_status' in columns  # ✅ PASSED

# Test 2: Recording connections and disconnections
from casman.assembly.connections import record_assembly_connection, record_assembly_disconnection

success1 = record_assembly_connection(
    'TEST001P1', 'ANTENNA', 'P1', '2024-01-01 10:00:00',
    'TEST002P1', 'LNA', 'P1', '2024-01-01 10:05:00', 'test_db'
)
assert success1  # ✅ PASSED

success2 = record_assembly_disconnection(
    'TEST001P1', 'ANTENNA', 'P1', '2024-01-01 10:00:00',
    'TEST002P1', 'LNA', 'P1', '2024-01-01 10:10:00', 'test_db'
)
assert success2  # ✅ PASSED

# Test 3: Filtering only shows connected parts
from casman.assembly.data import get_assembly_connections
connections = get_assembly_connections('test_db')
assert len(connections) == 1  # Only the 'connected' entry, not 'disconnected'  ✅ PASSED
```

## Migration for Existing Databases

Existing databases will be automatically migrated when `init_assembled_db()` is called:
1. The function checks if `connection_status` column exists
2. If not, it adds the column with `ALTER TABLE`
3. Updates all existing NULL values to `'connected'`
4. All future queries will respect the connection status

No manual migration is required.

## API Changes

### `record_assembly_connection()`
**New signature:**
```python
def record_assembly_connection(
    part_number: str,
    part_type: str,
    polarization: str,
    scan_time: str,
    connected_to: str,
    connected_to_type: str,
    connected_polarization: str,
    connected_scan_time: str,
    db_dir: Optional[str] = None,
    connection_status: str = "connected",  # NEW PARAMETER
) -> bool
```

### New Function: `record_assembly_disconnection()`
```python
def record_assembly_disconnection(
    part_number: str,
    part_type: str,
    polarization: str,
    scan_time: str,
    connected_to: str,
    connected_to_type: str,
    connected_polarization: str,
    connected_scan_time: str,
    db_dir: Optional[str] = None,
) -> bool
```

## Future Enhancements

Potential improvements for future development:
1. Add `casman scan reconnect` command to reconnect previously disconnected parts
2. Add visualization mode to show disconnection history
3. Add statistics breakdown showing connection/disconnection counts over time
4. Add search/filter by connection status in database queries
5. Add undo functionality for recent disconnections
