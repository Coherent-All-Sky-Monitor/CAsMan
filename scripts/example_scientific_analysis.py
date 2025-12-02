#!/usr/bin/env python3
"""
Scientific usage example: UV coverage and baseline analysis.
Demonstrates advanced features of the antenna array module.
"""

import sys
from pathlib import Path
from math import sqrt

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from casman.antenna.array import AntennaArray


def compute_uv_coordinates(baseline_ew, baseline_ns, wavelength=0.21):
    """
    Compute UV coordinates from baseline components.

    Args:
        baseline_ew: East-West baseline component (meters)
        baseline_ns: North-South baseline component (meters)
        wavelength: Observation wavelength (meters), default 21cm for HI

    Returns:
        (u, v) coordinates in wavelengths
    """
    u = baseline_ew / wavelength
    v = baseline_ns / wavelength
    return u, v


def analyze_array_coverage(array):
    """Analyze array configuration and UV coverage."""

    print("=" * 60)
    print("ANTENNA ARRAY ANALYSIS")
    print("=" * 60)

    # Basic statistics
    total = len(array)
    with_coords = array.filter_by_coordinates(has_coords=True)

    print(f"\nArray Statistics:")
    print(f"  Total antennas: {total}")
    print(f"  With coordinates: {len(with_coords)} ({100*len(with_coords)/total:.1f}%)")

    if len(with_coords) < 2:
        print("\n⚠️  Need at least 2 antennas with coordinates for analysis")
        return

    # Baseline analysis
    print(f"\n{'Baseline Analysis':-^60}")
    baselines = array.compute_all_baselines(use_coordinates=True, include_self=False)

    if not baselines:
        print("No baselines to analyze")
        return

    distances = [dist for _, _, dist in baselines]

    print(f"\nNumber of baselines: {len(baselines)}")
    print(f"  Shortest: {min(distances):.2f}m")
    print(f"  Longest: {max(distances):.2f}m")
    print(f"  Average: {sum(distances)/len(distances):.2f}m")
    print(f"  Median: {sorted(distances)[len(distances)//2]:.2f}m")

    # Baseline length distribution
    print("\nBaseline distribution:")
    bins = [0, 20, 50, 100, 200, float("inf")]
    bin_labels = ["0-20m", "20-50m", "50-100m", "100-200m", ">200m"]

    for i, (low, high) in enumerate(zip(bins[:-1], bins[1:])):
        count = sum(1 for d in distances if low <= d < high)
        pct = 100 * count / len(distances)
        bar = "█" * int(pct / 2)
        print(f"  {bin_labels[i]:>10}: {count:3d} ({pct:5.1f}%) {bar}")

    # UV coverage estimate (simplified)
    print(f"\n{'UV Coverage Analysis (21cm HI line)':-^60}")

    # Get antenna positions
    positions = {}
    for ant in with_coords:
        # Approximate EW/NS offsets from center
        # This is simplified - real UV analysis needs hour angle tracking
        lat_offset = (
            ant.latitude - with_coords[0].latitude
        ) * 111000  # ~111km per degree
        lon_offset = (
            (ant.longitude - with_coords[0].longitude) * 111000 * 0.798
        )  # cos(38°)
        positions[ant.antenna_number] = (lon_offset, lat_offset)

    # Compute UV points
    uv_points = []
    for ant1_num, ant2_num, _ in baselines:
        if ant1_num in positions and ant2_num in positions:
            pos1 = positions[ant1_num]
            pos2 = positions[ant2_num]
            ew = pos2[0] - pos1[0]
            ns = pos2[1] - pos1[1]
            u, v = compute_uv_coordinates(ew, ns, wavelength=0.21)
            uv_points.append((u, v))

    if uv_points:
        u_vals = [abs(u) for u, v in uv_points]
        v_vals = [abs(v) for u, v in uv_points]

        print(f"\nUV coverage points: {len(uv_points)}")
        print(f"  Max |u|: {max(u_vals):.1f} wavelengths")
        print(f"  Max |v|: {max(v_vals):.1f} wavelengths")
        print(f"  Angular resolution: ~{206265 / max(u_vals + v_vals):.1f} arcsec")

    # Find extremal antennas
    print(f"\n{'Extremal Antennas':-^60}")

    # Find north/south/east/west most antennas
    north_ant = max(with_coords, key=lambda a: a.latitude)
    south_ant = min(with_coords, key=lambda a: a.latitude)
    east_ant = max(with_coords, key=lambda a: a.longitude)
    west_ant = min(with_coords, key=lambda a: a.longitude)

    print(f"\n  Northernmost: {north_ant.antenna_number} @ {north_ant.grid_code}")
    print(f"                Lat: {north_ant.latitude:.6f}°")

    print(f"\n  Southernmost: {south_ant.antenna_number} @ {south_ant.grid_code}")
    print(f"                Lat: {south_ant.latitude:.6f}°")

    print(f"\n  Easternmost:  {east_ant.antenna_number} @ {east_ant.grid_code}")
    print(f"                Lon: {east_ant.longitude:.6f}°")

    print(f"\n  Westernmost:  {west_ant.antenna_number} @ {west_ant.grid_code}")
    print(f"                Lon: {west_ant.longitude:.6f}°")

    # Array extent
    lat_extent = (north_ant.latitude - south_ant.latitude) * 111000
    lon_extent = (east_ant.longitude - west_ant.longitude) * 111000 * 0.798

    print(f"\n  Array extent: {lat_extent:.1f}m (N-S) × {lon_extent:.1f}m (E-W)")


def find_nearest_neighbors(array, antenna_number, n=3):
    """Find N nearest neighbors to a given antenna."""

    target = array.get_antenna(antenna_number)
    if not target:
        print(f"Antenna {antenna_number} not found")
        return

    if not target.has_coordinates():
        print(f"Antenna {antenna_number} has no coordinates")
        return

    print(f"\n{'Nearest Neighbors':-^60}")
    print(f"\nTarget: {target.antenna_number} @ {target.grid_code}")

    # Compute distances to all other antennas
    neighbors = []
    for ant in array:
        if ant.antenna_number != antenna_number and ant.has_coordinates():
            dist = array.compute_baseline(target, ant, use_coordinates=True)
            neighbors.append((ant, dist))

    # Sort by distance and take top N
    neighbors.sort(key=lambda x: x[1])

    print(f"\nClosest {min(n, len(neighbors))} neighbors:")
    for i, (ant, dist) in enumerate(neighbors[:n], 1):
        print(f"  {i}. {ant.antenna_number} @ {ant.grid_code}")
        print(f"     Distance: {dist:.2f}m")


def main():
    db_path = Path(__file__).parent.parent / "database" / "parts.db"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return

    # Load array
    print("Loading antenna array...")
    array = AntennaArray.from_database(db_path, array_id="C")

    # Comprehensive analysis
    analyze_array_coverage(array)

    # Find nearest neighbors for first antenna
    with_coords = array.filter_by_coordinates(has_coords=True)
    if with_coords:
        find_nearest_neighbors(array, with_coords[0].antenna_number, n=3)

    print("\n" + "=" * 60)
    print("✓ Analysis complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
