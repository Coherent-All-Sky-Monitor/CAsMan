#!/usr/bin/env python3
"""
Example script demonstrating the standalone antenna module.

This script loads antenna positions from the database, computes baselines,
and generates summary statistics. It demonstrates the minimal-dependency
usage of casman.antenna.
"""

import sys
from pathlib import Path

# Add parent directory to path if running from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent))

from casman.antenna import AntennaArray


def main():
    print("=" * 70)
    print("CAsMan Antenna Array - Baseline Analysis Example")
    print("=" * 70)

    # Load array from database
    db_path = "database/parts.db"
    print(f"\nLoading antenna array from: {db_path}")

    try:
        array = AntennaArray.from_database(db_path)
    except FileNotFoundError:
        print(f"Error: Database not found at {db_path}")
        print("Please run this script from the CAsMan project root directory.")
        return 1

    print(f"✓ Loaded {len(array)} antennas")

    # Show summary
    with_coords = array.filter_by_coordinates(has_coords=True)

    print(f"\nArray Summary:")
    print(f"  Total antennas: {len(array)}")
    print(f"  With coordinates: {len(with_coords)}")

    # Show example antennas
    print(f"\nExample Antennas:")
    for ant in list(array)[:3]:
        print(f"\n  {ant.antenna_number}:")
        print(f"    Grid Position: {ant.grid_code}")
        print(f"    Row Offset: {ant.row_offset:+d}, East Column: {ant.east_col}")
        if ant.has_coordinates():
            print(f"    Coordinates: ({ant.latitude:.6f}°, {ant.longitude:.6f}°)")
            print(f"    Height: {ant.height:.2f} m ({ant.coordinate_system})")

    # Compute baselines for antennas with coordinates
    if len(with_coords) >= 2:
        print(f"\n{'='*70}")
        print("Baseline Calculations")
        print("=" * 70)

        # Example baseline between first two antennas with coordinates
        ant1 = with_coords[0]
        ant2 = with_coords[1]

        baseline_geo = array.compute_baseline(ant1, ant2, use_coordinates=True)
        baseline_grid = array.compute_baseline(ant1, ant2, use_coordinates=False)

        print(f"\nExample Baseline:")
        print(
            f"  {ant1.antenna_number} ({ant1.grid_code}) ↔ {ant2.antenna_number} ({ant2.grid_code})"
        )
        print(f"    Geodetic distance: {baseline_geo:.3f} m")
        print(f"    Grid distance (approx): {baseline_grid:.3f} m")

        # Compute all baselines (if not too many)
        if len(with_coords) <= 20:
            print(f"\nComputing all baselines for {len(with_coords)} antennas...")
            baselines = array.compute_all_baselines(use_coordinates=True)

            distances = [b[2] for b in baselines]

            print(f"\nBaseline Statistics ({len(baselines)} baselines):")
            print(f"  Minimum: {min(distances):.3f} m")
            print(f"  Maximum: {max(distances):.3f} m")
            print(f"  Average: {sum(distances)/len(distances):.3f} m")

            # Show shortest and longest baselines
            baselines.sort(key=lambda x: x[2])

            print(f"\nShortest Baselines:")
            for ant_a, ant_b, dist in baselines[:3]:
                print(f"  {ant_a} ↔ {ant_b}: {dist:.3f} m")

            print(f"\nLongest Baselines:")
            for ant_a, ant_b, dist in baselines[-3:]:
                print(f"  {ant_a} ↔ {ant_b}: {dist:.3f} m")
        else:
            print(
                f"\n({len(with_coords)} antennas - skipping full baseline computation for brevity)"
            )
    else:
        print(f"\n⚠ Not enough antennas with coordinates for baseline calculations")
        print(f"  Load coordinates with: casman database load-coordinates")

    print(f"\n{'='*70}")
    print("✓ Analysis complete")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
