"""
Database reading script for CAsMan.

This script reads and displays part records using the casman module.
Users can filter results by part type and polarization, or choose to view all records.
The script supports all part types defined in the casman.parts module.

Usage
-----
1. Run the script.
2. Select the part type by entering the corresponding integer.
3. Optionally enter a polarization, or press Enter to include all.
4. View the displayed records based on the selected criteria.
"""

import argparse
import logging
import os
import sqlite3

from casman.database.operations import get_parts_by_criteria
from casman.parts.types import load_part_types
from casman.config.utils import setup_logging

PART_TYPES = load_part_types()

# Configure logging from config
setup_logging()

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Read parts from the database.")
parser.add_argument(
    "--db_dir",
    type=str,
    default="database",
    help="Path to the database directory (default: 'database')",
)
args = parser.parse_args()


def read_database() -> None:
    """
    Read and display entries from the parts database filtered by part type and polarization.

    Returns
    -------
    None
    """
    # Display part type options
    print("Select part type:")
    # Show part types in required order (by PART_TYPES key, excluding SNAP)
    selectable_types = [
        (k, v) for k, v in sorted(PART_TYPES.items()) if v[0].upper() != "SNAP"
    ]
    for idx, (key, (name, _)) in enumerate(selectable_types, 1):
        print(f"{idx}: {name}")
    print(f"{len(selectable_types) + 1}: ALL")

    # Handle user selection for part type
    try:
        type_selection = int(input("Enter the number corresponding to the part type: "))
        if type_selection == len(selectable_types) + 1:
            # "ALL" option selected
            part_type = None
        elif 1 <= type_selection <= len(selectable_types):
            part_type = selectable_types[type_selection - 1][1][0]
        else:
            print("Invalid selection. Please enter a valid number.")
            return
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    # Prompt the user for polarization
    polarization = (
        input("Enter polarization (or press Enter to include all): ").strip().upper()
    )

    # Print the full path of the database being read
    db_path = os.path.abspath(os.path.join(args.db_dir, "parts.db"))
    print(f"Reading database from: {db_path}")

    # Get records using casman module
    if part_type is None:  # "ALL" option
        records = get_parts_by_criteria(None, None, args.db_dir)
    else:
        # Get all records of this part type first, then filter by polarization
        # if needed
        try:
            records = get_parts_by_criteria(part_type, None, args.db_dir)
            logging.debug("Fetched records for part type %s: %s", part_type, records)
        except sqlite3.OperationalError as op_err:
            logging.error("Operational error in database: %s", op_err)
            return
        except sqlite3.IntegrityError as int_err:
            logging.error("Integrity error in database: %s", int_err)
            return
        except sqlite3.DatabaseError as db_err:
            logging.error("General database error: %s", db_err)
            return

        # Apply polarization filtering manually if specified
        if polarization:
            filtered_records = []
            pattern = f"P{polarization}-"
            for record in records:
                part_number = record[1]  # part_number is at index 1
                if pattern in part_number:
                    filtered_records.append(record)
            records = filtered_records

    # Check if there are any records
    if not records:
        print("No records found for the specified criteria.")
    else:
        # Enhanced ASCII table
        headers = [
            "ID",
            "Part Number",
            "Part Type",
            "Polarization",
            "Date Created",
            "Date Modified",
        ]
        # Prepare rows for table (include polarization)
        table_rows = [
            [str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5])]
            for r in records
        ]
        # Calculate column widths
        col_widths = [
            max(len(str(row[i])) for row in table_rows + [headers])
            for i in range(len(headers))
        ]
        # Table drawing helpers

        def h(char: str, width: int) -> str:
            return char * width

        # Top border
        top = "┌" + "┬".join(h("─", w + 2) for w in col_widths) + "┐"
        # Header row
        header_row = (
            "│ "
            + " │ ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
            + " │"
        )
        # Separator
        sep = "├" + "┼".join(h("─", w + 2) for w in col_widths) + "┤"
        # Bottom border
        bottom = "└" + "┴".join(h("─", w + 2) for w in col_widths) + "┘"
        print(top)
        print(header_row)
        print(sep)
        for row in table_rows:
            row_str = (
                "│ "
                + " │ ".join(f"{row[i]:<{col_widths[i]}}" for i in range(len(row)))
                + " │"
            )
            print(row_str)
        print(bottom)


if __name__ == "__main__":
    read_database()
