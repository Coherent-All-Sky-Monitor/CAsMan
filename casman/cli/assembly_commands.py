"""
Assembly-related CLI commands for CAsMan.
"""

import argparse
import sys
from datetime import datetime

from casman.assembly import get_assembly_stats, record_assembly_connection
from casman.database import check_part_in_db, init_all_databases


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
    parser = argparse.ArgumentParser(description="CAsMan Scanning and Assembly")
    parser.add_argument("action", choices=["stats"], help="Action to perform")

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


def cmd_assemble() -> None:
    """
    Command-line interface for assembly operations.

    Provides streamlined part assembly functionality with connection recording.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(description="CAsMan Assembly Operations")
    parser.add_argument("action", choices=["connect"], help="Action to perform")
    parser.add_argument("--part1", required=True, help="First part number")
    parser.add_argument("--part1-type", required=True, help="First part type")
    parser.add_argument(
        "--part2", required=True, help="Second part number or SNAP connection"
    )
    parser.add_argument("--part2-type", required=True, help="Second part type")
    parser.add_argument(
        "--polarization", required=True, help="Polarization for both parts"
    )

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman assemble'

    init_all_databases()

    if args.action == "connect":
        # Validate parts exist in database
        part1_exists, _ = check_part_in_db(args.part1, args.part1_type)
        if not part1_exists:
            print(f"Error: {args.part1_type} part {args.part1} not found in database")
            return

        # For non-FENGINE connections, check if part2 exists
        if args.part2_type != "FENGINE":
            part2_exists, _ = check_part_in_db(args.part2, args.part2_type)
            if not part2_exists:
                print(
                    f"Error: {args.part2_type} part {args.part2} not found in database"
                )
                return

        # Record the connection
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        connected_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        success = record_assembly_connection(
            part_number=args.part1,
            part_type=args.part1_type,
            polarization=args.polarization,
            scan_time=scan_time,
            connected_to=args.part2,
            connected_to_type=args.part2_type,
            connected_polarization=(
                args.polarization if args.part2_type != "FENGINE" else "N/A"
            ),
            connected_scan_time=connected_scan_time,
        )

        if success:
            print(f"Successfully recorded connection: {args.part1} ---> {args.part2}")
        else:
            print(f"Error recording connection: {args.part1} ---> {args.part2}")
