"""Comprehensive tests for CAsMan barcode functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from PIL import Image

from casman.barcode.generation import generate_barcode, generate_coax_label
from casman.barcode.printing import generate_barcode_printpages


class TestBarcodeGeneration:
    """Test barcode generation functions."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @patch("casman.barcode.generation.get_config")
    @patch("casman.barcode.generation.Image.open")
    @patch("casman.barcode.generation.os.path.exists")
    @patch("casman.barcode.generation.os.remove")
    @patch("casman.barcode.generation.os.makedirs")
    @patch("casman.barcode.generation.barcode.get")
    def test_generate_barcode_success(
        self,
        mock_barcode_get,
        mock_makedirs,
        mock_remove,
        mock_exists,
        mock_image_open,
        mock_get_config,
    ):
        """Test successful barcode generation for standard part type."""
        # Setup mocks
        mock_get_config.side_effect = lambda key, default: {
            "barcode.width_inches": 1.2,
            "barcode.height_inches": 0.75,
            "barcode.page.dpi": 300,
        }.get(key, default)

        mock_barcode_instance = Mock()
        mock_barcode_get.return_value = mock_barcode_instance

        # Mock PIL Image operations
        mock_img = MagicMock()
        mock_resized = MagicMock()
        mock_img.resize.return_value = mock_resized
        mock_image_open.return_value.__enter__.return_value = mock_img

        mock_exists.return_value = True

        result = generate_barcode("ANT00001P1", "ANTENNA")

        assert "ANT00001P1.png" in result
        mock_barcode_get.assert_called_once()
        mock_barcode_instance.save.assert_called_once()
        mock_img.resize.assert_called_once_with((360, 225), Image.Resampling.LANCZOS)
        mock_resized.save.assert_called_once()

    @patch("casman.barcode.generation.get_config")
    @patch("casman.barcode.generation.Image.open")
    @patch("casman.barcode.generation.os.path.exists")
    @patch("casman.barcode.generation.os.remove")
    @patch("casman.barcode.generation.os.makedirs")
    @patch("casman.barcode.generation.barcode.get")
    def test_generate_barcode_coax_dimensions(
        self,
        mock_barcode_get,
        mock_makedirs,
        mock_remove,
        mock_exists,
        mock_image_open,
        mock_get_config,
    ):
        """Test barcode generation uses coax dimensions for coax part types."""
        # Setup mocks for coax dimensions
        mock_get_config.side_effect = lambda key, default: {
            "barcode.coax.width_inches": 1.0,
            "barcode.coax.height_inches": 0.34,
            "barcode.page.dpi": 300,
        }.get(key, default)

        mock_barcode_instance = Mock()
        mock_barcode_get.return_value = mock_barcode_instance

        mock_img = MagicMock()
        mock_resized = MagicMock()
        mock_img.resize.return_value = mock_resized
        mock_image_open.return_value.__enter__.return_value = mock_img

        mock_exists.return_value = True

        result = generate_barcode("CXS00001P1", "COAXSHORT")

        assert "CXS00001P1.png" in result
        # Verify coax dimensions: 1.0" × 0.34" at 300 DPI = 300 × 102 pixels
        mock_img.resize.assert_called_once_with((300, 102), Image.Resampling.LANCZOS)

    @patch("casman.barcode.generation.get_config")
    @patch("casman.barcode.generation.Image.open")
    @patch("casman.barcode.generation.os.path.exists")
    @patch("casman.barcode.generation.os.remove")
    @patch("casman.barcode.generation.os.makedirs")
    @patch("casman.barcode.generation.barcode.get")
    def test_generate_barcode_custom_format(
        self,
        mock_barcode_get,
        mock_makedirs,
        mock_remove,
        mock_exists,
        mock_image_open,
        mock_get_config,
    ):
        """Test barcode generation with custom format."""
        mock_get_config.side_effect = lambda key, default: {
            "barcode.width_inches": 1.2,
            "barcode.height_inches": 0.75,
            "barcode.page.dpi": 300,
        }.get(key, default)

        mock_barcode_instance = Mock()
        mock_barcode_get.return_value = mock_barcode_instance

        mock_img = MagicMock()
        mock_resized = MagicMock()
        mock_img.resize.return_value = mock_resized
        mock_image_open.return_value.__enter__.return_value = mock_img

        mock_exists.return_value = True

        result = generate_barcode("LNA00001P1", "LNA", barcode_format="code39")

        assert "LNA00001P1.png" in result
        mock_barcode_get.assert_called_once()
        args = mock_barcode_get.call_args[0]
        assert args[0] == "code39"
        assert args[1] == "LNA00001P1"

    @patch("casman.barcode.generation.get_config")
    @patch("casman.barcode.generation.os.makedirs")
    @patch("casman.barcode.generation.barcode.get")
    def test_generate_barcode_error_handling(
        self, mock_barcode_get, mock_makedirs, mock_get_config
    ):
        """Test error handling in barcode generation."""
        mock_get_config.side_effect = lambda key, default: {
            "barcode.width_inches": 1.2,
            "barcode.height_inches": 0.75,
            "barcode.page.dpi": 300,
        }.get(key, default)

        mock_barcode_get.side_effect = Exception("Barcode generation failed")

        with pytest.raises(ValueError, match="Failed to generate barcode"):
            generate_barcode("BAD00001P1", "BADTYPE")


class TestCoaxLabelGeneration:
    """Test coax label generation functions."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_generate_coax_label_coaxshort(self, temp_output_dir):
        """Test coax label generation for COAXSHORT - integration test."""
        result = generate_coax_label("CXS00001P1", "COAXSHORT", temp_output_dir)

        assert os.path.exists(result)
        assert "CXS00001P1.png" in result

        # Verify image was created and has reasonable properties
        img = Image.open(result)
        assert img.size[0] > 0  # Has width
        assert img.size[1] > 0  # Has height

    def test_generate_coax_label_coaxlong(self, temp_output_dir):
        """Test coax label generation for COAXLONG - integration test."""
        result = generate_coax_label("CXL00001P1", "COAXLONG", temp_output_dir)

        assert os.path.exists(result)
        assert "CXL00001P1.png" in result

        # Verify image was created
        img = Image.open(result)
        assert img.size[0] > 0
        assert img.size[1] > 0

    def test_generate_coax_label_invalid_part_type(self, temp_output_dir):
        """Test coax label generation with invalid part type."""
        with pytest.raises(ValueError, match="not supported"):
            generate_coax_label("ANT00001P1", "ANTENNA", temp_output_dir)

    def test_generate_coax_label_with_custom_output_dir(self, temp_output_dir):
        """Test coax label generation with custom output directory."""
        custom_dir = os.path.join(temp_output_dir, "custom")
        result = generate_coax_label("CXS00003P1", "COAXSHORT", custom_dir)

        assert os.path.exists(result)
        assert "custom" in result
        assert "CXS00003P1.png" in result


class TestBarcodeIntegration:
    """Integration tests for barcode/coax features."""

    def test_coax_dimensions_used_for_barcode(self):
        """Test that COAXSHORT uses coax dimensions for classic barcodes."""
        # This is tested via the generate_barcode function detecting coax type
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_barcode("CXS00010P1", "COAXSHORT", tmpdir)

            assert os.path.exists(result)
            img = Image.open(result)
            # Should use coax dimensions (1.0" × 0.34" = 300 × 102 at 300 DPI)
            assert img.size == (300, 102)

    def test_coaxlong_dimensions_used_for_barcode(self):
        """Test that COAXLONG also uses coax dimensions for classic barcodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_barcode("CXL00010P1", "COAXLONG", tmpdir)

            assert os.path.exists(result)
            img = Image.open(result)
            # Should use coax dimensions
            assert img.size == (300, 102)

    def test_standard_part_uses_standard_dimensions(self):
        """Test that non-coax parts use standard barcode dimensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_barcode("ANT00010P1", "ANTENNA", tmpdir)

            assert os.path.exists(result)
            img = Image.open(result)
            # Should use standard dimensions (1.2" × 0.75" = 360 × 225 at 300 DPI)
            assert img.size == (360, 225)

    def test_generate_barcode_with_custom_output_dir(self):
        """Test barcode generation with custom output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = os.path.join(tmpdir, "custom_barcodes")
            result = generate_barcode("LNA00001P1", "LNA", custom_dir)

            assert os.path.exists(result)
            assert "custom_barcodes" in result
            assert "LNA00001P1.png" in result

    def test_multiple_coax_labels_same_directory(self):
        """Test generating multiple coax labels in the same directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result1 = generate_coax_label("CXS00001P1", "COAXSHORT", tmpdir)
            result2 = generate_coax_label("CXS00002P1", "COAXSHORT", tmpdir)
            result3 = generate_coax_label("CXS00001P2", "COAXSHORT", tmpdir)

            assert os.path.exists(result1)
            assert os.path.exists(result2)
            assert os.path.exists(result3)
            assert result1 != result2 != result3


class TestBarcodePrintPages:
    """Test barcode print pages functionality."""

    def test_generate_printpages_invalid_range(self):
        """Test that invalid number ranges are rejected."""
        with pytest.raises(ValueError, match="Start number must be less than"):
            generate_barcode_printpages("ANTENNA", 10, 5)

    def test_generate_printpages_creates_pdf(self):
        """Test PDF generation for a small range."""
        # Function returns None but creates PDF file
        generate_barcode_printpages("ANTENNA", 1, 2)

        # Check that PDF was created in test barcode directory
        test_barcode_dir = os.environ.get("CASMAN_BARCODE_DIR")
        if test_barcode_dir:
            pdf_path = os.path.join(test_barcode_dir, "ANTENNA_00001_00002.pdf")
        else:
            # Fallback for when not using test isolation
            pdf_path = os.path.join(
                os.path.dirname(__file__), "..", "barcodes", "ANTENNA_00001_00002.pdf"
            )
        assert os.path.exists(pdf_path), f"PDF not found at {pdf_path}"

    def test_generate_printpages_coaxshort(self):
        """Test PDF generation for COAXSHORT with text labels."""
        generate_barcode_printpages("COAXSHORT", 1, 2)

        # Check that PDF was created in test barcode directory
        test_barcode_dir = os.environ.get("CASMAN_BARCODE_DIR")
        if test_barcode_dir:
            pdf_path = os.path.join(test_barcode_dir, "COAXSHORT_00001_00002.pdf")
        else:
            pdf_path = os.path.join(
                os.path.dirname(__file__), "..", "barcodes", "COAXSHORT_00001_00002.pdf"
            )
        assert os.path.exists(pdf_path), f"PDF not found at {pdf_path}"

    def test_generate_printpages_single_number(self):
        """Test PDF generation for a single part number."""
        generate_barcode_printpages("LNA", 1, 1)

        # Check that PDF was created in test barcode directory
        test_barcode_dir = os.environ.get("CASMAN_BARCODE_DIR")
        if test_barcode_dir:
            pdf_path = os.path.join(test_barcode_dir, "LNA_00001_00001.pdf")
        else:
            pdf_path = os.path.join(
                os.path.dirname(__file__), "..", "barcodes", "LNA_00001_00001.pdf"
            )
        assert os.path.exists(pdf_path), f"PDF not found at {pdf_path}"
