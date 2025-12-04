"""Antenna grid position utilities.

This module defines parsing, formatting, and validation helpers for antenna
position codes of the form:

    [A-Z][N/C/S][000-999]E[00-99]

Examples
--------
    CN002E03  -> Core array (C), 2 rows North of center, East column 3
    CS017E04  -> Core array (C), 17 rows South of center, East column 4
    CC000E01  -> Core array (C), Center row, East column 1

The format is intentionally expansive; while the core layout currently uses
only a 43 x 6 grid (rows N001..N021, C000, S001..S021 and E01..E06), the
specification reserves three digits for the north/south offset and two digits
for the east column to allow future expansion (e.g. additional arrays or
extended baselines).

Configuration
-------------
Grid boundaries for the core array are defined in ``config.yaml`` under the
``grid.core`` section:

```
grid:
  core:
    array_id: "C"
    north_rows: 21
    south_rows: 21
    east_columns: 6
    allow_expansion: true
```

If expansion is allowed, codes outside the core bounds remain syntactically
valid but should be treated as unassigned when rendering the core layout.

Internal Representation
-----------------------
Rows are converted to signed integer offsets relative to the center:

    N002 -> +2
    S017 -> -17
    C000 -> 0 (Center must always use offset 000)

East columns are one-based integers parsed from the two-digit field:

    E01 -> 1
    E06 -> 6

Data Model
----------
The :class:`AntennaGridPosition` dataclass stores both the canonical string
(`grid_code`) and normalized numeric fields for efficient storage and lookup.

Functions provided:
    - ``parse_grid_code(code)``: Validate and parse a grid code string.
    - ``format_grid_code(array_id, direction, offset, east_col)``: Build code.
    - ``direction_from_row(row_offset)``: Infer N/S/C from signed offset.
    - ``validate_components(array_id, direction, offset, east_col)``: Bounds check.

All functions raise ``ValueError`` on invalid inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional

from casman.config import get_config

GRID_CODE_PATTERN = re.compile(r"^[A-Z][NCS][0-9]{3}E[0-9]{2}$")


@dataclass(frozen=True)
class AntennaGridPosition:
    """Normalized representation of an antenna grid position.

    Parameters
    ----------
    array_id : str
        Leading uppercase letter designating the array (e.g. 'C').
    direction : str
        One of 'N', 'S', or 'C'.
    offset : int
        Absolute offset from center (0-999). Must be 0 when direction == 'C'.
    east_col : int
        Zero-based east column index (0-99). Core layout uses 0-5.
    row_offset : int
        Signed offset: positive for North, negative for South, zero for Center.
    grid_code : str
        Canonical code string matching the specification.

    Notes
    -----
    The ``offset`` field never stores sign; use ``row_offset`` for relative
    positioning logic. ``grid_code`` is always the authoritative string form.
    """

    array_id: str
    direction: str
    offset: int
    east_col: int
    row_offset: int
    grid_code: str

    def __post_init__(self) -> None:  # type: ignore[override]
        # Basic invariant checks
        if self.direction not in {"N", "S", "C"}:
            raise ValueError(f"Invalid direction: {self.direction}")
        if self.offset < 0 or self.offset > 999:
            raise ValueError(f"Offset out of range: {self.offset}")
        if self.direction == "C" and self.offset != 0:
            raise ValueError("Center (C) must have offset 0 (C000)")
        if self.direction != "C" and self.offset == 0:
            raise ValueError("North/South offsets must be >= 1 (e.g. N001)")
        if self.east_col < 1 or self.east_col > 99:
            raise ValueError(f"East column out of range: E{self.east_col:02d}")
        # Check grid code consistency
        expected = format_grid_code(
            self.array_id, self.direction, self.offset, self.east_col
        )
        if expected != self.grid_code:
            raise ValueError("grid_code mismatch with normalized components")


def load_core_layout() -> tuple[str, int, int, int, bool]:
    """Load core array layout limits from configuration.

    Returns
    -------
    (array_id, north_rows, south_rows, east_columns, allow_expansion)
        Tuple containing bounds for validation.

    Raises
    ------
    KeyError
        If required configuration keys are missing.
    """
    array_id = get_config("grid.core.array_id")
    north_rows = get_config("grid.core.north_rows")
    south_rows = get_config("grid.core.south_rows")
    east_columns = get_config("grid.core.east_columns")
    allow_expansion = bool(get_config("grid.core.allow_expansion", False))
    return (
        array_id,
        int(north_rows),
        int(south_rows),
        int(east_columns),
        allow_expansion,
    )


def load_array_layout(array_name: str) -> tuple[str, int, int, int, bool]:
    """Load array layout limits from configuration for any grid.

    Parameters
    ----------
    array_name : str
        Name of the array section in config (e.g., 'core', 'outriggers').

    Returns
    -------
    (array_id, north_rows, south_rows, east_columns, allow_expansion)
        Tuple containing bounds for validation.

    Raises
    ------
    KeyError
        If required configuration keys are missing.

    Examples
    --------
    >>> load_array_layout('core')
    ('C', 21, 21, 6, True)
    >>> load_array_layout('outriggers')
    ('O', 10, 10, 4, False)
    """
    array_id = get_config(f"grid.{array_name}.array_id")
    if array_id is None:
        raise KeyError(f"Array '{array_name}' not found in configuration")
    north_rows = get_config(f"grid.{array_name}.north_rows")
    south_rows = get_config(f"grid.{array_name}.south_rows")
    east_columns = get_config(f"grid.{array_name}.east_columns")
    allow_expansion = bool(get_config(f"grid.{array_name}.allow_expansion", False))
    return (
        str(array_id),
        int(north_rows),
        int(south_rows),
        int(east_columns),
        allow_expansion,
    )


def get_array_name_for_id(array_id: str) -> Optional[str]:
    """Look up the array name (config key) for a given array ID letter.

    Parameters
    ----------
    array_id : str
        Single letter array identifier (e.g., 'C', 'O').

    Returns
    -------
    str or None
        Array name (e.g., 'core', 'outriggers') or None if not found.

    Examples
    --------
    >>> get_array_name_for_id('C')
    'core'
    >>> get_array_name_for_id('O')
    'outriggers'
    >>> get_array_name_for_id('Z')
    None
    """
    try:
        # Get all grid configurations
        grid_config = get_config("grid", {})
        for array_name, array_data in grid_config.items():
            if isinstance(array_data, dict) and array_data.get("array_id") == array_id:
                return array_name
    except Exception:
        pass
    return None


def direction_from_row(row_offset: int) -> str:
    """Infer direction code from signed row offset.

    Parameters
    ----------
    row_offset : int
        Signed offset (negative for south, positive for north, zero for center).

    Returns
    -------
    str
        'N', 'S', or 'C'.
    """
    if row_offset == 0:
        return "C"
    return "N" if row_offset > 0 else "S"


def format_grid_code(array_id: str, direction: str, offset: int, east_col: int) -> str:
    """Compose a grid code from components.

    Parameters
    ----------
    array_id : str
        Single uppercase letter designating the array.
    direction : str
        'N', 'S', or 'C'.
    offset : int
        Absolute offset (0-999). Must be 0 if direction == 'C'.
    east_col : int
        One-based east column (1-99).

    Returns
    -------
    str
        Formatted grid code (e.g. 'CN002E03').

    Raises
    ------
    ValueError
        If components are invalid.
    """
    if (
        not array_id
        or len(array_id) != 1
        or not array_id.isalpha()
        or not array_id.isupper()
    ):
        raise ValueError("array_id must be one uppercase letter")
    if direction not in {"N", "S", "C"}:
        raise ValueError("direction must be one of N,S,C")
    if offset < 0 or offset > 999:
        raise ValueError("offset must be between 0 and 999")
    if direction == "C" and offset != 0:
        raise ValueError("Center direction must have offset 0 (C000)")
    if direction != "C" and offset == 0:
        raise ValueError("North/South offsets must be >= 1")
    if east_col < 1 or east_col > 99:
        raise ValueError("east_col must be between 1 and 99")
    return f"{array_id}{direction}{offset:03d}E{east_col:02d}"


def validate_components(
    array_id: str, row_offset: int, east_col: int, *, enforce_bounds: bool = True
) -> None:
    """Validate numeric components against configuration bounds.

    Parameters
    ----------
    array_id : str
        Array identifier letter.
    row_offset : int
        Signed offset (-999..999). Specific array bounds may be narrower.
    east_col : int
        East column index (1-based).
    enforce_bounds : bool, optional
        If True, apply array-specific layout limits unless expansion is enabled.

    Raises
    ------
    ValueError
        On any validation failure.
    """
    if (
        not array_id
        or len(array_id) != 1
        or not array_id.isalpha()
        or not array_id.isupper()
    ):
        raise ValueError("Invalid array_id")
    if east_col < 1 or east_col > 99:
        raise ValueError("east_col out of range (1-99)")
    if row_offset < -999 or row_offset > 999:
        raise ValueError("row_offset out of absolute range (±999)")

    if enforce_bounds:
        # Find the array configuration for this array_id
        array_name = get_array_name_for_id(array_id)
        if array_name:
            _, north_rows, south_rows, east_columns, allow_expansion = load_array_layout(array_name)
            if not allow_expansion:
                if row_offset > north_rows or row_offset < -south_rows:
                    raise ValueError(f"row_offset exceeds {array_name} array bounds")
                if east_col < 1 or east_col > east_columns:
                    raise ValueError(f"east_col exceeds {array_name} array column bounds (1-{east_columns})")


def parse_grid_code(
    code: str, *, enforce_bounds: bool = True
) -> AntennaGridPosition:
    """Parse and validate a grid code string.

    Parameters
    ----------
    code : str
        Grid code string in the canonical format.
    enforce_bounds : bool, optional
        Apply array-specific layout limits; ignored if expansion enabled in config.

    Returns
    -------
    AntennaGridPosition
        Dataclass with normalized components.

    Raises
    ------
    ValueError
        If the code is syntactically or semantically invalid.

    Examples
    --------
    >>> parse_grid_code("CN002E03")
    AntennaGridPosition(array_id='C', direction='N', offset=2, east_col=3, row_offset=2, grid_code='CN002E03')
    >>> parse_grid_code("CS017E04").row_offset
    -17
    >>> parse_grid_code("CC000E01").grid_code
    'CC000E01'
    """
    if not isinstance(code, str):
        raise ValueError("Grid code must be a string")
    code = code.strip().upper()
    if not GRID_CODE_PATTERN.match(code):
        raise ValueError(
            f"Grid code '{code}' does not match pattern [A-Z][NCS][000-999]E[01-99]"
        )

    array_id = code[0]
    direction = code[1]
    offset = int(code[2:5])
    east_col = int(code[6:8])

    # Direction-specific checks
    if direction == "C" and offset != 0:
        raise ValueError("Center row must use offset 000 (C000)")
    if direction in {"N", "S"} and offset == 0:
        raise ValueError("North/South rows must use offset >= 001")

    # Compute signed row offset
    if direction == "C":
        row_offset = 0
    elif direction == "N":
        row_offset = offset
    else:  # S
        row_offset = -offset

    # Bounds validation
    validate_components(
        array_id, row_offset, east_col, enforce_bounds=enforce_bounds
    )

    return AntennaGridPosition(
        array_id=array_id,
        direction=direction,
        offset=offset,
        east_col=east_col,
        row_offset=row_offset,
        grid_code=code,
    )


def to_grid_code(row_offset: int, east_col: int, array_id: Optional[str] = None) -> str:
    """Convert numeric offsets to a grid code.

    Parameters
    ----------
    row_offset : int
        Signed relative offset (negative south, positive north, zero center).
    east_col : int
        One-based east column (1-99).
    array_id : str, optional
        Array identifier; defaults to core array from config if omitted.

    Returns
    -------
    str
        Canonical grid code string.

    Raises
    ------
    ValueError
        If components invalid or out of bounds.
    """
    core_id, north_rows, south_rows, east_columns, allow_expansion = load_core_layout()
    if array_id is None:
        array_id = core_id

    direction = direction_from_row(row_offset)
    offset = abs(row_offset)

    if direction == "C":
        offset = 0
    elif offset == 0:
        raise ValueError("Non-center rows must have non-zero offset")

    # Enforce bounds via validate_components (any array unless expansion)
    validate_components(array_id, row_offset, east_col, enforce_bounds=True)
    return format_grid_code(array_id, direction, offset, east_col)


__all__ = [
    "AntennaGridPosition",
    "parse_grid_code",
    "format_grid_code",
    "direction_from_row",
    "validate_components",
    "to_grid_code",
    "load_core_layout",
    "load_array_layout",
    "get_array_name_for_id",
]
