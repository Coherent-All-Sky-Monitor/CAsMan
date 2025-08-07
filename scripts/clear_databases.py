"""
Clear CAsMan databases (parts.db and/or assembled_casm.db).

This script deletes all records from the parts and/or assembled_casm databases.
By default, both databases are cleared unless specific arguments are given.

Usage:
    python clear_databases.py           # Clears both databases (with confirmation)
    python clear_databases.py --parts   # Clears only parts.db
    python clear_databases.py --assembled  # Clears only assembled_casm.db
    python clear_databases.py --parts --assembled  # Clears both (explicit)
"""

from casman.database import get_database_path
from casman.config import get_config
import sys
import sqlite3
import os
import argparse


def print_stop_sign() -> None:
    """
    Print a full color enhanced ASCII stop sign to the terminal.
    """
    stop_sign = (
        "\x1b[1;37;41m\n"
        "\n"
        "                  ████████████████████████████████                \n"
        "                ████████████████████████████████████                \n"
        "              ████████████████████████████████████████            \n"
        "            ████████████████████████████████████████████         \n"
        "          ████████████████████████████████████████████████       \n"
        "        ████████████████████████████████████████████████████     \n"
        "      ████████████████████████████████████████████████████████   \n"
        "   █████████████████████████████████████████████████████████████  \n"
        " █████████████████████████      STOP       ███████████████████████ \n"
        "   █████████████████████████████████████████████████████████████  \n"
        "     █████████████████████████████████████████████████████████  \n"
        "       █████████████████████████████████████████████████████     \n"
        "         █████████████████████████████████████████████████       \n"
        "           █████████████████████████████████████████████         \n"
        "             █████████████████████████████████████████            \n"
        "               █████████████████████████████████████                \n"
        "                 █████████████████████████████████               \n"
        "\x1b[0m")
    print(stop_sign)


def clear_parts_db(db_dir: str) -> None:
    """
    Clear the parts database by deleting all records.
    """
    db_path = get_database_path("parts.db", db_dir)
    if not os.path.exists(db_path):
        print(f"Parts database not found at {db_path}. Nothing to clear.")
        return
    print_stop_sign()
    print(
        f"WARNING: This will DELETE ALL records from the parts database at: {db_path}")
    confirm1 = input(
        "Are you sure you want to clear the parts database? (yes/no): ").strip().lower()
    if confirm1 != "yes":
        print("Aborted.")
        return
    confirm2 = input(
        "This action is IRREVERSIBLE. Type 'yes' again to confirm: ").strip().lower()
    if confirm2 != "yes":
        print("Aborted.")
        return
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("DELETE FROM parts")
        conn.commit()
        conn.close()
        print("All records deleted from parts database.")
    except (sqlite3.Error, OSError) as e:
        print(f"Error clearing parts database: {e}")
        sys.exit(1)


def clear_assembled_db() -> None:
    """
    Clear all records from the assembled_casm.db database after double confirmation.
    """
    db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if db_path is None:
        print("Error: Database path could not be determined from config.")
        sys.exit(1)
    print_stop_sign()
    print(
        f"WARNING: This will DELETE ALL records from the assembled_casm database at: {db_path}")
    confirm1 = input(
        "Are you sure you want to clear the assembled_casm database? (yes/no): ").strip().lower()
    if confirm1 != "yes":
        print("Aborted.")
        return
    confirm2 = input(
        "This action is IRREVERSIBLE. Type 'yes' again to confirm: ").strip().lower()
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
        print(f"Error clearing assembled_casm database: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Clear CAsMan databases.")
    parser.add_argument(
        '--parts',
        action='store_true',
        help='Clear parts.db only')
    parser.add_argument(
        '--assembled',
        action='store_true',
        help='Clear assembled_casm.db only')
    args = parser.parse_args()

    # Default: clear both if no argument is given
    clear_parts = args.parts or not (args.parts or args.assembled)
    clear_assembled = args.assembled or not (args.parts or args.assembled)

    # Use current working directory as project root, database is at database/
    db_dir = "database"

    if clear_parts:
        clear_parts_db(db_dir)
    if clear_assembled:
        clear_assembled_db()


if __name__ == "__main__":
    main()
