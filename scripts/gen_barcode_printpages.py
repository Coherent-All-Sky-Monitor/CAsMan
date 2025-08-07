"""
Barcode PDF generation script for CAsMan.

This script arranges barcode images from a specified directory onto letter-sized pages
for printing using the casman module.

The images are resized and placed in rows on each page, then saved as a multi-page PDF.
"""

import argparse
import os

from casman.barcode_utils import arrange_barcodes_in_pdf
from casman.config import get_config


def main() -> None:
    """
    Parse command-line arguments and arrange barcode images into a PDF.

    Returns
    -------
    None
    """

    parser = argparse.ArgumentParser(description="Arrange barcode images into a PDF.")
    default_dir = get_config("CASMAN_BARCODE_DIR", "barcodes")
    parser.add_argument(
        "directory",
        type=str,
        nargs="?",
        default=default_dir,
        help="Directory containing barcode images (default: from config.yaml or 'barcodes')",
    )
    parser.add_argument("output_pdf", type=str, help="Output PDF file name")

    args = parser.parse_args()

    if not os.path.exists(args.directory):
        print(f"Directory does not exist: {args.directory}")
        return

    try:
        arrange_barcodes_in_pdf(args.directory, args.output_pdf)
        print(f"Successfully created PDF: {args.output_pdf}")
    except (OSError, ValueError) as e:
        print(f"Error creating PDF: {e}")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
