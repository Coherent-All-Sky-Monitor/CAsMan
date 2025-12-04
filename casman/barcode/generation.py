"""
Barcode generation utilities for CAsMan.

This module provides functions for generating barcode images for parts.
"""

import os
from typing import Optional

import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

from casman.config import get_config


def generate_barcode(
    part_number: str,
    part_type: str,
    output_dir: Optional[str] = None,
    barcode_format: str = "code128",
) -> str:
    """
    Generate a barcode image for a part number.

    Parameters
    ----------
    part_number : str
        The part number to encode in the barcode.
    part_type : str
        The part type (used for directory organization).
    output_dir : str, optional
        Custom output directory. If not provided, uses default barcodes structure.
    barcode_format : str, optional
        Barcode format to use (default: code128).

    Returns
    -------
    str
        Path to the generated barcode image.

    Raises
    ------
    ValueError
        If the barcode format is not supported.
    OSError
        If there's an error creating directories or files.
    """
    # Determine output directory
    if output_dir is None:
        # Check for test environment variable first
        env_barcode_dir = os.environ.get("CASMAN_BARCODE_DIR")
        if env_barcode_dir:
            barcode_dir = os.path.join(env_barcode_dir, part_type)
        else:
            barcode_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "barcodes", part_type
            )
    else:
        barcode_dir = os.path.join(output_dir, part_type)

    # Determine polarization from part number and create subdirectory
    if "P1" in part_number.upper():
        barcode_dir = os.path.join(barcode_dir, "P1")
    elif "P2" in part_number.upper():
        barcode_dir = os.path.join(barcode_dir, "P2")
    
    # Create the barcode directory if it doesn't exist
    if not os.path.exists(barcode_dir):
        os.makedirs(barcode_dir)

    try:
        # Check if this is a coax part type that should use coax dimensions
        is_coax = part_type.upper() in ["COAXSHORT", "COAXLONG"]

        # Get barcode dimensions from config (in inches)
        if is_coax:
            # Use coax-specific dimensions for coax cables
            width_inches = get_config("barcode.coax.width_inches", 1.0)
            height_inches = get_config("barcode.coax.height_inches", 0.34)
        else:
            # Use standard barcode dimensions for other part types
            width_inches = get_config("barcode.width_inches", 2.0)
            height_inches = get_config("barcode.height_inches", 0.7)

        dpi = get_config("barcode.page.dpi", 300)

        # Convert inches to pixels for final image size
        target_width = int(width_inches * dpi)
        target_height = int(height_inches * dpi)

        # Generate the barcode with ImageWriter and minimal margins
        writer = ImageWriter()
        
        # Writer options with 0.5mm quiet zone and spacing
        writer_options = {
            'module_width': 0.3,      # Width of barcode modules
            'module_height': 10.0,     # Height of barcode bars in mm
            'quiet_zone': 2.0,         # 0.5mm quiet zone (2.0mm before scaling)
            'text_distance': 5,        # Distance between barcode and text
            'font_size': 10,           # Font size for text
            'write_text': True,        # Include text below barcode
        }
        
        barcode_generator = barcode.get(barcode_format, part_number, writer=writer)

        # Save to temporary location first
        temp_path = os.path.join(barcode_dir, f"{part_number}_temp")
        barcode_generator.save(temp_path, writer_options)

        # Open the generated image and resize to exact dimensions
        temp_image_path = f"{temp_path}.png"
        with Image.open(temp_image_path) as img:
            # Resize to exact target dimensions (this includes the barcode + text)
            # Use LANCZOS for high-quality resampling
            resized_img = img.resize(
                (target_width, target_height), Image.Resampling.LANCZOS
            )

            # Save with final name
            final_path = os.path.join(barcode_dir, f"{part_number}.png")
            resized_img.save(final_path)

        # Clean up temporary file
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

        return final_path

    except Exception as e:
        raise ValueError(f"Failed to generate barcode for {part_number}: {e}")


def generate_coax_label(
    part_number: str,
    part_type: str,
    output_dir: Optional[str] = None,
) -> str:
    """
    Generate a text-based label for coax cables (no barcode).

    Used for thin cables (COAXSHORT/LMR95 and COAXLONG/LMR195) where barcodes
    are difficult to scan. Creates a label with text on multiple lines that
    fits the cable diameter.

    Parameters
    ----------
    part_number : str
        The part number to print on the label.
    part_type : str
        The part type (used for directory organization and diameter selection).
    output_dir : str, optional
        Custom output directory. If not provided, uses default barcodes structure.

    Returns
    -------
    str
        Path to the generated label image.

    Raises
    ------
    ValueError
        If the part type is not recognized or label generation fails.
    """
    # Determine output directory
    if output_dir is None:
        # Check for test environment variable first
        env_barcode_dir = os.environ.get("CASMAN_BARCODE_DIR")
        if env_barcode_dir:
            label_dir = os.path.join(env_barcode_dir, part_type)
        else:
            label_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "barcodes", part_type
            )
    else:
        label_dir = os.path.join(output_dir, part_type)

    # Determine polarization from part number and create subdirectory
    if "P1" in part_number.upper():
        label_dir = os.path.join(label_dir, "P1")
    elif "P2" in part_number.upper():
        label_dir = os.path.join(label_dir, "P2")
    
    # Create the label directory if it doesn't exist
    if not os.path.exists(label_dir):
        os.makedirs(label_dir)

    try:
        # Get coax label settings from config
        dpi = get_config("barcode.page.dpi", 300)
        bg_color = get_config("barcode.coax.background_color", "white")
        text_color = get_config("barcode.coax.text_color", "black")

        # Get coax-specific label dimensions from config
        label_width_inches = get_config("barcode.coax.width_inches", 1.0)
        label_height_inches = get_config("barcode.coax.height_inches", 0.34)

        # Convert to pixels
        label_width_pixels = int(label_width_inches * dpi)
        label_height_pixels = int(label_height_inches * dpi)

        # Determine cable diameter and calculate repetitions based on part type
        if part_type.upper() == "COAXSHORT":
            cable_diameter = get_config("barcode.coax.lmr95_diameter", 0.141)
            # Number of repetitions = height_inches / (0.9 * cable_diameter)
            num_repetitions = int(label_height_inches / (0.9 * cable_diameter))
        elif part_type.upper() == "COAXLONG":
            cable_diameter = get_config("barcode.coax.lmr195_diameter", 0.233)
            # Number of repetitions = height_inches / (0.9 * cable_diameter)
            num_repetitions = int(label_height_inches / (0.9 * cable_diameter))
        else:
            raise ValueError(
                f"Coax label generation not supported for part type: {part_type}"
            )

        # Ensure at least one repetition
        num_repetitions = max(1, num_repetitions)

        # Create image
        img = Image.new("RGB", (label_width_pixels, label_height_pixels), bg_color)
        draw = ImageDraw.Draw(img)

        # Validate dimensions
        if label_height_pixels <= 0:
            raise ValueError(f"Invalid label height: {label_height_pixels} pixels")
        if label_width_pixels <= 0:
            raise ValueError(f"Invalid label width: {label_width_pixels} pixels")

        # Repeat the same part number multiple times on the label
        # Number of repetitions calculated based on height / (0.9 * cable_diameter)
        lines = [part_number] * num_repetitions

        # Calculate font size to fit all repetitions
        # Divide height by number of lines, with some padding
        line_height = label_height_pixels / (len(lines) + 0.5)
        font_size = max(
            8, int(line_height * 0.7)
        )  # 70% of line height for font, minimum 8

        # Try to load a font, fall back to default if not available
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except (OSError, IOError):
                # Use default font
                font = ImageFont.load_default()

        # Draw each line of text, centered
        y_offset = label_height_pixels * 0.1  # Start with 10% padding
        for line in lines:
            # Get text bounding box for centering
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Center horizontally
            x = (label_width_pixels - text_width) / 2

            # Draw text
            draw.text((x, y_offset), line, fill=text_color, font=font)

            # Move to next line
            y_offset += text_height + (label_height_pixels * 0.05)  # 5% spacing

        # Save the label
        final_path = os.path.join(label_dir, f"{part_number}.png")
        img.save(final_path)

        return final_path

    except Exception as e:
        raise ValueError(f"Failed to generate coax label for {part_number}: {e}")
