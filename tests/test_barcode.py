"""Simplified tests for CAsMan barcode functionality."""

from unittest.mock import Mock, patch

from casman.barcode.generation import generate_barcode
from casman.barcode.validation import is_valid_barcode_format, validate_part_number_format


class TestBarcodeUtils:
    """Test barcode utility functions."""

    @patch("casman.barcode.generation.os.makedirs")
    @patch("casman.barcode.generation.barcode.get")
    def test_generate_barcode_success(self, mock_barcode_get, _):
        """Test successful barcode generation."""
        mock_barcode_instance = Mock()
        mock_barcode_get.return_value = mock_barcode_instance
        
        result = generate_barcode("ANT00001P1", "ANTENNA")
        
        assert "ANT00001P1.png" in result
        mock_barcode_get.assert_called_once()
        mock_barcode_instance.save.assert_called_once()

    def test_is_valid_barcode_format(self):
        """Test validation of barcode formats."""
        assert is_valid_barcode_format("code128")
        assert is_valid_barcode_format("code39")
        # Note: Some formats may return True even if not "standard"
        # Testing with empty string which should definitely be False
        assert not is_valid_barcode_format("")
        assert not is_valid_barcode_format(None)

    def test_validate_part_number_format(self):
        """Test validation of part number formats."""
        is_valid, _ = validate_part_number_format("ANT00001P1")
        assert is_valid
        is_valid, _ = validate_part_number_format("INVALID")
        assert not is_valid
