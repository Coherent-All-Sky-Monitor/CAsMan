"""
Remove duplicate part numbers from the assembly database, keeping only the latest entry and those with 'connected_to' filled.
Log all removals in logs/connection_modification_logs.
"""

import os
import sqlite3
from datetime import datetime


def main():
    db_path = os.path.join(os.path.dirname(__file__), "../database/assembled_casm.db")
    log_dir = os.path.join(os.path.dirname(__file__), "../logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "connection_modification_logs")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Find all duplicate part_numbers
    c.execute(
        """
        SELECT part_number, COUNT(*) as cnt
        FROM assembly
        GROUP BY part_number
        HAVING cnt > 1
    """
    )
    duplicates = c.fetchall()

    for part_number, _ in duplicates:
        # Get all rows for this part_number, order by scan_time DESC (latest first)
        c.execute(
            """
            SELECT rowid, scan_time, connected_to FROM assembly
            WHERE part_number = ?
            ORDER BY scan_time DESC
        """,
            (part_number,),
        )
        rows = c.fetchall()
        # Keep the latest and any with connected_to not null
        keep = set()
        for i, (rowid, scan_time, connected_to) in enumerate(rows):
            if i == 0 or connected_to:
                keep.add(rowid)
        # Delete all others
        for rowid, scan_time, connected_to in rows:
            if rowid not in keep:
                c.execute("DELETE FROM assembly WHERE rowid = ?", (rowid,))
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(log_path, "a", encoding="utf-8") as logf:
                    logf.write(
                        f"[{now}] Removed duplicate for part_number {part_number} (scan_time={scan_time}, connected_to={connected_to})\n"
                    )
    conn.commit()
    conn.close()
    print(
        "Duplicate removal complete. See logs/connection_modification_logs for details."
    )


if __name__ == "__main__":
    main()
