#!/usr/bin/env python3
"""
Generate WGS84 coordinates for all CASM grid positions.

Reference point: CC000E01 at LAT: 37.234167°, LON: -118.283333°, ELEV: 1206.84m
North-South distance: 50cm between rows
East-West distances: Alternating 38cm and 44.5cm pattern
"""

import csv
import math
from datetime import datetime

# Reference point (CC000E01)
REF_LAT = 37.234167
REF_LON = -118.283333
REF_ELEV = 1206.84
REF_ROW = 0  # Center row
REF_COL = 1  # East column 1

# Distances in meters
NS_DIST = 0.50  # 50cm between rows (N-S)

# East-West distances (alternating pattern)
# E0→E1: 38cm, E1→E2: 44.5cm, E2→E3: 38cm, E3→E4: 44.5cm, E4→E5: 38cm
EW_DISTS = {
    (0, 1): 0.38,   # E0 to E1
    (1, 2): 0.445,  # E1 to E2
    (2, 3): 0.38,   # E2 to E3
    (3, 4): 0.445,  # E3 to E4
    (4, 5): 0.38,   # E4 to E5
}

# Earth's radius in meters
EARTH_RADIUS = 6378137.0


def meters_to_degrees_lat(meters):
    """Convert meters to degrees latitude (constant)."""
    return meters / (EARTH_RADIUS * math.pi / 180.0)


def meters_to_degrees_lon(meters, latitude):
    """Convert meters to degrees longitude (varies with latitude)."""
    lat_rad = math.radians(latitude)
    return meters / (EARTH_RADIUS * math.cos(lat_rad) * math.pi / 180.0)


def calculate_ew_distance(col_from, col_to):
    """Calculate cumulative East-West distance between two columns."""
    if col_from == col_to:
        return 0.0
    
    start = min(col_from, col_to)
    end = max(col_from, col_to)
    total_dist = 0.0
    
    for col in range(start, end):
        # Get distance for this step
        if (col, col + 1) in EW_DISTS:
            total_dist += EW_DISTS[(col, col + 1)]
        else:
            # Extrapolate pattern: odd→even = 44.5cm, even→odd = 38cm
            if col % 2 == 0:
                total_dist += 0.38
            else:
                total_dist += 0.445
    
    # Negate if going west (decreasing column number)
    if col_to < col_from:
        total_dist = -total_dist
    
    return total_dist


def calculate_coordinates(row_offset, east_col):
    """Calculate WGS84 coordinates for a grid position."""
    # Calculate North-South offset from reference (positive = north)
    ns_offset_m = (row_offset - REF_ROW) * NS_DIST
    
    # Calculate East-West offset from reference (positive = east)
    ew_offset_m = calculate_ew_distance(REF_COL, east_col)
    
    # Convert to degrees
    lat_offset = meters_to_degrees_lat(ns_offset_m)
    lon_offset = meters_to_degrees_lon(ew_offset_m, REF_LAT)
    
    # Calculate final coordinates
    latitude = REF_LAT + lat_offset
    longitude = REF_LON + lon_offset
    height = REF_ELEV  # Assuming flat terrain for now
    
    return latitude, longitude, height


def generate_grid_positions(output_file='database/grid_positions.csv'):
    """Generate all grid positions and write to CSV."""
    positions = []
    
    # Get current date for notes
    update_date = datetime.now().strftime('%Y-%m-%d')
    
    # Generate all positions: CN021 to CS021, E00 to E05
    for row in range(-21, 22):  # -21 (S21) to +21 (N21), including 0 (C)
        for col in range(0, 6):  # E00 to E05
            # Determine array prefix
            if row > 0:
                prefix = 'CN'
                row_num = row
            elif row < 0:
                prefix = 'CS'
                row_num = abs(row)
            else:
                prefix = 'CC'
                row_num = 0
            
            # Format grid code
            grid_code = f"{prefix}{row_num:03d}E{col:02d}"
            
            # Calculate coordinates
            lat, lon, height = calculate_coordinates(row, col)
            
            positions.append({
                'grid_code': grid_code,
                'latitude': round(lat, 8),
                'longitude': round(lon, 8),
                'height': round(height, 2),
                'coordinate_system': 'WGS84',
                'notes': f'Generated from CC000E01 reference on {update_date}'
            })
    
    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'grid_code', 'latitude', 'longitude', 'height', 
            'coordinate_system', 'notes'
        ])
        writer.writeheader()
        writer.writerows(positions)
    
    print(f"Generated {len(positions)} grid positions")
    print(f"Written to {output_file}")
    print(f"Update date: {update_date}")
    
    # Print some samples for verification
    print("\nSample positions:")
    samples = ['CC000E01', 'CN001E00', 'CS001E05', 'CN021E00', 'CS021E05']
    for grid_code in samples:
        pos = next((p for p in positions if p['grid_code'] == grid_code), None)
        if pos:
            print(f"  {grid_code}: LAT {pos['latitude']:.8f}°, "
                  f"LON {pos['longitude']:.8f}°, ELEV {pos['height']:.2f}m")


if __name__ == '__main__':
    generate_grid_positions()
