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
        "Subcommands:\n"
        "  clear            - Clear database contents\n"
        "  print            - Display database tables\n"
        "  load-coordinates - Load grid coordinates from CSV\n"
        "  load-snap-boards - Load SNAP board configs from CSV\n"
        "  push             - Upload databases to GitHub Releases\n"
        "  pull             - Download databases from GitHub Releases\n"
        "  status           - Show database sync status\n\n"
        "Examples:\n"
        "  casman database clear --parts\n"
        "  casman database print\n"
        "  casman database push\n"
        "  casman database pull\n"
        "  casman database status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog="casman database",
    )

    subparsers = parser.add_subparsers(
        dest="subcommand", help="Database operation to perform", metavar="SUBCOMMAND"
    )

    # Clear database subcommand
    clear_parser = subparsers.add_parser(
        "clear",
        help="Clear database contents",
        description="Clear database contents with double confirmation.\n\n"
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
        help="Display database contents",
        description="Display assembled_casm.db contents in formatted tables.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Load coordinates subcommand
    coords_parser = subparsers.add_parser(
        "load-coordinates",
        help="Load grid coordinates from CSV",
        description="Load coordinates from CSV and update antenna_positions table.\n\n"
        "CSV Format:\n"
        "  grid_code,latitude,longitude,height,coordinate_system,notes\n\n"
        "Examples:\n"
        "  casman database load-coordinates\n"
        "  casman database load-coordinates --csv survey.csv",
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
        help="Load SNAP board configs from CSV",
        description="Load SNAP board configurations from CSV and update snap_boards table.\n\n"
        "CSV Format:\n"
        "  chassis,slot,sn,mac,ip,feng_id,notes\n\n"
        "Packet Index: packet_index = feng_id * 12 + port_number\n\n"
        "Examples:\n"
        "  casman database load-snap-boards\n"
        "  casman database load-snap-boards --csv boards.csv",
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
        help="Upload databases to GitHub Releases",
        description="Upload databases to GitHub Releases (requires GITHUB_TOKEN).\n\n"
        "Examples:\n"
        "  export GITHUB_TOKEN=ghp_xxxxx\n"
        "  casman database push\n"
        "  casman database push --cleanup 10",
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
        description="Download latest databases from GitHub Releases.\n\n"
        "Examples:\n"
        "  casman database pull\n"
        "  casman database pull --force",
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
        description="Display database synchronization status and latest GitHub Release info.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Restore database from backups subcommand
    restore_parser = subparsers.add_parser(
        "restore",
        help="Restore project databases from latest backups",
        description=(
            "Restore database/parts.db and/or database/assembled_casm.db from the latest "
            "timestamped .bak files in the project database directory.\n\n"
            "Examples:\n"
            "  casman database restore --latest            # Restore both DBs\n"
            "  casman database restore --latest --parts    # Restore only parts.db\n"
            "  casman database restore --latest --assembled # Restore only assembled_casm.db\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    restore_parser.add_argument(
        "--latest",
        action="store_true",
        help="Restore the most recent backup (default if no file specified)",
    )
    restore_parser.add_argument(
        "--parts",
        action="store_true",
        help="Restore parts.db only",
    )
    restore_parser.add_argument(
        "--assembled",
        action="store_true",
        help="Restore assembled_casm.db only",
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
    elif args.subcommand == "restore":
        # Reconstruct arguments for the restore subcommand
        restore_args = []
        if "restore" in args_to_parse:
            restore_index = args_to_parse.index("restore")
            restore_args = args_to_parse[restore_index + 1 :]
        cmd_database_restore(restore_parser, restore_args)
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

    from ..database.antenna_positions import load_grid_positions_from_csv
    from ..database.initialization import init_grid_positions_table

    print("Loading grid coordinates from CSV...")
    print("=" * 50)

    try:
        # Initialize the table first
        init_grid_positions_table()
        
        result = load_grid_positions_from_csv(csv_path=args.csv)

        print(f"\n[OK] Loaded:  {result['loaded']} position(s)")
        print(f"  Skipped: {result['skipped']} position(s)")

        if result["errors"]:
            print("\n[WARNING] Errors encountered:")
            for error in result["errors"]:
                print(f"  - {error}")

        if result["loaded"] > 0:
            print("\n[OK] Coordinate data loaded successfully")
        else:
            print("\n[WARNING] No positions were loaded")
            print("  Make sure:")
            print("  - CSV file has valid coordinate data")
            print("  - CSV format: grid_code,latitude,longitude,height,coordinate_system,notes")

    except FileNotFoundError as e:
        print(f"\n[ERROR] Error: {e}")
        print("  Default CSV path: database/grid_positions.csv")
        print("  Use --csv to specify a different file")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error loading coordinates: {e}")
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

        print(f"\n[OK] Loaded:  {result['loaded']} new board(s)")
        print(f"  Updated: {result['updated']} board(s)")
        print(f"  Skipped: {result['skipped']} board(s) (no changes)")

        if result["errors"]:
            print(f"\n[WARNING] Errors:  {result['errors']} board(s) failed")

        if result["loaded"] > 0 or result["updated"] > 0:
            print("\n[OK] SNAP board data loaded successfully")
        else:
            print("\n[WARNING] No boards were loaded or updated")
            print("  Make sure:")
            print("  - CSV file has valid board data")
            print("  - CSV format: chassis,slot,sn,mac,ip,notes")
            print("  - Chassis values are 1-4")
            print("  - Slot values are A-K")

    except FileNotFoundError as e:
        print(f"\n[ERROR] Error: {e}")
        print("  Default CSV path: database/snap_boards.csv")
        print("  Use --csv to specify a different file")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error loading SNAP boards: {e}")
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
        print("\n[ERROR] Error: GitHub sync not configured")
        print("  Check config.yaml for github_owner and github_repo settings")
        sys.exit(1)

    if not sync_manager.github_token:
        print("\n[ERROR] Error: GitHub token required for uploads")
        print("  Set GITHUB_TOKEN environment variable:")
        print("  export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx")
        sys.exit(1)

    # Get database paths
    try:
        parts_db_path = Path(get_database_path("parts.db"))
        assembled_db_path = Path(get_database_path("assembled_casm.db"))

        # Check that databases exist
        if not parts_db_path.exists():
            print(f"\n[ERROR] Error: parts.db not found at {parts_db_path}")
            sys.exit(1)

        if not assembled_db_path.exists():
            print(f"\n[ERROR] Error: assembled_casm.db not found at {assembled_db_path}")
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
            print(f"\n[OK] Successfully created release: {tag_name}")
            print(f"  Repository: {sync_manager.repo_owner}/{sync_manager.repo_name}")

            # Cleanup old releases if requested
            if args.cleanup:
                print(f"\nCleaning up old releases (keeping {args.cleanup} most recent)...")
                deleted_count = sync_manager.cleanup_old_releases(
                    keep_count=args.cleanup
                )
                print(f"[OK] Deleted {deleted_count} old release(s)")

        else:
            print("\n[ERROR] Failed to create GitHub Release")
            print("  Check logs for details")
            sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] Error pushing databases: {e}")
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
        print("\n[ERROR] Error: GitHub sync not configured")
        print("  Check config.yaml for github_owner and github_repo settings")
        sys.exit(1)

    try:
        # Get latest release info
        latest_release = sync_manager.get_latest_release()

        if latest_release is None:
            print("\n[ERROR] No database snapshots found on GitHub Releases")
            print(f"  Repository: {sync_manager.repo_owner}/{sync_manager.repo_name}")
            sys.exit(1)

        print(f"\nLatest release: {latest_release.release_name}")
        print(f"  Timestamp: {latest_release.timestamp}")
        print(f"  Size:      {latest_release.size_bytes / (1024 * 1024):.2f} MB")
        print(f"  Assets:    {', '.join(latest_release.assets)}")

        # Check if we need to download
        if not args.force and sync_manager._is_local_up_to_date(latest_release):
            print("\n[OK] Local databases are already up-to-date")
            print(f"  Location: {sync_manager.local_db_dir}")
            return

        # Download databases
        print(f"\nDownloading to {sync_manager.local_db_dir}...")
        success = sync_manager.download_databases(
            snapshot=latest_release, force=args.force
        )

        if success:
            print("\n[OK] Databases downloaded successfully")
            print(f"  Location: {sync_manager.local_db_dir}")
        else:
            print("\n[ERROR] Failed to download databases")
            print("  Check logs for details")
            sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] Error downloading databases: {e}")
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
        print("\n[ERROR] GitHub sync not configured")
        print("  Check config.yaml for github_owner and github_repo settings")
        sys.exit(1)

    print(f"\nRepository: {sync_manager.repo_owner}/{sync_manager.repo_name}")
    print(f"GitHub Token: {'[OK] Set' if sync_manager.github_token else '[ERROR] Not set'}")

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
            print("\n[WARNING] No releases found on GitHub")

    except Exception as e:
        print(f"\n[ERROR] Error fetching GitHub releases: {e}")

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
        auto_sync = get_config("database.sync.auto_sync_on_import", False)

        print(f"\nSync Configuration:")
        print(f"  Auto-sync on import: {auto_sync}")

    except Exception:
        pass


def cmd_database_restore(parser: argparse.ArgumentParser, remaining_args: list) -> None:
    """
    Restore project databases from latest timestamped backups.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser for the restore subcommand
    remaining_args : list
        Remaining command line arguments
    """
    args = parser.parse_args(remaining_args)

    from pathlib import Path
    from datetime import datetime
    import shutil

    from ..database.connection import get_database_path

    def find_latest_backup(db_path: Path) -> Path:
        db_dir = db_path.parent
        pattern = f"{db_path.name}."  # prefix before timestamp
        candidates = []
        for p in db_dir.glob(f"{db_path.name}.*.bak"):
            name = p.name
            if name.startswith(pattern) and name.endswith(".bak"):
                # Extract timestamp between last '.' and '.bak'
                ts_str = name[len(pattern) : -4]
                try:
                    ts = datetime.strptime(ts_str, "%Y%m%d-%H%M%S")
                    candidates.append((ts, p))
                except ValueError:
                    continue
        if not candidates:
            return Path()
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def restore(db_name: str) -> None:
        target = Path(get_database_path(db_name))
        latest = find_latest_backup(target)
        if not latest.exists():
            print(f"[WARNING] No backups found for {db_name} in {target.parent}")
            return

        # Backup current file before restore
        try:
            if target.exists():
                ts_now = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                pre_backup = target.with_name(f"{target.name}.pre-restore-{ts_now}.bak")
                shutil.copy2(str(target), str(pre_backup))
                print(f"  Current backup saved: {pre_backup}")
        except Exception as be:
            print(f"  [WARNING] Failed to backup current {db_name}: {be}")

        # Restore latest backup
        try:
            shutil.copy2(str(latest), str(target))
            size_mb = target.stat().st_size / (1024 * 1024)
            print(f"[OK] Restored {db_name} from {latest.name} ({size_mb:.2f} MB)")
        except Exception as e:
            print(f"[ERROR] Failed to restore {db_name}: {e}")

    # Determine which DBs to restore
    restore_parts = args.parts or (not args.parts and not args.assembled)
    restore_assembled = args.assembled or (not args.parts and not args.assembled)

    print("Restoring databases from latest backups...")
    print("=" * 50)

    if restore_parts:
        restore("parts.db")
    if restore_assembled:
        restore("assembled_casm.db")

    print("\nRestore operation completed")
