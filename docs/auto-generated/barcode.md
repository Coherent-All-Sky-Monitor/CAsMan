# Barcode Package

Documentation for the `casman.barcode` package.

## Overview

Barcode generation and printing for CAsMan.

This module provides barcode generation and printing utilities for managing part barcodes.

## Modules

### generation

Barcode generation utilities for CAsMan.

This module provides functions for generating barcode images for parts.

**Functions:**
- `generate_barcode()` - Generate a barcode image for a part number
- `generate_coax_label()` - Generate a text-based label for coax cables (no barcode)

### printing

Barcode printing utilities for CAsMan.

This module provides functions for generating barcode print pages.

**Functions:**
- `generate_barcode_printpages()` - Generate barcode printpages PDF for a range of part numbers

## Generation Module Details

This module provides functions for generating barcode images for parts.

## Functions

### generate_barcode

**Signature:** `generate_barcode(part_number: str, part_type: str, output_dir: Optional[str], barcode_format: str) -> str`

Generate a barcode image for a part number.

**Parameters:**

part_number : str
The part number to encode in the barcode.
part_type : str
The part type (used for directory organization).
output_dir : str, optional
Custom output directory. If not provided, uses default barcodes structure.
barcode_format : str, optional
Barcode format to use (default: code128).

**Returns:**

str
Path to the generated barcode image.

**Raises:**

ValueError
If the barcode format is not supported.
OSError
If there's an error creating directories or files.

---

### generate_coax_label

**Signature:** `generate_coax_label(part_number: str, part_type: str, output_dir: Optional[str]) -> str`

Generate a text-based label for coax cables (no barcode). Used for thin cables (COAXSHORT/LMR95 and COAXLONG/LMR195) where barcodes are difficult to scan. Creates a label with text on multiple lines that fits the cable diameter.

**Parameters:**

part_number : str
The part number to print on the label.
part_type : str
The part type (used for directory organization and diameter selection).
output_dir : str, optional
Custom output directory. If not provided, uses default barcodes structure.

**Returns:**

str
Path to the generated label image.

**Raises:**

ValueError
If the part type is not recognized or label generation fails.

---

## Printing Module Details

This module provides functions for generating barcode print pages.

## Functions

### generate_barcode_printpages

**Signature:** `generate_barcode_printpages(part_type: str, start_number: int, end_number: int) -> None`

Generate barcode printpages PDF for a range of part numbers. Creates a PDF with pol1 barcodes first, followed by pol2 barcodes.

**Parameters:**

part_type : str
The part type to generate barcodes for.
start_number : int
Starting part number.
end_number : int
Ending part number.

**Raises:**

ValueError
If part_type is unknown or number range is invalid.

---
