"""
Core visualization functions for CAsMan.

This module contains the legacy visualization functions that were previously
in the main visualization.py module.
"""

import logging
from typing import Dict, List, Set

from casman.assembly import build_connection_chains, get_assembly_connections

logger = logging.getLogger(__name__)


def format_ascii_chains() -> str:
    """
    Format assembly chains as ASCII text.

    Returns
    -------
    str
        Formatted ASCII representation of assembly chains.
    """
    chains = build_connection_chains()

    if not chains:
        return "No assembly connections found."

    # Track parts that have already been printed to avoid duplicate chains
    printed_parts = set()
    output_lines = []

    output_lines.append("CASM Assembly Connections:")
    output_lines.append("-" * 88)
    for part_number in chains:
        if part_number not in printed_parts:
            # Start a new chain from this part
            chain_queue = [[part_number]]

            while chain_queue:
                chain = chain_queue.pop()
                last_part = chain[-1]

                # Skip if this part has already been printed in another chain
                if last_part in printed_parts:
                    continue

                printed_parts.add(last_part)
                next_parts = chains.get(last_part, [])

                if not next_parts:
                    # If there are no further connections, print the chain
                    output_lines.append(" ---> ".join(chain))
                else:
                    # Extend the chain for each connected part
                    for next_part in next_parts:
                        if next_part not in printed_parts:
                            chain_queue.append(chain + [next_part])

    output_lines.append("-" * 88)
    return "\n".join(output_lines)


def get_visualization_data() -> Dict[str, List[Dict[str, str]]]:
    """
    Get data formatted for web visualization.

    Returns
    -------
    Dict[str, List[Dict[str, str]]]
        Dictionary containing nodes and links for visualization.
    """
    connections = get_assembly_connections()
    chains = build_connection_chains()

    # Create nodes
    all_parts: Set[str] = set()
    for part_number, connected_to, _, _, _ in connections:
        all_parts.add(part_number)
        if connected_to:
            all_parts.add(connected_to)

    nodes = [{"id": part, "label": part} for part in sorted(all_parts)]

    # Create links
    links = []
    for part_number, connected_parts in chains.items():
        for connected_part in connected_parts:
            links.append({"source": part_number, "target": connected_part})

    return {"nodes": nodes, "links": links}


def get_chain_summary() -> Dict[str, float]:
    """
    Get summary statistics about assembly chains.

    Returns
    -------
    Dict[str, float]
        Dictionary containing chain statistics.
    """
    connections = get_assembly_connections()
    chains = build_connection_chains()

    if not connections:
        return {
            "total_parts": 0,
            "total_connections": 0,
            "total_chains": 0,
            "longest_chain": 0,
            "average_chain_length": 0,
        }

    total_parts = len(set(part for part, _, _, _, _ in connections))
    total_connections = len([link for links in chains.values() for link in links])

    # Build forward direction map (what connects FROM each part)
    forward_chains: Dict[str, List[str]] = {}
    for part, connected_to_list in chains.items():
        for connected_to in connected_to_list:
            if connected_to not in forward_chains:
                forward_chains[connected_to] = []
            forward_chains[connected_to].append(part)

    # Find root parts (parts that don't connect to anything)
    all_parts = set(chains.keys())
    root_parts = [part for part in all_parts if not chains[part]]

    # Count chain lengths starting from root parts
    chain_lengths = []

    def get_chain_length(start_part: str, visited: Set[str]) -> int:
        """Get the longest chain length starting from a part."""
        if start_part in visited:
            return 0

        visited.add(start_part)
        max_length = 1

        next_parts = forward_chains.get(start_part, [])
        for next_part in next_parts:
            length = 1 + get_chain_length(next_part, visited.copy())
            max_length = max(max_length, length)

        return max_length

    for root_part in root_parts:
        chain_length = get_chain_length(root_part, set())
        chain_lengths.append(chain_length)

    # If no clear root parts, count from all parts
    if not chain_lengths:
        for part in all_parts:
            chain_length = get_chain_length(part, set())
            if chain_length > 0:
                chain_lengths.append(chain_length)

    return {
        "total_parts": total_parts,
        "total_connections": total_connections,
        "total_chains": len(chain_lengths) if chain_lengths else len(root_parts),
        "longest_chain": max(chain_lengths) if chain_lengths else 0,
        "average_chain_length": (
            sum(chain_lengths) / len(chain_lengths) if chain_lengths else 0
        ),
    }


def print_visualization_summary() -> None:
    """Print a summary of the visualization data."""
    summary = get_chain_summary()

    print("Assembly Visualization Summary:")
    print("-" * 40)
    print(f"Total parts: {summary['total_parts']}")
    print(f"Total connections: {summary['total_connections']}")
    print(f"Number of chains: {summary['total_chains']}")
    print(f"Longest chain: {summary['longest_chain']} parts")
    print(f"Average chain length: {summary['average_chain_length']:.1f} parts")
    print("-" * 40)


def main() -> None:
    """Main function for command-line usage."""
    print("CASM Visualization")
    print("1: Show ASCII chains")
    print("2: Show summary")

    try:
        choice = int(input("Enter your choice: "))

        if choice == 1:
            print("\n" + format_ascii_chains())
        elif choice == 2:
            print_visualization_summary()
        else:
            print("Invalid choice.")

    except ValueError:
        print("Invalid input. Please enter a valid number.")
