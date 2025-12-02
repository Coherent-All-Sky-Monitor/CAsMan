#!/usr/bin/env python3
"""
Example: Query SNAP port assignments for antennas.

This script demonstrates how to use the antenna module to:
1. Load antenna array from database
2. Query SNAP port assignments by tracing assembly chains
3. Display complete or incomplete chain status
"""

import sys
from pathlib import Path

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from casman.antenna.array import AntennaArray


def main():
    print("=" * 70)
    print("SNAP Port Assignment Lookup Example")
    print("=" * 70)

    # Load array from database
    db_path = Path(__file__).parent.parent / "database" / "parts.db"

    if not db_path.exists():
        print(f"\nError: Database not found at {db_path}")
        return 1

    print(f"\nLoading antenna array from: {db_path}")
    array = AntennaArray.from_database(db_path, array_id="C")
    print(f"✓ Loaded {len(array)} antennas")

    # Get first few antennas as examples
    example_antennas = list(array)[:5]

    print("\n" + "=" * 70)
    print("SNAP Port Assignments")
    print("=" * 70)

    for ant in example_antennas:
        print(f"\n{ant.antenna_number} @ {ant.grid_code}")
        print("-" * 40)

        # Get SNAP port assignments
        ports = ant.get_snap_ports()

        # Display P1 chain
        print("\nP1 Chain:")
        if ports["p1"]:
            print(f"  ✓ Connected to {ports['p1']['snap_part']}")
            print(f"    {ant.format_chain_status('P1')}")
            from casman.antenna.chain import format_snap_port

            print(f"    Location: {format_snap_port(ports['p1'])}")
        else:
            print(f"  ✗ {ant.format_chain_status('P1')}")

        # Display P2 chain
        print("\nP2 Chain:")
        if ports["p2"]:
            print(f"  ✓ Connected to {ports['p2']['snap_part']}")
            print(f"    {ant.format_chain_status('P2')}")
            from casman.antenna.chain import format_snap_port

            print(f"    Location: {format_snap_port(ports['p2'])}")
        else:
            print(f"  ✗ {ant.format_chain_status('P2')}")

    # Summary statistics
    print("\n" + "=" * 70)
    print("Summary Statistics")
    print("=" * 70)

    p1_connected = 0
    p2_connected = 0
    both_connected = 0

    for ant in array:
        ports = ant.get_snap_ports()
        p1_ok = ports["p1"] is not None
        p2_ok = ports["p2"] is not None

        if p1_ok:
            p1_connected += 1
        if p2_ok:
            p2_connected += 1
        if p1_ok and p2_ok:
            both_connected += 1

    total = len(array)
    print(f"\nTotal antennas: {total}")
    print(f"P1 chains complete: {p1_connected} ({100*p1_connected/total:.1f}%)")
    print(f"P2 chains complete: {p2_connected} ({100*p2_connected/total:.1f}%)")
    print(f"Both chains complete: {both_connected} ({100*both_connected/total:.1f}%)")

    print("\n" + "=" * 70)
    print("✓ Example completed successfully")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
