"""
Assembly chain building and analysis functionality.

This module handles building connection chains from assembly data
and provides analysis functions for understanding assembly relationships.
"""

import logging
from typing import Dict, List

from .data import get_assembly_connections

logger = logging.getLogger(__name__)


def build_connection_chains() -> Dict[str, List[str]]:
    """
    Build a dictionary mapping each part to its connected parts.

    Returns
    -------
    Dict[str, List[str]]
        Dictionary where keys are part numbers and values are lists
        of connected part numbers.

    Examples
    --------
    >>> chains = build_connection_chains()
    >>> print(chains.get('ANTP1-00001', []))
    ['LNA-P1-00001']
    """
    connections = get_assembly_connections()
    chains: Dict[str, List[str]] = {}

    for part_number, connected_to, _, _, _ in connections:
        if part_number not in chains:
            chains[part_number] = []
        if connected_to and connected_to not in chains[part_number]:
            chains[part_number].append(connected_to)

    return chains


def print_assembly_chains() -> None:
    """
    Print all assembly chains in a readable format.

    This function builds connection chains and prints them in a tree-like
    structure showing how parts are connected to each other.

    Examples
    --------
    >>> print_assembly_chains()
    Assembly Chains:
    ================
    ANTP1-00001 ---> LNA-P1-00001 ---> CX1-P1-00001
    ANTP1-00002 ---> LNA-P1-00002
    """
    chains = build_connection_chains()

    if not chains:
        print("No assembly connections found.")
        return

    print("Assembly Chains:")
    print("=" * 88)

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
    for start_part in starting_parts:
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
                print(" ---> ".join(chain))
            else:
                # Extend the chain for each connected part
                for next_part in next_parts:
                    if next_part not in printed_parts:
                        chain_queue.append(chain + [next_part])

    print("-" * 88)
