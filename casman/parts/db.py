"""
Database access utilities for CAsMan parts.
"""

from typing import List, Optional, Tuple

from casman.database.operations import get_parts_by_criteria


def read_parts(
    part_type: Optional[str] = None,
    polarization: Optional[str] = None,
    db_dir: Optional[str] = None,
) -> List[Tuple]:
    """
    Read parts from the database with optional filtering.
    """
    return get_parts_by_criteria(part_type, polarization, db_dir)
