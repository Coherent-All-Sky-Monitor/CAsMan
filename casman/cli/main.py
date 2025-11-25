"""
Main CLI entry point for CAsMan.

This module provides the main function that routes commands to appropriate
sub-command handlers.
"""

import argparse
import sys

import argcomplete

from .assembly_commands import cmd_scan
from .barcode_commands import cmd_barcode
from .database_commands import cmd_database
from .parts_commands import cmd_parts
from .utils import (
    show_commands_list,
    show_completion_help,
    show_help_with_completion,
    show_unknown_command_error,
    show_version,
)
from .visualization_commands import cmd_visualize
from .web_commands import cmd_web


def main() -> None:
    """
    Main command-line interface.

    Entry point for the CAsMan command-line application. Routes commands to
    appropriate sub-command handlers.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="CAsMan - CASM Assembly Manager\n\n"
        "A comprehensive toolkit for managing CASM assembly processes with connection validation,\n"
        "part tracking, barcode generation, and interactive visualization.\n\n"
        "Features: Interactive scanning, connection validation, duplicate detection,\n"
        "ASCII/web visualization, and comprehensive part management.\n\n"
        "Available Commands:\n"
        "  parts      - Manage parts in the database (list, add, search, validate)\n"
        "  scan       - Interactive scanning and assembly with real-time validation\n"
        "    └─ connection     Start interactive connection scanning with validation\n"
        "    └─ disconnection  Start interactive disconnection scanning\n"
        "    └─ connect        Full interactive part scanning and assembly operations\n"
        "    └─ disconnect     Full interactive part disconnection operations\n"
        "  database   - Database management operations (clear, print)\n"
        "    └─ clear       Safely clear database contents with confirmations\n"
        "    └─ print       Display formatted database tables and records\n"
        "  visualize  - Visualize assembly chains and connection statistics\n"
        "    └─ chains      Display ASCII visualization with duplicate detection\n"
        "  web        - Launch unified web application (scanner + visualization)\n"
        "    └─ --mode dev|production   Development (Flask) or production (Gunicorn) server\n"
        "    └─ --scanner-only          Enable only scanner interface\n"
        "    └─ --visualize-only        Enable only visualization interface\n"
        "    └─ --port <port>           Custom port (default: 5000 dev, 8000 prod)\n"
        "    └─ --workers <n>           Number of Gunicorn workers (production mode)\n"
        "  barcode    - Generate barcodes and printable pages for part identification\n"
        "    └─ printpages  Generate printable barcode pages for labeling\n"
        "  completion - Show shell completion setup instructions\n\n"
        "Use 'casman <command> --help' for detailed help on any command.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", help="Command to run")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--list-commands", action="store_true", help="List all available commands"
    )
    argcomplete.autocomplete(parser)

    commands = {
        "parts": "Manage parts in the database - list, add, search, and validate parts",
        "scan": "Interactive scanning and assembly with real-time validation",
        "database": "Database management operations - clear and print databases",
        "visualize": "Visualize assembly chains and connection statistics with duplicate detection",
        "web": "Launch unified web application - scanner and/or visualization (dev/production modes)",
        "barcode": "Generate barcodes and printable pages for part identification",
        "completion": "Show shell completion setup instructions for enhanced CLI experience",
    }

    # Check if a command with help is requested before full parsing
    if len(sys.argv) >= 3 and (
        sys.argv[2] in ["-h", "--help"]
        or (len(sys.argv) >= 4 and sys.argv[3] in ["-h", "--help"])
    ):
        command = sys.argv[1]
        if command == "parts":
            cmd_parts()
        elif command == "scan":
            cmd_scan()
        elif command == "database":
            cmd_database()
        elif command == "visualize":
            cmd_visualize()
        elif command == "web":
            cmd_web()
        elif command == "barcode":
            cmd_barcode()
        elif command == "completion":
            show_completion_help()
        else:
            # Let main parser handle unknown commands
            args, _ = parser.parse_known_args()
            show_unknown_command_error(command, parser)
        return

    args, remaining_args = parser.parse_known_args()

    # If help is requested for a specific command, let the command handle it
    if (
        len(remaining_args) > 0
        and remaining_args[0] in ["-h", "--help"]
        and args.command
    ):
        command = args.command
        if command == "parts":
            cmd_parts()
        elif command == "scan":
            cmd_scan()
        elif command == "database":
            cmd_database()
        elif command == "visualize":
            cmd_visualize()
        elif command == "web":
            cmd_web()
        elif command == "barcode":
            cmd_barcode()
        elif command == "completion":
            show_completion_help()
        else:
            show_unknown_command_error(command, parser)
        return

    args, _ = parser.parse_known_args()

    if args.version:
        show_version()

    if args.list_commands:
        show_commands_list(commands)

    if args.command is None:
        show_help_with_completion(parser)

    command = args.command

    if command == "parts":
        cmd_parts()
    elif command == "scan":
        cmd_scan()
    elif command == "database":
        cmd_database()
    elif command == "visualize":
        cmd_visualize()
    elif command == "web":
        cmd_web()
    elif command == "barcode":
        cmd_barcode()
    elif command == "completion":
        show_completion_help()
    else:
        show_unknown_command_error(command, parser)
