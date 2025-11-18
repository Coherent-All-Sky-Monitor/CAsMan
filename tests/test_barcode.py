"""Simplified tests for CAsMan barcode functionality."""

import os
import tempfile
from unittest.mock import Mock, patch, ANY, MagicMock

from PIL import Image

from casman.barcode.generation import (
    generate_barcode,
    generate_barcode_range,
    get_supported_barcode_formats,
    validate_barcode_format,
)
from casman.barcode.validation import (
    is_valid_barcode_format,
)
from casman.barcode.printing import (
    optimize_page_layout,
    calculate_printing_cost,
    generate_print_summary,
)
from casman.barcode.operations import (
    validate_barcode_file,
    get_directory_statistics,
    cleanup_invalid_barcodes,
    arrange_barcodes_in_pdf,
)


class TestBarcodeGeneration:
    """Test barcode generation functions."""

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

    @patch("casman.barcode.generation.os.makedirs")
    @patch("casman.barcode.generation.barcode.get")
    def test_generate_barcode_custom_format(self, mock_barcode_get, _):
        """Test barcode generation with custom format."""
        mock_barcode_instance = Mock()
        mock_barcode_get.return_value = mock_barcode_instance

        result = generate_barcode("LNA00001P1", "LNA", barcode_format="code39")

        assert "LNA00001P1.png" in result
        mock_barcode_get.assert_called_with("code39", "LNA00001P1", writer=ANY)

    @patch("casman.barcode.generation.generate_barcode")
    def test_generate_barcode_range(self, mock_generate):
        """Test generating range of barcodes."""
        mock_generate.return_value = "path/to/barcode.png"

        results = generate_barcode_range("ANTENNA", 1, 3)

        assert len(results) == 3
        assert mock_generate.call_count == 3

    def test_get_supported_barcode_formats(self):
        """Test retrieving supported barcode formats."""
        formats = get_supported_barcode_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert "code128" in formats

    def test_validate_barcode_format(self):
        """Test barcode format validation."""
        assert validate_barcode_format("code128")
        assert validate_barcode_format("code39")
        assert not validate_barcode_format("invalid_format")


class TestBarcodeValidation:
    """Test barcode validation functions."""

    def test_is_valid_barcode_format(self):
        """Test validation of barcode formats."""
        assert is_valid_barcode_format("code128")
        assert is_valid_barcode_format("code39")
        assert not is_valid_barcode_format("")
        assert not is_valid_barcode_format(None)

    def test_validate_part_number_format(self):
        """Test validation of barcode formats."""
        # Valid formats
        assert validate_barcode_format("code128")
        assert validate_barcode_format("code39")
        assert validate_barcode_format("ean13")

        # Invalid formats
        assert not validate_barcode_format("invalid_format")
        assert not validate_barcode_format("")
        assert not validate_barcode_format("code93")  # Not in supported list


class TestBarcodePrinting:
    """Test barcode printing and layout functions."""

    def test_optimize_page_layout_basic(self):
        """Test basic page layout optimization."""
        layout = optimize_page_layout(15)
        assert isinstance(layout, tuple)
        assert len(layout) == 2
        assert layout[0] > 0
        assert layout[1] > 0

    def test_optimize_page_layout_single_barcode(self):
        """Test layout optimization for single barcode."""
        layout = optimize_page_layout(1)
        assert layout[0] >= 1
        assert layout[1] >= 1

    def test_optimize_page_layout_large_batch(self):
        """Test layout optimization for large batch."""
        layout = optimize_page_layout(100)
        columns, rows = layout
        assert columns * rows >= 1
        assert columns >= 1
        assert rows >= 1

    def test_calculate_printing_cost(self):
        """Test printing cost calculation."""
        cost_info = calculate_printing_cost(50, cost_per_page=0.10)

        assert "num_barcodes" in cost_info
        assert cost_info["num_barcodes"] == 50
        assert "total_cost" in cost_info
        assert cost_info["total_cost"] >= 0
        assert "pages_needed" in cost_info
        assert cost_info["pages_needed"] > 0

    def test_calculate_printing_cost_zero_barcodes(self):
        """Test cost calculation with single barcode."""
        cost_info = calculate_printing_cost(1)
        assert cost_info["num_barcodes"] == 1
        assert cost_info["pages_needed"] >= 1
        assert cost_info["cost_per_barcode"] > 0

    def test_generate_print_summary(self):
        """Test print summary generation."""
        summary = generate_print_summary("ANTENNA", 1, 50)

        assert "part_type" in summary
        assert summary["part_type"] == "ANTENNA"
        assert "total_barcodes" in summary
        assert summary["total_barcodes"] == 50
        assert "recommended_layout" in summary
        assert "printing_info" in summary
