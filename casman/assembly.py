"""
Assembly and scanning utilities for CAsMan.

This module provides functions for scanning parts and managing assembly connections.
All functionality has been modularized into the assembly/ subpackage for better
organization, but this module maintains backward compatibility.
"""

# Import all functions from the modularized assembly package
from .assembly import *


def main() -> None:
    """
    Main function for command-line usage.

    Provides a menu-driven interface for assembly management operations
    including scanning parts, viewing chains, and getting statistics.

    Returns
    -------
    None
    """
    print("Assembly Management")
    print("=" * 20)
    print("1. Interactive scanning")
    print("2. View assembly chains")
    print("3. View assembly statistics")
    print("4. Quit")

    while True:
        try:
            choice = input("\nSelect option (1-4): ").strip()

            if choice == "1":
                scan_and_assemble_interactive()
            elif choice == "2":
                print_assembly_chains()
            elif choice == "3":
                stats = get_assembly_stats()
                print("\nAssembly Statistics:")
                print(f"Total scans: {stats['total_scans']}")
                print(f"Unique parts: {stats['unique_parts']}")
                print(f"Connected parts: {stats['connected_parts']}")
                print(f"Latest scan: {stats['latest_scan'] or 'None'}")
            elif choice == "4" or choice.lower() == "quit":
                print("Goodbye!")
                break
            else:
                print("Invalid option. Please select 1-4.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
