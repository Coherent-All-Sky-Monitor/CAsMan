"""
Core visualization functions for CAsMan.

This module contains the legacy visualization functions that were previously
in the main visualization.py module.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple

from casman.assembly.chains import build_connection_chains
from casman.assembly.data import get_assembly_connections

logger = logging.getLogger(__name__)


def format_ascii_chains(db_dir: Optional[str] = None) -> str:
    """
    Format assembly chains as ASCII text.

    Parameters
    ----------
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    str
        Formatted ASCII representation of assembly chains.
    """
    chains = build_connection_chains(db_dir)

    if not chains:
        return "No assembly connections found."

    output_lines = []
    output_lines.append("CASM Assembly Connections:")
    output_lines.append("-" * 88)

    # Track which parts have been printed to avoid duplicates
    printed_parts = set()

    # Find starting points (parts that aren't connected to by others)
    all_connected_parts = set()
    for connected_list in chains.values():
        all_connected_parts.update(connected_list)

    starting_parts = [part for part in chains.keys() if part not in all_connected_parts]

    # If no clear starting points, use all parts
    if not starting_parts:
        starting_parts = list(chains.keys())

    # Print chains starting from each starting point
    for start_part in sorted(starting_parts):  # Sort for consistent output
        if start_part in printed_parts:
            continue

        # Use BFS to find all connected parts
        chain_queue = [[start_part]]

        while chain_queue:
            chain = chain_queue.pop(0)
            current_part = chain[-1]

            if current_part in printed_parts:
                continue

            printed_parts.add(current_part)

            # Get connected parts
            next_parts = chains.get(current_part, [])

            if not next_parts:
                # If there are no further connections, print the chain
                output_lines.append(" ---> ".join(chain))
            else:
                # Extend the chain for each connected part
                for next_part in next_parts:
                    if next_part not in printed_parts:
                        chain_queue.append(chain + [next_part])

    output_lines.append("-" * 88)

    # Add duplicate connections information
    duplicates = get_duplicate_connections(db_dir)
    if duplicates:
        output_lines.append("")
        output_lines.append("DUPLICATE CONNECTIONS DETECTED:")
        output_lines.append("-" * 88)
        for part, entries in duplicates.items():
            output_lines.append(f"Part {part} has {len(entries)} database entries:")
            for i, (connected_to, scan_time, connected_scan_time) in enumerate(entries, 1):
                output_lines.append(
                    f"  {i}. FRM: {scan_time}, NXT: {connected_scan_time}, connects to: {connected_to}")
        output_lines.append("-" * 88)

    return "\n".join(output_lines)


def get_duplicate_connections(
        db_dir: Optional[str] = None) -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Get information about duplicate connections in the database.

    Returns
    -------
    Dict[str, List[Tuple[str, str, str]]]
        Dictionary mapping part numbers to list of (connected_to, scan_time, connected_scan_time) tuples
        for parts that appear multiple times in the database.
    """
    import sqlite3
    from casman.database.connection import get_database_path

    try:
        db_path = get_database_path("assembled_casm.db", db_dir)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.part_number, a.connected_to, a.scan_time, a.connected_scan_time
                FROM assembly a
                INNER JOIN (
                    SELECT part_number, connected_to, MAX(scan_time) as max_time
                    FROM assembly
                    GROUP BY part_number, connected_to
                ) latest
                ON a.part_number = latest.part_number
                AND a.connected_to = latest.connected_to
                AND a.scan_time = latest.max_time
                WHERE a.connection_status = 'connected'
                ORDER BY a.scan_time
                """
            )
            records = cursor.fetchall()
    except sqlite3.Error as e:
        logger.error("Database error getting duplicate connections: %s", e)
        return {}

    # Group connections by part number
    part_connections: Dict[str, List[Tuple[str, str, str]]] = {}
    for part_number, connected_to, scan_time, connected_scan_time in records:
        if part_number not in part_connections:
            part_connections[part_number] = []
        part_connections[part_number].append((
            connected_to or "None",
            scan_time or "None",
            connected_scan_time or "None"
        ))

    # Return only parts with duplicates
    duplicates = {}
    for part_number, entries in part_connections.items():
        if len(entries) > 1:
            duplicates[part_number] = entries

    return duplicates


def get_chain_summary(db_dir: Optional[str] = None) -> Dict[str, float]:
    """
    Get summary statistics about assembly chains.

    Parameters
    ----------
    db_dir : str, optional
        Custom database directory. If not provided, uses the project root's database directory.

    Returns
    -------
    Dict[str, float]
        Dictionary containing chain statistics.
    """
    chains = build_connection_chains(db_dir)

    if not chains:
        return {
            "total_parts": 0,
            "total_connections": 0,
            "total_chains": 0,
            "average_chain_length": 0.0,
            "longest_chain": 0,
        }

    total_parts = len(chains)
    total_connections = sum(len(connected) for connected in chains.values())

    # Calculate chain lengths
    chain_lengths = []
    visited: Set[str] = set()

    for part in chains:
        if part not in visited:
            length = _calculate_chain_length(part, chains, visited)
            if length > 0:
                chain_lengths.append(length)

    total_chains = len(chain_lengths)

    if chain_lengths:
        average_length = sum(chain_lengths) / len(chain_lengths)
        longest_chain = max(chain_lengths)
    else:
        average_length = 0.0
        longest_chain = 0

    return {
        "total_parts": total_parts,
        "total_connections": total_connections,
        "total_chains": total_chains,
        "average_chain_length": average_length,
        "longest_chain": longest_chain,
    }


def _calculate_chain_length(
        start_part: str, chains: Dict[str, List[str]], visited: Set[str]) -> int:
    """
    Calculate the length of a chain starting from a given part.

    Parameters
    ----------
    start_part : str
        The part to start calculating from
    chains : Dict[str, List[str]]
        The chains dictionary
    visited : Set[str]
        Set of already visited parts

    Returns
    -------
    int
        Length of the chain
    """
    if start_part in visited:
        return 0

    length = 1
    visited.add(start_part)

    connected_parts = chains.get(start_part, [])
    if connected_parts:
        # For simplicity, follow the first connection
        next_part = connected_parts[0]
        length += _calculate_chain_length(next_part, chains, visited)

    return length


def main() -> None:
    """Main function for command-line usage."""
    print("CASM Visualization")
    print("1: Show ASCII chains")

    try:
        choice = int(input("Enter your choice: "))

        if choice == 1:
            print("\n" + format_ascii_chains())
        else:
            print("Invalid choice.")
    except ValueError:
        print("Invalid input. Please enter a valid number.")
