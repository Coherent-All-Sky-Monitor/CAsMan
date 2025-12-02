"""Antenna grid positioning package.

This package provides utilities for managing antenna positions within
grid-based array layouts and tracing connections to SNAP ports.
"""

from .grid import (
    AntennaGridPosition,
    direction_from_row,
    format_grid_code,
    load_core_layout,
    parse_grid_code,
    to_grid_code,
    validate_components,
)
from .chain import (
    get_snap_port_for_chain,
    get_snap_ports_for_antenna,
    format_snap_port,
)
from .array import (
    AntennaPosition,
    AntennaArray,
)

__all__ = [
    "AntennaGridPosition",
    "parse_grid_code",
    "format_grid_code",
    "to_grid_code",
    "direction_from_row",
    "validate_components",
    "load_core_layout",
    "get_snap_port_for_chain",
    "get_snap_ports_for_antenna",
    "format_snap_port",
    "AntennaPosition",
    "AntennaArray",
]
