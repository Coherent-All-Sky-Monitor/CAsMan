"""
Web application commands for CAsMan CLI.

Provides commands to run the unified web application.
"""

import argparse
import sys


def cmd_web() -> None:
    """
    Command-line interface for unified web application.

    Launches the web application with configuration options for enabling
    scanner and/or visualization interfaces.

    Parameters
    ----------
    None
        Uses sys.argv for command-line argument parsing.

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        description="CAsMan Unified Web Application\n\n"
        "Launch a web interface serving the scanner and/or visualization tools.\n"
        "The scanner interface is used for commissioning and repairs.\n"
        "The visualization interface displays assembly chains and connections.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  casman web                              # Launch both interfaces (default)
  casman web --port 8080                  # Launch on specific port
  casman web --scanner-only               # Launch scanner interface only
  casman web --visualize-only             # Launch visualization interface only
  casman web --no-scanner                 # Disable scanner interface
  casman web --no-visualization           # Disable visualization interface
        """,
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to run the web server on (default: from config or 5000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host address to bind to (default: from config or 0.0.0.0)",
    )
    parser.add_argument(
        "--scanner-only",
        action="store_true",
        help="Enable only the scanner interface (for commissioning/repairs)",
    )
    parser.add_argument(
        "--visualize-only",
        action="store_true",
        help="Enable only the visualization interface",
    )
    parser.add_argument(
        "--no-scanner", action="store_true", help="Disable the scanner interface"
    )
    parser.add_argument(
        "--no-visualization",
        action="store_true",
        help="Disable the visualization interface",
    )
    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="dev",
        help="Server mode: dev (Flask debug) or prod (Gunicorn)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of workers for production mode (default: from config or 4)",
    )

    # Parse arguments
    if len(sys.argv) >= 3 and sys.argv[2] in ["-h", "--help"]:
        parser.print_help()
        return

    args = parser.parse_args(sys.argv[2:])  # Skip 'casman web'

    try:
        from casman.config.core import get_config
        from casman.web import run_dev_server, run_production_server

        # Determine which interfaces to enable
        enable_scanner = True
        enable_visualization = True

        if args.scanner_only:
            enable_visualization = False
        elif args.visualize_only:
            enable_scanner = False
        else:
            if args.no_scanner:
                enable_scanner = False
            if args.no_visualization:
                enable_visualization = False

            # Fall back to config if both still enabled
            if enable_scanner and enable_visualization:
                enable_scanner = get_config("web_app.enable_scanner", True)
                enable_visualization = get_config("web_app.enable_visualization", True)

        # Validate that at least one interface is enabled
        if not enable_scanner and not enable_visualization:
            print("❌ Error: At least one interface must be enabled!")
            print("   Remove conflicting flags or check your config.yaml")
            sys.exit(1)

        # Get configuration based on mode
        if args.mode == "prod":
            port = args.port or get_config("web_app.production.port", 8000)
            host = args.host or get_config("web_app.production.host", "0.0.0.0")
            workers = args.workers or get_config("web_app.production.workers", 4)
        else:
            port = args.port or get_config("web_app.dev.port", 5000)
            host = args.host or get_config("web_app.dev.host", "0.0.0.0")
            workers = 4  # Not used in dev mode

        # Run appropriate server
        if args.mode == "prod":
            run_production_server(
                host=host,
                port=port,
                workers=workers,
                enable_scanner=enable_scanner,
                enable_visualization=enable_visualization,
            )
        else:
            run_dev_server(
                host=host,
                port=port,
                enable_scanner=enable_scanner,
                enable_visualization=enable_visualization,
            )

    except ImportError as e:
        print(f"❌ Web application not available: {e}")
        print("💡 Make sure Flask is installed: pip install flask")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Web server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
