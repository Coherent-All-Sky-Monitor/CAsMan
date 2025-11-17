"""
Barcode generation utilities for CAsMan.

This module provides functions for generating individual and batch barcodes
with various formats and customization options.
"""

import os
from typing import Dict, List, Optional

import barcode
from barcode.writer import ImageWriter


def generate_barcode(
    part_number: str,
    part_type: str,
    output_dir: Optional[str] = None,
    barcode_format: str = "code128",
) -> str:
    """
    Generate a barcode image for a part number.

    Parameters
    ----------
    part_number : str
        The part number to encode in the barcode.
    part_type : str
        The part type (used for directory organization).
    output_dir : str, optional
        Custom output directory. If not provided, uses default barcodes structure.
    barcode_format : str, optional
        Barcode format to use (default: code128).

    Returns
    -------
    str
        Path to the generated barcode image.

    Raises
    ------
    ValueError
        If the barcode format is not supported.
    OSError
        If there's an error creating directories or files.
    """
    # Determine output directory
    if output_dir is None:
        barcode_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "barcodes", part_type
        )
    else:
        barcode_dir = os.path.join(output_dir, part_type)

    # Create the barcode directory if it doesn't exist
    if not os.path.exists(barcode_dir):
        os.makedirs(barcode_dir)

    try:
        # Generate the barcode
        barcode_generator = barcode.get(
            barcode_format, part_number, writer=ImageWriter()
        )
        barcode_path = os.path.join(barcode_dir, f"{part_number}")
        barcode_generator.save(barcode_path)

        return f"{barcode_path}.png"  # ImageWriter adds .png extension

    except Exception as e:
        raise ValueError(f"Failed to generate barcode for {part_number}: {e}")


def generate_multiple_barcodes(
    part_numbers: List[str],
    part_type: str,
    output_dir: Optional[str] = None,
    barcode_format: str = "code128",
) -> Dict[str, str]:
    """
    Generate barcodes for multiple part numbers.

    Parameters
    ----------
    part_numbers : List[str]
        List of part numbers to generate barcodes for.
    part_type : str
        The part type for all parts.
    output_dir : str, optional
        Custom output directory.
    barcode_format : str, optional
        Barcode format to use.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping part numbers to their barcode file paths.
        Failed generations will have empty string as value.
    """
    results = {}

    for part_number in part_numbers:
        try:
            barcode_path = generate_barcode(
                part_number, part_type, output_dir, barcode_format
            )
            results[part_number] = barcode_path
        except (ValueError, OSError) as e:
            print(f"Warning: Failed to generate barcode for {part_number}: {e}")
            results[part_number] = ""

    return results


def generate_barcode_range(
    part_type: str,
    start_number: int,
    end_number: int,
    prefix: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generate barcodes for a range of part numbers.

    Parameters
    ----------
    part_type : str
        The part type to generate barcodes for.
    start_number : int
        Starting part number.
    end_number : int
        Ending part number (inclusive).
    prefix : str, optional
        Custom prefix for part numbers. If not provided, derives from part type.
    output_dir : str, optional
        Custom output directory.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping part numbers to their barcode file paths.

    Raises
    ------
    ValueError
        If start_number > end_number or if part_type is unknown.
    """
    if start_number > end_number:
        raise ValueError("Start number must be less than or equal to end number")

    # Get prefix if not provided
    if prefix is None:
        # Import here to avoid circular imports
        from casman.parts.types import load_part_types
        PART_TYPES = load_part_types()

        part_abbrev = None
        for _, (full_name, abbrev) in PART_TYPES.items():
            if full_name.upper() == part_type.upper():
                part_abbrev = abbrev
                break

        if not part_abbrev:
            raise ValueError(f"Unknown part type: {part_type}")

        prefix = part_abbrev

    # Generate part numbers in new format: {PREFIX}{NUMBER}P{POLARIZATION}
    # Default to polarization 1
    part_numbers = [f"{prefix}{i:05d}P1" for i in range(start_number, end_number + 1)]

    return generate_multiple_barcodes(part_numbers, part_type, output_dir)


def get_supported_barcode_formats() -> List[str]:
    """
    Get list of supported barcode formats.

    Returns
    -------
    List[str]
        List of supported barcode format names.
    """
    return [
        "code128",
        "code39",
        "ean8",
        "ean13",
        "ean",
        "gtin",
        "isbn",
        "isbn10",
        "isbn13",
        "issn",
        "jan",
        "pzn",
        "upc",
        "upca",
    ]


def validate_barcode_format(barcode_format: str) -> bool:
    """
    Validate if a barcode format is supported.

    Parameters
    ----------
    barcode_format : str
        The barcode format to validate.

    Returns
    -------
    bool
        True if format is supported, False otherwise.
    """
    return barcode_format.lower() in get_supported_barcode_formats()
