# Barcode_Utils Module

Barcode utilities for CAsMan - Backward Compatibility Module.

This module provides backward compatibility by importing functions from
the new modular barcode package structure.

## Functions

### arrange_barcodes_in_pdf

**Signature:** `arrange_barcodes_in_pdf(directory, output_pdf)`

Arrange barcode images from a directory onto letter-sized PDF pages.

**Parameters:**

directory : str
Path to the directory containing barcode PNG images.
output_pdf : str
Path to the output PDF file.

---

### generate_barcode_printpages

**Signature:** `generate_barcode_printpages(part_type, start_number, end_number)`

Generate barcode printpages for a range of part numbers. This function maintains the original API for backward compatibility with tests.

**Parameters:**

part_type : str
The part type to generate barcodes for.
start_number : int
Starting part number.
end_number : int
Ending part number.

---

### main

**Signature:** `main()`

Main function for command-line usage - preserved for compatibility. This function maintains the original CLI interface while using the enhanced barcode generation capabilities.

---
