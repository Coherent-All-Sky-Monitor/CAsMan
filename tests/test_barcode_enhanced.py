"""
Enhanced tests for barcode generation modules.

These tests target specific functions in the barcode modules to improve
code coverage.
"""

import os
import tempfile
from unittest.mock import Mock, patch, ANY

from casman.barcode.generation import generate_barcode, generate_multiple_barcodes, validate_barcode_format
from casman.barcode.validation import is_valid_barcode_format, validate_part_number_format
from casman.barcode.operations import validate_barcode_file


class TestBarcodeGeneration:
    """Test barcode generation functionality."""

    @patch("casman.barcode.generation.barcode.get")
    @patch("casman.barcode.generation.os.makedirs")
    @patch("casman.barcode.generation.os.path.exists")
    def test_generate_barcode_custom_format(
        self, mock_exists: Mock, mock_makedirs: Mock, mock_barcode_get: Mock
    ) -> None:
        """Test generating barcode with custom format."""
        mock_exists.return_value = False
        mock_barcode_instance = Mock()
        mock_barcode_get.return_value = mock_barcode_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = generate_barcode(
                "ANT-P1-00001", 
                "ANTENNA", 
                output_dir=temp_dir,
                barcode_format="code39"
            )
            
            mock_barcode_get.assert_called_with("code39", "ANT-P1-00001", writer=ANY)
            assert "ANT-P1-00001.png" in result

    @patch("casman.barcode.generation.barcode.get")
    def test_generate_barcode_invalid_format(self, mock_barcode_get: Mock) -> None:
        """Test generating barcode with invalid format."""
        mock_barcode_get.side_effect = ValueError("Invalid barcode format")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                generate_barcode(
                    "ANT-P1-00001", 
                    "ANTENNA", 
                    output_dir=temp_dir,
                    barcode_format="invalid_format"
                )
                assert False, "Should have raised exception"
            except ValueError as e:
                assert "Invalid barcode format" in str(e)

    @patch("casman.barcode.generation.generate_barcode")
    def test_generate_multiple_barcodes(self, mock_generate: Mock) -> None:
        """Test multiple barcode generation."""
        mock_generate.return_value = "/path/to/barcode.png"
        
        part_numbers = ["ANT-P1-00001", "ANT-P1-00002", "ANT-P1-00003"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            results = generate_multiple_barcodes(part_numbers, "ANTENNA", temp_dir)
            
            assert len(results) == 3
            assert mock_generate.call_count == 3

    @patch("casman.barcode.generation.generate_barcode")
    def test_generate_multiple_barcodes_with_errors(self, mock_generate: Mock) -> None:
        """Test multiple barcode generation with some failures."""
        def side_effect(part_number, *args, **kwargs):
            if "002" in part_number:
                raise ValueError("Generation failed")
            return f"/path/to/{part_number}.png"
        
        mock_generate.side_effect = side_effect
        
        part_numbers = ["ANT-P1-00001", "ANT-P1-00002", "ANT-P1-00003"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            results = generate_multiple_barcodes(part_numbers, "ANTENNA", temp_dir)
            
            # Should have 3 results total: 2 successful and 1 failed (empty string)
            assert len(results) == 3
            assert results["ANT-P1-00001"] == "/path/to/ANT-P1-00001.png"
            assert results["ANT-P1-00002"] == ""  # Failed generation
            assert results["ANT-P1-00003"] == "/path/to/ANT-P1-00003.png"


class TestBarcodeValidation:
    """Test barcode validation functionality."""

    def test_is_valid_barcode_format_valid(self) -> None:
        """Test valid barcode format validation."""
        assert validate_barcode_format("code128") is True
        assert validate_barcode_format("code39") is True
        assert validate_barcode_format("ean13") is True

    def test_is_valid_barcode_format_invalid(self) -> None:
        """Test invalid barcode format validation."""
        assert validate_barcode_format("invalid_format") is False
        assert validate_barcode_format("") is False

    def test_validate_part_number_format_valid(self) -> None:
        """Test valid part number format validation."""
        assert validate_part_number_format("ANT-P1-00001")[0] is True
        assert validate_part_number_format("LNA-P1-12345")[0] is True
        assert validate_part_number_format("BAC-P1-00999")[0] is True

    def test_validate_part_number_format_invalid(self) -> None:
        """Test invalid part number format validation."""
        assert validate_part_number_format("INVALID")[0] is False
        assert validate_part_number_format("")[0] is False
        assert validate_part_number_format("123-456")[0] is False

    @patch("casman.barcode.operations.Image.open")
    @patch("casman.barcode.operations.os.path.exists")
    def test_validate_barcode_file_valid(self, mock_exists: Mock, mock_open: Mock) -> None:
        """Test barcode file validation."""
        mock_exists.return_value = True
        
        # Mock PIL Image object
        mock_img = Mock()
        mock_img.size = (200, 100)  # Valid barcode dimensions
        mock_open.return_value.__enter__.return_value = mock_img
        
        result, error = validate_barcode_file("/path/to/barcode.png")
        assert result is True
        assert error is None

    @patch("casman.barcode.operations.os.path.exists")
    def test_validate_barcode_file_missing(self, mock_exists: Mock) -> None:
        """Test barcode file validation with missing file."""
        mock_exists.return_value = False
        
        result, error = validate_barcode_file("/path/to/missing.png")
        assert result is False
        assert error is not None and "does not exist" in error


class TestBarcodeOperations:
    """Test barcode operations functionality."""

    @patch("casman.barcode.operations.os.path.exists")
    @patch("casman.barcode.operations.os.path.isfile")
    @patch("casman.barcode.operations.os.listdir")
    def test_scan_barcode_directory_with_files(
        self, mock_listdir: Mock, mock_isfile: Mock, mock_exists: Mock
    ) -> None:
        """Test scanning directory with barcode files."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_listdir.return_value = ["barcode1.png", "barcode2.png", "not_barcode.txt"]
        
        from casman.barcode.operations import scan_barcode_directory
        
        results = scan_barcode_directory("/path/to/barcodes")
        
        # Should return dictionary with file types
        assert isinstance(results, dict)
        assert "png" in results
        assert len(results["png"]) == 2  # Two PNG files
        assert "/path/to/barcodes/barcode1.png" in results["png"]
        assert "/path/to/barcodes/barcode2.png" in results["png"]
        assert len(results["other"]) == 1  # One TXT file

    @patch("casman.barcode.operations.os.path.exists")
    def test_scan_barcode_directory_missing(self, mock_exists: Mock) -> None:
        """Test scanning non-existent directory."""
        mock_exists.return_value = False
        
        from casman.barcode.operations import scan_barcode_directory
        
        results = scan_barcode_directory("/nonexistent/path")
        
        assert results == {}
