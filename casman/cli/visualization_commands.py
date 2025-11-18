"""
Visualization commands for CAsMan CLI.

Provides basic visualization functionality including ASCII chains and summaries.
"""

import argparse
import sys


def cmd_visualize() -> None:
    """
    Command-line interface for visualization.

    Provides functionality for ASCII chains and basic summaries.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="CAsMan Assembly Chain Visualization Tools\n\n"
        "Advanced visualization capabilities including ASCII chain display,\n"
        "web-based interactive interface, duplicate detection, connection\n"
        "statistics, and comprehensive assembly analysis with timestamps\n"
        "and validation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  casman visualize chains              # Show ASCII chains with duplicate detection

For web-based visualization, use:
  casman web --visualize-only          # Launch web visualization interface
  casman web --visualize-only --port 8080  # Custom port
        """,
    )

    subparsers = parser.add_subparsers(dest="action", help="Visualization actions")

    # Enhanced chains command
    subparsers.add_parser(
        "chains",
        help="Display ASCII visualization of assembly chains with duplicate detection",
    )

    # Parse arguments
    if len(sys.argv) < 3:
        parser.print_help()
        return

    # Check if help is requested or no arguments provided
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ["-h", "--help"]):
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman visualize'

    if not args.action:
        parser.print_help()
        return

    try:
        from casman.database.initialization import init_all_databases

        init_all_databases()

        if args.action == "chains":
            cmd_visualize_chains()
        else:
            parser.print_help()

    except ImportError as e:
        print(f"Visualization functionality not available: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_visualize_chains() -> None:
    """Show ASCII visualization chains."""
    try:
        from casman.visualization.core import format_ascii_chains

        print(format_ascii_chains())
    except ImportError:
        print("Visualization functionality not available")
