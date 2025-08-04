"""
This script reads and displays part records from a SQLite database.
Users can filter results by part type and polarization, or choose to view all records.
The script supports part types: ANTENNA, LNA, BACBOARD, and ALL.

Usage:
1. Run the script.
2. Select the part type by entering the corresponding integer.
3. Optionally enter a polarization, or press Enter to include all.
4. View the displayed records based on the selected criteria.
"""

import sqlite3

# Define part types and their corresponding integers
part_types = {1: "ANTENNA", 2: "LNA", 3: "BACBOARD", 4: "ALL"}


def read_database():
    """Read and display entries from the parts database filtered by part type and polarization."""
    # Connect to the database
    conn = sqlite3.connect("database/parts.db")
    c = conn.cursor()

    # Display part type options
    print("Select part type:")
    for key, name in part_types.items():
        print(f"{key}: {name}")

    # Handle user selection for part type
    try:
        type_selection = int(input("Enter the number corresponding to the part type: "))
        if type_selection not in part_types:
            print("Invalid selection. Please enter a valid number.")
            return
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    # Prompt the user for polarization
    polarization = (
        input("Enter polarization (or press Enter to include all): ").strip().upper()
    )

    # Construct the query based on user input
    if part_types[type_selection] == "ALL":
        query = "SELECT * FROM parts"
        params = ()
    else:
        query = "SELECT * FROM parts WHERE part_type = ?"
        params = (part_types[type_selection],)

        if polarization:
            query += " AND part_number LIKE ?"
            params += (f"%P{polarization}-%",)

    # Fetch records based on the constructed query
    c.execute(query, params)
    records = c.fetchall()

    # Check if there are any records
    if not records:
        print("No records found for the specified criteria.")
    else:
        # Print table headers
        print(
            "ID | Part Number       | Part Type | Created At          | Modified At         "
        )
        print(
            "---|-------------------|-----------|---------------------|---------------------"
        )

        # Iterate and print each record
        for record in records:
            print(
                f"{record[0]:<3} | {record[1]:<17} | {record[2]:<9} | {record[3]:<19} | {record[4]}"
            )

    # Close the database connection
    conn.close()


if __name__ == "__main__":
    read_database()
