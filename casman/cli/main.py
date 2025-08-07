"""
Main CLI entry point for CAsMan.

This module provides the main function that routes commands to appropriate
sub-command handlers.
"""

import argparse

import argcomplete

from .assembly_commands import cmd_assemble, cmd_scan
from .barcode_commands import cmd_barcode
from .parts_commands import cmd_parts
from .utils import (
    show_commands_list,
    show_completion_help,
    show_help_with_completion,
    show_unknown_command_error,
    show_version,
)
from .visualization_commands import cmd_visualize


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
    parser = argparse.ArgumentParser(description="CAsMan - CASM Assembly Manager")
    parser.add_argument("command", nargs="?", help="Command to run")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--list-commands", action="store_true", help="List all available commands"
    )
    argcomplete.autocomplete(parser)

    commands = {
        "parts": "Manage parts in the database",
        "scan": "Scan and manage parts using barcode scanning",
        "visualize": "Visualize assembly chains",
        "barcode": "Generate barcodes and printable pages",
        "assemble": "Record assembly connections (streamlined)",
        "completion": "Show shell completion instructions",
    }

    args, unknown_args = parser.parse_known_args()

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
    elif command == "visualize":
        cmd_visualize()
    elif command == "barcode":
        cmd_barcode()
    elif command == "assemble":
        cmd_assemble()
    elif command == "completion":
        show_completion_help()
    else:
        show_unknown_command_error(command, parser)
