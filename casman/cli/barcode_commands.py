"""
Barcode and visualization CLI commands for CAsMan.
"""

import argparse
import sys

from casman.barcode_utils import generate_barcode_printpages
from casman.database import init_all_databases
from casman.visualization import format_ascii_chains


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
    parser = argparse.ArgumentParser(description="CAsMan Barcode Generation")
    parser.add_argument("action", choices=["printpages"], help="Action to perform")
    parser.add_argument(
        "--part-type", required=True, help="Part type for barcode generation"
    )
    parser.add_argument(
        "--start-number", type=int, default=1, help="Starting part number"
    )
    parser.add_argument(
        "--end-number", type=int, required=True, help="Ending part number"
    )

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
