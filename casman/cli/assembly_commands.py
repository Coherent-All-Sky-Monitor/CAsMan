"""
Assembly-related CLI commands for CAsMan.
"""

import argparse
import sys

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
        "  connection     - Start interactive connection scanning with validation\n"
        "  disconnection  - Start interactive disconnection scanning\n"
        "  connect        - Full interactive part scanning and assembly operations\n"
        "  disconnect     - Full interactive part disconnection operations\n"
        "  web            - Launch web-based scanner interface (port 5001)\n\n"
        "The 'connect' and 'disconnect' actions provide complete workflows with:\n"
        "• USB barcode scanner support\n"
        "• Manual part number entry\n"
        "• Real-time part validation\n"
        "• Connection/disconnection tracking and SNAP/FENG mapping",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "action",
        choices=["connection", "disconnection", "connect", "disconnect", "web"],
        help="Action to perform:\n"
             "  connection     - Start interactive connection scanning with validation\n"
             "  disconnection  - Start interactive disconnection scanning\n"
             "  connect        - Full interactive part scanning and assembly operations\n"
             "  disconnect     - Full interactive part disconnection operations\n"
             "  web            - Launch web-based scanner interface"
    )

    # Check if help is requested or no arguments provided
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ['-h', '--help']):
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman scan'

    init_all_databases()

    if args.action == "connection":
        # Launch interactive connection scanner
        scan_and_assemble_interactive()
    elif args.action == "disconnection":
        # Launch interactive disconnection scanner
        from casman.assembly.interactive import scan_and_disassemble_interactive
        scan_and_disassemble_interactive()
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
            script_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'scripts',
                'scan_and_assemble.py')
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
    elif args.action == "disconnect":
        # Launch full disconnection workflow
        print("🔧 Starting Interactive Disconnection")
        print("=" * 50)
        print("Features available:")
        print("• USB barcode scanner support")
        print("• Manual part number entry")
        print("• Real-time validation")
        print("• Disconnection tracking")
        print("• SNAP/FENG support")
        print()

        # Import and run the disconnection script
        import subprocess
        import os

        try:
            script_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'scripts',
                'scan_and_disassemble.py')
            result = subprocess.run([sys.executable, script_path], check=False)
            if result.returncode != 0:
                print(f"❌ Disconnection process exited with code {result.returncode}")
                sys.exit(result.returncode)
        except KeyboardInterrupt:
            print("\n\n⚠️  Disconnection interrupted by user")
            sys.exit(0)
        except (OSError, subprocess.SubprocessError) as e:
            print(f"\n❌ Error during disconnection: {e}")
            sys.exit(1)
    elif args.action == "web":
        # Launch web scanner interface
        import subprocess
        import os

        # Get path to web_app.py script
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        web_app_script = os.path.join(script_dir, "scripts", "web_app.py")

        if not os.path.exists(web_app_script):
            print(f"❌ Error: Web app script not found at {web_app_script}")
            sys.exit(1)

        print("🔍 Starting CAsMan Web Scanner")
        print("=" * 50)
        print(f"📱 Server running at: http://localhost:5001")
        print("🌐 Access from other devices: http://<your-ip>:5001")
        print("⚠️  Press Ctrl+C to stop the server")
        print("=" * 50)
        print()

        try:
            # Build command for scanner-only mode
            cmd = [
                sys.executable,
                web_app_script,
                "--mode", "dev",
                "--host", "0.0.0.0",
                "--port", "5001",
                "--scanner-only"
            ]
            subprocess.run(cmd, check=False)
        except KeyboardInterrupt:
            print("\n\n⚠️  Scanner stopped by user")
            sys.exit(0)
        except (OSError, subprocess.SubprocessError) as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
