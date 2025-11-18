"""
Barcode printing and layout utilities for CAsMan.

This module provides functions for creating printable barcode layouts,
optimizing page arrangements, and generating print-ready documents.
"""

from typing import Tuple

from .generation import generate_barcode_range
from .operations import arrange_barcodes_in_pdf


def generate_barcode_printpages(
    part_type: str, start_number: int, end_number: int
) -> None:
    """
    Generate barcode printpages for a range of part numbers.

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
    print(f"Generating barcodes for {part_type} from {start_number} to {end_number}")

    # Generate all barcodes in the range
    results = generate_barcode_range(part_type, start_number, end_number)

    # Count successful generations
    successful = sum(1 for path in results.values() if path)
    failed = len(results) - successful

    print(f"Generated {successful} barcodes successfully")
    if failed > 0:
        print(f"Failed to generate {failed} barcodes")

    print(f"Barcode generation complete. Files saved in barcodes/{part_type}/")


def create_printable_pages(
    barcode_directory: str, output_pdf: str, page_layout: Tuple[int, int] = (3, 5)
) -> None:
    """
    Create printable pages from barcode images with custom layout.

    Parameters
    ----------
    barcode_directory : str
        Directory containing barcode images.
    output_pdf : str
        Path for the output PDF file.
    page_layout : Tuple[int, int], optional
        (columns, rows) for page layout. Default is (3, 5).

    Raises
    ------
    ValueError
        If directory doesn't exist or layout is invalid.
    """
    columns, rows = page_layout

    if columns < 1 or rows < 1:
        raise ValueError("Page layout must have at least 1 column and 1 row")

    if columns > 10 or rows > 15:
        raise ValueError("Page layout too large (max 10x15)")

    # Use the enhanced arrange_barcodes_in_pdf function
    arrange_barcodes_in_pdf(barcode_directory, output_pdf)


def optimize_page_layout(
    num_barcodes: int,
    page_size: Tuple[float, float] = (8.5, 11.0),
    barcode_size: Tuple[float, float] = (2.0, 0.7),
) -> Tuple[int, int]:
    """
    Calculate optimal page layout for given number of barcodes.

    Parameters
    ----------
    num_barcodes : int
        Total number of barcodes to fit.
    page_size : Tuple[int, int], optional
        Page dimensions in inches (width, height).
    barcode_size : Tuple[float, float], optional
        Barcode dimensions in inches (width, height).

    Returns
    -------
    Tuple[int, int]
        Optimal (columns, rows) layout for the page.
    """
    page_width, page_height = page_size
    barcode_width, barcode_height = barcode_size

    # Account for margins (0.5 inch on each side)
    usable_width = page_width - 1.0
    usable_height = page_height - 1.0

    # Calculate maximum possible columns and rows
    max_columns = int(usable_width / barcode_width)
    max_rows = int(usable_height / barcode_height)

    # Ensure at least 1x1
    max_columns = max(1, max_columns)
    max_rows = max(1, max_rows)

    # Find optimal layout that minimizes wasted space
    best_layout = (1, 1)
    best_efficiency = 0.0

    for cols in range(1, max_columns + 1):
        for rows in range(1, max_rows + 1):
            barcodes_per_page = cols * rows
            pages_needed = (num_barcodes + barcodes_per_page - 1) // barcodes_per_page
            total_slots = pages_needed * barcodes_per_page
            efficiency = num_barcodes / total_slots

            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_layout = (cols, rows)

    return best_layout


def calculate_printing_cost(num_barcodes: int, cost_per_page: float = 0.10) -> dict:
    """
    Calculate estimated printing costs for barcode sheets.

    Parameters
    ----------
    num_barcodes : int
        Number of barcodes to print.
    cost_per_page : float, optional
        Cost per printed page in dollars.

    Returns
    -------
    dict
        Dictionary with cost breakdown information.
    """
    layout = optimize_page_layout(num_barcodes)
    barcodes_per_page = layout[0] * layout[1]
    pages_needed = (num_barcodes + barcodes_per_page - 1) // barcodes_per_page

    total_cost = pages_needed * cost_per_page
    cost_per_barcode = total_cost / num_barcodes if num_barcodes > 0 else 0

    return {
        "num_barcodes": num_barcodes,
        "barcodes_per_page": barcodes_per_page,
        "pages_needed": pages_needed,
        "cost_per_page": cost_per_page,
        "total_cost": total_cost,
        "cost_per_barcode": cost_per_barcode,
        "layout": layout,
    }


def generate_print_summary(part_type: str, start_number: int, end_number: int) -> dict:
    """
    Generate a comprehensive summary for barcode printing job.

    Parameters
    ----------
    part_type : str
        The part type for barcodes.
    start_number : int
        Starting part number.
    end_number : int
        Ending part number.

    Returns
    -------
    dict
        Summary information for the printing job.
    """
    num_barcodes = end_number - start_number + 1
    cost_info = calculate_printing_cost(num_barcodes)

    return {
        "part_type": part_type,
        "number_range": (start_number, end_number),
        "total_barcodes": num_barcodes,
        "recommended_layout": cost_info["layout"],
        "printing_info": cost_info,
    }


def main() -> None:
    """
    Main entry point for barcode printing CLI.

    Provides interactive interface for generating barcode print pages.
    """
    print("CAsMan Barcode Printing Tool")
    print("=" * 30)

    try:
        part_type = (
            input("Enter part type (ANTENNA, LNA, BACBOARD, etc.): ").strip().upper()
        )
        if not part_type:
            print("Part type is required.")
            return

        start_num = int(input("Enter start number: "))
        end_num = int(input("Enter end number: "))

        if start_num > end_num:
            print("Start number must be <= end number.")
            return

        print(f"\nGenerating barcodes for {part_type} from {start_num} to {end_num}...")
        generate_barcode_printpages(part_type, start_num, end_num)

    except (ValueError, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            print("\nOperation cancelled.")
        else:
            print(f"Error: {e}")
    except (OSError, RuntimeError) as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
