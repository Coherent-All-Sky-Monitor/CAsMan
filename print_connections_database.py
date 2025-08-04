import sqlite3


def print_assembled_db():
    """Print the contents of the assembled_casm.db database."""
    conn = sqlite3.connect("database/assembled_casm.db")
    c = conn.cursor()

    # Fetch all records from the assembly table
    c.execute("SELECT * FROM assembly")
    records = c.fetchall()

    # Check if there are any records
    if records:
        print("Assembled Database Contents:")
        print("-" * 120)
        for record in records:
            print(f"ID: {record[0]}")
            print(f"Part Number: {record[1]}")
            print(f"Part Type: {record[2]}")
            print(f"Polarization: {record[3]}")
            print(f"Scan Time: {record[4]}")
            print(f"Connected To: {record[5]}")
            print(f"Connected Part Type: {record[6]}")
            print(f"Connected Part Polarization: {record[7]}")
            print(f"Connected Part Scan Time: {record[8]}")
            print("-" * 120)
    else:
        print("No records found in the assembled database.")

    conn.close()


if __name__ == "__main__":
    print_assembled_db()
