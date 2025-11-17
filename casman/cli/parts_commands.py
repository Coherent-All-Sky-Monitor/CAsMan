"""
Parts-related CLI commands for CAsMan.
"""

import argparse
import sys
import shutil

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
        "action", choices=[
            "list", "add"], help="Action to perform:\n"
        "  list - Display parts from database with optional filtering\n"
        "  add  - Interactive part addition with validation (supports single type or ALL types)")
    # Build part types help text from config
    from casman.parts.types import load_part_types
    part_types_list = ", ".join([name for _, (name, _) in sorted(load_part_types().items())])
    parser.add_argument("--type", help=f"Filter parts by type ({part_types_list})")
    parser.add_argument("--polarization", help="Filter parts by polarization (e.g., 1, 2)")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Print all parts in the database (ignores filters)")

    # Check if help is requested or no arguments provided
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ['-h', '--help']):
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman parts'

    init_all_databases()

    if args.action == "list":
        if args.all:
            parts = get_parts_by_criteria(None, None)
            if parts:
                headers = [
                    "ID",
                    "Part Number",
                    "Part Type",
                    "Polarization",
                    "Date Created",
                    "Date Modified"]
                col_widths = [max(len(str(row[i])) for row in parts + [headers]) for i in range(6)]
                table_width = sum(col_widths) + 5 * 3 + 2  # 3 spaces between columns, 2 for borders
                term_width = shutil.get_terminal_size((80, 20)).columns
                if table_width <= term_width:
                    # Enhanced ASCII table
                    sep = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"

                    def row_line(row):
                        return "| " + " | ".join(f"{str(cell):<{w}}" for cell,
                                                 w in zip(row, col_widths)) + " |"
                    print(sep)
                    print(row_line(headers))
                    print(sep)
                    for part in parts:
                        print(row_line(part))
                    print(sep)
                else:
                    # Fallback: flat list
                    for part in parts:
                        print(f"ID: {part[0]}")
                        print(f"Part Number: {part[1]}")
                        print(f"Part Type: {part[2]}")
                        print(f"Polarization: {part[3]}")
                        print(f"Date Created: {part[4]}")
                        print(f"Date Modified: {part[5]}")
                        print("-" * 80)
            else:
                print("No parts found in the database.")
        elif args.type or args.polarization:
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
