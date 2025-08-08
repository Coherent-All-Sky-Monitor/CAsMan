"""
Interactive assembly operations for CAsMan.

This module provides interactive command-line interfaces for scanning
and assembling parts.
"""

import logging
import sqlite3

from casman.barcode import generate_barcode
from casman.config.core import get_config
from casman.database.connection import get_database_path

logger = logging.getLogger(__name__)

# Define the valid connection chain sequence
VALID_CONNECTION_CHAIN = [
    "ANTENNA",    # Can connect to LNA
    "LNA",        # Can connect to COAX1
    "COAX1",      # Can connect to COAX2
    "COAX2",      # Can connect to BACBOARD
    "BACBOARD",   # Can connect to SNAP
    "SNAP"        # Terminal (no outgoing connections)
]

# Create mapping for valid next connections
VALID_NEXT_CONNECTIONS = {
    "ANTENNA": ["LNA"],
    "LNA": ["COAX1"],
    "COAX1": ["COAX2"],
    "COAX2": ["BACBOARD"],
    "BACBOARD": ["SNAP"],
    "SNAP": []  # Terminal - no outgoing connections
}


def validate_connection_rules(first_part: str, first_type: str, connected_part: str, connected_type: str) -> tuple[bool, str]:
    """
    Validate that the connection follows the defined chain rules.

    Args:
        first_part (str): The part making the connection
        first_type (str): The type of the first part
        connected_part (str): The part being connected to
        connected_type (str): The type of the connected part

    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    # Check if the connection sequence is valid
    valid_next = VALID_NEXT_CONNECTIONS.get(first_type, [])
    if connected_type not in valid_next:
        return False, f"'{first_type}' can only connect to {', '.join(valid_next) if valid_next else 'no other parts'}, not '{connected_type}'"

    return True, ""


def validate_chain_directionality(part_type: str, connection_direction: str) -> tuple[bool, str]:
    """
    Validate that parts follow proper chain directionality rules.

    Args:
        part_type (str): The type of the part (ANTENNA, LNA, etc.)
        connection_direction (str): Either 'outgoing' or 'incoming'

    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    # First part type (ANTENNA) can only have outgoing connections
    if part_type == "ANTENNA" and connection_direction == "incoming":
        return False, "ANTENNA parts can only make outgoing connections. They cannot receive incoming connections."

    # Final part type (SNAP) can only have incoming connections
    if part_type == "SNAP" and connection_direction == "outgoing":
        return False, "SNAP parts can only receive incoming connections. They cannot make outgoing connections."

    return True, ""


def check_existing_connections(part_number: str) -> tuple[bool, str, list]:
    """
    Check if a part already has existing connections to prevent duplicates/branches.

    Args:
        part_number (str): The part number to check

    Returns:
        tuple[bool, str, list]: (can_connect, error_message, existing_connections)
    """
    try:
        db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
        if db_path is None:
            raise ValueError("Database path for assembled_casm.db is not set.")

        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Check outgoing connections (this part connects to others)
        c.execute(
            "SELECT connected_to, connected_to_type FROM assembly WHERE part_number = ?",
            (part_number,)
        )
        outgoing_connections = c.fetchall()

        # Check incoming connections (other parts connect to this part)
        c.execute(
            "SELECT part_number, part_type FROM assembly WHERE connected_to = ?",
            (part_number,)
        )
        incoming_connections = c.fetchall()

        conn.close()

        # Rules:
        # 1. Each part can only have ONE outgoing connection (no branching)
        # 2. Each part (including SNAP) can only have ONE incoming connection (no multiple inputs)

        if outgoing_connections:
            existing_target = outgoing_connections[0][0]
            return False, f"Part {part_number} already connects to {existing_target}. Remove existing connection first.", outgoing_connections

        # ALL parts (including SNAP) can only have one incoming connection
        if incoming_connections:
            existing_source = incoming_connections[0][0]
            return False, f"Part {part_number} already has an incoming connection from {existing_source}. Each part can only have one input.", incoming_connections

        return True, "", []

    except (sqlite3.Error, OSError, IOError) as e:
        logger.error("Error checking existing connections for %s: %s", part_number, e)
        return False, f"Database error: {e}", []


def check_target_connections(connected_part: str) -> tuple[bool, str]:
    """
    Check if the target part can accept a new connection.

    Args:
        connected_part (str): The part that will be connected to

    Returns:
        tuple[bool, str]: (can_accept, error_message)
    """
    try:
        db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
        if db_path is None:
            raise ValueError("Database path for assembled_casm.db is not set.")

        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Check how many parts already connect to this target
        c.execute(
            "SELECT part_number FROM assembly WHERE connected_to = ?",
            (connected_part,)
        )
        incoming_parts = c.fetchall()
        conn.close()

        # ALL parts (including SNAP) can only have one incoming connection
        if incoming_parts:
            existing_source = incoming_parts[0][0]
            return False, f"Part {connected_part} already has an incoming connection from {existing_source}. Each part can only have one input."

        return True, ""

    except (sqlite3.Error, OSError, IOError) as e:
        logger.error("Error checking target connections for %s: %s", connected_part, e)
        return False, f"Database error: {e}"


def validate_part_in_database(part_number: str) -> tuple[bool, str, str]:
    """
    Validate if a part exists in the parts database or SNAP mapping.

    Args:
        part_number (str): The part number to validate

    Returns:
        tuple[bool, str, str]: (is_valid, part_type, polarization)
    """
    try:
        # Check if this is a SNAP part
        if part_number.startswith("SNAP") and "_ADC" in part_number:
            return validate_snap_part(part_number)

        # For non-SNAP parts, check the regular parts database
        db_path = get_config("CASMAN_PARTS_DB", "database/parts.db")
        if db_path is None:
            raise ValueError("Database path for parts.db is not set.")

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(
            "SELECT part_type, polarization FROM parts WHERE part_number = ?",
            (part_number,)
        )
        result = c.fetchone()
        conn.close()

        if result:
            part_type, polarization = result
            return True, part_type or "UNKNOWN", polarization or "X"
        else:
            return False, "", ""
    except (sqlite3.Error, OSError, IOError) as e:
        logger.error("Error validating part %s: %s", part_number, e)
        return False, "", ""


def validate_snap_part(part_number: str) -> tuple[bool, str, str]:
    """
    Validate a SNAP part against the snap_feng_map.yaml file.

    Args:
        part_number (str): The SNAP part number to validate (e.g., SNAP002_ADC02)

    Returns:
        tuple[bool, str, str]: (is_valid, part_type, polarization)
    """
    try:
        import yaml
        import os

        # Load the SNAP to FENG mapping
        snap_map_path = get_config("CASMAN_SNAP_MAP", "database/snap_feng_map.yaml")
        if snap_map_path is None:
            snap_map_path = "database/snap_feng_map.yaml"

        if not os.path.exists(snap_map_path):
            logger.error("SNAP mapping file not found: %s", snap_map_path)
            return False, "", ""

        with open(snap_map_path, "r", encoding="utf-8") as f:
            snap_map = yaml.safe_load(f)

        # Check if the SNAP part exists in the mapping
        if part_number in snap_map:
            # SNAP part is valid if it exists in the mapping
            return True, "SNAP", "N/A"  # SNAP parts don't have traditional polarization
        else:
            return False, "", ""

    except (yaml.YAMLError, OSError, IOError) as e:
        logger.error("Error validating SNAP part %s: %s", part_number, e)
        return False, "", ""


def scan_and_assemble_interactive() -> None:
    """
    Interactive scanning and assembly function.

    Provides a command-line interface for scanning parts and recording
    their connections. Continues until the user types 'quit'.

    Returns
    -------
    None

    Examples
    --------
    >>> scan_and_assemble_interactive()  # doctest: +SKIP
    Interactive Assembly Scanner
    ============================
    Type 'quit' to exit.

    Scan first part: ANTP1-00001
    Scan connected part: LNA-P1-00001
    Connection recorded: ANTP1-00001 -> LNA-P1-00001

    Scan first part: quit
    Goodbye!
    """
    print("Interactive Assembly Scanner")
    print("=" * 30)
    print("Type 'quit' to exit.")
    print()

    while True:
        try:
            # Get first part
            first_part = input("Scan first part: ").strip()
            if first_part.lower() == "quit":
                print("Goodbye!")
                break

            if not first_part:
                print("Please enter a part number.")
                continue

            # Validate first part in database
            is_valid_first, first_type, first_polarization = validate_part_in_database(first_part)
            if not is_valid_first:
                if first_part.startswith("SNAP") and "_ADC" in first_part:
                    print(f"❌ Error: SNAP part '{first_part}' not found in snap_feng_map.yaml.")
                else:
                    print(f"❌ Error: Part '{first_part}' not found in parts database.")
                print("Please check the part number and try again.")
                continue

            print(f"✅ Valid part: {first_part} ({first_type}, {first_polarization})")

            # Get connected part
            connected_part = input("Scan connected part: ").strip()
            if connected_part.lower() == "quit":
                print("Goodbye!")
                break

            if not connected_part:
                print("Please enter a connected part number.")
                continue

            # Validate connected part in database
            is_valid_connected, connected_type, connected_polarization = validate_part_in_database(connected_part)
            if not is_valid_connected:
                if connected_part.startswith("SNAP") and "_ADC" in connected_part:
                    print(f"❌ Error: SNAP part '{connected_part}' not found in snap_feng_map.yaml.")
                else:
                    print(f"❌ Error: Part '{connected_part}' not found in parts database.")
                print("Please check the part number and try again.")
                continue

            print(f"✅ Valid part: {connected_part} ({connected_type}, {connected_polarization})")

            # Validate connection rules
            is_valid_rules, rules_error = validate_connection_rules(first_part, first_type, connected_part, connected_type)
            if not is_valid_rules:
                print(f"❌ Error: {rules_error}")
                continue

            # Validate chain directionality (first/final part restrictions)
            is_valid_outgoing, outgoing_error = validate_chain_directionality(first_type, "outgoing")
            if not is_valid_outgoing:
                print(f"❌ Error: {outgoing_error}")
                continue

            is_valid_incoming, incoming_error = validate_chain_directionality(connected_type, "incoming")
            if not is_valid_incoming:
                print(f"❌ Error: {incoming_error}")
                continue

            # Check for existing connections to prevent duplicates/branches
            if not check_existing_connections(first_part):
                print(f"❌ Error: Part '{first_part}' already has an outgoing connection. Cannot create multiple connections.")
                continue

            # Check target connections (all parts can only have one incoming connection)
            if not check_target_connections(connected_part):
                print(f"❌ Error: Part '{connected_part}' already has an incoming connection. Cannot create multiple connections.")
                continue

            # Record the connection to the database
            try:
                from datetime import datetime
                from .connections import record_assembly_connection

                # Generate current timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                success = record_assembly_connection(
                    part_number=first_part,
                    part_type=first_type,
                    polarization=first_polarization,
                    scan_time=current_time,
                    connected_to=connected_part,
                    connected_to_type=connected_type,
                    connected_polarization=connected_polarization,
                    connected_scan_time=current_time,
                )

                if success:
                    print(f"✅ Connection recorded: {first_part} --> {connected_part}")
                else:
                    print("❌ Failed to record connection to database")
                print()
            except ImportError as e:
                logger.error("Import error: %s", e)
                print(f"Error: Missing required module: {e}")
                print("Please try again.")
                print()
            except (sqlite3.Error, OSError, IOError) as e:
                logger.error("Error recording connection: %s", e)
                print(f"Error recording connection: {e}")
                print("Please try again.")
                print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except (OSError, IOError) as e:
            logger.error("Error in interactive scanning: %s", e)
            print(f"Error: {e}")
            print("Please try again.")


def main() -> None:
    """
    Main entry point for assembly scanning CLI.
    
    Provides interactive interface for assembly management operations.
    """
    print("CAsMan Assembly Management")
    print("=" * 25)
    print("1. Interactive scanning")
    print("2. Quit")

    while True:
        try:
            choice = input("\nSelect option (1-2): ").strip()
            
            if choice == "1":
                scan_and_assemble_interactive()
            elif choice == "2" or choice.lower() == "quit":
                print("Goodbye!")
                break
            else:
                print("Invalid option. Please select 1-2.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")


if __name__ == "__main__":
    main()
