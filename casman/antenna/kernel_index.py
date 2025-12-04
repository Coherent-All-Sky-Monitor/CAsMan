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
    shape : tuple
        Shape of the arrays (n_rows, n_cols).
    """
    
    def __init__(
        self,
        kernel_indices: np.ndarray,
        grid_codes: np.ndarray,
        antenna_numbers: np.ndarray,
        snap_ports: np.ndarray,
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
        """
        self.kernel_indices = kernel_indices
        self.grid_codes = grid_codes
        self.antenna_numbers = antenna_numbers
        self.snap_ports = snap_ports
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
            Dictionary with keys: 'grid_code', 'antenna_number', 'snap_port', 'ns', 'ew'
            Returns None if kernel_idx is out of range or unmapped.
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
        
        return {
            'grid_code': self.grid_codes[row, col],
            'antenna_number': self.antenna_numbers[row, col],
            'snap_port': snap_tuple,
            'ns': int(row),
            'ew': int(col),
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
            Dictionary with keys: 'kernel_index', 'antenna_number', 'snap_port', 'ns', 'ew'
            Returns None if grid_code not found or unmapped.
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
        
        return {
            'kernel_index': int(kernel_idx),
            'antenna_number': self.antenna_numbers[row, col],
            'snap_port': snap_tuple,
            'ns': int(row),
            'ew': int(col),
        }
    
    def __repr__(self) -> str:
        """String representation of kernel index array."""
        return f"KernelIndexArray(shape={self.shape}, mapped_positions={np.sum(self.kernel_indices >= 0)})"


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
    # Check if kernel index is enabled for this array
    enabled = get_config(f"grid.{array_name}.kernel_index.enabled", False)
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


def get_antenna_kernel_idx(
    array_name: str = "core", *, db_dir: Optional[str] = None
) -> KernelIndexArray:
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
    
    Examples
    --------
    >>> kernel_data = get_antenna_kernel_idx()
    >>> kernel_data.shape
    (43, 6)
    >>> kernel_data.kernel_indices[0, 0]  # CN021E01
    0
    >>> kernel_data.grid_codes[0, 0]
    'CN021E01'
    >>> info = kernel_data.get_by_kernel_index(0)
    >>> info['grid_code']
    'CN021E01'
    """
    # Check if kernel index is enabled for this array
    enabled = get_config(f"grid.{array_name}.kernel_index.enabled", False)
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
                    if ports['p1'] and ports['p2']:
                        # Store P1 port as the primary SNAP port
                        p1 = ports['p1']
                        snap_ports[row, col] = np.array([
                            p1['chassis'],
                            ord(p1['slot']) if isinstance(p1['slot'], str) else p1['slot'],
                            p1['port']
                        ], dtype=object)
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
    )


__all__ = [
    "KernelIndexArray",
    "grid_to_kernel_index",
    "kernel_index_to_grid",
    "get_antenna_kernel_idx",
]
