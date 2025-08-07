"""
Visualization utilities for CAsMan.

This module provides functions for visualizing assembly connections and chains.
All functionality is available from the visualization.core module for better
organization, but this module maintains backward compatibility.
"""

# Import specific functions for backward compatibility
from casman.visualization.core import (
    format_ascii_chains,
    get_chain_summary,
    get_visualization_data,
    print_visualization_summary,
    main as core_main
)

# Re-export functions at module level
__all__ = [
    "format_ascii_chains",
    "get_chain_summary",
    "get_visualization_data",
    "print_visualization_summary",
    "main"
]


def main() -> None:
    """Main function for command-line usage."""
    core_main()


if __name__ == "__main__":
    main()
