"""
visualize_analog_chains_term.py

This script visualizes the connections between parts in the
assembled_casm.db database. It prints the assembly connections
in a readable ASCII format, showing how each part is connected to others.

Usage
-----
Run this script directly to print all assembly connections:

    python visualizer.py

The output will display each unique connection chain found in the database.
"""

import sqlite3
from typing import Dict, List


def print_assembled_connections() -> None:
    """
    Print the connections from the assembled_casm.db database in ASCII format,
    avoiding duplicate prints.

    This function fetches all part connection records from the 'assembly' table in the
    assembled_casm.db SQLite database. It builds a mapping of each part to its connected parts,
    then traverses and prints each unique connection chain in a readable ASCII format.

    Returns
    -------
    None
    """
    # Connect to the assembled_casm.db database
    conn = sqlite3.connect("database/assembled_casm.db")
    c = conn.cursor()

    # Fetch all records from the assembly table
    c.execute("SELECT part_number, connected_to FROM assembly")
    records = c.fetchall()
    # Build a dictionary to map parts to their connections
    connections: Dict[str, List[str]] = {}
    for part_number, connected_to in records:
        if part_number not in connections:
            connections[part_number] = []
        if connected_to:
            connections[part_number].append(connected_to)
            connections[part_number].append(connected_to)

    # Track parts that have already been printed to avoid duplicate chains
    printed_parts = set()

    # Display the connections in a chain format
    if connections:
        print("CASM Assembly Connections:")
        print("-" * 50)
        for part_number in connections:
            if part_number not in printed_parts:
                # Start a new chain from this part
                chains = [[part_number]]
                while chains:
                    chain = chains.pop()
                    last_part = chain[-1]
                    # Skip if this part has already been printed in another chain
                    if last_part in printed_parts:
                        continue
                    printed_parts.add(last_part)
                    next_parts = connections.get(last_part, [])
                    if not next_parts:
                        # If there are no further connections, print the chain
                        print(" ---> ".join(chain))
                    else:
                        # Extend the chain for each connected part
                        for next_part in next_parts:
                            if next_part not in printed_parts:
                                chains.append(chain + [next_part])
        print("-" * 50)
    else:
        print("No records found in the assembled database.")

    # Close the database connection
    conn.close()


if __name__ == "__main__":
    print_assembled_connections()
