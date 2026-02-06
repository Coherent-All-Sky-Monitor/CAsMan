"""
Database package for CAsMan.

This package provides core database functionality including connection management,
initialization, and data access operations.
"""

# Import core functionality from submodules
from .connection import get_database_path
from .initialization import init_all_databases, init_assembled_db, init_parts_db
from .operations import check_part_in_db, get_parts_by_criteria
from .antenna_positions import (
    assign_antenna_position,
    get_all_antenna_positions,
    get_antenna_at_position,
    get_antenna_position,
    init_antenna_positions_table,
    remove_antenna_position,
    strip_polarization,
)

# Export all public functions
__all__ = [
    # Connection management
    "get_database_path",
    # Database initialization
    "init_parts_db",
    "init_assembled_db",
    "init_all_databases",
    "init_antenna_positions_table",
    # Data operations
    "check_part_in_db",
    "get_parts_by_criteria",
    # Antenna position operations
    "assign_antenna_position",
    "get_antenna_position",
    "get_antenna_at_position",
    "get_all_antenna_positions",
    "remove_antenna_position",
    "strip_polarization",
]
