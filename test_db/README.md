# Test Database Directory

This directory is used for test database isolation.

## Purpose

When running tests, CAsMan creates temporary databases in isolated directories to prevent tests from:
- Modifying production databases in `database/`
- Creating test databases in the project root
- Interfering with each other

## How It Works

The test suite uses pytest fixtures in `tests/conftest.py` that:

1. Create a temporary directory for each test using `tmp_path`
2. Set environment variables to redirect database and barcode operations:
   - `CASMAN_PARTS_DB` → temp directory
   - `CASMAN_ASSEMBLED_DB` → temp directory
   - `CASMAN_DATABASE_DIR` → temp directory
   - `CASMAN_BARCODE_DIR` → temp directory

3. Clean up after tests complete

## What Gets Isolated

Tests are isolated from:
- **Production databases**: `database/parts.db` and `database/assembled_casm.db`
- **Production barcodes**: `barcodes/` directory contents
- **Other tests**: Each test gets its own temporary directory

### Important: CLI Database Command Tests

Tests that execute CLI database clear commands (`casman database clear`) mock the `sqlite3.connect` function to prevent actual database operations. This ensures that tests which verify database clearing functionality don't accidentally delete production data. The mocks are configured in `tests/test_cli.py` TestCLIDatabaseCommandsAdvanced class.

## Files in This Directory

Any `.db` files that appear here are test artifacts that can be safely deleted. They should be automatically cleaned up by pytest, but may persist if:
- Tests were interrupted (Ctrl+C)
- Tests crashed unexpectedly
- Cleanup fixtures failed

You can safely run:
```bash
rm -f test_db/*.db
```

## Environment Variables Used

The test isolation system respects these environment variables:

| Variable | Purpose |
|----------|---------|
| `CASMAN_PARTS_DB` | Path to parts database |
| `CASMAN_ASSEMBLED_DB` | Path to assembled CASM database |
| `CASMAN_DATABASE_DIR` | Directory containing databases |
| `CASMAN_BARCODE_DIR` | Directory for barcode outputs |

When these are set, CAsMan will use the specified paths instead of defaults, allowing tests to run in complete isolation from production data.
