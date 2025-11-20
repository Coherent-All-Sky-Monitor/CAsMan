"""
Interactive CLI utilities for CAsMan parts management.
"""

import sqlite3

from casman.parts.db import read_parts
from casman.parts.generation import generate_part_numbers
from casman.parts.types import load_part_types

PART_TYPES = load_part_types()


def display_parts_interactive() -> None:
    """Interactive function to display parts with user input."""
    print("Select part type (or alias):")
    # Show all part types except SNAP (type 6)
    for key, (name, abbrev) in PART_TYPES.items():
        if key != 6:  # Exclude SNAP
            print(f"{key}: {name} (alias: {abbrev})")
    print("0: ALL (show all part types)")
    type_input = input("Enter the number or alias for the part type: ").strip().upper()
    if type_input == "0":
        part_type = None
    elif type_input in (abbrev for key, (_, abbrev) in PART_TYPES.items() if key != 6):
        for key, (name, abbrev) in PART_TYPES.items():
            if key != 6 and type_input == abbrev:
                part_type = name
                break
    else:
        try:
            type_selection = int(type_input)
            if type_selection in PART_TYPES and type_selection != 6:
                part_type = PART_TYPES[type_selection][0]
            else:
                print("Invalid selection. Please enter a valid number or alias.")
                return
        except ValueError:
            print("Invalid input. Please enter a valid number or alias.")
            return
    polarization_input = (
        input("Enter polarization (1 or 2, or press Enter to include all): ")
        .strip()
        .upper()
    )
    polarization = polarization_input if polarization_input else None
    parts = read_parts(part_type, polarization)
    if parts:
        print(f"\nFound {len(parts)} part(s):")
        headers = [
            "ID",
            "Part Number",
            "Part Type",
            "Polarization",
            "Date Created",
            "Date Modified",
        ]
        col_widths = [
            max(len(str(row[i])) for row in parts + [headers])
            for i in range(len(headers))
        ]

        def h(char: str, width: int) -> str:
            return char * width

        top = "┌" + "┬".join(h("─", w + 2) for w in col_widths) + "┐"
        header_row = (
            "│ "
            + " │ ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
            + " │"
        )
        sep = "├" + "┼".join(h("─", w + 2) for w in col_widths) + "┤"
        bottom = "└" + "┴".join(h("─", w + 2) for w in col_widths) + "┘"
        print(top)
        print(header_row)
        print(sep)
        for part in parts:
            row = [
                str(part[0]),
                str(part[1]),
                str(part[2]),
                str(part[3]),
                str(part[4]),
                str(part[5]),
            ]
            row_str = (
                "│ "
                + " │ ".join(f"{row[i]:<{col_widths[i]}}" for i in range(len(row)))
                + " │"
            )
            print(row_str)
        print(bottom)
    else:
        criteria_desc = []
        if part_type:
            criteria_desc.append(f"part type '{part_type}'")
        if polarization:
            criteria_desc.append(f"polarization '{polarization}'")
        if criteria_desc:
            print(f"No parts found matching {' and '.join(criteria_desc)}.")
        else:
            print("No parts found in the database.")


def add_parts_interactive() -> None:
    """Interactive function to add new parts."""
    print("Select part type (or alias):")
    # Show all part types except SNAP (type 6)
    for key, (name, abbrev) in PART_TYPES.items():
        if key != 6:  # Exclude SNAP
            print(f"{key}: {name} (alias: {abbrev})")
    print("0: ALL (add parts for all types)")

    type_input = (
        input("Enter the number or abbreviation for the part type: ").strip().upper()
    )

    # Handle ALL option
    if type_input == "0":
        part_types_to_add = [name for key, (name, _) in PART_TYPES.items() if key != 6]
    elif type_input in (abbrev for key, (_, abbrev) in PART_TYPES.items() if key != 6):
        for key, (name, abbrev) in PART_TYPES.items():
            if key != 6 and type_input == abbrev:
                part_types_to_add = [name]
                break
    else:
        try:
            type_selection = int(type_input)
            if type_selection in PART_TYPES and type_selection != 6:
                part_types_to_add = [PART_TYPES[type_selection][0]]
            else:
                print("Invalid selection. Please enter a valid number or alias.")
                return
        except ValueError:
            print("Invalid input. Please enter a valid number or alias.")
            return

    try:
        count = int(
            input(
                "Enter the number of new part numbers to create for each type (must be > 0): "
            )
        )
        if count <= 0:
            print("Number of parts must be greater than 0.")
            return
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    polarization = input("Enter polarization for the new parts (1 or 2): ").strip()
    if polarization not in ["1", "2"]:
        print(
            "Invalid polarization. Please enter 1 or 2.\nPolarization refers to the signal orientation (e.g., 1 = X-pol, 2 = Y-pol)."
        )
        return

    try:
        total_created = 0
        for part_type in part_types_to_add:
            new_parts = generate_part_numbers(part_type, count, polarization)
            total_created += len(new_parts)
            print(
                f"\nSuccessfully created {len(new_parts)} new {part_type} part numbers:"
            )
            for part_number in new_parts:
                print(f"  {part_number}")
            print(f"Barcodes generated in barcodes/{part_type}/ directory.")

        if len(part_types_to_add) > 1:
            print(
                f"\nTotal: {total_created} parts created across {len(part_types_to_add)} part types!"
            )

    except (ValueError, sqlite3.Error) as e:
        print(f"Error creating parts: {e}")


def main() -> None:
    """Main function for command-line usage."""
    print("CAsMan Parts Management")
    print("1: Read parts")
    print("2: Add new parts")
    try:
        choice = int(input("Enter your choice: "))
        if choice == 1:
            display_parts_interactive()
        elif choice == 2:
            add_parts_interactive()
        else:
            print("Invalid choice.")
    except ValueError:
        print("Invalid input. Please enter a valid number.")


if __name__ == "__main__":
    main()
