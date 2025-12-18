"""Antenna grid positioning package.

This package provides utilities for managing antenna positions within
grid-based array layouts, tracing connections to SNAP ports, and mapping
grid coordinates to correlator kernel indices.
"""

import logging

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
    sync_database,
)
from .kernel_index import (
    KernelIndexArray,
    grid_to_kernel_index,
    kernel_index_to_grid,
    get_array_index_map,
)

# Auto-sync databases on module import (optional, non-blocking)
logger = logging.getLogger(__name__)

# Only auto-sync if explicitly enabled in config
try:
    from casman.config import get_config
    
    auto_sync_enabled = get_config().get("database", {}).get("sync", {}).get("auto_sync_on_import", False)
    
    if auto_sync_enabled:
        try:
            from .sync import sync_databases
            
            # Perform quiet sync on import (check every time, use stale on failure)
            sync_databases(quiet=True)
        except Exception as e:
            # Log warning but don't fail import if sync fails
            logger.debug(f"Auto-sync skipped: {e}")
except Exception:
    # Silently skip if config not available (e.g., during tests)
    pass

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
    "sync_database",
    "KernelIndexArray",
    "grid_to_kernel_index",
    "kernel_index_to_grid",
    "get_array_index_map",
]
