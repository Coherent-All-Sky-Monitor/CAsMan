"""
Part number generation script for CAsMan.

This script generates new part numbers using the casman module.
Users can specify the number of part numbers to create and the polarization.
The script ensures part numbers are unique and consistent with existing entries,
and generates corresponding barcodes.

Features
--------
- Uses centralized casman module for database operations.
- Increments from the last created part number.
- Supports user input for the number of parts and polarization.
- Updates the database with new part numbers and timestamps.
- Generates barcodes for each new part number.
- Supports generating parts for all part types with "ALL" option.
- Configurable database directory path.

Usage
-----
1. Run the script.
2. Enter the part type by selecting the corresponding integer (or 6 for ALL).
3. Enter the number of new part numbers to create.
4. Enter the polarization for the new parts.
"""


import argparse

from casman.config import get_config
from casman.database import init_all_databases
from casman.parts import PART_TYPES, generate_part_numbers

# Parse command-line arguments

parser = argparse.ArgumentParser(
    description="Generate new part numbers and barcodes.")
default_db_dir = get_config("CASMAN_DB_DIR", "database")
parser.add_argument(
    "--db_dir",
    type=str,
    default=default_db_dir,
    help="Path to the database directory (default: from config.yaml or 'database')",
)
args = parser.parse_args()


def main() -> None:
    """
    Main function to prompt the user for input and generate new part numbers.

    Returns
    -------
    None
    """
    # Initialize databases
    init_all_databases(args.db_dir)
    print(f"Database initialized at: {args.db_dir}/parts.db")

    print("Select part type:")
    for key, (name, _) in PART_TYPES.items():
        print(f"{key}: {name}")
    print("6: ALL (generate for all part types)")

    try:
        type_selection = int(
            input("Enter the number corresponding to the part type: "))
        if type_selection not in PART_TYPES and type_selection != 6:
            print("Invalid selection. Please enter a valid number.")
            return
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    # Handle "ALL" option
    if type_selection == 6:
        try:
            count = int(input("Enter number of parts for each part type: "))
        except ValueError:
            print("Invalid input. Please enter a valid integer for the number of parts.")
            return

        polarization = input("Enter polarization (1 or 2): ").strip()
        if polarization not in ['1', '2']:
            print("Invalid polarization. Please enter 1 or 2.")
            return

        # Generate parts for all part types
        all_generated_parts = []
        for _, (part_type_name, _) in PART_TYPES.items():
            try:
                new_part_numbers = generate_part_numbers(
                    part_type_name, count, polarization, args.db_dir
                )
                if new_part_numbers:
                    all_generated_parts.extend(new_part_numbers)
                    print(
                        f"Generated {len(new_part_numbers)} {part_type_name} parts")
            except (ValueError, OSError, RuntimeError) as e:
                print(f"Error generating {part_type_name} parts: {e}")

        if all_generated_parts:
            print(
                f"\nSuccessfully generated {len(all_generated_parts)} total part numbers:")
            for part_number in all_generated_parts:
                print(f"  - {part_number}")
        else:
            print("No part numbers were generated.")

    else:
        # Handle single part type selection
        try:
            count = int(
                input(f"Enter number of parts for {PART_TYPES[type_selection][0]}: "))
        except ValueError:
            print("Invalid input. Please enter a valid integer for the number of parts.")
            return

        polarization = input("Enter polarization (1 or 2): ").strip()
        if polarization not in ['1', '2']:
            print("Invalid polarization. Please enter 1 or 2.")
            return

        # Get part type name from selection
        part_type_name, _ = PART_TYPES[type_selection]

        try:
            # Generate part numbers using casman module
            new_part_numbers = generate_part_numbers(
                part_type_name, count, polarization, args.db_dir
            )

            if new_part_numbers:
                print(
                    f"\nSuccessfully generated {len(new_part_numbers)} part numbers:")
                for part_number in new_part_numbers:
                    print(f"  - {part_number}")
            else:
                print("No part numbers were generated.")

        except (ValueError, OSError, RuntimeError) as e:
            print(f"Error generating part numbers: {e}")


if __name__ == "__main__":
    main()
