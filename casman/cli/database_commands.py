"""
Database management commands for CAsMan CLI.

This module provides CLI commands for database operations including:
- Clearing databases with safety confirmations
- Printing database contents with formatted output
"""

import argparse
import sys

import argcomplete

from ..config import get_config


def cmd_database() -> None:
    """
    Database management command handler.

    Provides sub-commands for database operations:
    - clear: Clear database contents with safety confirmations
    - print: Display database contents in formatted tables
    """
    # Strip the main command from sys.argv if present
    args_to_parse = sys.argv[1:]  # Remove script name
    if args_to_parse and args_to_parse[0] == "database":
        args_to_parse = args_to_parse[1:]  # Remove the 'database' command

    parser = argparse.ArgumentParser(
        description="CAsMan Database Management\n\n"
        "Comprehensive database operations for parts and assembly management.\n"
        "Provides safe database clearing, formatted content display, interactive\n"
        "scanning workflows with validation, and GitHub-based synchronization.\n\n"
        "Subcommands:\n"
        "  clear            - Safely clear database contents with confirmations\n"
        "  print            - Display formatted database tables and records\n"
        "  load-coordinates - Load grid coordinates from CSV file\n"
        "  load-snap-boards - Load SNAP board configurations from CSV file\n"
        "  push             - Push databases to GitHub Releases (server-side)\n"
        "  pull             - Download databases from GitHub Releases\n"
        "  status           - Show database sync status\n\n"
        "Examples:\n"
        "  casman database clear --parts     # Clear only parts database\n"
        "  casman database print             # Show assembly database contents\n"
        "  casman database push              # Upload databases to GitHub\n"
        "  casman database pull              # Download latest databases\n"
        "  casman database status            # Show sync status\n\n"
        "Features:\n"
        "- Double confirmation for destructive operations\n"
        "- Visual warnings for database clearing\n"
        "- GitHub Releases-based synchronization\n"
        "- Validation and error handling\n"
        "- Database existence checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog="casman database",
    )

    subparsers = parser.add_subparsers(
        dest="subcommand", help="Database operation to perform", metavar="SUBCOMMAND"
    )

    # Clear database subcommand
    clear_parser = subparsers.add_parser(
        "clear",
        help="Clear database contents with safety confirmations",
        description="Safely clear database contents with visual warnings and double confirmation.\n"
        "By default, both databases are cleared unless specific options are used.\n\n"
        "Safety Features:\n"
        "- Visual stop sign warning\n"
        "- Double 'yes' confirmation required\n"
        "- Database existence verification\n"
        "- Graceful error handling\n\n"
        "Examples:\n"
        "  casman database clear              # Clear both databases\n"
        "  casman database clear --parts      # Clear only parts.db\n"
        "  casman database clear --assembled  # Clear only assembled_casm.db",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    clear_parser.add_argument(
        "--parts", action="store_true", help="Clear only the parts database (parts.db)"
    )
    clear_parser.add_argument(
        "--assembled",
        action="store_true",
        help="Clear only the assembly database (assembled_casm.db)",
    )

    # Print database subcommand
    print_parser = subparsers.add_parser(
        "print",
        help="Display formatted database contents",
        description="Display database contents in formatted tables with automatic width adjustment.\n"
        "Shows the assembled_casm.db database with proper column formatting,\n"
        "abbreviated headers for readability, and terminal width adaptation.\n\n"
        "Display Features:\n"
        "- ASCII box drawing for table borders\n"
        "- Automatic column width calculation\n"
        "- Terminal width detection and adaptation\n"
        "- Vertical layout for narrow terminals\n"
        "- Abbreviated column names for clarity\n\n"
        "Table Information:\n"
        "- Shows all records from assembled_casm.db\n"
        "- Displays connection chains and timestamps\n"
        "- Handles NULL values gracefully\n"
        "- Provides empty table notifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Load coordinates subcommand
    coords_parser = subparsers.add_parser(
        "load-coordinates",
        help="Load grid coordinates from CSV file",
        description="Load geographic coordinates from database/grid_positions.csv and update\n"
        "the antenna_positions table with latitude, longitude, height, and coordinate\n"
        "system information.\n\n"
        "CSV Format:\n"
        "  grid_code,latitude,longitude,height,coordinate_system,notes\n"
        "  CN021E00,37.8719,-122.2585,10.5,WGS84,North row 21\n\n"
        "Features:\n"
        "- Updates existing antenna position records\n"
        "- Skips empty coordinate values\n"
        "- Reports update counts and errors\n"
        "- Does not create new antenna assignments\n\n"
        "Examples:\n"
        "  casman database load-coordinates                    # Load default CSV\n"
        "  casman database load-coordinates --csv survey.csv   # Load custom CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    coords_parser.add_argument(
        "--csv",
        type=str,
        help="Path to CSV file (default: database/grid_positions.csv)",
    )

    # Load SNAP boards subcommand
    snap_parser = subparsers.add_parser(
        "load-snap-boards",
        help="Load SNAP board configurations from CSV file",
        description="Load SNAP board configurations from database/snap_boards.csv and update\n"
        "the snap_boards table with serial numbers, MAC addresses, IP addresses, and F-engine IDs.\n\n"
        "CSV Format:\n"
        "  chassis,slot,sn,mac,ip,feng_id,notes\n"
        "  1,A,SN01,00:11:22:33:01:00,192.168.1.1,0,Generated on 2025-01-01\n\n"
        "Packet Index Calculation:\n"
        "  packet_index = feng_id * 12 + port_number\n"
        "  Example: SNAP1A (feng_id=0) port 5 → packet_index = 5\n"
        "  Example: SNAP2A (feng_id=11) port 5 → packet_index = 137\n\n"
        "Features:\n"
        "- Creates new SNAP board records\n"
        "- Updates existing records if data changed\n"
        "- Reports load/update/skip counts and errors\n"
        "- Validates chassis (1-4), slot (A-K), and feng_id (0-43) values\n\n"
        "Examples:\n"
        "  casman database load-snap-boards                    # Load default CSV\n"
        "  casman database load-snap-boards --csv boards.csv   # Load custom CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    snap_parser.add_argument(
        "--csv",
        type=str,
        help="Path to CSV file (default: database/snap_boards.csv)",
    )

    # Sync push subcommand
    push_parser = subparsers.add_parser(
        "push",
        help="Push databases to GitHub Releases",
        description="Upload database snapshots to GitHub Releases for distribution.\n"
        "Creates a new release with timestamp-based tag (database-snapshot-YYYYMMDD-HHMMSS)\n"
        "and uploads both parts.db and assembled_casm.db as release assets.\n\n"
        "Requirements:\n"
        "- GITHUB_TOKEN environment variable must be set\n"
        "- Token needs 'repo' scope for creating releases\n"
        "- Repository must be configured in config.yaml\n\n"
        "Features:\n"
        "- Timestamp-based release naming\n"
        "- Automatic checksum calculation\n"
        "- Database validation before upload\n"
        "- Progress reporting\n\n"
        "Examples:\n"
        "  export GITHUB_TOKEN=ghp_xxxxx\n"
        "  casman database push                  # Push databases to GitHub\n"
        "  casman database push --cleanup 10     # Push and keep only 10 recent releases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    push_parser.add_argument(
        "--cleanup",
        type=int,
        metavar="N",
        help="Delete old releases, keeping only N most recent (default: 10)",
        default=10,
    )

    # Sync pull subcommand
    pull_parser = subparsers.add_parser(
        "pull",
        help="Download databases from GitHub Releases",
        description="Download the latest database snapshots from GitHub Releases.\n"
        "Fetches the most recent release and downloads both databases to the\n"
        "configured XDG data directory (~/.local/share/casman/databases/).\n\n"
        "Features:\n"
        "- Downloads latest release automatically\n"
        "- Validates SQLite database integrity\n"
        "- Atomic updates (temp file then move)\n"
        "- Progress reporting\n\n"
        "Examples:\n"
        "  casman database pull              # Download latest databases\n"
        "  casman database pull --force      # Force re-download even if up-to-date",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pull_parser.add_argument(
        "--force",
        action="store_true",
        help="Force download even if local databases are up-to-date",
    )

    # Sync status subcommand
    status_parser = subparsers.add_parser(
        "status",
        help="Show database sync status",
        description="Display information about database synchronization status.\n"
        "Shows the latest GitHub Release, local database status, and sync configuration.\n\n"
        "Information Displayed:\n"
        "- Latest GitHub Release details (name, timestamp, size)\n"
        "- Local database paths and sizes\n"
        "- Last sync check timestamp\n"
        "- Sync configuration (auto-push settings)\n\n"
        "Examples:\n"
        "  casman database status            # Show sync status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    argcomplete.autocomplete(parser)

    # Parse arguments with the cleaned argument list
    args, _ = parser.parse_known_args(args_to_parse)

    # Handle help for subcommands
    if args.subcommand is None:
        parser.print_help()
        return

    # Route to appropriate subcommand
    if args.subcommand == "clear":
        # Reconstruct arguments for the clear subcommand
        clear_args = []
        if "clear" in args_to_parse:
            clear_index = args_to_parse.index("clear")
            clear_args = args_to_parse[clear_index + 1 :]  # Everything after "clear"
        cmd_database_clear(clear_parser, clear_args)
    elif args.subcommand == "print":
        # Reconstruct arguments for the print subcommand
        print_args = []
        if "print" in args_to_parse:
            print_index = args_to_parse.index("print")
            print_args = args_to_parse[print_index + 1 :]  # Everything after "print"
        cmd_database_print(print_parser, print_args)
    elif args.subcommand == "load-coordinates":
        # Reconstruct arguments for the load-coordinates subcommand
        coords_args = []
        if "load-coordinates" in args_to_parse:
            coords_index = args_to_parse.index("load-coordinates")
            coords_args = args_to_parse[
                coords_index + 1 :
            ]  # Everything after "load-coordinates"
        cmd_database_load_coordinates(coords_parser, coords_args)
    elif args.subcommand == "load-snap-boards":
        # Reconstruct arguments for the load-snap-boards subcommand
        snap_args = []
        if "load-snap-boards" in args_to_parse:
            snap_index = args_to_parse.index("load-snap-boards")
            snap_args = args_to_parse[
                snap_index + 1 :
            ]  # Everything after "load-snap-boards"
        cmd_database_load_snap_boards(snap_parser, snap_args)
    elif args.subcommand == "push":
        # Reconstruct arguments for the push subcommand
        push_args = []
        if "push" in args_to_parse:
            push_index = args_to_parse.index("push")
            push_args = args_to_parse[push_index + 1 :]
        cmd_database_push(push_parser, push_args)
    elif args.subcommand == "pull":
        # Reconstruct arguments for the pull subcommand
        pull_args = []
        if "pull" in args_to_parse:
            pull_index = args_to_parse.index("pull")
            pull_args = args_to_parse[pull_index + 1 :]
        cmd_database_pull(pull_parser, pull_args)
    elif args.subcommand == "status":
        # Reconstruct arguments for the status subcommand
        status_args = []
        if "status" in args_to_parse:
            status_index = args_to_parse.index("status")
            status_args = args_to_parse[status_index + 1 :]
        cmd_database_status(status_parser, status_args)
    else:
        parser.print_help()


def cmd_database_clear(parser: argparse.ArgumentParser, remaining_args: list) -> None:
    """
    Handle database clear subcommand.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser for the clear subcommand
    remaining_args : list
        Remaining command line arguments
    """
    args = parser.parse_args(remaining_args)

    # Import database functions directly
    import os
    import sqlite3

    from ..database.connection import get_database_path

    def print_stop_sign() -> None:
        """Print a full color enhanced ASCII stop sign to the terminal."""
        stop_sign = (
            "\x1b[1;31;47m\n"
            "\n"
            "                  ████████████████████████             \n"
            "                 ██████████████████████████             \n"
            "                ████████████████████████████             \n"
            "               ██████████████████████████████            \n"
            "              ████████████████████████████████           \n"
            "             ██████████████████████████████████          \n"
            "            ████.     █.     █ .     █.     ████          \n"
            "           █████. ███████. ███  ███  █. ███ █████         \n"
            "          ██████.     ███. ███. ███  █.     ██████        \n"
            "           █████████. ███. ███. ███  █. █████████         \n"
            "            ████.     ███. ███       █. ████████           \n"
            "             ██████████████████████████████████            \n"
            "              ████████████████████████████████             \n"
            "               ██████████████████████████████                \n"
            "                ████████████████████████████                \n"
            "                 ██████████████████████████             \n"
            "                  ████████████████████████             \n"
            "\x1b[0m"
        )
        print(stop_sign)

    def clear_parts_db_local(db_dir: str) -> None:
        """Clear the parts database by deleting all records."""
        db_path = get_database_path("parts.db", db_dir)
        if not os.path.exists(db_path):
            print(f"Parts database not found at {db_path}. Nothing to clear.")
            return
        print_stop_sign()
        print(
            f"WARNING: This will DELETE ALL records from the parts database at: {db_path}"
        )
        confirm1 = (
            input("Are you sure you want to clear the parts database? (yes/no): ")
            .strip()
            .lower()
        )
        if confirm1 != "yes":
            print("Aborted.")
            return
        confirm2 = (
            input("This action is IRREVERSIBLE. Type 'yes' again to confirm: ")
            .strip()
            .lower()
        )
        if confirm2 != "yes":
            print("Aborted.")
            return
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("DELETE FROM parts")
            conn.commit()
            conn.close()
            print("All records deleted from parts database.")
        except (sqlite3.Error, OSError) as e:
            print(f"Error clearing parts database: {e}")
            sys.exit(1)

    def clear_assembled_db_local() -> None:
        """Clear all records from the assembled_casm.db database after double confirmation."""
        db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
        if db_path is None:
            print("Error: Database path could not be determined from config.")
            sys.exit(1)
        print_stop_sign()
        print(
            f"WARNING: This will DELETE ALL records from the assembled_casm database at: {db_path}"
        )
        confirm1 = (
            input(
                "Are you sure you want to clear the assembled_casm database? (yes/no): "
            )
            .strip()
            .lower()
        )
        if confirm1 != "yes":
            print("Aborted.")
            return
        confirm2 = (
            input("This action is IRREVERSIBLE. Type 'yes' again to confirm: ")
            .strip()
            .lower()
        )
        if confirm2 != "yes":
            print("Aborted.")
            return
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("DELETE FROM assembly")
            conn.commit()
            conn.close()
            print("All records deleted from assembled_casm database.")
        except (sqlite3.Error, OSError) as e:
            print(f"Error clearing assembled_casm database: {e}")
            sys.exit(1)

    # Default: clear both if no specific argument is given
    if not args.parts and not args.assembled:
        # No specific flags, clear both
        clear_parts = True
        clear_assembled = True
    else:
        # Specific flags given, only clear what's requested
        clear_parts = args.parts
        clear_assembled = args.assembled

    # Use database directory
    db_dir = "database"

    if clear_parts:
        clear_parts_db_local(db_dir)
    if clear_assembled:
        clear_assembled_db_local()


def cmd_database_print(parser: argparse.ArgumentParser, remaining_args: list) -> None:
    """
    Handle database print subcommand.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser for the print subcommand
    remaining_args : list
        Remaining command line arguments
    """
    parser.parse_args(remaining_args)

    # Print database function
    import os
    import sqlite3

    def print_db_schema(db_path: str) -> None:
        """Print all entries from each table in the SQLite database at db_path."""
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
                        "status",
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
                                f"  {abbr_names[i]:<{max(8, len(abbr_names[i]))}} : {val if val is not None else 'NULL'}"
                            )
                        print(sep_line)
            else:
                print("  (No entries in this table)\n")
        conn.close()

    assembled_db_path = get_config("CASMAN_ASSEMBLED_DB", "database/assembled_casm.db")
    if assembled_db_path is None:
        print("Error: Could not determine path to assembled_casm.db")
        sys.exit(1)

    print("Assembly Database Contents:")
    print("=" * 50)
    print_db_schema(str(assembled_db_path))


def cmd_database_load_coordinates(
    parser: argparse.ArgumentParser, remaining_args: list
) -> None:
    """
    Handle database load-coordinates subcommand.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser for the load-coordinates subcommand
    remaining_args : list
        Remaining command line arguments
    """
    args = parser.parse_args(remaining_args)

    from ..database.antenna_positions import load_grid_coordinates_from_csv

    print("Loading grid coordinates from CSV...")
    print("=" * 50)

    try:
        result = load_grid_coordinates_from_csv(csv_path=args.csv)

        print(f"\n✓ Updated: {result['updated']} position(s)")
        print(f"  Skipped: {result['skipped']} position(s)")

        if result["errors"]:
            print("\n⚠ Errors encountered:")
            for error in result["errors"]:
                print(f"  - {error}")

        if result["updated"] > 0:
            print("\n✓ Coordinate data loaded successfully")
        else:
            print("\n⚠ No positions were updated")
            print("  Make sure:")
            print("  - CSV file has valid coordinate data")
            print("  - Grid positions exist in antenna_positions table")
            print("  - CSV grid_code values match database records")

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("  Default CSV path: database/grid_positions.csv")
        print("  Use --csv to specify a different file")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error loading coordinates: {e}")
        sys.exit(1)


def cmd_database_load_snap_boards(
    parser: argparse.ArgumentParser, remaining_args: list
) -> None:
    """
    Handle database load-snap-boards subcommand.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser for the load-snap-boards subcommand
    remaining_args : list
        Remaining command line arguments
    """
    args = parser.parse_args(remaining_args)

    from ..database.snap_boards import load_snap_boards_from_csv

    print("Loading SNAP board configurations from CSV...")
    print("=" * 50)

    try:
        result = load_snap_boards_from_csv(csv_path=args.csv)

        print(f"\n✓ Loaded:  {result['loaded']} new board(s)")
        print(f"  Updated: {result['updated']} board(s)")
        print(f"  Skipped: {result['skipped']} board(s) (no changes)")

        if result["errors"]:
            print(f"\n⚠ Errors:  {result['errors']} board(s) failed")

        if result["loaded"] > 0 or result["updated"] > 0:
            print("\n✓ SNAP board data loaded successfully")
        else:
            print("\n⚠ No boards were loaded or updated")
            print("  Make sure:")
            print("  - CSV file has valid board data")
            print("  - CSV format: chassis,slot,sn,mac,ip,notes")
            print("  - Chassis values are 1-4")
            print("  - Slot values are A-K")

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("  Default CSV path: database/snap_boards.csv")
        print("  Use --csv to specify a different file")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error loading SNAP boards: {e}")
        sys.exit(1)


def cmd_database_push(parser: argparse.ArgumentParser, remaining_args: list) -> None:
    """
    Handle database push subcommand (push to GitHub Releases).

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser for the push subcommand
    remaining_args : list
        Remaining command line arguments
    """
    args = parser.parse_args(remaining_args)

    from pathlib import Path

    from ..database.connection import get_database_path
    from ..database.github_sync import get_github_sync_manager

    print("Pushing databases to GitHub Releases...")
    print("=" * 50)

    # Get sync manager
    sync_manager = get_github_sync_manager()
    if sync_manager is None:
        print("\n✗ Error: GitHub sync not configured")
        print("  Check config.yaml for github_owner and github_repo settings")
        sys.exit(1)

    if not sync_manager.github_token:
        print("\n✗ Error: GitHub token required for uploads")
        print("  Set GITHUB_TOKEN environment variable:")
        print("  export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx")
        sys.exit(1)

    # Get database paths
    try:
        parts_db_path = Path(get_database_path("parts.db"))
        assembled_db_path = Path(get_database_path("assembled_casm.db"))

        # Check that databases exist
        if not parts_db_path.exists():
            print(f"\n✗ Error: parts.db not found at {parts_db_path}")
            sys.exit(1)

        if not assembled_db_path.exists():
            print(f"\n✗ Error: assembled_casm.db not found at {assembled_db_path}")
            sys.exit(1)

        # Show database sizes
        parts_size_mb = parts_db_path.stat().st_size / (1024 * 1024)
        assembled_size_mb = assembled_db_path.stat().st_size / (1024 * 1024)

        print(f"\nDatabases to upload:")
        print(f"  parts.db:          {parts_size_mb:.2f} MB")
        print(f"  assembled_casm.db: {assembled_size_mb:.2f} MB")
        print(f"  Total:             {parts_size_mb + assembled_size_mb:.2f} MB")

        # Create GitHub Release with databases
        print(f"\nCreating GitHub Release...")
        tag_name = sync_manager.create_release(
            db_paths=[parts_db_path, assembled_db_path],
            description="Database snapshot from CLI",
        )

        if tag_name:
            print(f"\n✓ Successfully created release: {tag_name}")
            print(f"  Repository: {sync_manager.repo_owner}/{sync_manager.repo_name}")

            # Cleanup old releases if requested
            if args.cleanup:
                print(f"\nCleaning up old releases (keeping {args.cleanup} most recent)...")
                deleted_count = sync_manager.cleanup_old_releases(
                    keep_count=args.cleanup
                )
                print(f"✓ Deleted {deleted_count} old release(s)")

        else:
            print("\n✗ Failed to create GitHub Release")
            print("  Check logs for details")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error pushing databases: {e}")
        sys.exit(1)


def cmd_database_pull(parser: argparse.ArgumentParser, remaining_args: list) -> None:
    """
    Handle database pull subcommand (download from GitHub Releases).

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser for the pull subcommand
    remaining_args : list
        Remaining command line arguments
    """
    args = parser.parse_args(remaining_args)

    from ..database.github_sync import get_github_sync_manager

    print("Downloading databases from GitHub Releases...")
    print("=" * 50)

    # Get sync manager
    sync_manager = get_github_sync_manager()
    if sync_manager is None:
        print("\n✗ Error: GitHub sync not configured")
        print("  Check config.yaml for github_owner and github_repo settings")
        sys.exit(1)

    try:
        # Get latest release info
        latest_release = sync_manager.get_latest_release()

        if latest_release is None:
            print("\n✗ No database snapshots found on GitHub Releases")
            print(f"  Repository: {sync_manager.repo_owner}/{sync_manager.repo_name}")
            sys.exit(1)

        print(f"\nLatest release: {latest_release.release_name}")
        print(f"  Timestamp: {latest_release.timestamp}")
        print(f"  Size:      {latest_release.size_bytes / (1024 * 1024):.2f} MB")
        print(f"  Assets:    {', '.join(latest_release.assets)}")

        # Check if we need to download
        if not args.force and sync_manager._is_local_up_to_date(latest_release):
            print("\n✓ Local databases are already up-to-date")
            print(f"  Location: {sync_manager.local_db_dir}")
            return

        # Download databases
        print(f"\nDownloading to {sync_manager.local_db_dir}...")
        success = sync_manager.download_databases(
            snapshot=latest_release, force=args.force
        )

        if success:
            print("\n✓ Databases downloaded successfully")
            print(f"  Location: {sync_manager.local_db_dir}")
        else:
            print("\n✗ Failed to download databases")
            print("  Check logs for details")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error downloading databases: {e}")
        sys.exit(1)


def cmd_database_status(
    parser: argparse.ArgumentParser, remaining_args: list
) -> None:
    """
    Handle database status subcommand (show sync status).

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser for the status subcommand
    remaining_args : list
        Remaining command line arguments
    """
    parser.parse_args(remaining_args)

    from pathlib import Path

    from ..database.connection import get_database_path
    from ..database.github_sync import get_github_sync_manager

    print("Database Sync Status")
    print("=" * 50)

    # Get sync manager
    sync_manager = get_github_sync_manager()
    if sync_manager is None:
        print("\n✗ GitHub sync not configured")
        print("  Check config.yaml for github_owner and github_repo settings")
        sys.exit(1)

    print(f"\nRepository: {sync_manager.repo_owner}/{sync_manager.repo_name}")
    print(f"GitHub Token: {'✓ Set' if sync_manager.github_token else '✗ Not set'}")

    # Get latest release info
    try:
        latest_release = sync_manager.get_latest_release()

        if latest_release:
            print(f"\nLatest GitHub Release:")
            print(f"  Name:      {latest_release.release_name}")
            print(f"  Timestamp: {latest_release.timestamp}")
            print(f"  Size:      {latest_release.size_bytes / (1024 * 1024):.2f} MB")
            print(f"  Assets:    {', '.join(latest_release.assets)}")
        else:
            print("\n⚠ No releases found on GitHub")

    except Exception as e:
        print(f"\n✗ Error fetching GitHub releases: {e}")

    # Get local database info
    print(f"\nLocal Databases:")
    print(f"  XDG Path:  {sync_manager.local_db_dir}")

    for db_name in ["parts.db", "assembled_casm.db"]:
        try:
            db_path = Path(get_database_path(db_name))
            if db_path.exists():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                print(f"  {db_name:<18} {size_mb:>8.2f} MB  ({db_path})")
            else:
                print(f"  {db_name:<18}  Not found")
        except Exception as e:
            print(f"  {db_name:<18}  Error: {e}")

    # Get last check time
    last_check = sync_manager.get_last_check_time()
    if last_check:
        print(f"\nLast sync check: {last_check}")
    else:
        print(f"\nLast sync check: Never")

    # Show sync configuration
    try:
        enabled = get_config("database.sync.enabled", False)
        backend = get_config("database.sync.backend", "unknown")
        auto_sync = get_config("database.sync.auto_sync_on_import", False)
        auto_push = get_config("database.sync.server.auto_push_enabled", False)
        push_scans = get_config("database.sync.server.push_after_scans", 30)
        push_hours = get_config("database.sync.server.push_after_hours", 1.0)

        print(f"\nSync Configuration:")
        print(f"  Enabled:           {enabled}")
        print(f"  Backend:           {backend}")
        print(f"  Auto-sync:         {auto_sync}")
        print(f"  Auto-push:         {auto_push}")
        print(f"  Push after scans:  {push_scans}")
        print(f"  Push after hours:  {push_hours}")

    except Exception:
        pass
