"""
This script generates new part numbers, incrementing from the last created part number
in the database, and updates the database with these new entries. Users can specify the
number of part numbers to create and the polarization. The script ensures part numbers
are unique and consistent with existing entries, and generates corresponding barcodes.

Features
--------
- Checks the database for existing part numbers.
- Increments from the last created part number.
- Supports user input for the number of parts and polarization.
- Updates the database with new part numbers and timestamps.
- Generates barcodes for each new part number.

Usage
-----
1. Run the script.
2. Enter the part type by selecting the corresponding integer.
3. Enter the number of new part numbers to create.
4. Enter the polarization for the new parts.
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional

import barcode
from barcode.writer import ImageWriter

# Define part types and their corresponding integers
part_types = {
    1: ("ANTENNA", "ANT"),
    2: ("LNA", "LNA"),
    3: ("BACBOARD", "BAC"),
}


def init_db() -> None:
    """
    Initialize the SQLite database and create the parts table if it doesn't exist.

    Returns
    -------
    None
    """
    if not os.path.exists("database"):
        os.makedirs("database")

    conn = sqlite3.connect(os.path.join("database", "parts.db"))
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY,
            part_number TEXT UNIQUE,
            part_type TEXT,
            created_at TEXT,
            modified_at TEXT
        )"""
    )
    conn.commit()
    conn.close()


def get_last_part_number(part_type: str, polarization: str) -> Optional[str]:
    """
    Retrieve the last part number created for a given part type and polarization.
    Retrieve the last part number created for a given part type and polarization.

    Parameters
    ----------
    part_type : str
        The name of the part type.
    polarization : str
        The polarization value.

    Returns
    -------
    str or None
        The last part number if found, otherwise None.
    """
    conn = sqlite3.connect("database/parts.db")
    c = conn.cursor()
    query = """
    SELECT part_number FROM parts
    WHERE part_type = ? AND part_number LIKE ?
    ORDER BY part_number DESC LIMIT 1
    """
    c.execute(query, (part_type, f"%P{polarization}-%"))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def save_to_db(part_number: str, part_type: str) -> None:
    """
    Save the part number and part type to the database with timestamps.

    Parameters
    ----------
    part_number : str
        The part number to save.
    part_type : str
        The name of the part type.

    Returns
    -------
    None
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(os.path.join("database", "parts.db"))
        c = conn.cursor()
        c.execute(
            "INSERT INTO parts (part_number, part_type, created_at, modified_at) \
                VALUES (?, ?, ?, ?)",
            (part_number, part_type, now, now),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Part number {part_number} already exists in the database.")
    finally:
        conn.close()


def generate_barcode(part_number: str, directory: str) -> None:
    """
    Generate a barcode image for a given part number.

    Parameters
    ----------
    part_number : str
        The part number for which to generate a barcode.
    directory : str
        The directory to save the barcode image.

    Returns
    -------
    None
    """
    code128 = barcode.get("code128", part_number, writer=ImageWriter())
    barcode_path = os.path.join(directory, f"{part_number}")
    code128.save(barcode_path)
    print(f"Generated barcode for {part_number} at {barcode_path}")


def generate_new_parts(part_type: int, count: int, polarization: str) -> None:
    """
    Generate new part numbers, incrementing from the last created part number.

    Parameters
    ----------
    part_type : int
        The integer corresponding to the part type.
    count : int
        The number of new part numbers to create.
    polarization : str
        The polarization for the new parts.

    Returns
    -------
    None
    """
    type_name, prefix = part_types[part_type]

    # Create a directory for the part type if it doesn't exist
    part_dir = os.path.join("barcodes", type_name)
    if not os.path.exists(part_dir):
        os.makedirs(part_dir)

    # Determine the starting number
    last_part_number = get_last_part_number(type_name, polarization)
    if last_part_number:
        last_number = int(last_part_number.split("-")[-1])
    else:
        last_number = 0

    # Generate new part numbers
    if polarization not in ["1", "2"]:
        print("Invalid polarization. Please enter 1 or 2.")
        return

    for i in range(1, count + 1):
        new_number = last_number + i
        part_number = f"{prefix}{new_number:05d}P{polarization}"
        save_to_db(part_number, type_name)
        generate_barcode(part_number, part_dir)
        print(f"Generated and saved part number: {part_number}")


def main() -> None:
    """
    Main function to prompt the user for input and generate new part numbers.

    Returns
    -------
    None
    """
    init_db()

    print("Select part type:")
    for key, (name, _) in part_types.items():
        print(f"{key}: {name}")

    try:
        type_selection = int(input("Enter the number corresponding to the part type: "))
        if type_selection not in part_types:
            print("Invalid selection. Please enter a valid number.")
            return
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    try:
        count = int(input("Enter number of new part numbers to create: "))
    except ValueError:
        print("Invalid input. Please enter a valid integer for the number of parts.")
        return

    polarization = input("Enter polarization: ").strip().upper()

    generate_new_parts(type_selection, count, polarization)


if __name__ == "__main__":
    main()
