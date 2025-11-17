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

    Expected format: {PREFIX}{NUMBER}P{POLARIZATION}
    Example: ANT00001P1, LNA00123P2, BAC00001P1

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

    # Regular expression for part number format: PREFIX (2-4 letters) + NUMBER
    # (5 digits) + P + POLARIZATION (1-2 chars)
    pattern = r'^[A-Z]{2,4}\d{5}P[A-Z0-9]{1,2}$'

    if not re.match(pattern, part_number):
        return False

    # Extract prefix and check if it's a valid part type
    # Find where digits start
    for i, char in enumerate(part_number):
        if char.isdigit():
            prefix = part_number[:i]
            break
    else:
        return False

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

    # Parse the part number: {PREFIX}{NUMBER}P{POLARIZATION}
    # Find where digits start
    digit_start = 0
    for i, char in enumerate(part_number):
        if char.isdigit():
            digit_start = i
            break

    prefix = part_number[:digit_start]

    # Find where 'P' appears after the digits
    p_index = part_number.find('P', digit_start)
    if p_index == -1:
        return None

    number = part_number[digit_start:p_index]
    polarization = part_number[p_index + 1:]  # Everything after 'P'

    # Find the full part type name
    part_type = None
    for _, (name, abbrev) in PART_TYPES.items():
        if abbrev == prefix:
            part_type = name
            break

    return {
        'prefix': prefix,
        'part_type': part_type or 'UNKNOWN',
        'polarization': 'P' + polarization,
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

    # Ensure consistent formatting: {PREFIX}{NUMBER}P{POLARIZATION}
    polarization_suffix = part_info['polarization'][1:] if part_info['polarization'].startswith(
        'P') else part_info['polarization']
    return f"{part_info['prefix']}{part_info['number']}P{polarization_suffix}"
