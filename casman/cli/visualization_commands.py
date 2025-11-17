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
  casman visualize web                 # Launch web-based visualization interface
  casman visualize web --port 8080     # Launch web interface on specific port
        """,
    )

    subparsers = parser.add_subparsers(dest="action", help="Visualization actions")

    # Enhanced chains command
    subparsers.add_parser(
        "chains",
        help="Display ASCII visualization of assembly chains with duplicate detection")

    # Web visualization command
    web_parser = subparsers.add_parser("web", help="Launch web-based visualization interface")
    web_parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run web server on (default: 5000)")
    web_parser.add_argument(
        "--max-tries",
        type=int,
        default=10,
        help="Maximum number of ports to try if default is busy (default: 10)")

    # Parse arguments
    if len(sys.argv) < 3:
        parser.print_help()
        return

    # Check if help is requested or no arguments provided
    if len(sys.argv) <= 2 or (len(sys.argv) == 3 and sys.argv[2] in ['-h', '--help']):
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
        elif args.action == "web":
            cmd_visualize_web(args)
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


def cmd_visualize_web(args) -> None:
    """Launch web-based visualization interface."""
    import os
    import subprocess

    try:
        # Get path to web_app.py script
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        web_app_script = os.path.join(script_dir, "scripts", "web_app.py")

        if not os.path.exists(web_app_script):
            print(f"❌ Error: Web app script not found at {web_app_script}")
            sys.exit(1)

        print("📊 Starting CAsMan Web Visualization")
        print("=" * 50)
        print(f"📱 Server running at: http://localhost:{args.port}")
        print("🌐 Access from other devices: http://<your-ip>:" + str(args.port))
        print("⚠️  Press Ctrl+C to stop the server")
        print("=" * 50)
        print()

        # Build command for visualization-only mode
        cmd = [
            sys.executable,
            web_app_script,
            "--mode", "dev",
            "--host", "0.0.0.0",
            "--port", str(args.port),
            "--visualize-only"
        ]
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n\n⚠️  Visualization stopped by user")
        sys.exit(0)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
