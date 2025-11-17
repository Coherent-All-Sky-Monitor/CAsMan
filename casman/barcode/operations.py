"""
Barcode file operations and directory management for CAsMan.

This module provides functions for managing barcode files, directories,
and performing file validation operations.
"""

import os
from typing import Dict, List, Optional, Tuple

from PIL import Image






def validate_barcode_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a file is a valid barcode image.

    Parameters
    ----------
    file_path : str
        Path to the barcode file to validate.

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message) where is_valid is True if file is valid,
        and error_message contains details if validation fails.
    """
    if not os.path.exists(file_path):
        return False, f"File does not exist: {file_path}"

    try:
        with Image.open(file_path) as img:
            # Check if image can be opened
            img.verify()

        # Re-open for size check (verify() closes the image)
        with Image.open(file_path) as img:
            width, height = img.size

            # Basic sanity checks for barcode dimensions
            if width < 10 or height < 10:
                return False, "Image too small to be a valid barcode"

            if width > 5000 or height > 5000:
                return False, "Image unusually large for a barcode"

            # Check aspect ratio (barcodes are typically wider than tall)
            aspect_ratio = width / height
            if aspect_ratio < 0.5:  # Very tall image
                return False, "Unusual aspect ratio for barcode (too tall)"

        return True, None

    except (OSError, IOError) as e:
        return False, f"Cannot read image file: {e}"
    except ImportError as e:
        return False, f"PIL/Pillow not available: {e}"
    except Exception as e:  # Catch PIL-specific exceptions and others
        return False, f"Invalid image file: {e}"


def get_directory_statistics(directory: str) -> Dict[str, int]:
    """
    Get statistics about barcode files in a directory.

    Parameters
    ----------
    directory : str
        Path to the directory to analyze.

    Returns
    -------
    Dict[str, int]
        Dictionary with statistics about the directory contents.
    """
    stats = {
        "total_files": 0,
        "valid_barcodes": 0,
        "invalid_files": 0,
        "png_files": 0,
        "jpg_files": 0,
        "other_files": 0,
    }

    if not os.path.exists(directory):
        return stats

    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            stats["total_files"] += 1

            # Count by extension
            extension = file.lower().split(".")[-1] if "." in file else "other"
            if extension == "png":
                stats["png_files"] += 1
            elif extension in ["jpg", "jpeg"]:
                stats["jpg_files"] += 1
            else:
                stats["other_files"] += 1

            # Validate barcode
            is_valid, _ = validate_barcode_file(file_path)
            if is_valid:
                stats["valid_barcodes"] += 1
            else:
                stats["invalid_files"] += 1

    return stats


def cleanup_invalid_barcodes(directory: str, dry_run: bool = True) -> List[str]:
    """
    Remove invalid barcode files from a directory.

    Parameters
    ----------
    directory : str
        Path to the directory to clean up.
    dry_run : bool, optional
        If True, only report what would be deleted without actually deleting.

    Returns
    -------
    List[str]
        List of file paths that were (or would be) deleted.
    """
    if not os.path.exists(directory):
        return []

    files_to_delete: List[str] = []

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            is_valid, _error = validate_barcode_file(file_path)
            if not is_valid:
                files_to_delete.append(file_path)
                if not dry_run:
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        print(f"Warning: Could not delete {file_path}: {e}")

    return files_to_delete


def arrange_barcodes_in_pdf(directory: str, output_pdf: str) -> None:
    """
    Arrange barcode images from a directory onto letter-sized PDF pages.

    Parameters
    ----------
    directory : str
        Path to the directory containing barcode PNG images.
    output_pdf : str
        Path to the output PDF file.

    Raises
    ------
    ValueError
        If directory doesn't exist or contains no valid images.
    """
    if not os.path.exists(directory):
        raise ValueError(f"Directory does not exist: {directory}")

    # Letter size in inches: 8.5 x 11, convert to pixels (assuming 300 DPI)
    letter_size = (2550, 3300)
    margin = 100  # Margin in pixels
    images_per_row = 3
    max_width, max_height = (600, 200)  # Max dimensions for a barcode

    # Get all valid barcode images from the directory
    image_files = []
    for f in os.listdir(directory):
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            file_path = os.path.join(directory, f)
            is_valid, _ = validate_barcode_file(file_path)
            if is_valid:
                image_files.append(f)

    if not image_files:
        raise ValueError(f"No valid barcode images found in {directory}")

    image_files.sort()  # Sort files for consistent order

    pages = []  # List to store all pages
    x_offset = margin
    y_offset = margin
    page = Image.new("RGB", letter_size, "white")

    for index, image_file in enumerate(image_files):
        img_path = os.path.join(directory, image_file)
        img: Image.Image = Image.open(img_path)

        # Calculate the aspect ratio and resize the image
        aspect_ratio = img.width / img.height
        if aspect_ratio > 1:  # Wide image
            new_width = max_width
            new_height = int(max_width / aspect_ratio)
        else:  # Tall image
            new_height = max_height
            new_width = int(max_height * aspect_ratio)

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Check if we need to start a new row
        if (index % images_per_row) == 0 and index != 0:
            x_offset = margin
            y_offset += max_height + 50  # Add some vertical spacing

        # Check if we need to start a new page
        if y_offset + max_height > letter_size[1] - margin:
            pages.append(page)
            page = Image.new("RGB", letter_size, "white")
            x_offset = margin
            y_offset = margin

        # Paste the image onto the page
        page.paste(img, (x_offset, y_offset))
        x_offset += max_width + 50  # Add some horizontal spacing

    # Add the last page if it has content
    if y_offset >= margin or len(image_files) > 0:
        pages.append(page)

    # Save all pages as a PDF
    if pages:
        pages[0].save(output_pdf, save_all=True, append_images=pages[1:])
        print(f"PDF created: {output_pdf}")
    else:
        raise ValueError("No valid images to create PDF")
