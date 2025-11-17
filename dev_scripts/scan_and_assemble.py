"""
This script allows for entry of part numbers using a USB barcode scanner or manual input.
It verifies the connectivity and alignment of parts based on a specific order and stores the
results in a database called assembled_casm.db. The script ensures that part numbers for certain
types exist in the database and checks for matching polarizations. Timestamps are recorded for
each entry, and connections are stored appropriately.

Usage
-----
1. Run the script.
2. Choose to scan using a USB barcode reader or enter part numbers manually.
3. Follow the prompts to enter part numbers and connections in the required order.
4. Results are saved, and timestamps are updated accordingly.
"""

import sqlite3
from datetime import datetime

# Define part types with numerical selection
part_types = {
    1: ("ANTENNA", "ANT"),
    2: ("LNA", "LNA"),
    3: ("BACBOARD", "BAC"),
}

# Define the required part order
required_order = ["ANTENNA", "LNA", "BACBOARD", "SNAP"]


def init_assembled_db():
    """Initialize the assembled_casm.db database and create necessary tables if they don't exist."""
    with sqlite3.connect("database/assembled_casm.db") as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS assembly (
                id INTEGER PRIMARY KEY,
                part_number TEXT,
                part_type TEXT,
                polarization TEXT,
                scan_time TEXT,
                connected_to TEXT,
                connected_to_type TEXT,
                connected_polarization TEXT,
                connected_scan_time TEXT
            )"""
        )
        conn.commit()


def check_part_in_db(part_number, part_type):
    """
    Check if a part number exists in the parts.db database for the specified part type.

    Parameters
    ----------
    part_number : str
        The part number to check.
    part_type : str
        The type of the part.

    Returns
    -------
    bool
        True if the part exists, False otherwise.
    """
    with sqlite3.connect("database/parts.db") as conn:
        c = conn.cursor()
        c.execute(
            "SELECT part_number FROM parts WHERE part_number = ? AND part_type = ?",
            (part_number, part_type),
        )
        return c.fetchone() is not None


def update_modified_at(part_number):
    """
    Update the modified_at timestamp for a given part number in parts.db.

    Parameters
    ----------
    part_number : str
        The part number to update.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect("database/parts.db") as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE parts SET modified_at = ? WHERE part_number = ?", (now, part_number)
        )
        conn.commit()


def record_scan(
    part_number,
    part_type,
    polarization,
    scan_time,
    connected_to,
    connected_to_type,
    connected_polarization,
    connected_scan_time,
):
    """
    Record the scan information into the assembled_casm.db database.

    Parameters
    ----------
    part_number : str
        The part number scanned.
    part_type : str
        The type of the part.
    polarization : str or None
        The polarization of the part, or None for SNAP.
    scan_time : str
        The timestamp of the scan.
    connected_to : str
        Where the part is connected.
    connected_to_type : str
        The type of the connected part.
    connected_polarization : str
        The polarization of the connected part.
    connected_scan_time : str
        The timestamp of the connected part scan.
    """
    with sqlite3.connect("database/assembled_casm.db") as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO assembly (part_number, part_type, polarization, scan_time,
                                     connected_to, connected_to_type, connected_polarization, connected_scan_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                part_number,
                part_type,
                polarization,
                scan_time,
                connected_to,
                connected_to_type,
                connected_polarization,
                connected_scan_time,
            ),
        )
        conn.commit()
    print(f"Successfully updated database with part number: {part_number}")


def generate_part_number(part_type, polarization, number):
    """Generate a part number based on the part type, polarization, and number."""
    prefix_map = {
        "ANTENNA": "ANT",
        "LNA": "LNA",
        "BACBOARD": "BAC",
        "SNAP": "SNP",
    }
    prefix = prefix_map.get(part_type, "")

    if part_type == "SNAP":
        while True:
            try:
                adcin = int(input("Enter ADC input (0-11): ").strip())
                if 0 <= adcin <= 11:
                    break
                else:
                    print("Error: ADC input must be between 0 and 11.")
            except ValueError:
                print("Error: Invalid input. Please enter a number between 0 and 11.")

        snap_number = f"{number:03d}"
        if len(snap_number) != 3:
            print("Error: SNAP number must be exactly three digits.")
            return None

        return f"{prefix}-D211{snap_number}-ADC{adcin:02d}"

    return f"{prefix}{number:05d}P{polarization}"


def verify_connections(part_number, part_type):
    """
    Verify if the part can connect to another part based on the connection rules.

    Parameters
    ----------
    part_number : str
        The part number to verify.
    part_type : str
        The type of the part being verified.

    Returns
    -------
    bool
        True if the part can connect, False otherwise.
    """
    with sqlite3.connect("database/assembled_casm.db") as conn:
        c = conn.cursor()

        # Check the number of connections for ANTENNA, LNA, and BACBOARD
        if part_type == "ANTENNA":
            c.execute(
                "SELECT COUNT(*) FROM assembly WHERE connected_to = ? AND connected_to_type = 'LNA'",
                (part_number,),
            )
            lna_connections = c.fetchone()[0]
            if lna_connections >= 1:
                print(f"Error: {part_number} (ANTENNA) can only connect to one LNA.")
                return False
        elif part_type == "LNA":
            c.execute(
                "SELECT COUNT(*) FROM assembly WHERE part_number = ? AND part_type = 'ANTENNA'",
                (part_number,),
            )
            antenna_connections = c.fetchone()[0]
            c.execute(
                "SELECT COUNT(*) FROM assembly WHERE part_number = ? AND part_type = 'BACBOARD'",
                (part_number,),
            )
            bacboard_connections = c.fetchone()[0]
            if antenna_connections >= 1 and bacboard_connections >= 1:
                print(
                    f"Error: {part_number} (LNA) can only connect to one ANTENNA and one BACBOARD."
                )
                return False
        elif part_type == "BACBOARD":
            c.execute(
                "SELECT COUNT(*) FROM assembly WHERE connected_to = ? AND connected_to_type = 'LNA'",
                (part_number,),
            )
            lna_connections = c.fetchone()[0]
            if lna_connections >= 1:
                print(f"Error: {part_number} (BACBOARD) can only connect to one LNA.")
                return False

    return True


def main():
    """
    Main function to handle part entry and verify their connectivity.
    """
    init_assembled_db()  # Initialize the database

    while True:
        # Step 1: Choose entry method for the first part
        print("\nChoose entry method for any part:")
        choice = input(
            "Press 1 to scan using USB scanner or 2 to enter manually: "
        ).strip()

        if choice == "1":
            part_number = input("Enter part number using USB scanner: ").strip()
            # Determine part type from scanned part number
            part_type = next(
                (
                    ptype
                    for ptype, prefix in part_types.values()
                    if prefix in part_number
                ),
                None,
            )

            if not part_type:
                print(
                    "Error: Unable to determine part type from the scanned part number."
                )
                continue

            try:
                polarization_0 = part_number.split("P")[1].split("-")[0]
            except IndexError:
                print(f"Error: Invalid part number format for {part_type}.")
                break

            print(
                f"Scanned part number: {part_number}, type: {part_type}, pol: {polarization_0}"
            )
        elif choice == "2":
            print("\nEnter part details manually.")
            print("Select part type:")
            for key, (name, _) in part_types.items():
                print(f"{key}: {name}")
            part_type_index = int(
                input("Enter the number corresponding to the part type: ")
            )
            part_type = part_types[part_type_index][0]

            polarization_0 = input("Enter polarization: ").strip().upper()
            number = int(input("Enter part number: ").strip())
            part_number = generate_part_number(part_type, polarization_0, number)
            print(f"Manually entered part number: {part_number}")
        else:
            print("Invalid choice. Please enter 1 or 2.")
            continue

        if not check_part_in_db(part_number, part_type):
            print(
                f"Error: {part_type} part number {part_number} not found in the database."
            )
            continue

        # Record the first part
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Step 2: Enter the next part in the required order
        current_index = required_order.index(part_type)
        next_part_type = required_order[current_index + 1]
        print(f"\nEnter the part number of {next_part_type}:")

        if current_index < len(required_order) - 1:
            print(f"\nChoose entry method for {next_part_type}:")
            choice = input(
                "Press 1 to scan using USB scanner or 2 to enter manually: "
            ).strip()
            if choice == "1":
                next_part_number = input(
                    "Enter part number using USB scanner: "
                ).strip()
                part_type = next(
                    (
                        ptype
                        for ptype, prefix in part_types.values()
                        if prefix in next_part_number
                    ),
                    None,
                )

                if not part_type:
                    print(
                        "Error: Unable to determine part type from the scanned part number."
                    )
                    continue

                if part_type != next_part_type:
                    print(f"ERROR: Next part must be {next_part_type}")
                    break

                try:
                    polarization_1 = next_part_number.split("P")[1].split("-")[0]
                except IndexError:
                    print("Error: Invalid part number format")
                    break

                if polarization_1 != polarization_0:
                    print(
                        f"Error: Polarization mismatch for {part_type}. Expected P{polarization_0} alignment."
                    )
            else:
                print(f"Manually enter {next_part_type} part number: ")
                polarization_1 = input("Enter polarization: ").strip().upper()
                if polarization_1 != polarization_0:
                    print(
                        f"Error: Polarization mismatch for {part_type}. Expected P{polarization_0} alignment."
                    )
                    break
                number = int(input("Enter part number: ").strip())
                next_part_number = generate_part_number(
                    next_part_type, polarization_1, number
                )

            print(
                f"Scanned part number: {next_part_number}, type: {part_type}, pol: {polarization_0}"
            )

            if not check_part_in_db(next_part_number, next_part_type):
                print(
                    f"Error: {next_part_type} part number {next_part_number} not found in the database."
                )
                continue

            if not verify_connections(part_number, part_type):
                continue

            connected_to_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            record_scan(
                part_number,
                part_type,
                polarization_0,
                scan_time,
                next_part_number,
                next_part_type,
                polarization_1,
                connected_to_scan_time,
            )

            part_number = next_part_number
            part_type = next_part_type

        continue_choice = (
            input("Do you want to enter another set of parts? (y/n): ").strip().lower()
        )
        if continue_choice != "y":
            break


if __name__ == "__main__":
    main()
