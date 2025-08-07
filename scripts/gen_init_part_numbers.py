
"""
gen_init_part_numbers.py

Script to generate initial part numbers and barcodes for CAsMan.
Supports generating for a single part type or all types in one run.
Prompts user for part type, count, and polarization, \
    and uses the casman module for all DB and barcode operations.
"""


import argparse
from typing import List, Optional

from casman.config import get_config
from casman.database import init_all_databases
from casman.parts import PART_TYPES, generate_part_numbers


def prompt_int(prompt: str) -> int:
    """Prompt the user for an integer, reprompting on invalid input."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a valid integer.")


def prompt_polarization() -> str:
    """Prompt the user for polarization (1 or 2)."""
    while True:
        pol = input("Enter polarization (1 or 2): ").strip()
        if pol in ["1", "2"]:
            return pol
        print("Invalid polarization. Please enter 1 or 2.")


def main() -> None:
    """
    Main function to prompt the user for input and generate part numbers/barcodes.
    """

    parser = argparse.ArgumentParser(
        description="Generate initial part numbers and barcodes.")
    default_db_dir = get_config("CASMAN_DB_DIR", "database")
    parser.add_argument(
        "--db_dir",
        type=str,
        default=default_db_dir,
        help="Path to the database directory (default: from config.yaml or 'database')",
    )
    args = parser.parse_args()

    # Initialize databases
    init_all_databases(args.db_dir)
    print(f"Database initialized at: {args.db_dir}/parts.db")

    print("Select part type:")
    for key, (name, _) in PART_TYPES.items():
        if name != "SNAP":  # Exclude SNAP from part number generation
            print(f"{key}: {name}")
    print("7: ALL (generate for all part types except SNAP)")

    type_selection = prompt_int(
        "Enter the number corresponding to the part type: ")
    if type_selection not in PART_TYPES and type_selection != 7:
        print("Invalid selection. Please enter a valid number.")
        return

    # Check if user is trying to generate SNAP parts directly
    if type_selection in PART_TYPES and PART_TYPES[type_selection][0] == "SNAP":
        print("Error: SNAP part number generation is not allowed.")
        return

    if type_selection == 7:
        count = prompt_int("Enter number of parts for each part type: ")
        polarization = prompt_polarization()
        all_generated_parts: List[str] = []
        for _, (part_type_name, _) in PART_TYPES.items():
            # Skip SNAP parts
            if part_type_name == "SNAP":
                print(f"Skipping {part_type_name} (not allowed)")
                continue
            try:
                new_part_numbers: Optional[List[str]] = generate_part_numbers(
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
                print(f"  Generated {part_number}")
        else:
            print("No part numbers were generated.")
    else:
        count = prompt_int(
            f"Enter number of parts for {PART_TYPES[type_selection][0]}: ")
        polarization = prompt_polarization()
        part_type_name, _ = PART_TYPES[type_selection]
        try:
            single_part_numbers: Optional[List[str]] = generate_part_numbers(
                part_type_name, count, polarization, args.db_dir
            )
            if single_part_numbers:
                print(
                    f"\nSuccessfully generated {len(single_part_numbers)} part numbers:")
                for part_number in single_part_numbers:
                    print(f"  Generated {part_number}")
            else:
                print("No part numbers were generated.")
        except (ValueError, OSError, RuntimeError) as e:
            print(f"Error generating part numbers: {e}")


if __name__ == "__main__":
    main()
    import sys
    sys.exit(0)


if __name__ == "__main__":
    main()
