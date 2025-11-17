"""
Barcode and visualization CLI commands for CAsMan.
"""

import argparse
import sys

from casman.barcode import generate_barcode_printpages
from casman.database.initialization import init_all_databases
from casman.visualization.core import format_ascii_chains


def cmd_barcode() -> None:
    """
    Command-line interface for barcode generation.

    Generates barcode printpages for specified part types and number ranges.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.
        Requires --part-type, --end-number, and optional --start-number.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="CAsMan Barcode Generation and Printing Tools\n\n"
        "Generate professional barcode labels and printable pages for CASM parts.\n"
        "Supports all part types with customizable numbering ranges and formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "action",
        choices=["printpages"],
        help="Action to perform:\n"
             "  printpages - Generate printable barcode pages for part labeling"
    )
    # Build part types help text from config
    from casman.parts.types import load_part_types
    part_types_list = ", ".join([name for _, (name, _) in sorted(load_part_types().items())])
    parser.add_argument(
        "--part-type",
        required=True,
        help=f"Part type for barcode generation ({part_types_list})"
    )
    parser.add_argument(
        "--start-number",
        type=int,
        default=1,
        help="Starting part number (default: 1)"
    )
    parser.add_argument(
        "--end-number",
        type=int,
        required=True,
        help="Ending part number (inclusive)"
    )

    # Check if help is requested or no arguments provided
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ['-h', '--help']):
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman barcode'

    if args.action == "printpages":
        try:
            generate_barcode_printpages(
                args.part_type, args.start_number, args.end_number
            )
            print(
                f"Generated barcode printpages for {args.part_type} "
                f"from {args.start_number} to {args.end_number}"
            )
        except (ValueError, OSError) as e:
            print(f"Error generating barcode printpages: {e}")


def cmd_visualize() -> None:
    """
    Command-line interface for visualization.

    Provides functionality to display ASCII chains and visualization summaries.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(description="CAsMan Visualization")
    parser.add_argument("action", choices=["chains"], help="Action to perform")

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman visualize'

    init_all_databases()

    if args.action == "chains":
        print(format_ascii_chains())
