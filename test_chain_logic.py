#!/usr/bin/env python3
"""
Test script to verify chain building logic matches CLI output.
"""
import os
import sys
import sqlite3
from typing import Dict, List, Optional, Set, Tuple

# Add casman to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from casman.config import get_config

def get_all_chains_test() -> Tuple[List[List[str]], Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]]]:
    """Test version of get_all_chains function."""
    db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if db_path is None:
        raise ValueError("Database path for assembled_casm.db is not set.")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "SELECT part_number, connected_to, scan_time, connected_scan_time "
        "FROM assembly ORDER BY scan_time"
    )
    records = c.fetchall()
    
    print("Database records (ordered by scan_time):")
    for i, (part_number, connected_to, scan_time, connected_scan_time) in enumerate(records):
        print(f"{i+1}: {part_number} -> {connected_to} (scan: {scan_time})")
    print()
    
    # Build connections dictionary using the most recent scan for each part
    connections: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]] = {}
    for part_number, connected_to, scan_time, connected_scan_time in records:
        # Always use the most recent entry (since we order by scan_time)
        connections[part_number] = (connected_to, scan_time, connected_scan_time)
    
    conn.close()
    
    print("Final connections (most recent per part):")
    for part, (connected_to, scan_time, connected_scan_time) in connections.items():
        print(f"{part} -> {connected_to} (scan: {scan_time})")
    print()
    
    # Build chains similar to the CLI visualization approach
    all_chains: List[List[str]] = []
    visited: Set[str] = set()
    
    # Start from parts that are not connected to by any other part (root parts)
    all_parts = set(connections.keys())
    connected_to_parts = set()
    for connected_to, _, _ in connections.values():
        if connected_to:
            connected_to_parts.add(connected_to)
    
    root_parts = all_parts - connected_to_parts
    print(f"Root parts (not connected to by others): {sorted(root_parts)}")
    print(f"All parts: {sorted(all_parts)}")
    print(f"Connected to parts: {sorted(connected_to_parts)}")
    print()
    
    # Build chains starting from root parts
    for part in sorted(root_parts):  # Sort for consistent output
        if part not in visited:
            chain = build_chain_from_root(part, connections, visited)
            if chain:  # Only add non-empty chains
                all_chains.append(chain)
                print(f"Chain from {part}: {' ---> '.join(chain)}")
    
    return all_chains, connections

def build_chain_from_root(
    start_part: str,
    connections: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]],
    visited: Set[str],
) -> List[str]:
    """Build a chain of connections starting from the given root part."""
    chain: List[str] = []
    current_part = start_part
    
    while current_part and current_part not in visited:
        visited.add(current_part)
        chain.append(current_part)
        
        # Get the next part in the chain
        connection_info = connections.get(current_part)
        if connection_info and connection_info[0]:  # connected_to exists
            current_part = connection_info[0]
        else:
            break
    
    return chain

if __name__ == "__main__":
    print("Testing chain building logic...\n")
    chains, connections = get_all_chains_test()
    print(f"\nTotal chains found: {len(chains)}")
