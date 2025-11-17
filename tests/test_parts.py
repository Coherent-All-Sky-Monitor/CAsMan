"""Simplified tests for CAsMan parts functionality."""

from casman.parts.validation import (
    validate_part_number,
    validate_part_type,
    validate_polarization,
    get_part_info,
)


class TestPartsValidation:
    """Test parts validation functions."""

    def test_validate_part_number(self):
        """Test part number validation."""
        assert validate_part_number("ANT-P1-00001")
        assert validate_part_number("LNA-P2-00123")
        assert not validate_part_number("INVALID")
        assert not validate_part_number(None)

    def test_validate_part_type(self):
        """Test part type validation."""
        assert validate_part_type("ANTENNA")
        assert validate_part_type("LNA")
        assert not validate_part_type("INVALID_TYPE")
        assert not validate_part_type(None)

    def test_validate_polarization(self):
        """Test polarization validation."""
        assert validate_polarization("P1")
        assert validate_polarization("P2")
        assert validate_polarization("PV")
        assert not validate_polarization("INVALID")
        assert not validate_polarization(None)

    def test_get_part_info(self):
        """Test part info extraction."""
        info = get_part_info("ANT-P1-00001")
        assert info is not None
        assert info["prefix"] == "ANT"
        assert info["part_type"] == "ANTENNA"
        
        assert get_part_info("INVALID") is None
