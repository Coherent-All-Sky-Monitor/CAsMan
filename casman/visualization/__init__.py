"""
Visualization package for CAsMan.

This package provides basic visualization capabilities including:
- ASCII chain displays
- Basic statistics and summaries

The package focuses on core functionality for assembly visualization.
"""

# Import core visualization functions
from .core import (
    format_ascii_chains,
    get_chain_summary,
    get_visualization_data,
    print_visualization_summary,
    main as cli_main,
)

__all__ = [
    # Core functions
    "format_ascii_chains",
    "get_chain_summary",
    "get_visualization_data",
    "print_visualization_summary",
    "cli_main",
]


def main() -> None:
    """Main entry point for visualization package."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        print("Web visualization not available. Use standalone scripts instead.")
    else:
        print("CAsMan Visualization Tools")
        print("=" * 30)
        print("1. Command-line visualization")

        try:
            choice = input("Select option (1): ").strip()

            if choice == "1" or not choice:
                cli_main()
            else:
                print("Invalid option.")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")


if __name__ == "__main__":
    main()
