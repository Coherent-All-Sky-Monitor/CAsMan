"""
Assembly-related CLI commands for CAsMan.
"""

import argparse
import sys

from casman.assembly.data import get_assembly_stats
from casman.assembly.interactive import scan_and_assemble_interactive
from casman.database.initialization import init_all_databases


def cmd_scan() -> None:
    """
    Command-line interface for scanning and assembly.

    Provides functionality for interactive scanning and assembly statistics.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="CAsMan Interactive Scanning and Assembly Management\n\n"
                   "Provides interactive scanning capabilities with "
                   "comprehensive connection validation.\n"
                   "Features real-time part validation, sequence enforcement, "
                   "duplicate prevention, and full assembly workflows.\n\n"
                   "Available Actions:\n"
                   "  stats      - Display assembly statistics and connection counts\n"
                   "  connection - Start interactive connection scanning with validation\n"
                   "  connect    - Full interactive part scanning and assembly operations\n\n"
                   "The 'connect' action provides the complete scanning workflow with:\n"
                   "• USB barcode scanner support\n"
                   "• Manual part number entry\n"
                   "• Real-time part validation\n"
                   "• Connection tracking and SNAP/FENG mapping",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "action",
        choices=["stats", "connection", "connect"],
        help="Action to perform:\n"
             "  stats      - Display assembly statistics and connection counts\n"
             "  connection - Start interactive connection scanning with validation\n"
             "  connect    - Interactive part scanning and assembly operations"
    )

    # Check if help is requested or no arguments provided
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ['-h', '--help']):
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman scan'

    init_all_databases()

    if args.action == "stats":
        stats = get_assembly_stats()
        if stats:
            print("Assembly Statistics:")
            print(f"Total scans: {stats['total_scans']}")
            print(f"Unique parts: {stats['unique_parts']}")
            print(f"Connected parts: {stats['connected_parts']}")
            print(f"Latest scan: {stats['latest_scan'] or 'None'}")
        else:
            print("No assembly statistics available.")
    elif args.action == "connection":
        # Launch interactive connection scanner
        scan_and_assemble_interactive()
    elif args.action == "connect":
        # Launch full scanning and assembly workflow
        print("🔍 Starting Interactive Scanning and Assembly")
        print("=" * 50)
        print("Features available:")
        print("• USB barcode scanner support")
        print("• Manual part number entry")
        print("• Real-time validation")
        print("• Connection tracking")
        print("• SNAP/FENG mapping")
        print()
        
        # Import and run the scan script
        import subprocess
        import os
        
        try:
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'scan_and_assemble.py')
            result = subprocess.run([sys.executable, script_path], check=False)
            if result.returncode != 0:
                print(f"❌ Scanning process exited with code {result.returncode}")
                sys.exit(result.returncode)
        except KeyboardInterrupt:
            print("\n\n⚠️  Scanning interrupted by user")
            sys.exit(0)
        except (OSError, subprocess.SubprocessError) as e:
            print(f"\n❌ Error during scanning: {e}")
            sys.exit(1)
