"""
Part class and core part functionality for CAsMan.

This module provides the main Part class for representing individual parts
and their properties, along with related utility functions.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from .types import load_part_types
from .validation import (get_part_info, validate_part_number,
                         validate_part_type, validate_polarization)

# Load part types for reference
PART_TYPES = load_part_types()


class Part:
    """
    Represents a CAsMan part with validation and utility methods.

    This class encapsulates all properties and behaviors of a part,
    including validation, formatting, and database representation.
    """

    def __init__(
        self,
        part_number: str,
        part_type: Optional[str] = None,
        polarization: Optional[str] = None,
        date_created: Optional[str] = None,
        date_modified: Optional[str] = None,
    ) -> None:
        """
        Initialize a Part instance.

        Parameters
        ----------
        part_number : str
            The part number (e.g., "ANT00001P1")
        part_type : Optional[str]
            The part type (e.g., "ANTENNA"). If None, extracted from part_number
        polarization : Optional[str]
            The polarization (e.g., "P1"). If None, extracted from part_number
        date_created : Optional[str]
            Creation timestamp. If None, uses current time
        date_modified : Optional[str]
            Modification timestamp. If None, uses current time

        Raises
        ------
        ValueError
            If the part number is invalid or incompatible with provided type/polarization
        """
        # Validate the part number first
        if not validate_part_number(part_number):
            raise ValueError(f"Invalid part number format: {part_number}")

        self.part_number = part_number

        # Extract information from part number
        part_info = get_part_info(part_number)
        if not part_info:
            raise ValueError(f"Cannot parse part number: {part_number}")

        # Set part type - use provided or extracted
        if part_type is not None:
            if not validate_part_type(part_type):
                raise ValueError(f"Invalid part type: {part_type}")
            if part_type != part_info["part_type"]:
                raise ValueError(
                    f"Part type '{part_type}' doesn't match part number '{part_number}'"
                )
            self.part_type = part_type
        else:
            self.part_type = part_info["part_type"]

        # Set polarization - use provided or extracted
        if polarization is not None:
            if not validate_polarization(polarization):
                raise ValueError(f"Invalid polarization: {polarization}")
            if polarization != part_info["polarization"]:
                raise ValueError(
                    f"Polarization '{polarization}' doesn't match part number '{part_number}'"
                )
            self.polarization = polarization
        else:
            self.polarization = part_info["polarization"]

        # Set timestamps
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.date_created = date_created or current_time
        self.date_modified = date_modified or current_time

        # Store parsed info
        self.prefix = part_info["prefix"]
        self.number = part_info["number"]

    def __str__(self) -> str:
        """String representation of the part."""
        return f"Part({self.part_number}, {self.part_type}, {self.polarization})"

    def __repr__(self) -> str:
        """Detailed string representation of the part."""
        return (
            f"Part(part_number='{self.part_number}', part_type='{self.part_type}', "
            f"polarization='{self.polarization}', date_created='{self.date_created}')"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on part number."""
        if not isinstance(other, Part):
            return False
        return self.part_number == other.part_number

    def __hash__(self) -> int:
        """Hash based on part number for use in sets/dicts."""
        return hash(self.part_number)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert part to dictionary representation.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing all part properties
        """
        return {
            "part_number": self.part_number,
            "part_type": self.part_type,
            "polarization": self.polarization,
            "prefix": self.prefix,
            "number": self.number,
            "date_created": self.date_created,
            "date_modified": self.date_modified,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Part":
        """
        Create Part instance from dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary containing part data

        Returns
        -------
        Part
            New Part instance
        """
        return cls(
            part_number=data["part_number"],
            part_type=data.get("part_type"),
            polarization=data.get("polarization"),
            date_created=data.get("date_created"),
            date_modified=data.get("date_modified"),
        )

    @classmethod
    def from_database_row(cls, row: tuple) -> "Part":
        """
        Create Part instance from database row.

        Assumes row format: (id, part_number, part_type, polarization, date_created, date_modified)

        Parameters
        ----------
        row : tuple
            Database row tuple

        Returns
        -------
        Part
            New Part instance
        """
        if len(row) < 6:
            raise ValueError(f"Invalid database row format: {row}")

        _, part_number, part_type, polarization, date_created, date_modified = row
        return cls(
            part_number=part_number,
            part_type=part_type,
            polarization=polarization,
            date_created=date_created,
            date_modified=date_modified,
        )

    def is_valid(self) -> bool:
        """
        Check if the part is valid.

        Returns
        -------
        bool
            True if all part properties are valid
        """
        return (
            validate_part_number(self.part_number)
            and validate_part_type(self.part_type)
            and validate_polarization(self.polarization)
        )

    def get_barcode_filename(self) -> str:
        """
        Get the expected barcode filename for this part.

        Returns
        -------
        str
            Barcode filename (e.g., "ANT00001P1.png")
        """
        return f"{self.part_number}.png"

    def update_modified_time(self) -> None:
        """Update the modified timestamp to current time."""
        self.date_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_part(part_number: str, **kwargs) -> Part:
    """
    Convenience function to create a Part instance.

    Parameters
    ----------
    part_number : str
        The part number
    **kwargs
        Additional Part constructor arguments

    Returns
    -------
    Part
        New Part instance
    """
    return Part(part_number, **kwargs)
