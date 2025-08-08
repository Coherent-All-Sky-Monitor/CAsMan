"""
Clear the CAsMan database.

This script deletes all records from the parts database and resets it to an empty state.

Usage
1. Run the script.
2. Confirm the deletion twice when prompted.
"""

import argparse
import os
import sqlite3

from casman.config.core import get_config
from casman.database.connection import get_database_path


def clear_database(db_dir: str) -> None:
    """
    Clear the parts database by deleting all records.

    Parameters
    ----------
    db_dir : str
        Path to the database directory.

    Returns
    -------
    None
    """
    db_path = get_database_path("parts.db", db_dir)

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Nothing to clear.")
        return

    print(f"Attempting to clear database at: {db_path}")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Clear the parts table
    c.execute("DELETE FROM parts")
    conn.commit()
    conn.close()

    print("Database cleared successfully.")


# Parse command-line arguments


parser = argparse.ArgumentParser(description="Clear the CAsMan database.")
default_db_dir = get_config("CASMAN_DB_DIR", "database")
parser.add_argument(
    "--db_dir",
    type=str,
    default=default_db_dir,
    help="Path to the database directory (default: from config.yaml or 'database')",
)
args = parser.parse_args()


def main() -> None:
    """
    Main function to prompt the user for confirmation and clear the database.

    Returns
    -------
    None
    """
    db_dir = args.db_dir  # Use the argument parser to get the database directory
    print(f"Defaulting to database directory: {os.path.abspath(db_dir)}")

    print(
        "WARNING: This action will delete all records in the database and cannot be undone."
    )
    confirmation1 = (
        input("Are you sure you want to proceed? (yes/no): ").strip().lower()
    )

    if confirmation1 != "yes":
        print("Operation cancelled by the user.")
        return

    confirmation2 = input("Please type 'DELETE' to confirm deletion: ").strip().upper()

    if confirmation2 != "DELETE":
        print("Operation cancelled. You did not type 'DELETE'.")
        return

    clear_database(db_dir)


if __name__ == "__main__":
    main()
    main()
