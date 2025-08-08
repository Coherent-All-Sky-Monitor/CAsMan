"""
Parts-related CLI commands for CAsMan.
"""

import argparse
import sys

from casman.database.operations import get_parts_by_criteria
from casman.database.initialization import init_all_databases
from casman.parts.interactive import add_parts_interactive, display_parts_interactive


def cmd_parts() -> None:
    """
    Command-line interface for parts management.

    Provides functionality to list and add parts through command-line arguments.
    Supports filtering by part type and polarization.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="CAsMan Parts Database Management\n\n"
                   "Comprehensive part management including listing, adding, and filtering.\n"
                   "Supports all CASM part types with validation and database integration.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "action",
        choices=["list", "add"],
        help="Action to perform:\n"
             "  list - Display parts from database with optional filtering\n"
             "  add  - Interactive part addition with validation (supports single type or ALL types)"
    )
    parser.add_argument("--type", help="Filter parts by type (ANTENNA, LNA, COAX1, COAX2, BACBOARD, SNAP)")
    parser.add_argument("--polarization", help="Filter parts by polarization (e.g., 1, 2)")

    # Check if help is requested or no arguments provided
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ['-h', '--help']):
        parser.print_help()
        return

    # Check if help is requested or no arguments provided
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ['-h', '--help']):
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman parts'

    init_all_databases()

    if args.action == "list":
        if args.type or args.polarization:
            parts = get_parts_by_criteria(args.type, args.polarization)
            if parts:
                print(f"Found {len(parts)} part(s):")
                print("-" * 80)
                for part in parts:
                    print(f"ID: {part[0]}")
                    print(f"Part Number: {part[1]}")
                    print(f"Part Type: {part[2]}")
                    print(f"Polarization: {part[3]}")
                    print(f"Date Created: {part[4]}")
                    print(f"Date Modified: {part[5]}")
                    print("-" * 80)
            else:
                print("No parts found matching the criteria.")
        else:
            display_parts_interactive()
    elif args.action == "add":
        add_parts_interactive()
