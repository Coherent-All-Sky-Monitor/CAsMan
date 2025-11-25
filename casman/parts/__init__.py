"""
CAsMan parts subpackage: unified API for part management.

This __init__.py exposes the main part management functions, classes, and types.
"""

# Import barcode functionality for convenience
from casman.barcode import generate_barcode

from .db import read_parts
from .generation import generate_part_numbers, get_last_part_number
from .interactive import add_parts_interactive, display_parts_interactive
from .part import Part, create_part
from .search import (
    find_part,
    get_all_parts,
    get_part_statistics,
    get_recent_parts,
    search_by_prefix,
    search_parts,
)

# Import core functionality from submodules
from .types import load_part_types
from .validation import (
    get_part_info,
    normalize_part_number,
    validate_part_number,
    validate_part_type,
    validate_polarization,
)

# Create PART_TYPES at module level for backward compatibility
PART_TYPES = load_part_types()

# Define __all__ to specify what gets exported with 'from casman.parts
# import *'
__all__ = [
    # Type management
    "load_part_types",
    "PART_TYPES",
    # Part generation
    "generate_part_numbers",
    "get_last_part_number",
    # Database operations
    "read_parts",
    # Interactive functions
    "display_parts_interactive",
    "add_parts_interactive",
    # Validation functions
    "validate_part_number",
    "validate_part_type",
    "validate_polarization",
    "get_part_info",
    "normalize_part_number",
    # Core Part class
    "Part",
    "create_part",
    # Search functionality
    "search_parts",
    "get_all_parts",
    "search_by_prefix",
    "get_part_statistics",
    "find_part",
    "get_recent_parts",
    # Barcode utilities
    "generate_barcode",
]
