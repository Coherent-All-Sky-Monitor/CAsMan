#!/usr/bin/env python3
"""
Simplified example of antenna array baseline calculations.
This example works with just the array module (no web dependencies).
"""

import sys
from pathlib import Path

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from casman.antenna.array import AntennaArray


def main():
    # Load array from database
    db_path = Path(__file__).parent.parent / "database" / "parts.db"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return

    print("Loading antenna array from database...")
    array = AntennaArray.from_database(db_path=db_path, array_id="C")

    print(f"\nLoaded {len(array)} antennas")

    # Show antennas with coordinates
    with_coords = array.filter_by_coordinates(has_coords=True)
    print(f"Antennas with coordinates: {len(with_coords)}")

    # Display first few antennas as examples
    print("\n=== Example Antennas ===")
    for i, ant in enumerate(array):
        if i >= 3:
            break
        print(f"\n{ant.antenna_number} @ {ant.grid_code}")
        if ant.has_coordinates():
            print(
                f"  Lat: {ant.latitude:.6f}°, Lon: {ant.longitude:.6f}°, Height: {ant.height:.2f}m"
            )

    # Compute baselines if we have antennas with coordinates
    if len(with_coords) >= 2:
        print("\n=== Baseline Calculations ===")

        # Get first two antennas with coordinates
        ant1 = with_coords[0]
        ant2 = with_coords[1]

        # Compute geodetic baseline
        geo_baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)
        print(f"\nGeodetic baseline (Haversine):")
        print(f"  {ant1.antenna_number} <-> {ant2.antenna_number}")
        print(f"  Distance: {geo_baseline:.2f} meters")

        # Compute grid-based baseline
        grid_baseline = array.compute_baseline(ant1, ant2, use_coordinates=False)
        print(f"\nGrid-based baseline:")
        print(f"  {ant1.antenna_number} <-> {ant2.antenna_number}")
        print(f"  Distance: {grid_baseline:.2f} meters")

        # Compute all baselines
        if len(with_coords) <= 10:
            print("\n=== All Pairwise Baselines ===")
            baselines = array.compute_all_baselines(
                use_coordinates=True, include_self=False
            )

            print(f"Total baseline pairs: {len(baselines)}")

            # Show statistics
            distances = [dist for _, _, dist in baselines]
            if distances:
                print(f"  Min: {min(distances):.2f}m")
                print(f"  Max: {max(distances):.2f}m")
                print(f"  Avg: {sum(distances)/len(distances):.2f}m")
    else:
        print("\nNeed at least 2 antennas with coordinates for baseline calculations")
        print(
            "Load coordinates using: casman database load-coordinates --csv grid_positions.csv"
        )

    print("\n✓ Example completed successfully")


if __name__ == "__main__":
    main()
