"""
Barcode validation utilities for CAsMan.

This module provides functions for validating barcode formats,
content, and part number patterns.
"""

import re
from typing import List, Optional, Tuple


def is_valid_barcode_format(
        barcode_data: str,
        format_type: str = "code128") -> bool:
    """
    Validate if barcode data is compatible with the specified format.

    Parameters
    ----------
    barcode_data : str
        The data to encode in the barcode.
    format_type : str, optional
        The barcode format to validate against.

    Returns
    -------
    bool
        True if data is valid for the format, False otherwise.
    """
    if not barcode_data:
        return False

    format_type = format_type.lower()

    # Code128 validation
    if format_type == "code128":
        # Code128 can encode ASCII characters 0-127
        try:
            return all(0 <= ord(char) <= 127 for char in barcode_data)
        except TypeError:
            return False

    # Code39 validation
    elif format_type == "code39":
        # Code39 supports: 0-9, A-Z, space, and some special chars
        valid_chars = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%")
        return all(char.upper() in valid_chars for char in barcode_data)

    # EAN/UPC validation (numeric only)
    elif format_type in ["ean8", "ean13", "upc", "upca"]:
        return barcode_data.isdigit()

    # For other formats, assume valid (basic validation)
    else:
        return len(barcode_data) > 0


def validate_part_number_format(
        part_number: str) -> Tuple[bool, Optional[str]]:
    """
    Validate CAsMan part number format.

    Parameters
    ----------
    part_number : str
        The part number to validate.

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message) where is_valid is True if format is correct,
        and error_message contains details if validation fails.
    """
    if not part_number:
        return False, "Part number cannot be empty"

    # Expected pattern: XXX-P1-NNNNN or XXXP1-NNNNN
    # Where XXX is 2-4 letter abbreviation, P1 is literal, NNNNN is 5-digit
    # number
    pattern = r'^([A-Z]{2,4})-?(P1)-(\d{5})$'

    match = re.match(pattern, part_number.upper())
    if not match:
        return False, ("Invalid part number format. Expected format: "
                       "XXX-P1-NNNNN or XXXP1-NNNNN (e.g., ANT-P1-00001)")

    prefix, pol, number = match.groups()

    # Additional validations
    if len(prefix) < 2:
        return False, "Part type abbreviation too short (minimum 2 characters)"

    if len(prefix) > 4:
        return False, "Part type abbreviation too long (maximum 4 characters)"

    number_val = int(number)
    if number_val < 1:
        return False, "Part number must be greater than 0"

    if number_val > 99999:
        return False, "Part number exceeds maximum value (99999)"

    return True, None


def validate_barcode_content(
        content: str, part_type: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate barcode content for CAsMan standards.

    Parameters
    ----------
    content : str
        The content to be encoded in the barcode.
    part_type : str, optional
        Expected part type for additional validation.

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message) where is_valid is True if content is valid,
        and error_message contains details if validation fails.
    """
    # First check if it's a valid part number
    is_valid_part, part_error = validate_part_number_format(content)

    if not is_valid_part:
        # Check if it's some other valid content
        if len(content) < 3:
            return False, "Barcode content too short (minimum 3 characters)"

        if len(content) > 50:
            return False, "Barcode content too long (maximum 50 characters)"

        # Allow non-part-number content but with basic validation
        if not content.strip():
            return False, "Barcode content cannot be only whitespace"

        # Check for potentially problematic characters
        problematic_chars = set('\n\r\t\f\v')
        if any(char in problematic_chars for char in content):
            return False, "Barcode content contains invalid control characters"

        return True, None

    # If it's a valid part number, do additional part-type checking
    if part_type:
        # Extract prefix from part number
        pattern = r'^([A-Z]{2,4})-?P1-\d{5}$'
        match = re.match(pattern, content.upper())

        if match:
            prefix = match.group(1)

            # Import here to avoid circular imports
            from casman.parts import PART_TYPES

            expected_prefix = None
            for _, (full_name, abbrev) in PART_TYPES.items():
                if full_name.upper() == part_type.upper():
                    expected_prefix = abbrev
                    break

            if expected_prefix and prefix != expected_prefix:
                return False, (f"Part number prefix '{prefix}' doesn't match "
                               f"expected prefix '{expected_prefix}' for part type '{part_type}'")

    return True, None


def get_barcode_validation_rules() -> dict:
    """
    Get comprehensive barcode validation rules for CAsMan.

    Returns
    -------
    dict
        Dictionary containing validation rules and standards.
    """
    return {
        'part_number_format': {
            'pattern': 'XXX-P1-NNNNN or XXXP1-NNNNN',
            'prefix_length': (2, 4),
            'number_range': (1, 99999),
            'examples': ['ANT-P1-00001', 'LNAP1-00123', 'BAC-P1-05678']
        },
        'content_constraints': {
            'min_length': 3,
            'max_length': 50,
            'forbidden_chars': ['\n', '\r', '\t', '\f', '\v'],
            'encoding': 'ASCII (0-127)'
        },
        'barcode_formats': {
            'recommended': 'code128',
            'supported': ['code128', 'code39', 'ean8', 'ean13', 'upc', 'upca'],
            'format_constraints': {
                'code128': 'ASCII characters 0-127',
                'code39': 'Alphanumeric + special chars',
                'ean/upc': 'Numeric only'
            }
        }
    }
