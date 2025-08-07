"""
print_connections_database.py

Prints the full schema (all tables and columns) of the assembled_casm.db database.
"""

import os
import sqlite3

from casman.config import get_config


def print_db_schema(db_path: str) -> None:
    """
    Print all entries from each table in the SQLite database at db_path.
    Uses extended ASCII for tables, and prints entries vertically if the terminal is too narrow.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file.

    Returns
    -------
    None
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Only print entries for each table, no schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in c.fetchall()]
    for table in tables:
        c.execute(f"SELECT * FROM {table}")
        rows = c.fetchall()
        if rows:
            col_names = [desc[0] for desc in c.description]
            # Use user-suggested abbreviations for the assembly table
            if table == "assembly":
                abbr_names = [
                    "id",
                    "part_#",
                    "Partype",
                    "pol",
                    "start scan",
                    "connected",
                    "Contype",
                    "conn_pol",
                    "Finish time",
                ]
            else:

                def abbr(s: str) -> str:
                    return s[:8]

                abbr_names = [abbr(n) for n in col_names]
            col_widths = [
                max(len(abbr_names[i]), *(len(str(row[i])) for row in rows))
                for i in range(len(col_names))
            ]
            table_width = sum(col_widths) + 3 * len(col_widths) + 1
            try:
                term_width = os.get_terminal_size().columns
            except OSError:
                term_width = 80
            if table_width <= term_width:
                # Extended ASCII box drawing
                def h(char: str, width: int) -> str:
                    return char * width

                top = "  ┌" + "┬".join(h("─", w + 2) for w in col_widths) + "┐"
                header = (
                    "  │ "
                    + " │ ".join(
                        f"{abbr_names[i]:<{col_widths[i]}}"
                        for i in range(len(col_names))
                    )
                    + " │"
                )
                sep = "  ├" + "┼".join(h("─", w + 2) for w in col_widths) + "┤"
                bottom = "  └" + "┴".join(h("─", w + 2) for w in col_widths) + "┘"
                print(top)
                print(header)
                print(sep)
                for row in rows:
                    row_str = " │ ".join(
                        f"{str(x) if x is not None else 'NULL':<{col_widths[i]}}"
                        for i, x in enumerate(row)
                    )
                    print(f"  │ {row_str} │")
                print(bottom)
            else:
                # Print each entry vertically, separated by a line
                sep_line = "  " + "─" * min(term_width, 60)
                for row in rows:
                    for i, val in enumerate(row):
                        print(
                            f"  {abbr_names[i]:<{max(8, len(abbr_names[i]))}} : \
                                {val if val is not None else 'NULL'}"
                        )
                    print(sep_line)
        else:
            print("  (No entries in this table)\n")
    conn.close()


if __name__ == "__main__":
    assembled_db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if assembled_db_path is None:
        raise RuntimeError("Could not determine path to assembled_casm.db")
    print_db_schema(str(assembled_db_path))


def print_assembled_db() -> None:
    """
    Print the contents of the assembled_casm.db database.

    Returns
    -------
    None
    """
