#!/usr/bin/env python3
"""
Plot CASM grid positions from grid_positions.csv.

Shows a scatter plot of all grid positions with labeled axes.
Only labels major rows (S21, C00, N21) and columns (E1-E6).
"""

import csv
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def plot_grid_positions(csv_file='database/grid_positions.csv'):
    """Plot grid positions from CSV file."""
    # Read data
    grid_codes = []
    latitudes = []
    longitudes = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['latitude'] and row['longitude']:
                grid_codes.append(row['grid_code'])
                latitudes.append(float(row['latitude']))
                longitudes.append(float(row['longitude']))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 14))
    
    # Plot all points
    ax.scatter(longitudes, latitudes, c='blue', s=20, alpha=0.6, zorder=2)
    
    # Parse grid codes to find specific points for labeling
    label_points = {}
    for i, grid_code in enumerate(grid_codes):
        # Extract row and column info
        if grid_code.startswith('CN'):
            row_label = f"N{grid_code[2:5]}"
        elif grid_code.startswith('CS'):
            row_label = f"S{grid_code[2:5]}"
        else:  # CC
            row_label = f"C{grid_code[2:5]}"
        
        col_num = int(grid_code[-2:])
        col_label = f"E{col_num}"
        
        # Store points we want to label
        key = (row_label, col_label)
        label_points[key] = (longitudes[i], latitudes[i])
    
    # Label major rows on the left (at E01
    major_rows = ['N21', 'N10', 'C00', 'S10', 'S21']
    for row_label in major_rows:
        row_key = f"{row_label[0]}{int(row_label[1:]):03d}"
        key = (row_key, 'E01')
        if key in label_points:
            lon, lat = label_points[key]
            ax.annotate(row_label, xy=(lon, lat), xytext=(-15, 0),
                       textcoords='offset points', ha='right', va='center',
                       fontsize=10, fontweight='bold', color='darkred')
    
    # Label all columns on top (at N21)
    for col in range(1, 7):
        col_label = f"E{col:02d}"
        key = ('N021', col_label)
        if key in label_points:
            lon, lat = label_points[key]
            ax.annotate(col_label, xy=(lon, lat), xytext=(0, 10),
                       textcoords='offset points', ha='center', va='bottom',
                       fontsize=10, fontweight='bold', color='darkblue')
    
    # Styling
    ax.set_xlabel('Longitude (°)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitude (°)', fontsize=12, fontweight='bold')
    ax.set_title('CASM Grid Positions (WGS84)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal', adjustable='datalim')
    
    # Add info text
    info_text = f"Total positions: {len(grid_codes)}\n"
    info_text += f"Rows: S21 to N21\n"
    info_text += f"Columns: E1 to E6"
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    import sys
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'database/grid_positions.csv'
    plot_grid_positions(csv_file)
