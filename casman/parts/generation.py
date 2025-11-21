"""
Part number and barcode generation utilities for CAsMan.
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Optional

from casman.barcode import generate_barcode
from casman.config import get_config
from casman.database.connection import get_database_path
from casman.database.initialization import init_parts_db

from .types import load_part_types

PART_TYPES = load_part_types()


def get_last_part_number(part_type: str, db_dir: Optional[str] = None) -> Optional[str]:
    """
    Get the last part number for a given part type.
    """
    if db_dir is not None:
        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "SELECT part_number FROM parts WHERE part_type = ? ORDER BY id DESC LIMIT 1",
        (part_type,),
    )
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def generate_part_numbers(
    part_type: str, count: int, polarization: str, db_dir: Optional[str] = None
) -> List[str]:
    """
    Generate new part numbers for a given part type.
    """
    init_parts_db(db_dir)
    part_abbrev = None
    for _, (full_name, abbrev) in PART_TYPES.items():
        if full_name == part_type:
            part_abbrev = abbrev
            break
    if not part_abbrev:
        raise ValueError(f"Unknown part type: {part_type}")

    if db_dir is not None:
        db_path = os.path.join(db_dir, "parts.db")
    else:
        db_path = get_database_path("parts.db", None)

    temp_conn = sqlite3.connect(db_path)
    temp_c = temp_conn.cursor()
    temp_c.execute(
        "SELECT part_number FROM parts WHERE part_type = ? AND \
            polarization = ? ORDER BY id DESC LIMIT 1",
        (part_type, polarization),
    )
    result = temp_c.fetchone()
    last_part_number = result[0] if result else None
    temp_conn.close()
    if last_part_number:
        try:
            # Parse part number format: ANT00011P1
            # Extract the numeric portion between abbreviation and 'P'
            # Find where 'P' appears (e.g., P1 or P2)
            p_index = last_part_number.rfind("P")
            if p_index > 0:
                # Extract the numeric part before 'P'
                numeric_part = last_part_number[len(part_abbrev) : p_index]
                last_number = int(numeric_part)
            else:
                last_number = 0
        except (ValueError, IndexError):
            last_number = 0
    else:
        last_number = 0
    new_part_numbers = []
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if this is a coax cable part type and if it should use text labels
    is_coax = part_type.upper() in ["COAXSHORT", "COAXLONG"]
    use_barcode_for_coax = get_config("barcode.coax.use_barcode", False)

    for i in range(count):
        part_number = f"{part_abbrev}{last_number + i + 1:05d}P{polarization}"
        c.execute(
            "INSERT INTO parts (part_number, part_type, polarization, date_created, date_modified) "
            "VALUES (?, ?, ?, ?, ?)",
            (part_number, part_type, polarization, current_time, current_time),
        )

        # Generate appropriate label based on part type and config
        if is_coax and not use_barcode_for_coax:
            from casman.barcode.generation import generate_coax_label

            generate_coax_label(part_number, part_type)
        else:
            generate_barcode(part_number, part_type)

        new_part_numbers.append(part_number)
    conn.commit()
    conn.close()
    return new_part_numbers
