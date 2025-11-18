"""
This script arranges barcode images from a specified directory onto letter-sized pages
for printing.

The images are resized and placed in rows on each page, then saved as a multi-page PDF.
"""

import argparse
import os

from PIL import Image
from PIL.Image import Resampling

from casman.config.core import get_config


def arrange_barcodes_in_pdf(directory, output_pdf):
    """
    Arrange barcode images from a directory onto letter-sized PDF pages.

    Parameters
    ----------
    directory : str
        Path to the directory containing barcode PNG images.
    output_pdf : str
        Path to the output PDF file.

    Returns
    -------
    None
    """
    # Get barcode layout settings from config
    margin = get_config("barcode.margin_pixels", 100)
    images_per_row = get_config("barcode.images_per_row", 3)
    max_width = get_config("barcode.max_barcode_width", 600)
    max_height = get_config("barcode.max_barcode_height", 200)

    # Letter size in inches: 8.5 x 11, convert to pixels (assuming 300 DPI)
    letter_size = (2550, 3300)

    # Get all PNG images from the directory
    image_files = [f for f in os.listdir(directory) if f.endswith(".png")]
    image_files.sort()  # Optional: sort files for consistent order

    pages = []  # List to store all pages
    x_offset = margin
    y_offset = margin
    page = Image.new("RGB", letter_size, "white")

    for index, image_file in enumerate(image_files):
        img_path = os.path.join(directory, image_file)
        img = Image.open(img_path)

        # Calculate the aspect ratio and resize the image
        aspect_ratio = img.width / img.height
        if aspect_ratio > 1:  # Wide image
            new_width = max_width
            new_height = int(max_width / aspect_ratio)
        else:  # Tall image
            new_height = max_height
            new_width = int(max_height * aspect_ratio)
        img = img.resize((new_width, new_height), Resampling.LANCZOS)
        img = img.resize((new_width, new_height), Image.LANCZOS)

        # Check if image fits in the current position, else start a new page
        if y_offset + new_height + margin > letter_size[1]:
            pages.append(page)
            page = Image.new("RGB", letter_size, "white")
            x_offset, y_offset = margin, margin

        # Paste image onto the page
        page.paste(img, (x_offset, y_offset))

        # Update position for next image
        if (index + 1) % images_per_row == 0:
            x_offset = margin
            y_offset += new_height + margin
        else:
            x_offset += new_width + margin

    # Append the last page if it contains any images
    if any(page.getbbox()):
        pages.append(page)

    # Save all pages as a PDF
    pages[0].save(
        output_pdf, "PDF", resolution=300, save_all=True, append_images=pages[1:]
    )
    print(f"PDF saved as {output_pdf}")


def main():
    """
    Parse command-line arguments and arrange barcode images into a PDF.

    Returns
    -------
    None
    """

    parser = argparse.ArgumentParser(description="Arrange barcode images into a PDF.")
    parser.add_argument(
        "directory", type=str, help="Directory containing barcode images"
    )
    parser.add_argument("output_pdf", type=str, help="Output PDF file name")

    args = parser.parse_args()

    if not os.path.exists(args.directory):
        print("Directory does not exist.")
        return

    arrange_barcodes_in_pdf(args.directory, args.output_pdf)


if __name__ == "__main__":
    main()
