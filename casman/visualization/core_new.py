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
    chains = build_connection_chains()
    
    if not chains:
        return {
            "total_parts": 0,
            "total_connections": 0,
            "average_chain_length": 0.0,
            "longest_chain": 0,
        }
    
    total_parts = len(chains)
    total_connections = sum(len(connected) for connected in chains.values())
    
    # Calculate chain lengths
    chain_lengths = []
    visited = set()
    
    for part in chains:
        if part not in visited:
            length = _calculate_chain_length(part, chains, visited)
            if length > 0:
                chain_lengths.append(length)
    
    if chain_lengths:
        average_length = sum(chain_lengths) / len(chain_lengths)
        longest_chain = max(chain_lengths)
    else:
        average_length = 0.0
        longest_chain = 0
    
    return {
        "total_parts": total_parts,
        "total_connections": total_connections,
        "average_chain_length": average_length,
        "longest_chain": longest_chain,
    }


def _calculate_chain_length(start_part: str, chains: Dict[str, List[str]], visited: Set[str]) -> int:
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


def format_chain_summary() -> str:
    """
    Format chain summary statistics as text.
    
    Returns
    -------
    str
        Formatted summary statistics
    """
    stats = get_chain_summary()
    
    output_lines = []
    output_lines.append("Assembly Chain Summary:")
    output_lines.append("=" * 50)
    output_lines.append(f"Total parts in chains: {stats['total_parts']}")
    output_lines.append(f"Total connections: {stats['total_connections']}")
    output_lines.append(f"Average chain length: {stats['average_chain_length']:.1f}")
    output_lines.append(f"Longest chain: {stats['longest_chain']}")
    output_lines.append("=" * 50)
    
    return "\n".join(output_lines)
