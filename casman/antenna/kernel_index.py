"""Kernel index mapping for antenna grid positions.

This module provides functions to convert between grid coordinates and kernel indices
used by the correlator. The kernel index is a 0-indexed linear mapping of antenna
positions in the grid, used for correlator processing.

For the core array with 43 rows (N021 to S021) and 6 columns (E01-E06):
- Kernel indices 0-255 map to a 43x6 grid (258 total positions)
- Mapping follows row-major order starting from CN021E01
- Only the first 256 positions are mapped (CS021E05 and CS021E06 are unmapped)
"""

from typing import Optional, Tuple
import numpy as np

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from casman.config import get_config
from casman.antenna.grid import parse_grid_code, format_grid_code


class KernelIndexArray:
    """Container for kernel index mapping arrays.
    
    Attributes
    ----------
    kernel_indices : np.ndarray
        2D array of kernel indices, shape (n_rows, n_cols).
        -1 indicates unmapped positions.
    grid_codes : np.ndarray
        2D array of grid code strings, shape (n_rows, n_cols).
        Empty string indicates unmapped positions.
    antenna_numbers : np.ndarray
        2D array of antenna part numbers, shape (n_rows, n_cols).
        Empty string indicates unassigned positions.
    snap_ports : np.ndarray
        2D array of SNAP port tuples (chassis, slot, port), shape (n_rows, n_cols).
        None indicates unassigned or unmapped positions.
    snap_board_info : np.ndarray
        2D array of SNAP board configuration dicts, shape (n_rows, n_cols).
        Each dict contains: ip_address, mac_address, serial_number, feng_id, 
        packet_index, adc_input. None for unassigned positions.
    coordinates : np.ndarray
        3D array of coordinates, shape (n_rows, n_cols, 3).
        Each position contains [latitude, longitude, height] in decimal degrees and meters.
        Loaded from grid_positions data in the database.
    shape : tuple
        Shape of the arrays (n_rows, n_cols).
    """
    
    def __init__(
        self,
        kernel_indices: np.ndarray,
        grid_codes: np.ndarray,
        antenna_numbers: np.ndarray,
        snap_ports: np.ndarray,
        snap_board_info: Optional[np.ndarray] = None,
        coordinates: Optional[np.ndarray] = None,
    ):
        """Initialize kernel index array container.
        
        Parameters
        ----------
        kernel_indices : np.ndarray
            2D array of kernel indices
        grid_codes : np.ndarray
            2D array of grid code strings
        antenna_numbers : np.ndarray
            2D array of antenna part numbers
        snap_ports : np.ndarray
            2D array of SNAP port tuples
        snap_board_info : np.ndarray, optional
            2D array of SNAP board configuration dicts
        coordinates : np.ndarray, optional
            3D array of shape (n_rows, n_cols, 3) containing [lat, lon, height]
        """
        self.kernel_indices = kernel_indices
        self.grid_codes = grid_codes
        self.antenna_numbers = antenna_numbers
        self.snap_ports = snap_ports
        self.snap_board_info = snap_board_info
        self.coordinates = coordinates
        self.shape = kernel_indices.shape
    
    def get_by_kernel_index(self, kernel_idx: int) -> Optional[dict]:
        """Get information for a specific kernel index.
        
        Parameters
        ----------
        kernel_idx : int
            Kernel index to query (0-255)
        
        Returns
        -------
        dict or None
            Dictionary with keys: 'grid_code', 'antenna_number', 'snap_port', 
            'snap_board_info', 'ns', 'ew'. Returns None if kernel_idx is out of 
            range or unmapped.
            
            snap_board_info dict contains: 'ip_address', 'mac_address', 
            'serial_number', 'feng_id', 'packet_index', 'adc_input'
        """
        # Check if kernel_idx is valid
        if kernel_idx < 0:
            return None
        
        # Find position of kernel_idx in array
        positions = np.where(self.kernel_indices == kernel_idx)
        if len(positions[0]) == 0:
            return None
        
        row, col = positions[0][0], positions[1][0]
        
        snap_port = self.snap_ports[row, col]
        snap_tuple = tuple(snap_port) if snap_port is not None else None
        
        board_info = None
        if self.snap_board_info is not None:
            board_info = self.snap_board_info[row, col]
        
        # Get coordinates
        lat, lon, hgt = None, None, None
        if self.coordinates is not None:
            lat = float(self.coordinates[row, col, 0])
            lon = float(self.coordinates[row, col, 1])
            hgt = float(self.coordinates[row, col, 2])
        
        return {
            'grid_code': self.grid_codes[row, col],
            'antenna_number': self.antenna_numbers[row, col],
            'snap_port': snap_tuple,
            'snap_board_info': board_info,
            'ns': int(row),
            'ew': int(col),
            'latitude': lat,
            'longitude': lon,
            'height': hgt,
        }
    
    def get_by_grid_code(self, grid_code: str) -> Optional[dict]:
        """Get information for a specific grid code.
        
        Parameters
        ----------
        grid_code : str
            Grid code to query (e.g., 'CN021E01')
        
        Returns
        -------
        dict or None
            Dictionary with keys: 'kernel_index', 'antenna_number', 'snap_port', 
            'snap_board_info', 'ns', 'ew'. Returns None if grid_code not found 
            or unmapped.
            
            snap_board_info dict contains: 'ip_address', 'mac_address', 
            'serial_number', 'feng_id', 'packet_index', 'adc_input'
        """
        # Find position of grid_code in array
        positions = np.where(self.grid_codes == grid_code.upper())
        if len(positions[0]) == 0:
            return None
        
        row, col = positions[0][0], positions[1][0]
        kernel_idx = self.kernel_indices[row, col]
        
        if kernel_idx == -1:
            return None
        
        snap_port = self.snap_ports[row, col]
        snap_tuple = tuple(snap_port) if snap_port is not None else None
        
        board_info = None
        if self.snap_board_info is not None:
            board_info = self.snap_board_info[row, col]
        
        # Get coordinates
        lat, lon, hgt = None, None, None
        if self.coordinates is not None:
            lat = float(self.coordinates[row, col, 0])
            lon = float(self.coordinates[row, col, 1])
            hgt = float(self.coordinates[row, col, 2])
        
        return {
            'kernel_index': int(kernel_idx),
            'antenna_number': self.antenna_numbers[row, col],
            'snap_port': snap_tuple,
            'snap_board_info': board_info,
            'ns': int(row),
            'ew': int(col),
            'latitude': lat,
            'longitude': lon,
            'height': hgt,
        }
    
    def __repr__(self) -> str:
        """String representation of kernel index array."""
        return f"KernelIndexArray(shape={self.shape}, mapped_positions={np.sum(self.kernel_indices >= 0)})"
    
    def plot_positions(self, show: bool = True):
        """Plot grid positions with labeled axes.
        
        Shows a scatter plot of all grid positions with coordinates.
        Labels major rows (S21, S10, C00, N10, N21) and all columns (E01-E06).
        
        Parameters
        ----------
        show : bool, optional
            If True, display the plot immediately (default: True).
            If False, return the figure and axes for further customization.
        
        Returns
        -------
        tuple of (fig, ax) if show=False, None otherwise
        
        Examples
        --------
        >>> array_map = get_array_index_map()
        >>> array_map.plot_positions()  # Display plot
        
        >>> fig, ax = array_map.plot_positions(show=False)
        >>> ax.set_title('Custom Title')
        >>> plt.show()
        """
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib is required for plotting. Install with: pip install matplotlib")
        
        if self.coordinates is None:
            raise ValueError("No coordinate data available. Load coordinates first.")
        
        # Extract coordinates and convert to local meters
        n_rows, n_cols = self.shape
        
        # Find CC000E01 as reference point
        ref_lat, ref_lon = None, None
        for row in range(n_rows):
            for col in range(n_cols):
                if self.grid_codes[row, col] == 'CC000E01':
                    ref_lat = self.coordinates[row, col, 0]
                    ref_lon = self.coordinates[row, col, 1]
                    break
            if ref_lat is not None:
                break
        
        if ref_lat is None:
            raise ValueError("Reference point CC000E01 not found")
        
        # Convert to local Easting/Northing in meters relative to CC000E01
        # At ~37° latitude: 1° lat ≈ 111,132 m, 1° lon ≈ 88,649 m
        meters_per_deg_lat = 111132.0
        meters_per_deg_lon = 88649.0  # at 37° latitude
        
        eastings = []
        northings = []
        grid_codes = []
        
        for row in range(n_rows):
            for col in range(n_cols):
                grid_code = self.grid_codes[row, col]
                if grid_code:  # Skip empty positions
                    lat = self.coordinates[row, col, 0]
                    lon = self.coordinates[row, col, 1]
                    if lat != 0.0 or lon != 0.0:  # Skip zero coordinates
                        # Convert to meters relative to reference
                        easting = (lon - ref_lon) * meters_per_deg_lon
                        northing = (lat - ref_lat) * meters_per_deg_lat
                        eastings.append(easting)
                        northings.append(northing)
                        grid_codes.append(grid_code)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Plot all points with square markers
        ax.scatter(eastings, northings, c='blue', s=20, alpha=0.6, zorder=2, marker='s')
        
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
            col_label = f"E{col_num:02d}"
            
            # Store points we want to label
            key = (row_label, col_label)
            label_points[key] = (eastings[i], northings[i])
        
        # Label major rows on the left (at E01)
        major_rows = ['N21', 'N10', 'C00', 'S10', 'S21']
        for row_label in major_rows:
            row_key = f"{row_label[0]}{int(row_label[1:]):03d}"
            key = (row_key, 'E01')
            if key in label_points:
                east, north = label_points[key]
                ax.annotate(row_label, xy=(east, north), xytext=(-15, 0),
                           textcoords='offset points', ha='right', va='center',
                           fontsize=10, fontweight='bold', color='darkred')
        
        # Label only E01 and E06 columns on top (at N21)
        for col in [1, 6]:
            col_label = f"E{col:02d}"
            key = ('N021', col_label)
            if key in label_points:
                east, north = label_points[key]
                ax.annotate(col_label, xy=(east, north), xytext=(0, 10),
                           textcoords='offset points', ha='center', va='bottom',
                           fontsize=10, fontweight='bold', color='darkblue')
        
        # Annotate CC000E01 with geographic coordinates
        key = ('C000', 'E01')
        if key in label_points:
            east, north = label_points[key]
            geo_text = f'CC000E01\n({ref_lat:.6f}°, {ref_lon:.6f}°)'
            ax.annotate(geo_text, xy=(east, north), xytext=(-20, -10),
                       textcoords='offset points', ha='right', va='top',
                       fontsize=8, color='green',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', color='green', lw=1))
        
        # Styling
        ax.set_xlabel('Easting (m)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Northing (m)', fontsize=12, fontweight='bold')
        ax.set_title('CASM Grid Positions (Local Coordinates)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_aspect('equal', adjustable='datalim')
                
        plt.tight_layout()
        
        if show:
            plt.show()
            return None
        else:
            return fig, ax


def grid_to_kernel_index(
    grid_code: str, array_name: str = "core"
) -> Optional[int]:
    """Convert grid coordinate to kernel index.
    
    Parameters
    ----------
    grid_code : str
        Grid position code (e.g., 'CN021E01')
    array_name : str, optional
        Name of array in config (default: 'core')
    
    Returns
    -------
    int or None
        Kernel index (0-255) if position is mapped, None otherwise
    
    Examples
    --------
    >>> grid_to_kernel_index('CN021E01')
    0
    >>> grid_to_kernel_index('CN021E06')
    5
    >>> grid_to_kernel_index('CS021E04')
    255
    >>> grid_to_kernel_index('CS021E06')  # Not mapped
    None
    """
    # Check if kernel index is enabled for this array (default: True for core)
    default_enabled = array_name == "core"  # Core array enabled by default
    enabled = get_config(f"grid.{array_name}.kernel_index.enabled", default_enabled)
    if not enabled:
        return None
    
    # Parse grid code
    try:
        position = parse_grid_code(grid_code)
    except ValueError:
        return None
    
    # Get kernel index configuration
    max_index = get_config(f"grid.{array_name}.kernel_index.max_index", 255)
    start_row = get_config(f"grid.{array_name}.kernel_index.start_row", 21)
    start_column = get_config(f"grid.{array_name}.kernel_index.start_column", 1)
    
    # Get array dimensions
    north_rows = get_config(f"grid.{array_name}.north_rows", 21)
    south_rows = get_config(f"grid.{array_name}.south_rows", 21)
    east_columns = get_config(f"grid.{array_name}.east_columns", 6)
    
    # Convert grid position to array indices
    # Map row_offset: north_rows (N021) -> 0, ..., 0 (C000) -> north_rows, ..., -south_rows (S021) -> north_rows + south_rows
    if position.direction == 'N':
        array_row = north_rows - position.offset
    elif position.direction == 'C':
        array_row = north_rows
    else:  # 'S'
        array_row = north_rows + position.offset
    
    # Map east_col: 1 (E01) -> 0, 2 (E02) -> 1, ...
    array_col = position.east_col - 1
    
    # Check if position is within bounds
    if array_row < 0 or array_row >= (north_rows + south_rows + 1):
        return None
    if array_col < 0 or array_col >= east_columns:
        return None
    
    # Calculate kernel index using row-major ordering
    kernel_idx = array_row * east_columns + array_col
    
    # Check if kernel index exceeds maximum
    if kernel_idx > max_index:
        return None
    
    return kernel_idx


def kernel_index_to_grid(
    kernel_idx: int, array_name: str = "core"
) -> Optional[str]:
    """Convert kernel index to grid coordinate.
    
    Parameters
    ----------
    kernel_idx : int
        Kernel index (0-255)
    array_name : str, optional
        Name of array in config (default: 'core')
    
    Returns
    -------
    str or None
        Grid position code (e.g., 'CN021E01') if valid, None otherwise
    
    Examples
    --------
    >>> kernel_index_to_grid(0)
    'CN021E01'
    >>> kernel_index_to_grid(5)
    'CN021E06'
    >>> kernel_index_to_grid(255)
    'CS021E04'
    >>> kernel_index_to_grid(256)  # Out of range
    None
    """
    # Check if kernel index is enabled for this array
    enabled = get_config(f"grid.{array_name}.kernel_index.enabled", False)
    if not enabled:
        return None
    
    # Get kernel index configuration
    max_index = get_config(f"grid.{array_name}.kernel_index.max_index", 255)
    
    # Check if kernel index is valid
    if kernel_idx < 0 or kernel_idx > max_index:
        return None
    
    # Get array dimensions
    north_rows = get_config(f"grid.{array_name}.north_rows", 21)
    south_rows = get_config(f"grid.{array_name}.south_rows", 21)
    east_columns = get_config(f"grid.{array_name}.east_columns", 6)
    array_id = get_config(f"grid.{array_name}.array_id", "C")
    
    # Convert kernel index to array indices (row-major order)
    array_row = kernel_idx // east_columns
    array_col = kernel_idx % east_columns
    
    # Convert array indices to grid position
    # Map array_row: 0 -> N021, ..., north_rows -> C000, ..., north_rows + south_rows -> S021
    if array_row < north_rows:
        direction = 'N'
        offset = north_rows - array_row
    elif array_row == north_rows:
        direction = 'C'
        offset = 0
    else:
        direction = 'S'
        offset = array_row - north_rows
    
    # Map array_col: 0 -> E01, 1 -> E02, ...
    east_col = array_col + 1
    
    # Format grid code
    try:
        grid_code = format_grid_code(array_id, direction, offset, east_col)
        return grid_code
    except ValueError:
        return None


def get_array_index_map(
    array_name: str = "core", *, db_dir: Optional[str] = None
) -> "KernelIndexArray":
    """Get complete kernel index mapping with antenna and SNAP port information.
    
    This function creates 2D arrays mapping kernel indices to grid coordinates,
    antenna part numbers, and SNAP port assignments. Arrays are sized according
    to the array configuration: (north_rows + south_rows + 1) × east_columns.
    
    Parameters
    ----------
    array_name : str, optional
        Name of array in config (default: 'core')
    db_dir : str, optional
        Custom database directory for testing
    
    Returns
    -------
    KernelIndexArray
        Object containing 2D numpy arrays:
        - kernel_indices: int array, -1 for unmapped positions
        - grid_codes: str array, empty string for invalid positions
        - antenna_numbers: str array, empty string for unassigned positions
        - snap_ports: object array of tuples (chassis, slot, port), None for unassigned
        - snap_board_info: object array of dicts with SNAP board configuration
          (ip_address, mac_address, serial_number, feng_id, packet_index, adc_input)
        - coordinates: 3D float array of shape (n_rows, n_cols, 3) containing
          [latitude, longitude, height] for all grid positions
    
    Examples
    --------
    >>> kernel_data = get_array_index_map()
    >>> kernel_data.shape
    (43, 6)
    >>> kernel_data.kernel_indices[0, 0]  # CN021E01
    0
    >>> kernel_data.grid_codes[0, 0]
    'CN021E01'
    >>> info = kernel_data.get_by_kernel_index(0)
    >>> info['grid_code']
    'CN021E01'
    >>> info['snap_board_info']['ip_address']
    '192.168.1.1'
    >>> info['snap_board_info']['packet_index']
    5
    """
    # Check if kernel index is enabled for this array (default: True for core)
    default_enabled = array_name == "core"  # Core array enabled by default
    enabled = get_config(f"grid.{array_name}.kernel_index.enabled", default_enabled)
    if not enabled:
        raise ValueError(f"Kernel index mapping not enabled for array '{array_name}'")
    
    # Get array dimensions
    north_rows = get_config(f"grid.{array_name}.north_rows", 21)
    south_rows = get_config(f"grid.{array_name}.south_rows", 21)
    east_columns = get_config(f"grid.{array_name}.east_columns", 6)
    array_id = get_config(f"grid.{array_name}.array_id", "C")
    
    # Calculate array shape
    n_rows = north_rows + south_rows + 1
    n_cols = east_columns
    
    # Initialize arrays
    kernel_indices = np.full((n_rows, n_cols), -1, dtype=np.int16)
    grid_codes = np.full((n_rows, n_cols), "", dtype=object)
    antenna_numbers = np.full((n_rows, n_cols), "", dtype=object)
    snap_ports = np.full((n_rows, n_cols), None, dtype=object)
    snap_board_info = np.full((n_rows, n_cols), None, dtype=object)
    coordinates = np.zeros((n_rows, n_cols, 3), dtype=np.float64)
    
    # Populate grid codes and kernel indices
    for row in range(n_rows):
        for col in range(n_cols):
            # Convert array indices to grid position
            if row < north_rows:
                direction = 'N'
                offset = north_rows - row
            elif row == north_rows:
                direction = 'C'
                offset = 0
            else:
                direction = 'S'
                offset = row - north_rows
            
            east_col = col + 1
            
            try:
                grid_code = format_grid_code(array_id, direction, offset, east_col)
                grid_codes[row, col] = grid_code
                
                # Calculate kernel index
                kernel_idx = grid_to_kernel_index(grid_code, array_name)
                if kernel_idx is not None:
                    kernel_indices[row, col] = kernel_idx
            except ValueError:
                # Invalid grid code
                pass
    
    # Load grid coordinates from database for ALL positions
    try:
        import sqlite3
        from casman.database.connection import get_database_path
        
        if db_dir is not None:
            import os
            db_path = os.path.join(db_dir, "parts.db")
        else:
            db_path = get_database_path("parts.db", None)
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get coordinates for all grid positions from grid_positions table
            cursor.execute("""
                SELECT grid_code, latitude, longitude, height
                FROM grid_positions
            """)
            
            for row_data in cursor.fetchall():
                grid_code = row_data['grid_code'].upper()
                matches = np.where(grid_codes == grid_code)
                if len(matches[0]) > 0:
                    row, col = matches[0][0], matches[1][0]
                    coordinates[row, col, 0] = row_data['latitude']
                    coordinates[row, col, 1] = row_data['longitude']
                    coordinates[row, col, 2] = row_data['height']
    except Exception:
        # Database not available or table doesn't exist, coordinates will be zero
        pass
    
    # Get antenna position assignments from database
    try:
        # Import here to avoid circular imports
        from casman.database.antenna_positions import get_all_antenna_positions
        from casman.antenna.chain import get_snap_ports_for_antenna
        
        positions = get_all_antenna_positions(db_dir=db_dir)
        
        for pos in positions:
            grid_code = pos.get('grid_code', '').upper()
            antenna_num = pos.get('antenna_number', '')
            
            # Find this grid code in our array
            matches = np.where(grid_codes == grid_code)
            if len(matches[0]) > 0:
                row, col = matches[0][0], matches[1][0]
                antenna_numbers[row, col] = antenna_num
                
                # Get SNAP ports for this antenna
                try:
                    ports = get_snap_ports_for_antenna(antenna_num, db_dir=db_dir)
                    if ports['p1']:
                        # Store P1 port as the primary SNAP port
                        p1 = ports['p1']
                        snap_ports[row, col] = (
                            p1['chassis'],
                            p1['slot'],
                            p1['port']
                        )
                        
                        # Store SNAP board info if available
                        if 'board_info' in p1:
                            board_info = p1['board_info']
                            snap_board_info[row, col] = {
                                'ip_address': board_info.get('ip_address', ''),
                                'mac_address': board_info.get('mac_address', ''),
                                'serial_number': board_info.get('serial_number', ''),
                                'feng_id': board_info.get('feng_id', -1),
                                'packet_index': board_info.get('packet_index', -1),
                                'adc_input': p1['port'],
                            }
                except Exception:
                    # SNAP ports not available for this antenna
                    pass
    except Exception:
        # Database not available or error reading positions
        pass
    
    return KernelIndexArray(
        kernel_indices=kernel_indices,
        grid_codes=grid_codes,
        antenna_numbers=antenna_numbers,
        snap_ports=snap_ports,
        snap_board_info=snap_board_info,
        coordinates=coordinates,
    )


__all__ = [
    "KernelIndexArray",
    "grid_to_kernel_index",
    "kernel_index_to_grid",
    "get_array_index_map",
]
