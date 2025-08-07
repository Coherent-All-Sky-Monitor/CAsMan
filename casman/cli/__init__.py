"""
CAsMan CLI command handlers.

This module provides the command-line interface functionality organized into
focused submodules for different command categories.
"""

from .assembly_commands import cmd_assemble, cmd_scan
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
try:
    from casman.assembly import get_assembly_stats
    from casman.barcode_utils import generate_barcode_printpages
    from casman.database import get_parts_by_criteria
    from casman.parts import add_parts_interactive
    from casman.visualization import format_ascii_chains
except ImportError:
    # Fallback definitions if modules aren't available
    def add_parts_interactive() -> None:
        """Fallback function."""
        pass

    def get_parts_by_criteria(part_type=None, polarization=None) -> list:
        """Fallback function."""
        return []

    def get_assembly_stats() -> dict:
        """Fallback function."""
        return {}

    def format_ascii_chains() -> str:
        """Fallback function."""
        return ""

    def generate_barcode_printpages(*args) -> None:
        """Fallback function."""
        pass


__all__ = [
    "main",
    "cmd_parts",
    "cmd_scan",
    "cmd_assemble",
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
    "get_assembly_stats",
    "format_ascii_chains",
    "generate_barcode_printpages",
]
