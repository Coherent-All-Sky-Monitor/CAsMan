"""
CLI utilities for CAsMan.
"""

import sys

# Color utilities
try:
    from colorama import Fore, Style
    from colorama import init as colorama_init

    colorama_init()
    COLOR_ERROR = Fore.RED + Style.BRIGHT
    COLOR_RESET = Style.RESET_ALL
except ImportError:
    COLOR_ERROR = ""
    COLOR_RESET = ""


def show_completion_help() -> None:
    """Show shell completion setup instructions."""
    print("To enable shell completion, run:")
    print('  eval "$(register-python-argcomplete casman)"')
    print("Or for global setup, see argcomplete docs.")
    sys.exit(0)


def show_version() -> None:
    """Show version information."""
    print("CAsMan version 1.0.0")
    sys.exit(0)


def show_commands_list(commands: dict) -> None:
    """Show list of available commands."""
    print("Available commands:")
    for cmd, desc in commands.items():
        print(f"  {cmd:<10} {desc}")
    sys.exit(0)


def show_help_with_completion(parser) -> None:
    """Show help message with completion hint."""
    parser.print_help()
    print("\nFor shell completion, run: casman completion")
    sys.exit(1)


def show_unknown_command_error(command: str, parser) -> None:
    """Show error for unknown command."""
    print(f"{COLOR_ERROR}Unknown command: {command}{COLOR_RESET}")
    parser.print_help()
    sys.exit(1)
