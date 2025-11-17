"""
gen_init_part_number.py Generate Initial Part Number

This script generates unique part numbers and corresponding barcodes for the first time.
It uses a SQLite database to store part numbers and ensure their uniqueness.
The user can select part types and specify the number of part numbers to generate.

Features
--------
- Supports part types: ANTENNA, LNA, COAX1, COAX2, BACBOARD.
- Generates barcodes using the Code128 format.
- Stores part numbers and types in a SQLite database.
- Organizes barcode images in directories based on part type.
- Tracks creation and modification dates for each part.

Usage
-----
1. Run the script.
2. Select the part type.
3. Enter the number of part numbers to generate.
4. Enter the polarization.
5. The script generates part numbers, saves them to the database, and creates barcode images.
"""

import os
import sqlite3
from datetime import datetime

import barcode
from barcode.writer import ImageWriter

# Define part types and their prefixes
part_types = {
    1: ("ANTENNA", "ANT"),
    2: ("LNA", "LNA"),
    3: ("COAX1", "COX1"),
    4: ("COAX2", "COX2"),
    5: ("BACBOARD", "BAC"),
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
            "INSERT INTO parts (part_number, part_type, created_at, \
            modified_at) VALUES (?, ?, ?, ?)",
            (part_number, part_type, now, now),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Part number {part_number} already exists in the database.")
    finally:
        conn.close()


def generate_parts(part_type: int, count: int) -> None:
    """
    Generate part numbers and corresponding barcode images for a given part type.

    Parameters
    ----------
    part_type : int
        The integer corresponding to the part type.
    count : int
        The number of parts to generate.

    Returns
    -------
    None
    """
    if part_type not in part_types:
        print(f"Unknown part type: {part_type}")
        return

    type_name, prefix = part_types[part_type]
    part_numbers = []

    part_dir = os.path.join("barcodes", type_name)
    if not os.path.exists(part_dir):
        os.makedirs(part_dir)

    polarization = input("Enter polarization (1 or 2): ").strip()
    if polarization not in ["1", "2"]:
        print("Invalid polarization. Please enter 1 or 2.")
        return

    for i in range(1, count + 1):
        part_number = f"{prefix}{i:05d}P{polarization}"
        part_numbers.append(part_number)
        save_to_db(part_number, type_name)
        generate_barcode(part_number, part_dir)


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
    print(f"Generated {part_number} with barcode saved to {barcode_path}")


def main() -> None:
    """
    Main function to prompt the user for input and generate parts accordingly.

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
        count = int(
            input(f"Enter number of parts for {part_types[type_selection][0]}: ")
        )
    except ValueError:
        print("Invalid input. Please enter a valid integer for the number of parts.")
        return

    generate_parts(type_selection, count)


if __name__ == "__main__":
    main()
