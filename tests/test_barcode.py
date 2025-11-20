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


class TestBarcodeOperations:
    """Test barcode file operations."""

    def test_validate_barcode_file_nonexistent(self):
        """Test validation of nonexistent file."""
        is_valid, error = validate_barcode_file("/nonexistent/path/file.png")
        assert not is_valid
        assert "does not exist" in error

    def test_validate_barcode_file_valid(self):
        """Test validation of valid barcode image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid test image
            img_path = os.path.join(tmpdir, "test_barcode.png")
            img = Image.new("RGB", (200, 100), color="white")
            img.save(img_path)

            is_valid, error = validate_barcode_file(img_path)
            assert is_valid
            assert error is None

    def test_validate_barcode_file_too_small(self):
        """Test validation rejects images that are too small."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "tiny.png")
            img = Image.new("RGB", (5, 5), color="white")
            img.save(img_path)

            is_valid, error = validate_barcode_file(img_path)
            assert not is_valid
            assert "too small" in error

    def test_validate_barcode_file_too_large(self):
        """Test validation rejects images that are too large."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "huge.png")
            img = Image.new("RGB", (6000, 3000), color="white")
            img.save(img_path)

            is_valid, error = validate_barcode_file(img_path)
            assert not is_valid
            assert "unusually large" in error

    def test_validate_barcode_file_unusual_aspect_ratio(self):
        """Test validation rejects images with unusual aspect ratios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "tall.png")
            # Very tall image (aspect ratio < 0.5)
            img = Image.new("RGB", (100, 300), color="white")
            img.save(img_path)

            is_valid, error = validate_barcode_file(img_path)
            assert not is_valid
            assert "aspect ratio" in error.lower()

    def test_validate_barcode_file_invalid_image(self):
        """Test validation of corrupted/invalid image file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "invalid.png")
            # Write non-image data
            with open(img_path, "w") as f:
                f.write("Not an image file")

            is_valid, error = validate_barcode_file(img_path)
            assert not is_valid
            assert error is not None

    def test_get_directory_statistics_nonexistent(self):
        """Test statistics for nonexistent directory."""
        stats = get_directory_statistics("/nonexistent/directory")
        assert stats["total_files"] == 0
        assert stats["valid_barcodes"] == 0
        assert stats["invalid_files"] == 0

    def test_get_directory_statistics_empty(self):
        """Test statistics for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = get_directory_statistics(tmpdir)
            assert stats["total_files"] == 0
            assert stats["valid_barcodes"] == 0
            assert stats["png_files"] == 0
            assert stats["jpg_files"] == 0

    def test_get_directory_statistics_with_files(self):
        """Test statistics for directory with mixed files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid PNG barcode
            png_path = os.path.join(tmpdir, "barcode1.png")
            img = Image.new("RGB", (200, 100), color="white")
            img.save(png_path)

            # Create valid JPG barcode
            jpg_path = os.path.join(tmpdir, "barcode2.jpg")
            img = Image.new("RGB", (200, 100), color="white")
            img.save(jpg_path)

            # Create invalid file (too small)
            invalid_path = os.path.join(tmpdir, "invalid.png")
            img = Image.new("RGB", (5, 5), color="white")
            img.save(invalid_path)

            # Create text file
            txt_path = os.path.join(tmpdir, "readme.txt")
            with open(txt_path, "w") as f:
                f.write("Test")

            stats = get_directory_statistics(tmpdir)
            assert stats["total_files"] == 4
            assert stats["png_files"] == 2
            assert stats["jpg_files"] == 1
            assert stats["other_files"] == 1
            assert stats["valid_barcodes"] == 2
            assert stats["invalid_files"] == 2

    def test_cleanup_invalid_barcodes_dry_run(self):
        """Test cleanup in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid barcode
            valid_path = os.path.join(tmpdir, "valid.png")
            img = Image.new("RGB", (200, 100), color="white")
            img.save(valid_path)

            # Create invalid barcode
            invalid_path = os.path.join(tmpdir, "invalid.png")
            img = Image.new("RGB", (5, 5), color="white")
            img.save(invalid_path)

            # Dry run should identify but not delete
            deleted = cleanup_invalid_barcodes(tmpdir, dry_run=True)
            assert len(deleted) == 1
            assert invalid_path in deleted
            assert os.path.exists(invalid_path)  # File still exists
            assert os.path.exists(valid_path)

    def test_cleanup_invalid_barcodes_real_deletion(self):
        """Test cleanup with actual file deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid barcode
            valid_path = os.path.join(tmpdir, "valid.png")
            img = Image.new("RGB", (200, 100), color="white")
            img.save(valid_path)

            # Create invalid barcode
            invalid_path = os.path.join(tmpdir, "invalid.png")
            img = Image.new("RGB", (5, 5), color="white")
            img.save(invalid_path)

            # Real deletion
            deleted = cleanup_invalid_barcodes(tmpdir, dry_run=False)
            assert len(deleted) == 1
            assert invalid_path in deleted
            assert not os.path.exists(invalid_path)  # File deleted
            assert os.path.exists(valid_path)  # Valid file remains

    def test_cleanup_invalid_barcodes_nonexistent_directory(self):
        """Test cleanup on nonexistent directory."""
        deleted = cleanup_invalid_barcodes("/nonexistent/directory")
        assert len(deleted) == 0

    @patch("casman.barcode.operations.get_config")
    def test_arrange_barcodes_in_pdf_nonexistent_directory(self, mock_config):
        """Test PDF arrangement with nonexistent directory."""
        mock_config.side_effect = lambda key, default: default

        with tempfile.TemporaryDirectory() as tmpdir:
            output_pdf = os.path.join(tmpdir, "output.pdf")
            
            try:
                arrange_barcodes_in_pdf("/nonexistent/directory", output_pdf)
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "does not exist" in str(e)

    @patch("casman.barcode.operations.get_config")
    def test_arrange_barcodes_in_pdf_no_valid_images(self, mock_config):
        """Test PDF arrangement with no valid images."""
        mock_config.side_effect = lambda key, default: default

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory with no valid images
            input_dir = os.path.join(tmpdir, "input")
            os.makedirs(input_dir)
            
            # Create invalid file
            with open(os.path.join(input_dir, "test.txt"), "w") as f:
                f.write("Not an image")

            output_pdf = os.path.join(tmpdir, "output.pdf")
            
            try:
                arrange_barcodes_in_pdf(input_dir, output_pdf)
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "No valid barcode images" in str(e)

    @patch("casman.barcode.operations.get_config")
    def test_arrange_barcodes_in_pdf_success(self, mock_config):
        """Test successful PDF arrangement."""
        mock_config.side_effect = lambda key, default: default

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input directory with valid barcodes
            input_dir = os.path.join(tmpdir, "input")
            os.makedirs(input_dir)
            
            # Create valid barcode images
            for i in range(3):
                img_path = os.path.join(input_dir, f"barcode{i}.png")
                img = Image.new("RGB", (300, 100), color="white")
                img.save(img_path)

            output_pdf = os.path.join(tmpdir, "output.pdf")
            
            # Should not raise exception
            arrange_barcodes_in_pdf(input_dir, output_pdf)
            
            # PDF should be created
            assert os.path.exists(output_pdf)
            assert os.path.getsize(output_pdf) > 0
