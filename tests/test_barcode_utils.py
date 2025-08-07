"""Tests for the barcode utilities module."""

from io import StringIO
from unittest.mock import Mock, patch

from casman.barcode_utils import (arrange_barcodes_in_pdf, generate_barcode,
                                  generate_barcode_printpages,
                                  get_available_barcode_directories)


class TestBarcodeUtils:
    """Test barcode utility functions."""

    @patch('casman.barcode_utils.barcode.get')
    @patch('casman.barcode_utils.os.makedirs')
    def test_generate_barcode(
            self,
            mock_makedirs: Mock,
            mock_barcode_get: Mock) -> None:
        """Test generating a barcode."""
        # Setup mocks
        mock_barcode_instance = Mock()
        mock_barcode_get.return_value = mock_barcode_instance
        mock_barcode_instance.save.return_value = None

        # Test barcode generation
        with patch('casman.barcode_utils.os.path.exists', return_value=False):
            result = generate_barcode("ANTP1-00001", "ANTENNA")

        # Verify calls
        mock_makedirs.assert_called_once()
        mock_barcode_get.assert_called_once()
        mock_barcode_instance.save.assert_called_once()

        assert "ANTP1-00001.png" in result
        assert "ANTENNA" in result

    @patch('casman.barcode_utils.os.path.exists')
    def test_generate_barcode_existing_directory(
            self, mock_exists: Mock) -> None:
        """Test generating barcode when directory exists."""
        mock_exists.return_value = True

        with patch('casman.barcode_utils.barcode.get') as mock_barcode_get:
            mock_barcode_instance = Mock()
            mock_barcode_get.return_value = mock_barcode_instance

            result = generate_barcode("LNAP1-00001", "LNA")

            assert "LNAP1-00001.png" in result
            assert "LNA" in result

    @patch('casman.barcode_utils.os.listdir')
    @patch('casman.barcode_utils.os.path.exists')
    def test_get_available_barcode_directories(
            self, mock_exists: Mock, mock_listdir: Mock) -> None:
        """Test getting available barcode directories."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["ANTENNA", "LNA", "BACBOARD", "file.txt"]

        with patch('casman.barcode_utils.os.path.isdir') as mock_isdir:
            # Mock that first three are directories, last is file
            mock_isdir.side_effect = lambda path: not path.endswith('file.txt')

            result = get_available_barcode_directories()

            assert isinstance(result, list)
            assert "ANTENNA" in result
            assert "LNA" in result
            assert "BACBOARD" in result
            assert "file.txt" not in result

    @patch('casman.barcode_utils.os.path.exists')
    def test_get_available_barcode_directories_no_dir(
            self, mock_exists: Mock) -> None:
        """Test getting directories when barcodes directory doesn't exist."""
        mock_exists.return_value = False

        result = get_available_barcode_directories()

        assert result == []

    @patch('casman.barcode_utils.generate_barcode')
    def test_generate_barcode_printpages(self, mock_generate: Mock) -> None:
        """Test generating barcode print pages."""
        mock_generate.side_effect = [
            "barcodes/ANTENNA/ANTP1-00001.png.png",
            "barcodes/ANTENNA/ANTP1-00002.png.png",
            "barcodes/ANTENNA/ANTP1-00003.png.png"
        ]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            generate_barcode_printpages("ANTENNA", 1, 3)

        # Should generate 3 barcodes
        assert mock_generate.call_count == 3

        # Check output contains expected messages
        output = mock_stdout.getvalue()
        assert "Generating barcodes for ANTENNA" in output
        assert "Barcode generation complete" in output

    @patch('casman.barcode_utils.Image.open')
    @patch('casman.barcode_utils.os.listdir')
    def test_arrange_barcodes_in_pdf(
            self,
            mock_listdir: Mock,
            mock_image_open: Mock) -> None:
        """Test arranging barcodes in PDF."""
        mock_listdir.return_value = [
            "ANTP1-00001.png.png",
            "ANTP1-00002.png.png"]

        # Mock image objects
        mock_image = Mock()
        mock_image.size = (200, 100)
        mock_image.width = 200
        mock_image.height = 100
        mock_image.resize.return_value = mock_image
        mock_image_open.return_value = mock_image

        # Mock Image.new for page creation
        with patch('casman.barcode_utils.Image.new') as mock_new:
            mock_page = Mock()
            mock_new.return_value = mock_page

            # Test that function can be called without error
            try:
                arrange_barcodes_in_pdf("barcodes/ANTENNA", "output.pdf")
                test_passed = True
            except (OSError, IOError):
                # Expected exceptions for file operations
                test_passed = False

            # Verify basic operations occurred
            assert test_passed
            mock_new.assert_called()
            mock_page.paste.assert_called()

    def test_generate_barcode_path_format(self) -> None:
        """Test that barcode path format is correct."""
        with patch('casman.barcode_utils.barcode.get') as mock_barcode_get:
            with patch('casman.barcode_utils.os.makedirs'):
                with patch('casman.barcode_utils.os.path.exists', return_value=True):
                    mock_barcode_instance = Mock()
                    mock_barcode_get.return_value = mock_barcode_instance

                    result = generate_barcode("TEST1-00001", "TEST")

                    # Check path format
                    assert result.endswith(".png")
                    assert "TEST1-00001" in result
                    assert "TEST" in result

    def test_generate_barcode_part_type_handling(self) -> None:
        """Test that different part types create different paths."""
        part_types = ["ANTENNA", "LNA", "BACBOARD"]
        part_number = "TEST1-00001"

        results = []
        for part_type in part_types:
            with patch('casman.barcode_utils.barcode.get') as mock_barcode_get:
                with patch('casman.barcode_utils.os.makedirs'):
                    with patch('casman.barcode_utils.os.path.exists', return_value=True):
                        mock_barcode_instance = Mock()
                        mock_barcode_get.return_value = mock_barcode_instance

                        result = generate_barcode(part_number, part_type)
                        results.append(result)

        # All results should be different
        assert len(set(results)) == len(results)

        # Each should contain the part type
        for i, part_type in enumerate(part_types):
            assert part_type in results[i]

    @patch('casman.barcode_utils.os.path.exists')
    def test_directory_creation_logic(self, mock_exists: Mock) -> None:
        """Test that directories are created when they don't exist."""
        mock_exists.return_value = False

        with patch('casman.barcode_utils.os.makedirs') as mock_makedirs:
            with patch('casman.barcode_utils.barcode.get') as mock_barcode_get:
                mock_barcode_instance = Mock()
                mock_barcode_get.return_value = mock_barcode_instance

                generate_barcode("TEST1-00001", "TEST")

                # Should attempt to create directory
                mock_makedirs.assert_called_once()
