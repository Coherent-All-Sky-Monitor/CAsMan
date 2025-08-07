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
        description='CAsMan Visualization Tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  casman visualize chains              # Show ASCII chains
  casman visualize summary             # Show summary statistics
        """
    )

    subparsers = parser.add_subparsers(dest='action', help='Visualization actions')

    # Legacy chains command
    subparsers.add_parser('chains', help='Show ASCII visualization chains')

    # Summary command
    subparsers.add_parser('summary', help='Show visualization summary')

    # Parse arguments
    if len(sys.argv) < 3:
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman visualize'

    if not args.action:
        parser.print_help()
        return

    try:
        from casman.database import init_all_databases
        init_all_databases()

        if args.action == 'chains':
            cmd_visualize_chains()
        elif args.action == 'summary':
            cmd_visualize_summary()
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
        from casman.visualization import format_ascii_chains
        print(format_ascii_chains())
    except ImportError:
        print("Visualization functionality not available")


def cmd_visualize_summary() -> None:
    """Show visualization summary."""
    try:
        from casman.visualization import print_visualization_summary
        print_visualization_summary()
    except ImportError:
        print("Visualization functionality not available")
