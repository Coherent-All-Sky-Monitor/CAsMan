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
        "Provides safe database clearing, formatted content display, and\n"
        "interactive scanning workflows with validation.\n\n"
        "Subcommands:\n"
        "  clear   - Safely clear database contents with confirmations\n"
        "  print   - Display formatted database tables and records\n\n"
        "Examples:\n"
        "  casman database clear --parts     # Clear only parts database\n"
        "  casman database clear --assembled # Clear only assembly database\n"
        "  casman database print             # Show assembly database contents\n\n"
        "Safety Features:\n"
        "- Double confirmation for destructive operations\n"
        "- Visual warnings for database clearing\n"
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
