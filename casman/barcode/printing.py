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

    # Determine base output directory
    env_barcode_dir = os.environ.get("CASMAN_BARCODE_DIR")
    if env_barcode_dir:
        base_dir = env_barcode_dir
    else:
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "barcodes")

    # Create separate files for P1 and P2
    output_p1_pdf = os.path.join(
        base_dir,
        f"{part_type}_P1_{start_number:05d}_{end_number:05d}.pdf",
    )
    output_p2_pdf = os.path.join(
        base_dir,
        f"{part_type}_P2_{start_number:05d}_{end_number:05d}.pdf",
    )

    # Create LaTeX/PDF files for coax labels (separate for P1 and P2)
    if is_coax:
        output_p1_tex = output_p1_pdf.replace('.pdf', '.tex')
        output_p2_tex = output_p2_pdf.replace('.pdf', '.tex')
        
        _create_latex_barcode_page(pol1_results, {}, output_p1_tex)
        _create_latex_barcode_page({}, pol2_results, output_p2_tex)
        
        print(f"P1 LaTeX file created: {output_p1_tex}")
        print(f"P2 LaTeX file created: {output_p2_tex}")
        print(f"To generate PDFs, run:")
        print(f"  pdflatex {output_p1_tex}")
        print(f"  pdflatex {output_p2_tex}")
    else:
        _create_barcode_pdf(pol1_results, {}, output_p1_pdf)
        _create_barcode_pdf({}, pol2_results, output_p2_pdf)
        print(f"P1 PDF created: {output_p1_pdf}")
        print(f"P2 PDF created: {output_p2_pdf}")

    print(f"Barcode generation complete. Files saved in barcodes/{part_type}/P1 and barcodes/{part_type}/P2")


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
    # Determine if this is a coax part type by checking the first barcode path
    is_coax = False
    first_path = None
    for path in list(pol1_results.values()) + list(pol2_results.values()):
        if path:
            first_path = path
            # Check if path contains COAXSHORT or COAXLONG
            is_coax = "COAXSHORT" in path or "COAXLONG" in path
            break
    
    # Get layout settings from config (all in inches)
    if is_coax:
        # Use coax-specific page layout settings
        page_width_inches = get_config("barcode.coax.page_layout.page_width", 8.5)
        page_height_inches = get_config("barcode.coax.page_layout.page_height", 11.0)
        margin_top = get_config("barcode.coax.page_layout.margin_top", 0.5)
        margin_bottom = get_config("barcode.coax.page_layout.margin_bottom", 0.5)
        margin_left = get_config("barcode.coax.page_layout.margin_left", 0.5)
        margin_right = get_config("barcode.coax.page_layout.margin_right", 0.5)
        h_spacing_inches = get_config("barcode.coax.page_layout.horizontal_spacing", 0.25)
        v_spacing_inches = get_config("barcode.coax.page_layout.vertical_spacing", 0.25)
        images_per_row = get_config("barcode.coax.page_layout.columns", 3)
        rows_per_page = get_config("barcode.coax.page_layout.rows", 8)
        width_inches = get_config("barcode.coax.width_inches", 1.0)
        height_inches = get_config("barcode.coax.height_inches", 0.34)
    else:
        # Use standard page layout settings
        page_width_inches = 8.5  # US Letter
        page_height_inches = 11.0  # US Letter
        margin_top = margin_bottom = margin_left = margin_right = get_config("barcode.page.margin_inches", 0.5)
        h_spacing_inches = get_config("barcode.page.horizontal_spacing_inches", 0.25)
        v_spacing_inches = get_config("barcode.page.vertical_spacing_inches", 0.25)
        images_per_row = get_config("barcode.page.images_per_row", 3)
        rows_per_page = None  # Auto-calculate based on page height
        width_inches = get_config("barcode.width_inches", 2.0)
        height_inches = get_config("barcode.height_inches", 0.7)
    
    dpi = get_config("barcode.page.dpi", 300)

    # Convert inches to pixels - use round for precise conversions
    margin_left_px = round(margin_left * dpi)
    margin_right_px = round(margin_right * dpi)
    margin_top_px = round(margin_top * dpi)
    margin_bottom_px = round(margin_bottom * dpi)
    h_spacing = round(h_spacing_inches * dpi)
    v_spacing = round(v_spacing_inches * dpi)
    barcode_width = round(width_inches * dpi)
    barcode_height = round(height_inches * dpi)

    # Page size in pixels
    page_size = (round(page_width_inches * dpi), round(page_height_inches * dpi))
    
    # Verify layout fits on page (for coax with fixed rows/columns)
    if is_coax and rows_per_page:
        required_width = margin_left_px + (images_per_row * barcode_width) + ((images_per_row - 1) * h_spacing) + margin_right_px
        required_height = margin_top_px + (rows_per_page * barcode_height) + ((rows_per_page - 1) * v_spacing) + margin_bottom_px
        if required_width > page_size[0] or required_height > page_size[1]:
            print(f"Warning: Layout doesn't fit! Required: {required_width/dpi:.3f}\" x {required_height/dpi:.3f}\", Page: {page_width_inches}\" x {page_height_inches}\"")
            print(f"  Width: {required_width} px (available: {page_size[0]} px)")
            print(f"  Height: {required_height} px (available: {page_size[1]} px)")

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
    page = Image.new("RGB", page_size, "white")
    
    current_row = 0
    current_col = 0

    for index, barcode_path in enumerate(all_barcode_paths):
        img = Image.open(barcode_path)

        # Resize to exact dimensions from config - preserves dimensions in inches
        img = img.resize((barcode_width, barcode_height), Image.Resampling.LANCZOS)

        # Check if we need to start a new row
        if current_col >= images_per_row:
            current_col = 0
            current_row += 1

        # Check if we need to start a new page
        if rows_per_page and current_row >= rows_per_page:
            # Fixed rows per page (for coax)
            pages.append(page)
            page = Image.new("RGB", page_size, "white")
            current_row = 0
            current_col = 0

        # Calculate exact position based on row/column using config values
        x_offset = margin_left_px + (current_col * (barcode_width + h_spacing))
        y_offset = margin_top_px + (current_row * (barcode_height + v_spacing))
        
        # For non-coax with auto page breaks
        if not rows_per_page and y_offset + barcode_height > page_size[1] - margin_bottom_px:
            pages.append(page)
            page = Image.new("RGB", page_size, "white")
            current_row = 0
            current_col = 0
            x_offset = margin_left_px + (current_col * (barcode_width + h_spacing))
            y_offset = margin_top_px + (current_row * (barcode_height + v_spacing))
        
        # Paste the image onto the page
        page.paste(img, (x_offset, y_offset))
        current_col += 1

    # Add the last page if it has content
    if current_row > 0 or current_col > 0 or len(all_barcode_paths) > 0:
        pages.append(page)

    # Save all pages as a PDF with correct DPI to preserve physical dimensions
    if pages:
        pages[0].save(
            output_pdf, 
            save_all=True, 
            append_images=pages[1:],
            resolution=dpi,
            dpi=(dpi, dpi)
        )
    else:
        raise ValueError("No valid images to create PDF")


def _create_latex_barcode_page(
    pol1_results: Dict[str, str], pol2_results: Dict[str, str], output_tex: str
) -> None:
    """
    Create a LaTeX file that references barcode images in a precise grid layout.

    Parameters
    ----------
    pol1_results : Dict[str, str]
        Dictionary of P1 part numbers to barcode file paths.
    pol2_results : Dict[str, str]
        Dictionary of P2 part numbers to barcode file paths.
    output_tex : str
        Path to output LaTeX file.
    """
    # Get layout settings from config
    page_width = get_config("barcode.coax.page_layout.page_width", 8.5)
    page_height = get_config("barcode.coax.page_layout.page_height", 11.0)
    margin_top = get_config("barcode.coax.page_layout.margin_top", 0.984252)
    margin_bottom = get_config("barcode.coax.page_layout.margin_bottom", 0.669291)
    margin_left = get_config("barcode.coax.page_layout.margin_left", 0.433071)
    margin_right = get_config("barcode.coax.page_layout.margin_right", 0.433071)
    h_spacing = get_config("barcode.coax.page_layout.horizontal_spacing", 0.108268)
    v_spacing = get_config("barcode.coax.page_layout.vertical_spacing", 0.393701)
    columns = get_config("barcode.coax.page_layout.columns", 7)
    rows = get_config("barcode.coax.page_layout.rows", 13)
    label_width = get_config("barcode.coax.width_inches", 1.0)
    label_height = get_config("barcode.coax.height_inches", 0.34)

    # Collect all barcode paths: pol1 first, then pol2
    all_barcode_paths: List[str] = []
    for part_number in sorted(pol1_results.keys()):
        if pol1_results[part_number]:
            all_barcode_paths.append(pol1_results[part_number])
    for part_number in sorted(pol2_results.keys()):
        if pol2_results[part_number]:
            all_barcode_paths.append(pol2_results[part_number])

    if not all_barcode_paths:
        raise ValueError("No valid barcode images to create LaTeX file")

    # Start LaTeX document
    latex_content = []
    latex_content.append(r"\documentclass[letterpaper]{article}")
    latex_content.append(r"\usepackage{graphicx}")
    latex_content.append(r"\usepackage[margin=0in,top=0in,bottom=0in,left=0in,right=0in]{geometry}")
    latex_content.append(r"\pagestyle{empty}")
    latex_content.append(r"\setlength{\parindent}{0pt}")
    latex_content.append(r"\setlength{\parskip}{0pt}")
    latex_content.append(r"\setlength{\topskip}{0pt}")
    latex_content.append(r"\setlength{\baselineskip}{0pt}")
    latex_content.append(r"\begin{document}")
    latex_content.append(r"\vspace*{" + f"{margin_top}in" + r"}")
    latex_content.append("")

    # Process barcodes in pages
    labels_per_page = columns * rows
    total_pages = (len(all_barcode_paths) + labels_per_page - 1) // labels_per_page

    for page_num in range(total_pages):
        start_idx = page_num * labels_per_page
        end_idx = min(start_idx + labels_per_page, len(all_barcode_paths))
        page_barcodes = all_barcode_paths[start_idx:end_idx]

        if page_num > 0:
            latex_content.append(r"\clearpage")
            latex_content.append(r"\vspace*{" + f"{margin_top}in" + r"}")

        # Create the grid with precise positioning
        latex_content.append(r"\noindent")
        
        for row in range(rows):
            if row > 0:
                latex_content.append(f"\\\\[{v_spacing}in]")
            latex_content.append(r"\noindent")
            latex_content.append(f"\\hspace*{{{margin_left}in}}%")
            
            for col in range(columns):
                idx = start_idx + (row * columns + col)
                if idx >= end_idx:
                    break
                
                barcode_path = page_barcodes[idx - start_idx]
                # Convert absolute path to relative path from barcodes directory
                rel_path = os.path.relpath(barcode_path, os.path.dirname(output_tex))
                
                if col > 0:
                    latex_content.append(f"\\hspace{{{h_spacing}in}}%")
                
                latex_content.append(f"\\includegraphics[width={label_width}in,height={label_height}in]{{{rel_path}}}%")

    latex_content.append("")
    latex_content.append(r"\end{document}")

    # Write to file
    with open(output_tex, 'w') as f:
        f.write('\n'.join(latex_content))
