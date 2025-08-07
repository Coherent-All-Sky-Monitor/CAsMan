#!/usr/bin/env python3
"""
Database Directory Configuration Demo for CAsMan Scripts.

This script demonstrates how the updated CAsMan scripts can now work with
custom database directories or automatically find the project's database directory.

Key Features:
1. Automatic project root detection
2. Custom database directory support
3. Backward compatibility with existing behavior

Usage Examples:
- Default behavior: Scripts automatically find project root database directory
- Custom database: Pass db_dir parameter to casman functions
"""

import os
import tempfile

from casman.database import (
    check_part_in_db,
    find_project_root,
    get_database_path,
    init_all_databases,
)
from casman.parts import generate_part_numbers


def demo_automatic_detection() -> None:
    """Demonstrate automatic project root and database detection."""
    print("=== Automatic Database Detection ===")

    # Show automatic project root detection
    project_root = find_project_root()
    print(f"Detected project root: {project_root}")

    # Show automatic database path resolution
    parts_db_path = get_database_path("parts.db")
    assembly_db_path = get_database_path("assembled_casm.db")
    print(f"Parts database path: {parts_db_path}")
    print(f"Assembly database path: {assembly_db_path}")

    # Check if databases exist
    print(f"Parts DB exists: {os.path.exists(parts_db_path)}")
    print(f"Assembly DB exists: {os.path.exists(assembly_db_path)}")
    print()


def demo_custom_database_directory() -> None:
    """Demonstrate using a custom database directory."""
    print("=== Custom Database Directory ===")

    # Create a temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_db_dir = os.path.join(temp_dir, "custom_casman_db")
        print(f"Using custom database directory: {custom_db_dir}")

        # Initialize databases in custom directory
        print("Initializing databases in custom directory...")
        init_all_databases(db_dir=custom_db_dir)

        # Show the created database files
        parts_db_path = get_database_path("parts.db", custom_db_dir)
        assembly_db_path = get_database_path("assembled_casm.db", custom_db_dir)
        print(f"Custom parts DB: {parts_db_path}")
        print(f"Custom assembly DB: {assembly_db_path}")
        print(f"Parts DB exists: {os.path.exists(parts_db_path)}")
        print(f"Assembly DB exists: {os.path.exists(assembly_db_path)}")

        # Generate some sample parts in the custom database
        print("\nGenerating sample parts in custom database...")
        try:
            sample_parts = generate_part_numbers(
                "ANTENNA", 3, "1", db_dir=custom_db_dir
            )
            print(f"Generated parts: {sample_parts}")

            # Check if a part exists in the custom database
            if sample_parts:
                exists, polarization = check_part_in_db(
                    sample_parts[0], "ANTENNA", db_dir=custom_db_dir
                )
                print(
                    f"Part {sample_parts[0]} exists in custom DB: {exists}, \
                        polarization: {polarization}"
                )

        except (ValueError, OSError) as e:
            print(f"Error generating parts: {e}")

    print("Custom database directory demo completed (temp files cleaned up)")
    print()


def demo_script_usage() -> None:
    """Show how scripts can be used with different database configurations."""
    print("=== Script Usage Examples ===")

    print("1. Default usage (automatic database detection):")
    print("   python scripts/scan_and_assemble.py")
    print("   # Uses project's database/ directory automatically")
    print()

    print("2. Scripts work from any directory now:")
    print("   cd /any/directory")
    print("   python /path/to/casman/scripts/scan_and_assemble.py")
    print("   # Still finds the correct database directory")
    print()

    print("3. Programmatic usage with custom database:")
    print("   from casman.assembly import scan_part")
    print("   scan_part('ANTP1-00001', 'LNAP1-00001', db_dir='/custom/path')")
    print()

    print("4. All casman functions now accept optional db_dir parameter:")
    print("   - init_all_databases(db_dir='/custom/path')")
    print("   - generate_part_numbers('ANTENNA', 5, '1', db_dir='/custom/path')")
    print("   - scan_part('part1', 'part2', db_dir='/custom/path')")
    print("   - check_part_in_db('ANTP1-00001', 'ANTENNA', db_dir='/custom/path')")
    print()


def main() -> None:
    """Main demonstration function."""
    print("CAsMan Database Directory Configuration Demo")
    print("=" * 50)
    print()

    demo_automatic_detection()
    demo_custom_database_directory()
    demo_script_usage()

    print("=== Summary ===")
    print("✅ Scripts now automatically find the project database directory")
    print("✅ Scripts work from any directory (not just project root)")
    print("✅ All casman functions accept optional db_dir parameter")
    print("✅ Backward compatibility maintained")
    print("✅ Custom database directories supported")
    print()
    print("The scripts in scripts/ directory now work reliably regardless of")
    print("where they are executed from, while still supporting custom database")
    print("directories when needed.")


if __name__ == "__main__":
    main()
