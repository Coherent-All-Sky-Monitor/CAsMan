"""
Barcode package for CAsMan.

This package provides modular barcode functionality including generation,
validation, batch operations, and PDF printing capabilities.
"""

# Import core functionality from submodules
from .generation import generate_barcode, generate_multiple_barcodes
from .operations import (
    arrange_barcodes_in_pdf,
    validate_barcode_file,
)
from .printing import (
    create_printable_pages,
    generate_barcode_printpages,
    optimize_page_layout,
)
from .validation import (
    is_valid_barcode_format,
    validate_part_number_format,
)

# Export all public functions
__all__ = [
    # Barcode generation
    "generate_barcode",
    "generate_multiple_barcodes",
    # File operations
    "arrange_barcodes_in_pdf",
    "validate_barcode_file",
    # Printing utilities
    "create_printable_pages",
    "generate_barcode_printpages",
    "optimize_page_layout",
    # Validation
    "is_valid_barcode_format",
    "validate_part_number_format",
]
