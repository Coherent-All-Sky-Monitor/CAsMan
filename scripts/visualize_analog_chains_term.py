"""
Terminal visualization script for CAsMan.

This script visualizes the connections between parts in the
assembled_casm.db database using the casman module. It prints the assembly connections
in a readable ASCII format, showing how each part is connected to others.

Usage
-----
Run this script directly to print all assembly connections:

    python visualize_analog_chains_term.py

The output will display each unique connection chain found in the database.
"""

from casman.assembly import print_assembly_chains


def print_assembled_connections() -> None:
    """
    Print the connections from the assembled_casm.db database in ASCII format.

    This function uses the casman.assembly module to fetch and display
    all part connection records in a readable ASCII format.

    Returns
    -------
    None
    """
    print_assembly_chains()


if __name__ == "__main__":
    print_assembled_connections()
