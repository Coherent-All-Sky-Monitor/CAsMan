"""
Assembly management functionality for CAsMan.

This module provides functionality for recording and retrieving assembly connections,
building connection chains, and interactive assembly scanning.
"""

# Import logger for backward compatibility with tests
import logging

from .chains import build_connection_chains, print_assembly_chains

# Import all functions from submodules
from .connections import record_assembly_connection
from .data import get_assembly_connections, get_assembly_stats
from .interactive import scan_and_assemble_interactive

# Create logger for backward compatibility with tests
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the casman-scan command.

    Launches the interactive assembly scanner.
    """
    import sys

    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print("casman-scan: Interactive Assembly Scanner")
        print()
        print("Usage: casman-scan")
        print()
        print("Description:")
        print("  Launches an interactive command-line interface for scanning")
        print("  and recording assembly connections between parts.")
        print()
        print("  The scanner will:")
        print("  1. Validate each part against the parts database")
        print("  2. Prompt for the first part number")
        print("  3. Prompt for the connected part number")
        print("  4. Record the connection with timestamp")
        print("  5. Display the connection as: PART1 --> PART2")
        print()
        print("  Features:")
        print("  • Part validation: Ensures parts exist in database")
        print("    - Regular parts: Validated against parts.db")
        print("    - SNAP parts: Validated against snap_feng_map.yaml")
        print("  • Connection format: Shows A --> B connections")
        print("  • Error handling: Clear error messages for invalid parts")
        print("  • Database recording: Stores connections with timestamps")
        print()
        print("  Type 'quit' at any prompt to exit.")
        print()
        print("Examples:")
        print("  casman-scan           Start interactive scanner")
        print("  casman-scan --help    Show this help message")
        return

    # Launch interactive scanner
    scan_and_assemble_interactive()


__all__ = [
    "record_assembly_connection",
    "get_assembly_connections",
    "get_assembly_stats",
    "build_connection_chains",
    "print_assembly_chains",
    "scan_and_assemble_interactive",
    "main",
    "logger",  # Export logger for test compatibility
]
