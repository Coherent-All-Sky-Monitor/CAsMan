"""
Script to retroactively fix NULL part_type values \
    in the assembly table by inferring from part_number prefix.
"""

import sqlite3
from typing import Optional

from casman.parts import PART_TYPES


def infer_part_type(part_number: str) -> Optional[str]:
    """
    Infer the part type from a part number by matching \
        its prefix or substring to known abbreviations in PART_TYPES.

    Parameters
    ----------
    part_number : str
        The part number string to analyze.

    Returns
    -------
    str or None
        The inferred part type name, or None if not found.
    """
    # Try to match prefix with PART_TYPES abbreviation
    prefix = part_number.split("-")[0]
    for name, abbrev in PART_TYPES.values():
        if abbrev == prefix:
            return name
    # fallback: try to match in part_number
    for name, abbrev in PART_TYPES.values():
        if f"{abbrev}-" in part_number:
            return name
    return None


def fix_null_part_types(database_path: str) -> None:
    """
    Update all rows in the assembly table where part_type is \
        NULL by inferring the type from the part_number.

    Parameters
    ----------
    database_path : str
        Path to the SQLite database file containing the assembly table.

    Returns
    -------
    None
    """
    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.execute("SELECT id, part_number FROM assembly WHERE part_type IS NULL")
    rows = c.fetchall()
    fixed = 0
    for row in rows:
        row_id, part_number = row
        part_type = infer_part_type(part_number)
        if part_type:
            c.execute(
                "UPDATE assembly SET part_type = ? WHERE id = ?", (part_type, row_id)
            )
            fixed += 1
            print(
                f"Updated id={row_id}: part_number={part_number} -> part_type={part_type}"
            )
        else:
            print(
                f"Could not infer part_type for id={row_id}, part_number={part_number}"
            )
    conn.commit()
    conn.close()
    print(f"Fixed {fixed} rows with NULL part_type.")


if __name__ == "__main__":
    # Main entry point for the script. Fixes NULL part_type values in the
    # default assembled_casm.db database.
    db_path = "database/assembled_casm.db"
    fix_null_part_types(db_path)
