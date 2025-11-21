"""
Barcode printing utilities for CAsMan.

This module provides functions for generating barcode print pages.
"""

import os
from typing import Dict, List

from PIL import Image

from casman.config import get_config

from .generation import generate_barcode


def generate_barcode_printpages(
    part_type: str, start_number: int, end_number: int
) -> None:
    """
    Generate barcode printpages PDF for a range of part numbers.

    Creates a PDF with pol1 barcodes first, followed by pol2 barcodes.

    Parameters
    ----------
    part_type : str
        The part type to generate barcodes for.
    start_number : int
        Starting part number.
    end_number : int
        Ending part number.

    Raises
    ------
    ValueError
        If part_type is unknown or number range is invalid.
    """
    if start_number > end_number:
        raise ValueError("Start number must be less than or equal to end number")

    print(f"Generating barcodes for {part_type} from {start_number} to {end_number}")

    # Get prefix from part type
    from casman.parts.types import load_part_types

    PART_TYPES = load_part_types()

    part_abbrev = None
    for _, (full_name, abbrev) in PART_TYPES.items():
        if full_name.upper() == part_type.upper():
            part_abbrev = abbrev
            break

    if not part_abbrev:
        raise ValueError(f"Unknown part type: {part_type}")

    # Check if this is a coax cable part type and if it should use text labels
    is_coax = part_type.upper() in ["COAXSHORT", "COAXLONG"]
    use_barcode_for_coax = get_config("barcode.coax.use_barcode", False)

    # Generate barcodes/labels for both polarizations
    pol1_results: Dict[str, str] = {}
    pol2_results: Dict[str, str] = {}

    for i in range(start_number, end_number + 1):
        # Generate P1 (polarization 1)
        part_number_p1 = f"{part_abbrev}{i:05d}P1"
        try:
            if is_coax and not use_barcode_for_coax:
                from .generation import generate_coax_label

                label_path = generate_coax_label(part_number_p1, part_type)
                pol1_results[part_number_p1] = label_path
            else:
                barcode_path = generate_barcode(part_number_p1, part_type)
                pol1_results[part_number_p1] = barcode_path
        except (ValueError, OSError) as e:
            print(f"Warning: Failed to generate label for {part_number_p1}: {e}")
            pol1_results[part_number_p1] = ""

        # Generate P2 (polarization 2)
        part_number_p2 = f"{part_abbrev}{i:05d}P2"
        try:
            if is_coax and not use_barcode_for_coax:
                from .generation import generate_coax_label

                label_path = generate_coax_label(part_number_p2, part_type)
                pol2_results[part_number_p2] = label_path
            else:
                barcode_path = generate_barcode(part_number_p2, part_type)
                pol2_results[part_number_p2] = barcode_path
        except (ValueError, OSError) as e:
            print(f"Warning: Failed to generate label for {part_number_p2}: {e}")
            pol2_results[part_number_p2] = ""

    # Count successful generations
    successful_p1 = sum(1 for path in pol1_results.values() if path)
    successful_p2 = sum(1 for path in pol2_results.values() if path)
    failed_p1 = len(pol1_results) - successful_p1
    failed_p2 = len(pol2_results) - successful_p2

    print(f"Generated {successful_p1} P1 barcodes successfully")
    print(f"Generated {successful_p2} P2 barcodes successfully")
    if failed_p1 > 0 or failed_p2 > 0:
        print(f"Failed to generate {failed_p1 + failed_p2} barcodes")

    # Create PDF with pol1 first, then pol2
    # Check for test environment variable first
    env_barcode_dir = os.environ.get("CASMAN_BARCODE_DIR")
    if env_barcode_dir:
        output_pdf = os.path.join(
            env_barcode_dir,
            f"{part_type}_{start_number:05d}_{end_number:05d}.pdf",
        )
    else:
        output_pdf = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "barcodes",
            f"{part_type}_{start_number:05d}_{end_number:05d}.pdf",
        )

    _create_barcode_pdf(pol1_results, pol2_results, output_pdf)

    print(f"Barcode generation complete. Files saved in barcodes/{part_type}/")
    print(f"PDF created: {output_pdf}")


def _create_barcode_pdf(
    pol1_results: Dict[str, str], pol2_results: Dict[str, str], output_pdf: str
) -> None:
    """
    Create a PDF with barcode images arranged on pages.

    Parameters
    ----------
    pol1_results : Dict[str, str]
        Dictionary of P1 part numbers to barcode file paths.
    pol2_results : Dict[str, str]
        Dictionary of P2 part numbers to barcode file paths.
    output_pdf : str
        Path to output PDF file.
    """
    # Get layout settings from config (all in inches)
    margin_inches = get_config("barcode.page.margin_inches", 0.5)
    h_spacing_inches = get_config("barcode.page.horizontal_spacing_inches", 0.25)
    v_spacing_inches = get_config("barcode.page.vertical_spacing_inches", 0.25)
    images_per_row = get_config("barcode.page.images_per_row", 3)
    dpi = get_config("barcode.page.dpi", 300)

    width_inches = get_config("barcode.width_inches", 2.0)
    height_inches = get_config("barcode.height_inches", 0.7)

    # Convert inches to pixels
    margin = int(margin_inches * dpi)
    h_spacing = int(h_spacing_inches * dpi)
    v_spacing = int(v_spacing_inches * dpi)
    barcode_width = int(width_inches * dpi)
    barcode_height = int(height_inches * dpi)

    # Letter size in inches: 8.5 x 11, convert to pixels
    letter_size = (int(8.5 * dpi), int(11 * dpi))

    # Collect all barcode paths: pol1 first, then pol2
    all_barcode_paths: List[str] = []
    for part_number in sorted(pol1_results.keys()):
        if pol1_results[part_number]:
            all_barcode_paths.append(pol1_results[part_number])
    for part_number in sorted(pol2_results.keys()):
        if pol2_results[part_number]:
            all_barcode_paths.append(pol2_results[part_number])

    if not all_barcode_paths:
        raise ValueError("No valid barcode images to create PDF")

    pages = []
    x_offset = margin
    y_offset = margin
    page = Image.new("RGB", letter_size, "white")

    for index, barcode_path in enumerate(all_barcode_paths):
        img = Image.open(barcode_path)

        # Resize to exact dimensions from config
        img = img.resize((barcode_width, barcode_height), Image.Resampling.LANCZOS)

        # Check if we need to start a new row
        if (index % images_per_row) == 0 and index != 0:
            x_offset = margin
            y_offset += barcode_height + v_spacing

        # Check if we need to start a new page
        if y_offset + barcode_height > letter_size[1] - margin:
            pages.append(page)
            page = Image.new("RGB", letter_size, "white")
            x_offset = margin
            y_offset = margin

        # Paste the image onto the page
        page.paste(img, (x_offset, y_offset))
        x_offset += barcode_width + h_spacing

    # Add the last page if it has content
    if y_offset >= margin or len(all_barcode_paths) > 0:
        pages.append(page)

    # Save all pages as a PDF
    if pages:
        pages[0].save(output_pdf, save_all=True, append_images=pages[1:])
    else:
        raise ValueError("No valid images to create PDF")
