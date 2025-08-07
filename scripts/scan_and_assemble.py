"""
Part scanning and assembly script for CAsMan.

This script allows for entry of part numbers using a USB barcode scanner or manual input.
It verifies the connectivity and alignment of parts based on a specific order and stores the
results in a database using the casman module. The script ensures that part numbers for certain
types exist in the database and checks for matching polarizations. Timestamps are recorded for
each entry, and connections are stored appropriately.

Usage
-----
1. Run the script.
2. Choose to scan using a USB barcode reader or enter part numbers manually.
3. Follow the prompts to enter part numbers and connections in the required order.
4. Results are saved, and timestamps are updated accordingly.
"""


import os
import sqlite3
from datetime import datetime
from typing import List, Optional

import yaml

from casman.assembly import record_assembly_connection
from casman.database import check_part_in_db, get_database_path, init_all_databases
from casman.parts import PART_TYPES

# Dynamically determine the required part order from PART_TYPES dict
# Only use the first N-1 part types for the main scan menu
ALL_PART_TYPES: List[str] = [
    name for _, (name, _) in sorted(
        PART_TYPES.items())]
REQUIRED_ORDER: List[str] = ALL_PART_TYPES[:-1]  # N-1 types for menu
FINAL_TYPE: str = ALL_PART_TYPES[-1]  # e.g., BACBOARD


def check_part_already_scanned(part_number: str, db_dir: Optional[str] = None) -> bool:
    """
    Check if a part has already been scanned/assembled.

    Parameters
    ----------
    part_number : str
        The part number to check.
    db_dir : Optional[str]
        Custom database directory.

    Returns
    -------
    bool
        True if the part has already been scanned, False otherwise.
    """
    try:
        db_path = get_database_path('assembled_casm.db', db_dir)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM assembly WHERE part_number = ?',
                (part_number,)
            )
            count = cursor.fetchone()[0]
            return count > 0
    except (sqlite3.Error, OSError):
        return False


def get_part_connection_count(part_number: str, db_dir: Optional[str] = None) -> int:
    """
    Get the number of times a part has been used in connections.

    Parameters
    ----------
    part_number : str
        The part number to check.
    db_dir : Optional[str]
        Custom database directory.

    Returns
    -------
    int
        Number of connections this part has been involved in.
    """
    try:
        db_path = get_database_path('assembled_casm.db', db_dir)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Count both as source and target
            cursor.execute(
                '''SELECT COUNT(*) FROM assembly
                   WHERE part_number = ? OR connected_to = ?''',
                (part_number, part_number)
            )
            count = cursor.fetchone()[0]
            return count
    except (sqlite3.Error, OSError):
        return 0


def validate_connection_order(from_type: str, to_type: str) -> bool:
    """
    Validate if a connection between two part types is allowed.

    Parameters
    ----------
    from_type : str
        The source part type.
    to_type : str
        The target part type.

    Returns
    -------
    bool
        True if connection is allowed, False otherwise.
    """
    # Define the allowed connection chain
    connection_chain = ["ANTENNA", "LNA", "COAX1", "COAX2", "BACBOARD", "SNAP"]

    try:
        from_index = connection_chain.index(from_type)
        to_index = connection_chain.index(to_type)
        # Connection is valid only if target is the next part in the chain
        return to_index == from_index + 1
    except ValueError:
        return False


def generate_part_number(
        part_type: str,
        polarization: Optional[str],
        number: int) -> Optional[str]:
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
        # Prompt for crate, snap letter, adc number
        crate = input("Enter crate number (1 or 2): ").strip()
        snap_letter = input("Enter SNAP letter (A-V): ").strip().upper()
        try:
            adcin = int(input("Enter ADC input (0-11): ").strip())
            if not 0 <= adcin <= 11:
                print("Error: ADC input must be between 0 and 11.")
                return None
        except ValueError:
            print("Error: Invalid input. Please enter a number between 0 and 11.")
            return None

        # Find SNAP number based on crate and snap letter
        # Crate 1: SNAP001-SNAP022 (A-V), Crate 2: SNAP023-SNAP043 (A-V)
        snap_letters = [chr(ord('A') + i) for i in range(22)]
        if snap_letter not in snap_letters:
            print("Error: Invalid SNAP letter. Must be A-V.")
            return None
        if crate not in ["1", "2"]:
            print("Error: Crate must be 1 or 2.")
            return None

        snap_index = snap_letters.index(snap_letter)
        if crate == "1":
            snap_number = snap_index + 1
        else:
            snap_number = 22 + snap_index + 1
        snap_str = f"SNAP{snap_number:03d}_ADC{adcin:02d}"

        # Load mapping from YAML
        db_dir = "database"
        mapping_path = os.path.join(db_dir, 'snap_feng_map.yaml')
        if os.path.exists(mapping_path):
            with open(mapping_path, 'r', encoding='utf-8') as f:
                snap_map = yaml.safe_load(f)
            if snap_str not in snap_map:
                print(
                    f"Error: SNAP input {snap_str} does not exist in the mapping YAML. \
                        Please check your entry.")
                return None
            feng_id = snap_map.get(snap_str)
            print(f"FENG ID for {snap_str}: {feng_id}")
        else:
            print("Warning: snap_feng_map.yaml not found. Skipping FENG mapping lookup.")
            return None

        return snap_str

    # Standard format: <prefix>-P<polarization>-<number>
    return f"{prefix}-P{polarization}-{number:05d}"


def main() -> None:
    """
    Main function to handle part entry and verify their connectivity.

    Returns
    -------
    None
    """
    # Initialize databases using casman module
    init_all_databases()

    while True:
        # Step 1: Choose entry method for the first part
        print("\nEnter part details for the assembly chain:")
        print("Select part type:")
        for idx, name in enumerate(REQUIRED_ORDER):
            print(f"{idx}: {name}")
        part_type_index = int(input(
            f"Enter the number corresponding to the part type (0-{len(REQUIRED_ORDER)-1}): "))
        if not (0 <= part_type_index < len(REQUIRED_ORDER)):
            print("Invalid selection. Please enter a valid number.")
            continue
        part_type = REQUIRED_ORDER[part_type_index]

        # Enforce starting with ANTENNA for a proper assembly chain
        if part_type != "ANTENNA":
            print("Warning: Assembly chains should start with ANTENNA for proper connectivity.")
            print("Do you want to continue with a partial chain? (y/n): ", end="")
            confirm = input().strip().lower()
            if confirm != "y":
                continue

        choice = input(
            "Press 1 to scan using USB scanner or 2 to enter manually: ").strip()
        if choice == "1":
            part_number = input(
                "Enter part number using USB scanner: ").strip()
            # Determine polarization from scanned part number
            try:
                polarization_0 = part_number.split("-P")[1].split("-")[0]
            except IndexError:
                print(f"Error: Invalid part number format for {part_type}.")
                continue
            print(
                f"Scanned part number: {part_number}, type: {part_type}, pol: {polarization_0}")
        elif choice == "2":
            polarization_0 = input("Enter polarization: ").strip().upper()
            number = int(input("Enter part number: ").strip())
            generated_part_number = generate_part_number(
                part_type, polarization_0, number)
            if generated_part_number is None:
                print("Error: Failed to generate part number.")
                continue
            part_number = generated_part_number
            print(f"Manually entered part number: {part_number}")
        else:
            print("Invalid choice. Please enter 1 or 2.")
            continue

        # Check if part exists in database
        part_exists, _ = check_part_in_db(part_number, part_type)
        if not part_exists:
            print(
                f"Error: {part_type} part number {part_number} not found in the database. Exiting.")
            exit(1)
        else:
            print(
                f"Valid part: {part_type} part number {part_number} found in the database.")

        # Check if part has already been scanned
        if check_part_already_scanned(part_number):
            connection_count = get_part_connection_count(part_number)
            print(
                f"Warning: Part {part_number} has already been scanned and used in {connection_count} connection(s).")
            print("Each part can only be used once in an assembly chain.")
            print("Please use a different part number.")
            continue

        # Step 2: Only allow scanning/connecting for the first N-1 part types
        current_index = REQUIRED_ORDER.index(part_type)
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if current_index == len(REQUIRED_ORDER) - 1:
            print(
                f"This is the last part in the sequence ({FINAL_TYPE}). It must be connected to a SNAP board.")
            # Prompt for SNAP connection
            print("Enter SNAP/FENG connection details:")
            crate = input("Enter crate number (1 or 2): ").strip()
            snap_letter = input("Enter SNAP letter (A-V): ").strip().upper()
            try:
                adcin = int(input("Enter ADC input (0-11): ").strip())
                if not 0 <= adcin <= 11:
                    print("Error: ADC input must be between 0 and 11.")
                    continue
            except ValueError:
                print("Error: Invalid input. Please enter a number between 0 and 11.")
                continue

            snap_letters = [chr(ord('A') + i) for i in range(22)]
            if snap_letter not in snap_letters:
                print("Error: Invalid SNAP letter. Must be A-V.")
                continue
            if crate not in ["1", "2"]:
                print("Error: Crate must be 1 or 2.")
                continue

            snap_index = snap_letters.index(snap_letter)
            if crate == "1":
                snap_number = snap_index + 1
            else:
                snap_number = 22 + snap_index + 1
            snap_str = f"SNAP{snap_number:03d}_ADC{adcin:02d}"
            feng_id = f"FENG_{crate}{snap_letter}{adcin:02d}"

            # Load mapping from YAML
            db_dir = "database"
            mapping_path = os.path.join(db_dir, 'snap_feng_map.yaml')
            if os.path.exists(mapping_path):
                with open(mapping_path, 'r', encoding='utf-8') as f:
                    snap_map = yaml.safe_load(f)
                if snap_str not in snap_map:
                    print(
                        f"Error: SNAP input {snap_str} does not exist in the mapping YAML. Please check your entry.")
                    continue
                if snap_map[snap_str] != feng_id:
                    print(
                        f"Error: FENG ID mismatch. Expected {feng_id} for {snap_str}, found {snap_map[snap_str]} in YAML.")
                    continue
                print(f"FENG ID for {snap_str}: {feng_id}")
            else:
                print(
                    "Warning: snap_feng_map.yaml not found. Skipping FENG mapping lookup.")
                continue

            connected_to_type = "FENGINE"
            connected_polarization = "N/A"
            connected_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Save to database
            success = record_assembly_connection(
                part_number=part_number,
                part_type=part_type,
                polarization=polarization_0,
                scan_time=scan_time,
                connected_to=snap_str,
                connected_to_type=connected_to_type,
                connected_polarization=connected_polarization,
                connected_scan_time=connected_scan_time
            )
            if success:
                print(
                    f"Successfully recorded connection: {part_number} ---> {snap_str} / {feng_id}")
            else:
                print(
                    f"Error recording connection: {part_number} ---> {snap_str} / {feng_id}")
            # Ask if user wants to scan another part after final connection
            continue_choice = input(
                "Do you want to enter another set of parts? (y/n): ").strip().lower()
            if continue_choice != "y":
                print("Exiting program.")
                break
            else:
                continue

        # Only prompt for next part if not at the last part type
        next_part_type = REQUIRED_ORDER[current_index + 1]
        print(f"\nEnter the part number of {next_part_type}:")

        print(f"\nChoose entry method for {next_part_type}:")
        choice = input(
            "Press 1 to scan using USB scanner or 2 to enter manually: "
        ).strip()

        if choice == "1":
            next_part_number = input(
                "Enter part number using USB scanner: "
            ).strip()

            # Determine part type from scanned part number
            scanned_part_type = None
            for ptype_info in PART_TYPES.values():
                if f"{ptype_info[1]}-" in next_part_number:
                    scanned_part_type = ptype_info[0]
                    break

            if not scanned_part_type:
                print(
                    "Error: Unable to determine part type from the scanned part number."
                )
                continue

            if scanned_part_type != next_part_type:
                print(f"ERROR: Next part must be {next_part_type}")
                continue

            try:
                polarization_1 = next_part_number.split("-P")[1].split("-")[0]
            except IndexError:
                print("Error: Invalid part number format")
                continue

            if polarization_1 != polarization_0:
                print(
                    f"Error: Polarization mismatch for {scanned_part_type}. "
                    f"Expected P{polarization_0} alignment."
                )
                continue
        else:
            print(f"Manually enter {next_part_type} part number: ")
            polarization_1 = input("Enter polarization: ").strip().upper()
            if polarization_1 != polarization_0:
                print(
                    f"Error: Polarization mismatch for {next_part_type}. \
                        Expected P{polarization_0} alignment."
                )
                continue
            number = int(input("Enter part number: ").strip())
            generated_next_part_number = generate_part_number(
                next_part_type, polarization_1, number
            )
            if generated_next_part_number is None:
                print("Error: Failed to generate part number.")
                continue
            next_part_number = generated_next_part_number

        print(
            f"Next part number: {next_part_number}, type: {next_part_type}, pol: {polarization_1}"
        )

        # Check if next part exists in database using casman module
        next_part_exists, _ = check_part_in_db(
            next_part_number, next_part_type)
        if not next_part_exists:
            print(
                f"Error: {next_part_type} part number {next_part_number} not found in the database."
            )
            continue

        # Check if next part has already been scanned
        if check_part_already_scanned(next_part_number):
            connection_count = get_part_connection_count(next_part_number)
            print(
                f"Warning: Part {next_part_number} has already been scanned and used in {connection_count} connection(s).")
            print("Each part can only be used once in an assembly chain.")
            print("Please use a different part number.")
            continue

        # Validate connection order
        if not validate_connection_order(part_type, next_part_type):
            print(
                f"Error: Invalid connection order. {part_type} cannot be connected to {next_part_type}.")
            print("Valid connection order: ANTENNA → LNA → COAX1 → COAX2 → BACBOARD → SNAP")
            continue

        connected_to_type = next_part_type
        connected_polarization = polarization_1
        connected_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Save to database
        success = record_assembly_connection(
            part_number=part_number,
            part_type=part_type,
            polarization=str(polarization_0) if polarization_0 is not None else "",
            scan_time=scan_time,
            connected_to=next_part_number,
            connected_to_type=connected_to_type,
            connected_polarization=str(connected_polarization) if connected_polarization is not None else "",
            connected_scan_time=connected_scan_time)
        if success:
            print(
                f"Successfully recorded connection: {part_number} ---> {next_part_number}")
        else:
            print(
                f"Error recording connection: {part_number} ---> {next_part_number}")

        continue_choice = (
            input("Do you want to enter another set of parts? (y/n): ").strip().lower())
        if continue_choice != "y":
            break


if __name__ == "__main__":
    main()
