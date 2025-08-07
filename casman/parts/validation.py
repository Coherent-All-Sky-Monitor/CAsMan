"""
Part validation utilities for CAsMan.

This module provides validation functions for part numbers, part types,
and other part-related data integrity checks.
"""
import re
from typing import Dict, Optional

from .types import load_part_types

# Load part types for validation
PART_TYPES = load_part_types()


def validate_part_number(part_number: str) -> bool:
    """
    Validate a part number format.

    Expected format: {PREFIX}-P{POLARIZATION}-{NUMBER}
    Example: ANT-P1-00001, LNA-P2-00123, BAC-PV-00001

    Parameters
    ----------
    part_number : str
        The part number to validate

    Returns
    -------
    bool
        True if the part number is valid, False otherwise
    """
    if not isinstance(part_number, str):
        return False

    # Regular expression for part number format
    pattern = r'^[A-Z]{2,4}-P[A-Z0-9]+-\d{5}$'

    if not re.match(pattern, part_number):
        return False

    # Extract prefix and check if it's a valid part type
    prefix = part_number.split('-')[0]
    valid_prefixes = [abbrev for _, (_, abbrev) in PART_TYPES.items()]

    return prefix in valid_prefixes


def validate_part_type(part_type: str) -> bool:
    """
    Validate if a part type is supported.

    Parameters
    ----------
    part_type : str
        The part type to validate

    Returns
    -------
    bool
        True if the part type is valid, False otherwise
    """
    if not isinstance(part_type, str):
        return False

    valid_types = [name for _, (name, _) in PART_TYPES.items()]
    return part_type in valid_types


def validate_polarization(polarization: str) -> bool:
    """
    Validate polarization format.

    Valid polarizations: P1, P2, PV (and potentially others)

    Parameters
    ----------
    polarization : str
        The polarization to validate

    Returns
    -------
    bool
        True if the polarization is valid, False otherwise
    """
    if not isinstance(polarization, str):
        return False

    # Common polarization patterns
    valid_patterns = [r'^P[12]$', r'^PV$', r'^P[A-Z0-9]+$']

    return any(re.match(pattern, polarization) for pattern in valid_patterns)


def get_part_info(part_number: str) -> Optional[Dict[str, str]]:
    """
    Extract part information from a valid part number.

    Parameters
    ----------
    part_number : str
        The part number to parse

    Returns
    -------
    Optional[Dict[str, str]]
        Dictionary with part info (prefix, type, polarization, number) or None if invalid
    """
    if not validate_part_number(part_number):
        return None

    # Parse the part number
    parts = part_number.split('-')
    prefix = parts[0]
    polarization_part = parts[1]  # e.g., "P1"
    number = parts[2]

    # Find the full part type name
    part_type = None
    for _, (name, abbrev) in PART_TYPES.items():
        if abbrev == prefix:
            part_type = name
            break

    return {
        'prefix': prefix,
        'part_type': part_type or 'UNKNOWN',
        'polarization': polarization_part,
        'number': number,
        'full_number': part_number
    }


def normalize_part_number(part_number: str) -> Optional[str]:
    """
    Normalize a part number to standard format.

    Parameters
    ----------
    part_number : str
        The part number to normalize

    Returns
    -------
    Optional[str]
        Normalized part number or None if invalid
    """
    part_info = get_part_info(part_number)
    if not part_info:
        return None

    # Ensure consistent formatting
    return f"{part_info['prefix']}-{part_info['polarization']}-{part_info['number']}"
