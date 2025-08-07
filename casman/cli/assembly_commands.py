"""
Assembly-related CLI commands for CAsMan.
"""

import argparse
import sys

from casman.assembly.data import get_assembly_stats
from casman.assembly.interactive import scan_and_assemble_interactive
from casman.database.initialization import init_all_databases


def cmd_scan() -> None:
    """
    Command-line interface for scanning and assembly.

    Provides functionality for interactive scanning and assembly statistics.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="CAsMan Interactive Scanning and Assembly Management\n\n"
                   "Provides interactive scanning capabilities with "
                   "comprehensive connection validation.\n"
                   "Features real-time part validation, sequence enforcement, "
                   "and duplicate prevention.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "action",
        choices=["stats", "connection"],
        help="Action to perform:\n"
             "  stats      - Display assembly statistics and connection counts\n"
             "  connection - Start interactive connection scanning with validation"
    )

    # Check if help is requested or no arguments provided
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ['-h', '--help']):
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman scan'

    init_all_databases()

    if args.action == "stats":
        stats = get_assembly_stats()
        if stats:
            print("Assembly Statistics:")
            print(f"Total scans: {stats['total_scans']}")
            print(f"Unique parts: {stats['unique_parts']}")
            print(f"Connected parts: {stats['connected_parts']}")
            print(f"Latest scan: {stats['latest_scan'] or 'None'}")
        else:
            print("No assembly statistics available.")
    elif args.action == "connection":
        # Launch interactive connection scanner
        scan_and_assemble_interactive()
