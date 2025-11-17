# Migration Guide: CAsMan v1.x to v2.0

This guide helps you migrate from CAsMan v1.x to v2.0, which introduces breaking changes due to complete package modularization.

## Overview of Changes

CAsMan v2.0 represents a complete architectural overhaul:

- **Complete modularization** of all packages

- **New CLI command structure** with database management

- **Enhanced safety features** with visual warnings

- **Improved documentation** and help system

- **Better error handling** and validation

## Breaking Changes

### 1. Import Structure Changes

The most significant change is the new modular import structure.

#### Parts Management

```python

# OLD (v1.x) - No longer works
from casman.parts import add_parts_interactive, get_last_part_number

# NEW (v2.x) - Required
from casman.parts.interactive import add_parts_interactive
from casman.parts.generation import get_last_part_number

```python

#### Assembly Operations

```python

# OLD (v1.x) - No longer works
from casman.assembly import build_connection_chains, print_assembly_chains

# NEW (v2.x) - Required  
from casman.assembly.chains import build_connection_chains, print_assembly_chains

```python

#### Database Operations

```python

# OLD (v1.x) - No longer works
from casman.database import get_parts_by_criteria, init_parts_db

# NEW (v2.x) - Required
from casman.database.operations import get_parts_by_criteria
from casman.database.initialization import init_parts_db

```python

#### Configuration

```python

# OLD (v1.x) - No longer works
from casman.config import get_config, load_config

# NEW (v2.x) - Required
from casman.config.core import get_config, load_config

```python

#### Barcode Operations

```python

# OLD (v1.x) - No longer works
from casman.barcode_utils import generate_barcode, create_printpage

# NEW (v2.x) - Required
from casman.barcode.generation import generate_barcode
from casman.barcode.printing import create_printpage

```python

#### Visualization

```python

# OLD (v1.x) - No longer works
from casman.visualization import format_ascii_chains, get_chain_summary

# NEW (v2.x) - Required
from casman.visualization.core import format_ascii_chains, get_chain_summary

```python

### 2. CLI Command Changes

While most CLI commands remain the same, there are important changes:

#### Database Scanning Command Moved

```bash

# OLD (v1.x) - No longer works
casman database scan

# NEW (v2.x) - Required
casman scan connect      # Full interactive scanning workflow
casman scan connection   # Basic connection scanning

```python

#### New Database Management Commands

```bash

# NEW in v2.x - Enhanced database management
casman database clear                # Clear databases with safety features
casman database clear --parts        # Clear only parts database
casman database clear --assembled    # Clear only assembly database
casman database print               # Display formatted database contents

```python

#### Enhanced Parts Commands

```bash

# Enhanced in v2.x
casman parts list                    # List all parts (unchanged)
casman parts add                     # Interactive addition with ALL option
casman parts search                  # NEW: Search functionality
casman parts validate                # NEW: Validation tools

```python

## Migration Steps

### Step 1: Update Python Imports

1. **Identify all CAsMan imports** in your code:
   ```bash

   grep -r "from casman" your_project/
   grep -r "import casman" your_project/
   ```

2. **Update each import** according to the mapping above

3. **Test your imports**:
   ```python

   # Test script to verify imports work
   try:
       from casman.parts.interactive import add_parts_interactive
       from casman.assembly.chains import build_connection_chains
       from casman.database.operations import get_parts_by_criteria
       print("✅ All imports successful")
   except ImportError as e:
       print(f"❌ Import failed: {e}")
   ```

### Step 2: Update CLI Usage

1. **Update any scripts** that use the old database scan command:
   ```bash

   # Replace this
   casman database scan
   
   # With this
   casman scan connect
   ```

2. **Take advantage of new database commands**:
   ```bash

   # New safety features for database management
   casman database clear --parts        # Safer than manual deletion
   casman database print               # Better than manual SQL queries
   ```

### Step 3: Update Documentation and Scripts

1. **Update any documentation** that references old CLI commands
2. **Update shell scripts** that use CAsMan commands
3. **Update CI/CD pipelines** if they use CAsMan

### Step 4: Test Migration

1. **Run your existing tests** to ensure functionality works
2. **Test CLI commands** manually to verify behavior
3. **Check error handling** to ensure proper error messages

## Common Migration Issues

### Issue 1: Import Errors

**Problem**: `ImportError: cannot import name 'function_name' from 'casman.module'`

**Solution**: Update the import to use the new modular structure:

```python

# If you see this error:

# ImportError: cannot import name 'add_parts_interactive' from 'casman.parts'

# Change this:
from casman.parts import add_parts_interactive

# To this:
from casman.parts.interactive import add_parts_interactive

```python

### Issue 2: CLI Command Not Found

**Problem**: `casman database scan` returns "command not found"

**Solution**: Use the new command structure:

```bash

# Old command no longer exists
casman database scan

# Use new command
casman scan connect

```python

### Issue 3: Configuration Loading

**Problem**: Configuration functions not found

**Solution**: Update config imports:

```python

# Change this:
from casman.config import get_config

# To this:
from casman.config.core import get_config

```python

## Compatibility Layer

CAsMan v2.0 does **not** include a compatibility layer for v1.x imports due to the complete architectural changes. All code must be updated to use the new modular structure.

## New Features Available After Migration

After migrating, you can take advantage of new v2.0 features:

### Enhanced Safety Features

```python

# New safety features in database operations
from casman.database.operations import backup_database
from casman.database.migrations import check_database_integrity

# Create backups before operations
backup_database("parts.db", "pre_migration")

```python

### Improved Validation

```python

# Enhanced part validation
from casman.parts.validation import validate_part_format
from casman.assembly.connections import validate_connection_rules

# Validate parts before operations
is_valid = validate_part_format("ANT00001P1")

```python

### Better Configuration Management

```python

# Enhanced configuration handling
from casman.config.core import get_config
from casman.config.environments import load_environment_config

# Environment-specific configurations
config = load_environment_config("production")

```python

## Testing Your Migration

### Automated Testing

Create a test script to verify your migration:

```python

#!/usr/bin/env python3
"""
CAsMan v2.0 Migration Test Script
"""

def test_imports():
    """Test that all new imports work correctly."""
    try:
        # Test parts imports
        from casman.parts.interactive import add_parts_interactive
        from casman.parts.generation import get_last_part_number
        
        # Test assembly imports  
        from casman.assembly.chains import build_connection_chains
        from casman.assembly.connections import validate_connection_rules
        
        # Test database imports
        from casman.database.operations import get_parts_by_criteria
        from casman.database.initialization import init_parts_db
        
        # Test configuration imports
        from casman.config.core import get_config
        
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_cli_commands():
    """Test that CLI commands work correctly."""
    import subprocess
    
    commands = [
        ["casman", "--help"],
        ["casman", "parts", "--help"],
        ["casman", "scan", "--help"],
        ["casman", "database", "--help"],
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Command works: {' '.join(cmd)}")
            else:
                print(f"❌ Command failed: {' '.join(cmd)}")
                return False
        except FileNotFoundError:
            print(f"❌ Command not found: {' '.join(cmd)}")
            return False
    
    return True

if __name__ == "__main__":
    print("Testing CAsMan v2.0 Migration...")
    
    if test_imports() and test_cli_commands():
        print("\n🎉 Migration successful! CAsMan v2.0 is ready to use.")
    else:
        print("\n❌ Migration issues detected. Please review the errors above.")

```python

### Manual Testing

Test key functionality manually:

```bash

# Test CLI structure
casman --help

# Test parts management
casman parts list

# Test scanning workflow
casman scan connect

# Test database management
casman database print

# Test visualization
casman visualize chains

```python

## Getting Help

If you encounter issues during migration:

1. **Check the documentation**: All modules have updated documentation
2. **Use CLI help**: Every command has `--help` for detailed information
3. **Review examples**: The README includes comprehensive examples
4. **Check GitHub issues**: For persistent problems or bug reports

## Benefits After Migration

Once migrated to v2.0, you'll benefit from:

- **🛡️ Enhanced safety features** preventing accidental data loss

- **🎯 Better organization** with focused, modular packages

- **📚 Improved documentation** with comprehensive help

- **🔧 Better maintainability** for your code

- **⚡ Performance improvements** from optimized imports

- **🧪 Enhanced testing** capabilities with modular structure

## Timeline for Migration

- **v1.x support**: Will be maintained for bug fixes only

- **Recommended migration timeframe**: 3-6 months

- **v1.x deprecation**: Will be announced with sufficient notice

The modular v2.0 architecture provides a solid foundation for future development and significantly improves the user experience with enhanced safety features and better organization.
