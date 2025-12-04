"""Antenna grid positioning package.

This package provides utilities for managing antenna positions within
grid-based array layouts, tracing connections to SNAP ports, and mapping
grid coordinates to correlator kernel indices.
"""

from .grid import (
    AntennaGridPosition,
    direction_from_row,
    format_grid_code,
    load_core_layout,
    load_array_layout,
    get_array_name_for_id,
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
from .kernel_index import (
    KernelIndexArray,
    grid_to_kernel_index,
    kernel_index_to_grid,
    get_antenna_kernel_idx,
)

__all__ = [
    "AntennaGridPosition",
    "parse_grid_code",
    "format_grid_code",
    "to_grid_code",
    "direction_from_row",
    "validate_components",
    "load_core_layout",
    "load_array_layout",
    "get_array_name_for_id",
    "get_snap_port_for_chain",
    "get_snap_ports_for_antenna",
    "format_snap_port",
    "AntennaPosition",
    "AntennaArray",
    "KernelIndexArray",
    "grid_to_kernel_index",
    "kernel_index_to_grid",
    "get_antenna_kernel_idx",
]
