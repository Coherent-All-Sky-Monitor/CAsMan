"""
Scanner CLI commands for CAsMan.

This module provides CLI commands for launching the web-based scanner interface.
"""

import argparse
import sys


def cmd_scanner() -> None:
    """
    Command-line interface for launching the web scanner.

    Provides functionality for starting the web-based scanner interface
    for connecting and disconnecting parts.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="CAsMan Web Scanner Interface\n\n"
        "Launch a web-based interface for scanning and managing part connections.\n\n"
        "Features:\n"
        "• Barcode reader support (HID mode)\n"
        "• Camera-based barcode scanning\n"
        "• Manual part entry\n"
        "• Connect and disconnect workflows\n"
        "• Real-time validation\n"
        "• Connection history tracking\n\n"
        "Access the interface at http://localhost:5001 after starting.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Port to run the web server on (default: 5001)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    # Check if help is requested
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ['-h', '--help']):
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman scanner'

    # Use the unified web app in scanner-only mode
    import os
    import subprocess

    # Get path to web_app.py script
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    web_app_script = os.path.join(script_dir, "scripts", "web_app.py")

    if not os.path.exists(web_app_script):
        print(f"❌ Error: Web app script not found at {web_app_script}")
        sys.exit(1)

    print("🔍 Starting CAsMan Web Scanner")
    print("=" * 50)
    print(f"📱 Server running at: http://localhost:{args.port}")
    print("🌐 Access from other devices: http://<your-ip>:" + str(args.port))
    print("⚠️  Press Ctrl+C to stop the server")
    print("=" * 50)
    print()

    try:
        # Build command for scanner-only mode
        cmd = [
            sys.executable,
            web_app_script,
            "--mode", "dev",
            "--host", args.host,
            "--port", str(args.port),
            "--scanner-only"
        ]
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n\n⚠️  Scanner stopped by user")
        sys.exit(0)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
