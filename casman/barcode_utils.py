"""
Barcode utilities for CAsMan - Backward Compatibility Module.

This module provides backward compatibility by importing functions from
the new modular barcode package structure.
"""

import os
import barcode
from PIL import Image

# Import all functions from the new barcode package for backward compatibility
from .barcode import (
    generate_barcode,
    get_available_barcode_directories,
)

# Override arrange_barcodes_in_pdf to maintain backward compatibility with
# tests


def arrange_barcodes_in_pdf(directory: str, output_pdf: str) -> None:
    """
    Arrange barcode images from a directory onto letter-sized PDF pages.

    Parameters
    ----------
    directory : str
        Path to the directory containing barcode PNG images.
    output_pdf : str
        Path to the output PDF file.
    """
    # Letter size in inches: 8.5 x 11, convert to pixels (assuming 300 DPI)
    letter_size = (2550, 3300)
    margin = 100  # Margin in pixels
    images_per_row = 3
    max_width, max_height = (600, 200)  # Max dimensions for a barcode

    # Get all PNG images from the directory (legacy behavior - no validation)
    image_files = [f for f in os.listdir(directory) if f.endswith(".png")]
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

        # Move to the next position
        x_offset += max_width + 50  # Add some horizontal spacing

    # Add the last page if it has content
    if y_offset > margin:
        pages.append(page)

    # Save all pages as a PDF
    if pages:
        pages[0].save(output_pdf, save_all=True, append_images=pages[1:], format="PDF")


# Override generate_barcode_printpages to maintain backward compatibility
# with tests


def generate_barcode_printpages(
    part_type: str, start_number: int, end_number: int
) -> None:
    """
    Generate barcode printpages for a range of part numbers.

    This function maintains the original API for backward compatibility with tests.

    Parameters
    ----------
    part_type : str
        The part type to generate barcodes for.
    start_number : int
        Starting part number.
    end_number : int
        Ending part number.
    """
    # Import here to avoid circular import issues
    from .parts import PART_TYPES

    # Get the abbreviation for the part type
    part_abbrev = None
    for _, (full_name, abbrev) in PART_TYPES.items():
        if full_name.upper() == part_type.upper():
            part_abbrev = abbrev
            break

    if not part_abbrev:
        raise ValueError(f"Unknown part type: {part_type}")

    print(f"Generating barcodes for {part_type} from {start_number} to {end_number}")

    for i in range(start_number, end_number + 1):
        part_number = f"{part_abbrev}P1-{i:05d}"
        generate_barcode(part_number, part_type)
        print(f"Generated barcode for {part_number}")

    print(f"Barcode generation complete. Files saved in barcodes/{part_type}/")


# Export for backward compatibility
__all__ = [
    "arrange_barcodes_in_pdf",
    "generate_barcode",
    "get_available_barcode_directories",
    "generate_barcode_printpages",
    "main",
    "os",
    "barcode",
]


# Preserve the original main function for CLI compatibility
def main() -> None:
    """
    Main function for command-line usage - preserved for compatibility.

    This function maintains the original CLI interface while using
    the enhanced barcode generation capabilities.
    """
    import argparse
    from .barcode.generation import generate_barcode_range

    parser = argparse.ArgumentParser(description="Generate barcodes for CAsMan parts")
    parser.add_argument("part_type", help="Part type (ANTENNA, LNA, BACBOARD)")
    parser.add_argument("start_number", type=int, help="Starting part number")
    parser.add_argument("end_number", type=int, help="Ending part number")

    args = parser.parse_args()

    try:
        results = generate_barcode_range(
            args.part_type, args.start_number, args.end_number
        )

        # Count successful generations
        successful = sum(1 for path in results.values() if path)
        failed = len(results) - successful

        print(f"Generated {successful} barcodes successfully")
        if failed > 0:
            print(f"Failed to generate {failed} barcodes")

    except ValueError as e:
        print(f"Error: {e}")
    except OSError as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
