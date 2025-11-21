"""
Part scanning and disassembly script for CAsMan.

This script allows for entry of part numbers using a USB barcode scanner or manual input
to record disconnections. It verifies parts exist in the database and stores disconnection
records with timestamps.

Usage
-----
1. Run the script.
2. Choose to scan using a USB barcode reader or enter part numbers manually.
3. Follow the prompts to enter part numbers being disconnected.
4. Disconnection records are saved with timestamps.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

from casman.assembly.connections import record_assembly_disconnection
from casman.database.operations import check_part_in_db
from casman.database.connection import get_database_path
from casman.database.initialization import init_all_databases
from casman.parts.types import load_part_types

PART_TYPES = load_part_types()

# Dynamically determine all part types
ALL_PART_TYPES: List[str] = [name for _, (name, _) in sorted(PART_TYPES.items())]
REQUIRED_ORDER: List[str] = ALL_PART_TYPES[:-1]  # N-1 types for menu


def get_part_details(part_number: str, db_dir: Optional[str] = None):
    """
    Get part details from the database.

    Parameters
    ----------
    part_number : str
        The part number to look up.
    db_dir : Optional[str]
        Custom database directory.

    Returns
    -------
    tuple or None
        (part_type, polarization) if found, None otherwise.
    """
    try:
        db_path = get_database_path("parts.db", db_dir)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT part_type, polarization FROM parts WHERE part_number = ?",
                (part_number,),
            )
            result = cursor.fetchone()
            return result if result else None
    except (sqlite3.Error, OSError):
        return None


def validate_snap_part(snap_str: str) -> bool:
    """
    Validate a SNAP part format (SNAP<chassis><slot><port>).

    Parameters
    ----------
    snap_str : str
        The SNAP part identifier (e.g., SNAP1A00).

    Returns
    -------
    bool
        True if valid format, False otherwise.
    """
    import re

    # Format: SNAP<chassis 1-4><slot A-K><port 00-11>
    pattern = r"^SNAP[1-4][A-K](0[0-9]|1[01])$"
    return bool(re.match(pattern, snap_str))


def generate_part_number(
    part_type: str, polarization: Optional[str], number: int
) -> Optional[str]:
    """
    Generate a part number based on the part type, polarization, and number.

    Parameters
    ----------
    part_type : str
        The type of the part.
    polarization : Optional[str]
        The polarization value, or None for SNAP parts.
    number : int
        The part number.

    Returns
    -------
    Optional[str]
        The generated part number, or None if invalid.
    """
    # Dynamically generate prefix map from PART_TYPES
    prefix_map = {name: abbrev for _, (name, abbrev) in PART_TYPES.items()}
    prefix = prefix_map.get(part_type, "")

    if part_type == "SNAP":
        # Prompt for chassis, snap slot, port number
        chassis = input("Enter chassis number (1-4): ").strip()
        snap_slot = input("Enter SNAP slot (A-K): ").strip().upper()
        try:
            port = int(input("Enter SNAP port (0-11): ").strip())
            if not 0 <= port <= 11:
                print("Error: SNAP port must be between 0 and 11.")
                return None
        except ValueError:
            print("Error: Invalid input. Please enter a number between 0 and 11.")
            return None

        # Validate chassis and slot
        valid_slots = [chr(ord("A") + i) for i in range(11)]  # A-K
        if snap_slot not in valid_slots:
            print("Error: Invalid SNAP slot. Must be A-K.")
            return None
        if chassis not in ["1", "2", "3", "4"]:
            print("Error: Chassis must be 1-4.")
            return None

        snap_str = f"SNAP{chassis}{snap_slot}{port:02d}"
        print(f"SNAP connection: {snap_str}")

        return snap_str

    # Standard format: {PREFIX}{NUMBER}P{POLARIZATION}
    return f"{prefix}{number:05d}P{polarization}"


def main() -> None:
    """
    Main function to handle part disconnection entry.

    Returns
    -------
    None
    """
    # Initialize databases using casman module
    init_all_databases()

    while True:
        print("\n" + "=" * 60)
        print("DISCONNECTION WORKFLOW")
        print("=" * 60)

        # Step 1: Get first part
        print("\nEnter the FIRST part being disconnected:")
        print("Select part type:")
        for idx, name in enumerate(ALL_PART_TYPES):
            print(f"{idx}: {name}")

        try:
            part_type_index = int(
                input(
                    f"Enter the number corresponding to the part type (0-{len(ALL_PART_TYPES)-1}): "
                )
            )
            if not (0 <= part_type_index < len(ALL_PART_TYPES)):
                print("Invalid selection. Please enter a valid number.")
                continue
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        part_type = ALL_PART_TYPES[part_type_index]

        choice = input(
            "Press 1 to scan using USB scanner or 2 to enter manually: "
        ).strip()

        if choice == "1":
            part_number = input("Scan first part number: ").strip()
            # Get part details from database
            part_details = get_part_details(part_number)
            if not part_details:
                print(f"Error: Part {part_number} not found in database.")
                continue
            db_part_type, polarization_0 = part_details
            print(
                f"Scanned: {part_number}, type: {db_part_type}, polarization: {polarization_0}"
            )
        elif choice == "2":
            if part_type == "SNAP":
                part_number = generate_part_number(part_type, None, 0)
                if part_number is None:
                    continue
                polarization_0 = "N/A"
            else:
                polarization_0 = input("Enter polarization: ").strip().upper()
                number = int(input("Enter part number: ").strip())
                part_number = generate_part_number(part_type, polarization_0, number)
                if part_number is None:
                    continue
            print(f"Manually entered: {part_number}")
        else:
            print("Invalid choice. Please enter 1 or 2.")
            continue

        # Validate first part exists
        if part_type != "SNAP":
            part_exists, _ = check_part_in_db(part_number, part_type)
            if not part_exists:
                print(f"Error: {part_type} part {part_number} not found in database.")
                continue
        else:
            if not validate_snap_part(part_number):
                print(
                    f"Error: Invalid SNAP part format {part_number}. Expected format: SNAP<chassis><slot><port> (e.g., SNAP1A00)"
                )
                continue

        print(f"✓ Valid first part: {part_number}")

        # Step 2: Check for existing connections with latest status
        try:
            db_path = get_database_path("assembled_casm.db", None)
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Get all connections for this part where latest status is 'connected'
                # This ensures we only show connections that haven't been disconnected
                cursor.execute(
                    """SELECT a.part_number, a.connected_to, a.connected_to_type, a.scan_time
                       FROM assembly a
                       INNER JOIN (
                           SELECT part_number, connected_to, MAX(scan_time) as max_time
                           FROM assembly
                           WHERE part_number = ? OR connected_to = ?
                           GROUP BY part_number, connected_to
                       ) latest
                       ON a.part_number = latest.part_number
                       AND a.connected_to = latest.connected_to
                       AND a.scan_time = latest.max_time
                       WHERE a.connection_status = 'connected'
                       AND (a.part_number = ? OR a.connected_to = ?)
                       ORDER BY a.scan_time DESC""",
                    (part_number, part_number, part_number, part_number),
                )
                connections = cursor.fetchall()

            if not connections:
                print(f"\n✗ Error: Part '{part_number}' is not connected to anything.")
                print("Cannot disconnect a part that has no connections.")
                print("Please scan a different part or exit.")
                continue

            # Display connections and let user choose
            print(f"\n📋 Found {len(connections)} connection(s) for {part_number}:")
            print("-" * 70)
            for idx, (part_num, connected, conn_type, scan_time) in enumerate(
                connections, 1
            ):
                if part_num == part_number:
                    print(
                        f"{idx}. {part_num} --> {connected} ({conn_type}) [Scanned: {scan_time}]"
                    )
                else:
                    print(
                        f"{idx}. {part_num} --> {connected} ({conn_type}) [Scanned: {scan_time}]"
                    )
            print("-" * 70)

            try:
                choice_str = input(
                    f"Select connection to disconnect (1-{len(connections)}): "
                ).strip()
                choice_idx = int(choice_str) - 1
                if not (0 <= choice_idx < len(connections)):
                    print(
                        f"Error: Invalid selection. Please enter a number between 1 and {len(connections)}."
                    )
                    continue
            except ValueError:
                print("Error: Invalid input. Please enter a number.")
                continue

            # Get the selected connection details
            selected_connection = connections[choice_idx]
            conn_part_num, conn_connected_to, second_part_type, _ = selected_connection

            # Determine which part is which: part_number should be first, the other is second
            # The selected connection could have part_number as either source or target
            if conn_part_num == part_number:
                # part_number is the source, connected_to is the target
                second_part_number = conn_connected_to
            else:
                # part_number is the target, conn_part_num is the source
                # We need to swap them so part_number is first
                second_part_number = conn_part_num
                # Get the second part type from database
                second_details = get_part_details(second_part_number)
                if second_details:
                    second_part_type, _ = second_details

            # Determine polarization for the second part
            if second_part_type == "SNAP":
                polarization_1 = "N/A"
            else:
                part_details = get_part_details(second_part_number)
                if part_details:
                    _, polarization_1 = part_details
                else:
                    print(f"Error: Could not retrieve details for {second_part_number}")
                    continue

            print(f"✓ Selected connection: {part_number} -X-> {second_part_number}")

        except (sqlite3.Error, OSError) as e:
            print(f"Error checking connections: {e}")
            continue

        # Record disconnection
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        connected_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        success = record_assembly_disconnection(
            part_number=part_number,
            part_type=part_type,
            polarization=polarization_0,
            scan_time=scan_time,
            connected_to=second_part_number,
            connected_to_type=second_part_type,
            connected_polarization=polarization_1,
            connected_scan_time=connected_scan_time,
        )

        if success:
            print(
                f"\n✓ Successfully recorded disconnection: {part_number} -X-> {second_part_number}"
            )
        else:
            print(
                f"\n✗ Error recording disconnection: {part_number} -X-> {second_part_number}"
            )

        # Ask if user wants to continue
        continue_choice = (
            input("\nDo you want to disconnect another pair of parts? (y/n): ")
            .strip()
            .lower()
        )
        if continue_choice != "y":
            print("Exiting disconnection workflow.")
            break


if __name__ == "__main__":
    main()
