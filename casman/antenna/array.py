"""
Lightweight antenna array position management.

This module provides a minimal-dependency interface for working with antenna
positions, coordinates, and baseline calculations. It can be installed
independently of the full CAsMan toolkit.

Classes
-------
AntennaPosition : Dataclass representing a single antenna with all metadata
AntennaArray : Collection of antennas with baseline computation methods

Example
-------
>>> from casman.antenna.array import AntennaArray
>>> array = AntennaArray.from_database('database/parts.db')
>>> ant1 = array.get_antenna('ANT00001')
>>> ant2 = array.get_antenna('ANT00002')
>>> baseline = array.compute_baseline(ant1, ant2)
>>> print(f"Baseline: {baseline:.2f} meters")
"""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple, Dict

from .grid import AntennaGridPosition, parse_grid_code


@dataclass
class AntennaPosition:
    """Complete antenna position information including coordinates and SNAP mapping.

    Attributes
    ----------
    antenna_number : str
        Base antenna number without polarization (e.g., 'ANT00001')
    grid_position : AntennaGridPosition
        Parsed grid position object with row/column offsets
    latitude : float, optional
        Latitude in decimal degrees (WGS84 or other coordinate system)
    longitude : float, optional
        Longitude in decimal degrees
    height : float, optional
        Height/elevation in meters above reference
    coordinate_system : str, optional
        Coordinate system identifier (e.g., 'WGS84', 'local')
    assigned_at : str, optional
        ISO timestamp of position assignment
    notes : str, optional
        Field notes or comments
    db_dir : str, optional
        Database directory path for chain lookups (internal use)

    Methods
    -------
    has_coordinates() : bool
        Check if geographic coordinates are available
    get_snap_ports() : dict
        Get SNAP port assignments for both polarizations by tracing assembly chains
    format_chain_status(polarization='P1') : str
        Format the assembly chain status for display
    """

    antenna_number: str
    grid_position: AntennaGridPosition
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    height: Optional[float] = None
    coordinate_system: Optional[str] = None
    assigned_at: Optional[str] = None
    notes: Optional[str] = None
    db_dir: Optional[str] = field(default=None, repr=False, compare=False)

    def has_coordinates(self) -> bool:
        """Check if this antenna has geographic coordinates."""
        return self.latitude is not None and self.longitude is not None

    def get_snap_ports(self) -> dict:
        """Get SNAP port assignments by tracing assembly chains.

        Traces the analog signal chain from this antenna through LNA, COAX,
        and BACKBOARD to determine which SNAP board ports the antenna connects to.

        Returns
        -------
        dict
            SNAP port information for both polarizations:
            {
                'antenna': str,        # Base antenna number (ANT00001)
                'p1': dict or None,    # SNAP info for P1 chain
                'p2': dict or None     # SNAP info for P2 chain
            }

            Each polarization dict (if connected) contains:
            {
                'snap_part': str,      # e.g. 'SNAP1A05'
                'chassis': int,        # 1-4
                'slot': str,           # A-K
                'port': int,           # 0-11
                'chain': list[str]     # Full connection chain
            }

        Examples
        --------
        >>> ant = array.get_antenna('ANT00001')
        >>> ports = ant.get_snap_ports()
        >>> if ports['p1']:
        ...     print(f"P1 connected to {ports['p1']['snap_part']}")
        ... else:
        ...     print("P1 chain not complete")
        """
        from .chain import get_snap_ports_for_antenna

        return get_snap_ports_for_antenna(self.antenna_number, db_dir=self.db_dir)

    def format_chain_status(self, polarization: str = "P1") -> str:
        """Format assembly chain status for display.

        Shows the complete analog signal chain from antenna to SNAP port,
        or indicates where the chain is incomplete.

        Parameters
        ----------
        polarization : str, optional
            Polarization to display ('P1' or 'P2'), default 'P1'

        Returns
        -------
        str
            Formatted chain status, either:
            - "ANT00001P1 → LNA00001P1 → COAX1-001P1 → ... → SNAP1A05"
            - "Chain not connected: ANT00001P1 → LNA00001P1 → [disconnected]"

        Examples
        --------
        >>> ant = array.get_antenna('ANT00001')
        >>> print(ant.format_chain_status('P1'))
        ANT00001P1 → LNA00005P1 → COAX1-023P1 → BACBOARD2-023P1 → SNAP2C04

        >>> print(ant.format_chain_status('P2'))
        Chain not connected: ANT00001P2 → [not assembled]
        """
        pol = polarization.upper()
        if pol not in ["P1", "P2"]:
            return f"Invalid polarization: {polarization}"

        ports = self.get_snap_ports()
        pol_key = pol.lower()
        pol_info = ports.get(pol_key)

        if pol_info and "chain" in pol_info:
            # Chain is complete
            chain_str = " → ".join(pol_info["chain"])
            return chain_str
        else:
            # Chain is incomplete - try to get partial chain
            from casman.database.connection import get_database_path

            if self.db_dir:
                import os

                db_path = os.path.join(self.db_dir, "assembled_casm.db")
            else:
                db_path = get_database_path("assembled_casm.db", None)

            # Trace as far as we can
            start_part = f"{self.antenna_number}{pol}"
            partial_chain = [start_part]

            try:
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()

                    current_part = start_part.upper()
                    max_depth = 10

                    for _ in range(max_depth):
                        cursor.execute(
                            """
                            SELECT connected_to, connection_status
                            FROM assembly
                            WHERE part_number = ?
                            ORDER BY id DESC
                            LIMIT 1
                        """,
                            (current_part,),
                        )

                        row = cursor.fetchone()
                        if not row:
                            partial_chain.append("[not assembled]")
                            break

                        if row["connection_status"] != "connected":
                            partial_chain.append(f"[{row['connection_status']}]")
                            break

                        partial_chain.append(row["connected_to"])
                        current_part = row["connected_to"]

                        if current_part.startswith("SNAP"):
                            break
            except Exception:
                partial_chain.append("[error reading database]")

            chain_str = " → ".join(partial_chain)
            return f"Chain not connected: {chain_str}"

    @property
    def grid_code(self) -> str:
        """Get the grid code string (e.g., 'CN002E03')."""
        return self.grid_position.grid_code

    @property
    def row_offset(self) -> int:
        """Get signed row offset (-999 to +999)."""
        return self.grid_position.row_offset

    @property
    def east_col(self) -> int:
        """Get zero-based east column index."""
        return self.grid_position.east_col


class AntennaArray:
    """Collection of antenna positions with baseline computation capabilities.

    This class provides efficient access to antenna metadata and methods for
    computing baselines between antenna pairs. It can load data from a CAsMan
    database or be constructed programmatically.

    Parameters
    ----------
    antennas : list of AntennaPosition
        List of antenna position objects

    Attributes
    ----------
    antennas : list of AntennaPosition
        All loaded antenna positions

    Methods
    -------
    from_database(db_path, array_id='C') : AntennaArray
        Load antenna array from CAsMan database
    get_antenna(antenna_number) : AntennaPosition or None
        Retrieve antenna by part number
    get_antenna_at_position(grid_code) : AntennaPosition or None
        Retrieve antenna by grid position
    compute_baseline(ant1, ant2, use_coordinates=True) : float
        Compute baseline distance between two antennas
    compute_all_baselines(use_coordinates=True) : list of tuple
        Compute all pairwise baselines
    filter_by_coordinates(has_coords=True) : list of AntennaPosition
        Filter antennas based on coordinate availability

    Examples
    --------
    >>> array = AntennaArray.from_database('database/parts.db')
    >>> print(f"Loaded {len(array.antennas)} antennas")
    >>>
    >>> # Get specific antenna
    >>> ant = array.get_antenna('ANT00001')
    >>> print(f"{ant.antenna_number} at {ant.grid_code}")
    >>>
    >>> # Compute baseline
    >>> ant1 = array.get_antenna('ANT00001')
    >>> ant2 = array.get_antenna('ANT00002')
    >>> baseline = array.compute_baseline(ant1, ant2)
    >>> print(f"Baseline: {baseline:.2f} m")
    """

    def __init__(self, antennas: List[AntennaPosition]):
        """Initialize antenna array with list of positions.

        Parameters
        ----------
        antennas : list of AntennaPosition
            Antenna position objects to include in array
        """
        self.antennas = antennas
        self._antenna_map = {ant.antenna_number: ant for ant in antennas}
        self._grid_map = {ant.grid_code: ant for ant in antennas}

    @classmethod
    def from_database(
        cls, db_path: str | Path, array_id: str = "C", db_dir: Optional[str] = None
    ) -> AntennaArray:
        """Load antenna array from CAsMan database.

        Parameters
        ----------
        db_path : str or Path
            Path to parts.db database file
        array_id : str, optional
            Array identifier to load (default: 'C' for core array)
        db_dir : str, optional
            Database directory for assembly chain lookups (default: use parent of db_path)

        Returns
        -------
        AntennaArray
            Loaded antenna array object

        Raises
        ------
        FileNotFoundError
            If database file doesn't exist
        sqlite3.Error
            If database query fails

        Examples
        --------
        >>> array = AntennaArray.from_database('database/parts.db')
        >>> array = AntennaArray.from_database('database/parts.db', array_id='C')
        """
        db_path = Path(db_path)
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        # Determine database directory for chain lookups
        if db_dir is None:
            db_dir = str(db_path.parent)

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Load antenna positions with coordinates
        cursor.execute(
            """
            SELECT 
                antenna_number, grid_code, array_id, row_offset, east_col,
                latitude, longitude, height, coordinate_system,
                assigned_at, notes
            FROM antenna_positions
            WHERE array_id = ?
            ORDER BY row_offset DESC, east_col ASC
        """,
            (array_id,),
        )

        position_rows = cursor.fetchall()

        conn.close()

        # Build AntennaPosition objects
        antennas = []
        for row in position_rows:
            grid_pos = parse_grid_code(row["grid_code"], enforce_core_bounds=False)

            ant_pos = AntennaPosition(
                antenna_number=row["antenna_number"],
                grid_position=grid_pos,
                latitude=row["latitude"],
                longitude=row["longitude"],
                height=row["height"],
                coordinate_system=row["coordinate_system"],
                assigned_at=row["assigned_at"],
                notes=row["notes"],
                db_dir=db_dir,
            )
            antennas.append(ant_pos)

        return cls(antennas)

    def get_antenna(self, antenna_number: str) -> Optional[AntennaPosition]:
        """Get antenna by part number.

        Parameters
        ----------
        antenna_number : str
            Antenna part number (e.g., 'ANT00001')

        Returns
        -------
        AntennaPosition or None
            Antenna position if found, None otherwise
        """
        return self._antenna_map.get(antenna_number)

    def get_antenna_at_position(self, grid_code: str) -> Optional[AntennaPosition]:
        """Get antenna at specific grid position.

        Parameters
        ----------
        grid_code : str
            Grid position code (e.g., 'CN002E03')

        Returns
        -------
        AntennaPosition or None
            Antenna at position if found, None otherwise
        """
        return self._grid_map.get(grid_code.upper())

    def compute_baseline(
        self, ant1: AntennaPosition, ant2: AntennaPosition, use_coordinates: bool = True
    ) -> float:
        """Compute baseline distance between two antennas.

        Parameters
        ----------
        ant1 : AntennaPosition
            First antenna
        ant2 : AntennaPosition
            Second antenna
        use_coordinates : bool, optional
            If True and coordinates available, compute geodetic distance.
            If False or coordinates unavailable, compute grid spacing distance.
            Default: True

        Returns
        -------
        float
            Baseline distance in meters

        Notes
        -----
        When using geographic coordinates, this computes the great circle
        distance using the Haversine formula. Height differences are included
        in the 3D Euclidean distance if both heights are available.

        When using grid spacing, assumes uniform spacing (which may not be
        accurate for real deployments). Geographic coordinates are preferred.

        Examples
        --------
        >>> ant1 = array.get_antenna('ANT00001')
        >>> ant2 = array.get_antenna('ANT00002')
        >>> baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)
        """
        if use_coordinates and ant1.has_coordinates() and ant2.has_coordinates():
            return self._compute_geodetic_baseline(ant1, ant2)
        else:
            return self._compute_grid_baseline(ant1, ant2)

    def _compute_geodetic_baseline(
        self, ant1: AntennaPosition, ant2: AntennaPosition
    ) -> float:
        """Compute geodetic baseline using Haversine formula.

        Includes height difference if both antennas have height data.
        """
        lat1 = math.radians(ant1.latitude)
        lat2 = math.radians(ant2.latitude)
        lon1 = math.radians(ant1.longitude)
        lon2 = math.radians(ant2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula for great circle distance
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Earth radius in meters (mean radius)
        earth_radius = 6371000.0
        horizontal_distance = earth_radius * c

        # Include height difference if available
        if ant1.height is not None and ant2.height is not None:
            dh = ant2.height - ant1.height
            return math.sqrt(horizontal_distance**2 + dh**2)

        return horizontal_distance

    def _compute_grid_baseline(
        self, ant1: AntennaPosition, ant2: AntennaPosition, grid_spacing: float = 0.40
    ) -> float:
        """Compute baseline from grid spacing (approximate).

        Parameters
        ----------
        grid_spacing : float, optional
            Assumed grid spacing in meters (default: 0.4 m)

        Notes
        -----
        This is an approximation assuming uniform grid spacing.
        Use geodetic coordinates for accurate measurements.
        """
        drow = ant2.row_offset - ant1.row_offset
        dcol = ant2.east_col - ant1.east_col

        # Pythagorean distance in grid units
        grid_distance = math.sqrt(drow**2 + dcol**2)

        return grid_distance * grid_spacing

    def compute_all_baselines(
        self, use_coordinates: bool = True, include_self: bool = False
    ) -> List[Tuple[str, str, float]]:
        """Compute all pairwise baselines.

        Parameters
        ----------
        use_coordinates : bool, optional
            Whether to use geographic coordinates (default: True)
        include_self : bool, optional
            Whether to include zero-length self-baselines (default: False)

        Returns
        -------
        list of tuple
            List of (ant1_number, ant2_number, baseline_meters) tuples

        Examples
        --------
        >>> baselines = array.compute_all_baselines()
        >>> for ant1, ant2, dist in baselines[:5]:
        ...     print(f"{ant1} - {ant2}: {dist:.2f} m")
        """
        baselines = []

        for i, ant1 in enumerate(self.antennas):
            start_j = i if include_self else i + 1
            for ant2 in self.antennas[start_j:]:
                baseline = self.compute_baseline(ant1, ant2, use_coordinates)
                baselines.append((ant1.antenna_number, ant2.antenna_number, baseline))

        return baselines

    def filter_by_coordinates(self, has_coords: bool = True) -> List[AntennaPosition]:
        """Filter antennas by coordinate availability.

        Parameters
        ----------
        has_coords : bool, optional
            If True, return antennas with coordinates.
            If False, return antennas without coordinates.
            Default: True

        Returns
        -------
        list of AntennaPosition
            Filtered antenna list
        """
        if has_coords:
            return [ant for ant in self.antennas if ant.has_coordinates()]
        else:
            return [ant for ant in self.antennas if not ant.has_coordinates()]

    def __len__(self) -> int:
        """Return number of antennas in array."""
        return len(self.antennas)

    def __iter__(self):
        """Iterate over antennas."""
        return iter(self.antennas)

    def __repr__(self) -> str:
        """String representation."""
        return f"AntennaArray({len(self.antennas)} antennas)"


__all__ = ["AntennaPosition", "AntennaArray"]
