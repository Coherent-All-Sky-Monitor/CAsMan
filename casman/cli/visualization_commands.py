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
  casman visualize summary             # Show detailed summary statistics
  casman visualize web                 # Launch web-based visualization interface
  casman visualize web --port 8080     # Launch web interface on specific port
        """,
    )

    subparsers = parser.add_subparsers(dest="action", help="Visualization actions")

    # Enhanced chains command
    subparsers.add_parser("chains", help="Display ASCII visualization of assembly chains with duplicate detection")

    # Enhanced summary command
    subparsers.add_parser("summary", help="Show comprehensive assembly statistics and chain analysis")

    # Web visualization command
    web_parser = subparsers.add_parser("web", help="Launch web-based visualization interface")
    web_parser.add_argument("--port", type=int, default=5000, help="Port to run web server on (default: 5000)")
    web_parser.add_argument("--max-tries", type=int, default=10, help="Maximum number of ports to try if default is busy (default: 10)")

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
        elif args.action == "summary":
            cmd_visualize_summary()
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


def cmd_visualize_summary() -> None:
    """Show visualization summary."""
    try:
        from casman.visualization.core import print_visualization_summary

        print_visualization_summary()
    except ImportError:
        print("Visualization functionality not available")


def cmd_visualize_web(args) -> None:
    """Launch web-based visualization interface."""
    import os

    try:
        # Import Flask to check if it's available
        import flask  # noqa: F401

        print("🌐 Starting CAsMan web visualization interface...")
        print(f"🚀 Looking for available port starting from {args.port}")
        print("🛑 Press Ctrl+C to stop the server")
        print()

        # Get the path to the web visualization script
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        web_script_path = os.path.join(script_dir, "scripts", "visualize_analog_chains_web.py")

        if not os.path.exists(web_script_path):
            print(f"❌ Error: Web visualization script not found at {web_script_path}")
            sys.exit(1)

        # Import and run the web application
        sys.path.insert(0, os.path.dirname(web_script_path))

        # Import the necessary functions from the web script
        spec = __import__('importlib.util').util.spec_from_file_location("web_viz", web_script_path)
        web_module = __import__('importlib.util').util.module_from_spec(spec)
        spec.loader.exec_module(web_module)

        # Set up the Flask app with custom port configuration
        web_module.run_flask_with_free_port(web_module.app, start_port=args.port, max_tries=args.max_tries)

    except ImportError as e:
        if "flask" in str(e).lower():
            print("❌ Flask is required for web visualization")
            print("💡 Install with: pip install flask")
        else:
            print(f"❌ Web visualization not available: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Web server stopped by user")
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"❌ Network error: {e}")
        sys.exit(1)
