"""
Assembly-related CLI commands for CAsMan.
"""

import argparse
import sys

from casman.assembly.interactive import scan_and_assemble_interactive
from casman.database.initialization import init_all_databases


def cmd_scan() -> None:
    """
    Command-line interface for scanning and assembly.

    Provides functionality for interactive scanning and assembly statistics.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="CAsMan Interactive Scanning and Assembly Management\n\n"
        "Provides interactive scanning capabilities with "
        "comprehensive connection validation.\n"
        "Features real-time part validation, sequence enforcement, "
        "duplicate prevention, and full assembly workflows.\n\n"
        "Available Actions:\n"
        "  connection     - Start interactive connection scanning with validation\n"
        "  disconnection  - Start interactive disconnection scanning\n"
        "  connect        - Full interactive part scanning and assembly operations\n"
        "  disconnect     - Full interactive part disconnection operations\n"
        "  remove         - Remove a part by disconnecting all its connections\n\n"
        "The 'connect' and 'disconnect' actions provide complete workflows with:\n"
        "• USB barcode scanner support\n"
        "• Manual part number entry\n"
        "• Real-time part validation\n"
        "• Connection/disconnection tracking and SNAP/FENG mapping\n\n"
        "For web-based scanner interface, use: casman web --scanner-only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "action",
        choices=["connection", "disconnection", "connect", "disconnect", "remove"],
        help="Action to perform:\n"
        "  connection     - Start interactive connection scanning with validation\n"
        "  disconnection  - Start interactive disconnection scanning\n"
        "  connect        - Full interactive part scanning and assembly operations\n"
        "  disconnect     - Full interactive part disconnection operations\n"
        "  remove         - Remove a part by disconnecting all its connections",
    )

    # Check if help is requested or no arguments provided
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ["-h", "--help"]):
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman scan'

    init_all_databases()

    if args.action == "connection":
        # Launch interactive connection scanner
        scan_and_assemble_interactive()
    elif args.action == "disconnection":
        # Launch interactive disconnection scanner
        from casman.assembly.interactive import scan_and_disassemble_interactive

        scan_and_disassemble_interactive()
    elif args.action == "connect":
        # Launch full scanning and assembly workflow
        print("Starting Interactive Scanning and Assembly")
        print("=" * 50)
        print("Features available:")
        print("• USB barcode scanner support")
        print("• Manual part number entry")
        print("• Real-time validation")
        print("• Connection tracking")
        print("• SNAP/FENG mapping")
        print()

        # Import and run the scan script
        import os
        import subprocess

        try:
            script_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "scripts", "scan_and_assemble.py"
            )
            result = subprocess.run([sys.executable, script_path], check=False)
            if result.returncode != 0:
                print(f"Scanning process exited with code {result.returncode}")
                sys.exit(result.returncode)
        except KeyboardInterrupt:
            print("\n\nScanning interrupted by user")
            sys.exit(0)
        except (OSError, subprocess.SubprocessError) as e:
            print(f"\nError during scanning: {e}")
            sys.exit(1)
    elif args.action == "disconnect":
        # Launch full disconnection workflow
        print("Starting Interactive Disconnection")
        print("=" * 50)
        print("Features available:")
        print("• USB barcode scanner support")
        print("• Manual part number entry")
        print("• Real-time validation")
        print("• Disconnection tracking")
        print("• SNAP/FENG support")
        print()

        # Import and run the disconnection script
        import os
        import subprocess

        try:
            script_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "scripts",
                "scan_and_disassemble.py",
            )
            result = subprocess.run([sys.executable, script_path], check=False)
            if result.returncode != 0:
                print(f"Disconnection process exited with code {result.returncode}")
                sys.exit(result.returncode)
        except KeyboardInterrupt:
            print("\n\nDisconnection interrupted by user")
            sys.exit(0)
        except (OSError, subprocess.SubprocessError) as e:
            print(f"\nError during disconnection: {e}")
            sys.exit(1)
    elif args.action == "remove":
        # Remove part by disconnecting all connections
        import sqlite3
        from datetime import datetime

        from casman.database.connection import get_database_path

        print("\n" + "=" * 60)
        print("REMOVE PART - Disconnect All Connections")
        print("=" * 60)
        print("\nThis will disconnect ALL connections (forward and backward)")
        print("associated with the specified part.\n")

        # Get part number
        part_number = input("Enter part number to remove: ").strip()
        if not part_number:
            print("Error: Part number cannot be empty")
            sys.exit(1)

        try:
            # Connect to assembled database
            assembled_db = get_database_path("assembled_casm.db", None)

            assembled_conn = sqlite3.connect(assembled_db)
            assembled_conn.row_factory = sqlite3.Row

            # Infer part type from part number
            if part_number.startswith("SNAP"):
                part_type = "SNAP"
            elif part_number.startswith("ANT"):
                part_type = "ANTENNA"
            elif part_number.startswith("LNA"):
                part_type = "LNA"
            elif part_number.startswith("CXS"):
                part_type = "COAXSHORT"
            elif part_number.startswith("CXL"):
                part_type = "COAXLONG"
            elif part_number.startswith("BAC"):
                part_type = "BACBOARD"
            else:
                part_type = "UNKNOWN"

            print(f"\nSearching for: {part_type} {part_number}")

            # Get all connections using the same logic as web app
            cursor = assembled_conn.execute(
                """
                WITH normalized_pairs AS (
                    SELECT 
                        CASE WHEN part_number < connected_to 
                            THEN part_number ELSE connected_to END as part1,
                        CASE WHEN part_number < connected_to 
                            THEN connected_to ELSE part_number END as part2,
                        part_number,
                        connected_to,
                        connected_to_type,
                        connection_status,
                        scan_time,
                        id
                    FROM assembly
                    WHERE part_number = ? OR connected_to = ?
                ),
                latest_per_pair AS (
                    SELECT part1, part2, MAX(scan_time) as max_time
                    FROM normalized_pairs
                    GROUP BY part1, part2
                )
                SELECT np.id, np.part_number, np.connected_to, np.connected_to_type, np.scan_time
                FROM normalized_pairs np
                INNER JOIN latest_per_pair lpp
                    ON np.part1 = lpp.part1 
                    AND np.part2 = lpp.part2 
                    AND np.scan_time = lpp.max_time
                WHERE np.connection_status = 'connected'
                ORDER BY np.scan_time DESC
                """,
                (part_number, part_number),
            )

            connections = cursor.fetchall()

            if not connections:
                print(f"\nNo active connections found for {part_number}")
                print("Part has no connections to remove.")
                assembled_conn.close()
                sys.exit(0)

            # Display connections
            print(f"\nFound {len(connections)} active connection(s):")
            print("-" * 60)
            for i, conn in enumerate(connections, 1):
                conn_time = conn["scan_time"]
                other_part = (
                    conn["connected_to"]
                    if conn["part_number"] == part_number
                    else conn["part_number"]
                )
                print(f"{i}. {part_number} ↔ {other_part}")
                print(f"   Connected: {conn_time}")
            print("-" * 60)

            # Confirm removal
            confirm = (
                input(f"\nDisconnect all {len(connections)} connection(s)? (yes/no): ")
                .strip()
                .lower()
            )
            if confirm not in ["yes", "y"]:
                print("Removal cancelled")
                assembled_conn.close()
                sys.exit(0)

            # Disconnect all connections using the proper API
            from casman.assembly.connections import record_assembly_disconnection

            disconnect_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            disconnected = 0
            failed = 0

            print("\nDisconnecting...")
            for conn in connections:
                try:
                    # Determine which part is which in the connection
                    if conn["part_number"] == part_number:
                        this_part = part_number
                        this_type = part_type
                        other_part = conn["connected_to"]
                        other_type = conn["connected_to_type"]
                    else:
                        this_part = part_number
                        this_type = part_type
                        other_part = conn["part_number"]
                        # Infer the other part's type from its part number
                        if other_part.startswith("SNAP"):
                            other_type = "SNAP"
                        elif other_part.startswith("ANT"):
                            other_type = "ANTENNA"
                        elif other_part.startswith("LNA"):
                            other_type = "LNA"
                        elif other_part.startswith("CXS"):
                            other_type = "COAXSHORT"
                        elif other_part.startsWith("CXL"):
                            other_type = "COAXLONG"
                        elif other_part.startswith("BAC"):
                            other_type = "BACBOARD"
                        else:
                            other_type = "UNKNOWN"

                    # Record disconnection (polarization not critical for removal)
                    success = record_assembly_disconnection(
                        part_number=this_part,
                        part_type=this_type,
                        polarization="X",  # Use default for removal
                        scan_time=disconnect_time,
                        connected_to=other_part,
                        connected_to_type=other_type,
                        connected_polarization="X",
                        connected_scan_time=disconnect_time,
                    )

                    if success:
                        print(f"Disconnected: {this_part} ↔ {other_part}")
                        disconnected += 1
                    else:
                        print(f"Failed to disconnect {this_part} ↔ {other_part}")
                        failed += 1

                except Exception as e:
                    print(f"Failed to disconnect {this_part} ↔ {other_part}: {e}")
                    failed += 1

            # Close connection
            assembled_conn.close()

            # Summary
            print("\n" + "=" * 60)
            if failed == 0:
                print(f"SUCCESS: All {disconnected} connection(s) removed")
                sys.exit(0)
            else:
                print(f"PARTIAL SUCCESS: {disconnected} disconnected, {failed} failed")
                sys.exit(1)

        except Exception as e:
            print(f"Error removing part: {e}")
            sys.exit(1)
