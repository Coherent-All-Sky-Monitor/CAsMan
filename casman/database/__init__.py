"""
Database package for CAsMan.

This package provides modular database functionality including connection management,
schema operations, data access utilities, and database migrations.
"""

# Import core functionality from submodules
from .connection import find_project_root, get_database_path
from .initialization import init_all_databases, init_assembled_db, init_parts_db
from .migrations import (
    DatabaseMigrator,
    backup_database,
    check_database_integrity,
    get_table_info,
)
from .operations import (
    check_part_in_db,
    get_all_parts,
    get_assembly_records,
    get_last_update,
    get_parts_by_criteria,
)

# Export all public functions
__all__ = [
    # Connection management
    "get_database_path",
    "find_project_root",
    # Database initialization
    "init_parts_db",
    "init_assembled_db",
    "init_all_databases",
    # Data operations
    "get_all_parts",
    "get_last_update",
    "get_assembly_records",
    "check_part_in_db",
    "get_parts_by_criteria",
    # Migration utilities
    "DatabaseMigrator",
    "get_table_info",
    "backup_database",
    "check_database_integrity",
]
