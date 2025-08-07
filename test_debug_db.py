"""Debugging test for the parts database issue."""

import os
import sqlite3
from casman.database import init_parts_db, get_database_path
from casman.database.connection import find_project_root


def test_debug_database_paths():
    """Debug test to check database paths during pytest."""
    print("\n=== DEBUG INFO ===")
    print(f"CWD: {os.getcwd()}")
    print(f"Project root: {find_project_root()}")

    db_path = get_database_path('parts.db', None)
    print(f"Database path: {db_path}")
    print(f"Database exists before init: {os.path.exists(db_path)}")

    # Try to initialize
    print("Initializing database...")
    init_parts_db(None)

    print(f"Database exists after init: {os.path.exists(db_path)}")

    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        conn.close()

    # Try to call generate_part_numbers
    from casman.parts.generation import generate_part_numbers

    print("Calling generate_part_numbers...")
    try:
        result = generate_part_numbers("ANTENNA", 0, "1")
        print(f"Success! Result: {result}")
        assert isinstance(result, list)
    except Exception as e:
        print(f"Failed: {e}")
        raise


if __name__ == "__main__":
    test_debug_database_paths()
