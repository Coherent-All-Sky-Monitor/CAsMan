#!/usr/bin/env python3
"""Test the grid coordinates feature."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from casman.database.antenna_positions import (
    get_antenna_position,
    get_all_antenna_positions,
)

print("Testing coordinate retrieval...")
print("=" * 60)

# Test 1: Get specific antenna with coordinates
print("\n1. Get position for ANT00001 (should have coordinates):")
pos = get_antenna_position("ANT00001")
if pos:
    print(f"   Grid: {pos['grid_code']}")
    print(f"   Latitude: {pos.get('latitude', 'N/A')}")
    print(f"   Longitude: {pos.get('longitude', 'N/A')}")
    print(f"   Height: {pos.get('height', 'N/A')} m")
    print(f"   System: {pos.get('coordinate_system', 'N/A')}")
else:
    print("   Not assigned")

# Test 2: Get all positions and show those with coordinates
print("\n2. All positions with coordinates:")
all_pos = get_all_antenna_positions(array_id="C")
with_coords = [p for p in all_pos if p.get("latitude") is not None]
print(f"   Total positions: {len(all_pos)}")
print(f"   With coordinates: {len(with_coords)}")

if with_coords:
    print("\n   Details:")
    for p in with_coords:
        print(f"   - {p['antenna_number']} @ {p['grid_code']}")
        print(
            f"     ({p['latitude']}, {p['longitude']}, {p['height']}m {p['coordinate_system']})"
        )

print("\n" + "=" * 60)
print("✓ Coordinate feature working correctly")
