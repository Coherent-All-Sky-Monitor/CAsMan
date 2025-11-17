"""
CAsMan CLI command handlers.

This module provides the command-line interface functionality organized into
focused submodules for different command categories.
"""

from .assembly_commands import cmd_scan
from .barcode_commands import cmd_barcode
from .main import main
from .parts_commands import cmd_parts
from .utils import (
    show_commands_list,
    show_completion_help,
    show_help_with_completion,
    show_unknown_command_error,
    show_version,
)
from .visualization_commands import cmd_visualize

# Import functions that tests still expect to be available

from casman.barcode import generate_barcode_printpages
from casman.database.operations import get_parts_by_criteria
from casman.parts.interactive import add_parts_interactive
from casman.visualization.core import format_ascii_chains


__all__ = [
    "main",
    "cmd_parts",
    "cmd_scan",
    "cmd_barcode",
    "cmd_visualize",
    "show_completion_help",
    "show_version",
    "show_commands_list",
    "show_help_with_completion",
    "show_unknown_command_error",
    # Functions that tests expect
    "add_parts_interactive",
    "get_parts_by_criteria",

    "format_ascii_chains",
    "generate_barcode_printpages",
]
