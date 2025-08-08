"""Tests for the barcode utilities module."""

from io import StringIO
from unittest.mock import Mock, patch

from casman.barcode import (
    arrange_barcodes_in_pdf,
    generate_barcode,
    generate_barcode_printpages,
    get_available_barcode_directories,
)

class TestBarcodeUtils:
    """Test barcode utility functions."""

    @patch("casman.barcode.generation.barcode.get")
    @patch("casman.barcode.generation.os.makedirs")
    def test_generate_barcode(
        self, mock_makedirs: Mock, mock_barcode_get: Mock
    ) -> None:
        """Test generating a barcode."""
        # Setup mocks
        mock_barcode_instance = Mock()
        mock_barcode_get.return_value = mock_barcode_instance
        mock_barcode_instance.save.return_value = None

        # Test barcode generation
        with patch("casman.barcode.generation.os.path.exists", return_value=False):
            result = generate_barcode("ANTP1-00001", "ANTENNA")

        # Verify calls
        mock_makedirs.assert_called_once()
        mock_barcode_get.assert_called_once()
        mock_barcode_instance.save.assert_called_once()

        assert "ANTP1-00001.png" in result
        assert "ANTENNA" in result

    @patch("casman.barcode.generation.os.path.exists")
    def test_generate_barcode_existing_directory(self, mock_exists: Mock) -> None:
        """Test generating barcode when directory exists."""
        mock_exists.return_value = True

        with patch("casman.barcode.generation.barcode.get") as mock_barcode_get:
            mock_barcode_instance = Mock()
            mock_barcode_get.return_value = mock_barcode_instance

            result = generate_barcode("LNAP1-00001", "LNA")

            assert "LNAP1-00001.png" in result
            assert "LNA" in result

    @patch("casman.barcode.operations.os.listdir")
    @patch("casman.barcode.operations.os.path.exists")
    def test_get_available_barcode_directories(
        self, mock_exists: Mock, mock_listdir: Mock
    ) -> None:
        """Test getting available barcode directories."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["ANTENNA", "LNA", "BACBOARD", "file.txt"]

        with patch("casman.barcode.operations.os.path.isdir") as mock_isdir:
            # Mock that first three are directories, last is file
            mock_isdir.side_effect = lambda path: not path.endswith("file.txt")

            result = get_available_barcode_directories()

            assert isinstance(result, list)
            assert "ANTENNA" in result
            assert "LNA" in result
            assert "BACBOARD" in result
            assert "file.txt" not in result

    @patch("casman.barcode.generation.os.path.exists")
    def test_get_available_barcode_directories_no_dir(self, mock_exists: Mock) -> None:
        """Test getting directories when barcodes directory doesn't exist."""
        mock_exists.return_value = False

        result = get_available_barcode_directories()

        assert result == []

    @patch("casman.barcode.printing.generate_barcode_range")
    def test_generate_barcode_printpages(self, mock_generate: Mock) -> None:
        """Test generating barcode print pages."""
        mock_generate.return_value = {
            "ANTP1-00001": "barcodes/ANTENNA/ANTP1-00001.png",
            "ANTP1-00002": "barcodes/ANTENNA/ANTP1-00002.png",
            "ANTP1-00003": "barcodes/ANTENNA/ANTP1-00003.png",
        }

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            generate_barcode_printpages("ANTENNA", 1, 3)

        # Should call generate_barcode_range once for the range
        assert mock_generate.call_count == 1

        # Check output contains expected messages
        output = mock_stdout.getvalue()
        assert "Generating barcodes for ANTENNA" in output
        assert "Barcode generation complete" in output

    @patch("casman.barcode.operations.os.path.exists")
    @patch("casman.barcode.operations.os.listdir") 
    @patch("casman.barcode.operations.Image.open")
    @patch("casman.barcode.operations.validate_barcode_file")
    def test_arrange_barcodes_in_pdf(
        self, mock_validate: Mock, mock_image_open: Mock, mock_listdir: Mock, mock_exists: Mock
    ) -> None:
        """Test arranging barcodes in PDF."""
        # Mock directory existence and file listing
        mock_exists.return_value = True
        mock_listdir.return_value = ["ANTP1-00001.png", "ANTP1-00002.png"]
        
        # Mock validation to return True for our test files
        mock_validate.return_value = (True, None)
        
        # Mock image objects with proper attributes
        mock_image = Mock()
        mock_image.size = (200, 100)
        mock_image.width = 200
        mock_image.height = 100
        mock_resized_image = Mock()
        mock_resized_image.width = 600
        mock_resized_image.height = 200
        mock_image.resize.return_value = mock_resized_image
        mock_image_open.return_value = mock_image

        # Mock Image.new for page creation and Image.Resampling
        with patch("casman.barcode.operations.Image.new") as mock_new, \
             patch("casman.barcode.operations.Image.Resampling"):
            
            mock_page = Mock()
            mock_page.paste = Mock()
            mock_page.save = Mock()
            mock_new.return_value = mock_page

            # Test that function executes successfully
            arrange_barcodes_in_pdf("barcodes/ANTENNA", "output.pdf")

            # Verify that the function processed the files
            assert mock_validate.call_count == 2  # Called for both PNG files
            assert mock_image_open.call_count == 2  # Opened both images
            mock_new.assert_called_with("RGB", (2550, 3300), "white")
            assert mock_page.paste.call_count == 2  # Pasted both images
            mock_page.save.assert_called_once_with("output.pdf", save_all=True, append_images=[])

    def test_generate_barcode_path_format(self) -> None:
        """Test that barcode path format is correct."""
        with patch("casman.barcode.generation.barcode.get") as mock_barcode_get:
            with patch("casman.barcode.generation.os.makedirs"):
                with patch("casman.barcode.generation.os.path.exists", return_value=True):
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
            with patch("casman.barcode.generation.barcode.get") as mock_barcode_get:
                with patch("casman.barcode.generation.os.makedirs"):
                    with patch(
                        "casman.barcode.operations.os.path.exists", return_value=True
                    ):
                        mock_barcode_instance = Mock()
                        mock_barcode_get.return_value = mock_barcode_instance

                        result = generate_barcode(part_number, part_type)
                        results.append(result)

        # All results should be different
        assert len(set(results)) == len(results)

        # Each should contain the part type
        for i, part_type in enumerate(part_types):
            assert part_type in results[i]

    @patch("casman.barcode.generation.os.path.exists")
    def test_directory_creation_logic(self, mock_exists: Mock) -> None:
        """Test that directories are created when they don't exist."""
        mock_exists.return_value = False

        with patch("casman.barcode.generation.os.makedirs") as mock_makedirs:
            with patch("casman.barcode.generation.barcode.get") as mock_barcode_get:
                mock_barcode_instance = Mock()
                mock_barcode_get.return_value = mock_barcode_instance

                generate_barcode("TEST1-00001", "TEST")

                # Should attempt to create directory
                mock_makedirs.assert_called_once()
