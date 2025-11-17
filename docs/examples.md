# Examples and Tutorials

This document provides comprehensive examples and step-by-step tutorials for using CAsMan v2.0.

## Quick Start Tutorial

### Step 1: Installation and Setup

```bash

# Clone and install CAsMan
git clone https://github.com/Coherent-All-Sky-Monitor/CAsMan.git
cd CAsMan

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

```python

### Step 2: Initialize System

```bash

# Check installation
casman --help

# Initialize databases (creates necessary tables)
casman parts list

# Verify database creation
casman database print

```python

### Step 3: Add Your First Parts

```bash

# Start interactive part addition
casman parts add

# Example session:

# Select part type:

# 1: ANTENNA (alias: ANT)

# 2: LNA (alias: LNA)

# 3: COAXSHORT (alias: CXS)

# 4: COAXLONG (alias: CXL)

# 5: BACBOARD (alias: BAC)

# 0: ALL (add parts for all types)

# Enter your choice (0-5): 1

# How many ANTENNA parts do you want to create? 5

# Enter polarization (1 or 2): 1

# ✅ Created: ANT00001P1

# ✅ Created: ANT00002P1

# ✅ Created: ANT00003P1

# ✅ Created: ANT00004P1

# ✅ Created: ANT00005P1

```python

### Step 4: Your First Assembly

```bash

# Start interactive scanning and assembly
casman scan connect

# Example assembly session:

# 🔍 Starting Interactive Scanning and Assembly

# ==================================================

# Features available:

# • USB barcode scanner support

# • Manual part number entry

# • Real-time validation

# • Connection tracking

# • SNAP/FENG mapping

# Enter part details for the assembly chain:

# Select part type:

# 0: ANTENNA

# 1: LNA

# 2: COAXSHORT

# 3: COAXLONG

# 4: BACBOARD

# Enter the number (0-4): 0

# Scan or enter the ANTENNA part number: ANT00001P1

# ✅ Valid part: ANT00001P1 (ANTENNA, Polarization 1)

# Scan or enter the LNA part number: LNA-P1-00001  

# ✅ Valid part: LNA-P1-00001 (LNA, Polarization 1)

# ✅ Connection recorded: ANT-P1-00001 --> LNA-P1-00001

```python

### Step 5: Visualize Your Assembly

```bash

# View assembly chains
casman visualize chains

# Example output:

# Assembly Chain Visualization

# ============================

# Chain 1:

# ANT-P1-00001 → LNA-P1-00001
#

# Assembly Statistics:

# Total parts: 2

# Total connections: 1

# Chains found: 1

```python

## Comprehensive Examples

### Parts Management Examples

#### Example 1: Adding Multiple Part Types

```bash

# Add parts for all types at once
casman parts add

# Select option 0 (ALL) in the menu

# This will walk you through adding parts for each type:

# - ANTENNA parts

# - LNA parts  

# - COAX1 parts

# - COAX2 parts

# - BACBOARD parts

```python

#### Example 2: Listing and Searching Parts

```bash

# List all parts in the database
casman parts list

# Search for specific part types
casman parts search --type ANTENNA

# Search by polarization
casman parts search --polarization 1

# Validate parts database
casman parts validate

```python

### Database Management Examples

#### Example 3: Safe Database Operations

```bash

# View current database contents
casman database print

# Clear specific database with safety confirmation
casman database clear --parts

# Example safety workflow:

# 🛑 [STOP SIGN DISPLAYED]

# WARNING: This will DELETE ALL records from the parts database at: /path/to/parts.db

# Are you sure you want to clear the parts database? (yes/no): yes

# This action is IRREVERSIBLE. Type 'yes' again to confirm: yes

# All records deleted from parts database.

# Clear both databases (double confirmation required)
casman database clear

```python

### Assembly and Scanning Examples

#### Example 4: Complete Assembly Chain

```bash

# Build a complete assembly chain
casman scan connect

# Follow the sequence: ANT → LNA → COAX1 → COAX2 → BACBOARD → SNAP

# 1. Scan ANT-P1-00001

# 2. Scan LNA-P1-00001 

# 3. Scan CX1-P1-00001

# 4. Scan CX2-P1-00001

# 5. Scan BAC-P1-00001

# 6. Enter SNAP part (validated against snap_feng_map.yaml)

# Result: Complete validated assembly chain

```python

#### Example 5: Assembly Statistics


### Visualization Examples

#### Example 6: ASCII Chain Visualization

```bash

# Simple chain visualization
casman visualize chains

# Example output:

# 📊 Assembly Summary

# ==================

# Active Chains: 3

# 
# Chain 1 (Complete):

# ANT-P1-00001 → LNA-P1-00001 → CX1-P1-00001 → CX2-P1-00001 → BAC-P1-00001 → SNAP-001

# 
# Chain 2 (Partial):  

# ANT-P1-00002 → LNA-P1-00002
#

# Chain 3 (Complete):

# ANT-P2-00001 → LNA-P2-00001 → CX1-P2-00001 → CX2-P2-00001 → BAC-P2-00001 → SNAP-002

```python

#### Example 7: Web Visualization

```bash

# Launch web interface on default port (5000)
casman visualize web

# Launch on custom port
casman visualize web --port 8080

# Opens browser to http://localhost:8080 with interactive visualization

```python

### Barcode Examples

#### Example 8: Generate Barcode Pages

```bash

# Generate barcode pages for ANTENNA parts
casman barcode printpages --part-type ANTENNA --start-number 1 --end-number 50

# Generate for specific polarization and range
casman barcode printpages --part-type LNA --start-number 10 --end-number 20

# Generated files saved to barcodes/ANTENNA/ directory

```python

## Advanced Workflows

### Workflow 1: Production Assembly Line

```bash

#!/bin/bash

# Production assembly workflow script

# 1. Initialize system
echo "🚀 Starting production assembly workflow..."
casman database print > daily_start_state.txt

# 2. Verify parts database
echo "📋 Verifying parts database..."
casman parts validate

# 3. Start assembly scanning  
echo "🔍 Starting assembly scanning..."
casman scan connect

# 4. Generate assembly report
echo "📊 Generating assembly report..."
casman visualize chains > daily_assembly_report.txt

echo "✅ Workflow complete. Reports saved."

```python

### Workflow 2: Quality Control Check

```bash

#!/bin/bash

# Quality control workflow

# 1. Backup current state
echo "💾 Creating backup..."
cp database/assembled_casm.db "backups/assembled_$(date +%Y%m%d_%H%M%S).db"

# 2. Validate all assemblies
echo "🔍 Validating assemblies..."
casman visualize chains > validation_report.txt

# 3. View assembly chains
echo "⚠️ Reviewing assembly chains..."
casman visualize chains >> validation_report.txt

# 4. Generate barcode verification
echo "🏷️ Generating barcode verification..."
casman barcode printpages --part-type ANTENNA --start-number 1 --end-number 10

echo "✅ Quality control complete."

```python

### Workflow 3: Database Maintenance

```bash

#!/bin/bash

# Weekly database maintenance

# 1. Create backup
echo "💾 Creating weekly backup..."
timestamp=$(date +%Y%m%d_%H%M%S)
cp database/parts.db "backups/parts_weekly_$timestamp.db"
cp database/assembled_casm.db "backups/assembled_weekly_$timestamp.db"

# 2. Generate chain report
echo "📊 Generating weekly chain report..."
casman visualize chains > "reports/weekly_chains_$timestamp.txt"

# 3. Validate database integrity
echo "🔍 Validating database integrity..."
casman parts validate >> "reports/weekly_chains_$timestamp.txt"

# 4. Clean up old temporary files (optional)
echo "🧹 Cleaning temporary files..."
find barcodes/ -name "*.png" -mtime +30 -delete

echo "✅ Weekly maintenance complete."

```python

## Integration Examples

### Example 9: Python Script Integration

```python

#!/usr/bin/env python3
"""
Example: Integrating CAsMan with custom Python scripts
"""

from casman.parts.generation import get_last_part_number
from casman.database.operations import get_parts_by_criteria
from casman.assembly.chains import build_connection_chains
from casman.visualization.core import format_ascii_chains

def generate_assembly_report():
    """Generate a custom assembly report."""
    
    # Get all ANTENNA parts
    antenna_parts = get_parts_by_criteria(part_type="ANTENNA", polarization=None)
    print(f"Total ANTENNA parts: {len(antenna_parts)}")
    
    # Get last part number for each type
    last_ant = get_last_part_number("ANTENNA", "1")
    last_lna = get_last_part_number("LNA", "1")
    print(f"Last ANTENNA P1: {last_ant}")
    print(f"Last LNA P1: {last_lna}")
    
    # Build and visualize chains
    chains = build_connection_chains()
    if chains:
        visualization = format_ascii_chains(chains)
        print("\nAssembly Chains:")
        print(visualization)
    else:
        print("No assembly chains found.")

def validate_part_inventory():
    """Validate that part inventory is consistent."""
    
    part_types = ["ANTENNA", "LNA", "COAX1", "COAX2", "BACBOARD"]
    
    for part_type in part_types:
        for polarization in ["1", "2"]:
            parts = get_parts_by_criteria(part_type=part_type, polarization=polarization)
            print(f"{part_type} P{polarization}: {len(parts)} parts")
            
            # Check for gaps in part numbers
            if parts:
                numbers = [int(part[1].split('-')[-1]) for part in parts]
                expected = list(range(1, len(numbers) + 1))
                missing = [n for n in expected if n not in numbers]
                if missing:
                    print(f"  ⚠️  Missing part numbers: {missing}")
                else:
                    print(f"  ✅ No gaps in part numbers")

if __name__ == "__main__":
    print("🔍 CAsMan Custom Integration Example")
    print("=" * 40)
    
    generate_assembly_report()
    print("\n" + "=" * 40)
    validate_part_inventory()

```python

### Example 10: Automated Testing Integration

```python

#!/usr/bin/env python3
"""
Example: Automated testing with CAsMan
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_casman_functionality():
    """Test core CAsMan functionality."""
    
    tests = [
        ("CLI Help", "casman --help"),
        ("Parts List", "casman parts list"),
        ("Database Print", "casman database print"),
        ("Scan Help", "casman scan --help"),
        ("Visualize Help", "casman visualize --help"),
    ]
    
    results = []
    
    for test_name, command in tests:
        print(f"Running: {test_name}")
        success, stdout, stderr = run_command(command)
        
        if success:
            print(f"  ✅ {test_name} - PASSED")
        else:
            print(f"  ❌ {test_name} - FAILED")
            print(f"     Error: {stderr}")
        
        results.append((test_name, success))
    
    # Summary
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    if test_casman_functionality():
        sys.exit(0)
    else:
        sys.exit(1)

```python

## Troubleshooting Examples

### Common Issues and Solutions

#### Issue 1: Import Errors

```bash

# Problem: ImportError when using old imports

# Solution: Update to new modular imports

# OLD (causes error):

# from casman.parts import add_parts_interactive

# NEW (works):
from casman.parts.interactive import add_parts_interactive

```python

#### Issue 2: Database Connection Issues

```bash

# Problem: Database not found errors

# Solution: Initialize databases first

casman parts list  # This creates databases if they don't exist

```python

#### Issue 3: Part Validation Failures

```bash

# Problem: Parts not validating during scanning

# Solution: Check part format and database

# 1. Validate parts database
casman parts validate

# 2. Check part exists
casman parts list | grep "ANT-P1-00001"

# 3. Verify part format (should be: TYPE-P#-#####)

```python

#### Issue 4: Assembly Chain Breaks

```bash

# Problem: Assembly chains not forming correctly

# Solution: Check connection sequence and validation

# 1. Visualize current chains
casman visualize chains

# 3. Verify connection sequence: ANT → LNA → COAX1 → COAX2 → BACBOARD → SNAP

```python

## Performance Tips

### Optimization Examples

1. **Batch Operations**: Use the "ALL" option when adding multiple part types
2. **Database Maintenance**: Regular backups and validation improve performance
3. **Terminal Width**: Larger terminal windows provide better visualization
4. **Virtual Environment**: Use virtual environments for better dependency management

### Monitoring Examples

```bash

# Monitor database size
ls -lh database/

# Monitor barcode generation
find barcodes/ -name "*.png" | wc -l

```python

## Next Steps

After completing these examples:

1. **Read the [Migration Guide](migration_guide.md)** if upgrading from v1.x
2. **Review [Safety Features](safety_features.md)** for production use
3. **Check [Development Guide](development.md)** for customization
4. **Explore [API Reference](api_reference.md)** for advanced integration

## Getting Help

- **CLI Help**: Use `casman [command] --help` for any command

- **Documentation**: Check the `docs/` directory for detailed guides

- **Issues**: Report bugs or ask questions on GitHub

- **Examples**: More examples available in the `examples/` directory (if available)
