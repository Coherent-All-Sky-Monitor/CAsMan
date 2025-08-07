"""
Additional tests for enhanced parts functionality.

These tests cover the new Part class, validation functions, and search capabilities
added to the parts package.
"""

import tempfile

import pytest

from casman.database import init_parts_db
from casman.parts import (
    Part,
    create_part,
    find_part,
    get_part_info,
    get_part_statistics,
    normalize_part_number,
    search_parts,
    validate_part_number,
    validate_part_type,
    validate_polarization,
)


class TestPartValidation:
    """Test part validation functions."""

    def test_validate_part_number_valid(self):
        """Test validation of valid part numbers."""
        assert validate_part_number("ANT-P1-00001")
        assert validate_part_number("LNA-P2-00123")
        assert validate_part_number("BAC-PV-00001")

    def test_validate_part_number_invalid(self):
        """Test validation of invalid part numbers."""
        assert not validate_part_number("INVALID")
        assert not validate_part_number("ANT-P1")  # Missing number
        assert not validate_part_number("123-P1-00001")  # Invalid prefix
        assert not validate_part_number("ANT-P1-1")  # Number too short
        assert not validate_part_number(None)
        assert not validate_part_number(123)

    def test_validate_part_type(self):
        """Test part type validation."""
        assert validate_part_type("ANTENNA")
        assert validate_part_type("LNA")
        assert not validate_part_type("INVALID_TYPE")
        assert not validate_part_type(None)
        assert not validate_part_type(123)

    def test_validate_polarization(self):
        """Test polarization validation."""
        assert validate_polarization("P1")
        assert validate_polarization("P2")
        assert validate_polarization("PV")
        assert not validate_polarization("INVALID")
        assert not validate_polarization(None)
        assert not validate_polarization(123)

    def test_get_part_info_valid(self):
        """Test part info extraction from valid part numbers."""
        info = get_part_info("ANT-P1-00001")
        assert info is not None
        assert info["prefix"] == "ANT"
        assert info["part_type"] == "ANTENNA"
        assert info["polarization"] == "P1"
        assert info["number"] == "00001"
        assert info["full_number"] == "ANT-P1-00001"

    def test_get_part_info_invalid(self):
        """Test part info extraction from invalid part numbers."""
        assert get_part_info("INVALID") is None
        assert get_part_info(None) is None

    def test_normalize_part_number(self):
        """Test part number normalization."""
        assert normalize_part_number("ANT-P1-00001") == "ANT-P1-00001"
        assert normalize_part_number("INVALID") is None


class TestPartClass:
    """Test the Part class functionality."""

    def test_part_creation_valid(self):
        """Test creating valid Part instances."""
        part = Part("ANT-P1-00001", "ANTENNA", "P1")
        assert part.part_number == "ANT-P1-00001"
        assert part.part_type == "ANTENNA"
        assert part.polarization == "P1"
        assert part.prefix == "ANT"
        assert part.number == "00001"
        assert part.is_valid()

    def test_part_creation_auto_extract(self):
        """Test creating Part with auto-extracted type and polarization."""
        part = Part("LNA-P2-00123")
        assert part.part_type == "LNA"
        assert part.polarization == "P2"

    def test_part_creation_invalid_number(self):
        """Test creating Part with invalid part number."""
        with pytest.raises(ValueError, match="Invalid part number format"):
            Part("INVALID")

    def test_part_creation_mismatched_type(self):
        """Test creating Part with mismatched type."""
        with pytest.raises(ValueError, match="doesn't match part number"):
            Part("ANT-P1-00001", "LNA")

    def test_part_equality(self):
        """Test Part equality comparison."""
        part1 = Part("ANT-P1-00001")
        part2 = Part("ANT-P1-00001")
        part3 = Part("LNA-P1-00001")

        assert part1 == part2
        assert part1 != part3
        assert part1 != "not a part"

    def test_part_hash(self):
        """Test Part hashing for use in sets/dicts."""
        part1 = Part("ANT-P1-00001")
        part2 = Part("ANT-P1-00001")

        assert hash(part1) == hash(part2)
        assert len({part1, part2}) == 1  # Should be treated as same in set

    def test_part_string_representation(self):
        """Test Part string representations."""
        part = Part("ANT-P1-00001")
        assert "ANT-P1-00001" in str(part)
        assert "ANTENNA" in str(part)
        assert "P1" in str(part)

    def test_part_to_dict(self):
        """Test Part to dictionary conversion."""
        part = Part("ANT-P1-00001")
        data = part.to_dict()

        assert data["part_number"] == "ANT-P1-00001"
        assert data["part_type"] == "ANTENNA"
        assert data["polarization"] == "P1"
        assert "date_created" in data
        assert "date_modified" in data

    def test_part_from_dict(self):
        """Test Part creation from dictionary."""
        data = {
            "part_number": "LNA-P2-00123",
            "part_type": "LNA",
            "polarization": "P2",
            "date_created": "2024-01-01 10:00:00",
            "date_modified": "2024-01-01 10:00:00",
        }
        part = Part.from_dict(data)

        assert part.part_number == "LNA-P2-00123"
        assert part.part_type == "LNA"
        assert part.date_created == "2024-01-01 10:00:00"

    def test_part_from_database_row(self):
        """Test Part creation from database row."""
        row = (
            1,
            "BAC-PV-00001",
            "BACBOARD",
            "PV",
            "2024-01-01 10:00:00",
            "2024-01-01 10:00:00",
        )
        part = Part.from_database_row(row)

        assert part.part_number == "BAC-PV-00001"
        assert part.part_type == "BACBOARD"
        assert part.polarization == "PV"

    def test_part_barcode_filename(self):
        """Test barcode filename generation."""
        part = Part("ANT-P1-00001")
        assert part.get_barcode_filename() == "ANT-P1-00001.png"

    def test_create_part_function(self):
        """Test convenience create_part function."""
        part = create_part("ANT-P1-00001")
        assert isinstance(part, Part)
        assert part.part_number == "ANT-P1-00001"


class TestPartSearch:
    """Test part search functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            yield temp_dir

    def test_search_parts_empty_db(self, temp_db):
        """Test searching in empty database."""
        results = search_parts(db_dir=temp_db)
        assert results == []

    def test_get_part_statistics_empty_db(self, temp_db):
        """Test getting statistics from empty database."""
        stats = get_part_statistics(db_dir=temp_db)
        assert stats["total_parts"] == 0
        assert stats["latest_part"]["part_number"] is None

    def test_find_part_not_found(self, temp_db):
        """Test finding non-existent part."""
        result = find_part("ANT-P1-00001", db_dir=temp_db)
        assert result is None
