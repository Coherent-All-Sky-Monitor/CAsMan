"""
clear_assembled_db.py

Script to clear (delete all records from) the assembled_casm.db database.
Asks the user for confirmation twice before proceeding.
Uses the database path from config.yaml via casman.config.get_config.
"""

import os
import sqlite3
import sys

from casman.config import get_config

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "casman"))
)


def main() -> None:
    """
    Clear all records from the assembled_casm.db database after double confirmation.
    The database path is read from config.yaml via casman.config.get_config.
    Asks the user for confirmation twice before proceeding.
    """
    db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if db_path is None:
        print("Error: Database path could not be determined from config.")
        sys.exit(1)
    print(
        f"WARNING: This will DELETE ALL records from the assembled_casm database at: {db_path}"
    )
    confirm1 = (
        input("Are you sure you want to clear the assembled_casm database? (yes/no): ")
        .strip()
        .lower()
    )
    if confirm1 != "yes":
        print("Aborted.")
        return
    confirm2 = (
        input("This action is IRREVERSIBLE. Type 'yes' again to confirm: ")
        .strip()
        .lower()
    )
    if confirm2 != "yes":
        print("Aborted.")
        return
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("DELETE FROM assembly")
        conn.commit()
        conn.close()
        print("All records deleted from assembled_casm database.")
    except (sqlite3.Error, OSError) as e:
        print(f"Error clearing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
