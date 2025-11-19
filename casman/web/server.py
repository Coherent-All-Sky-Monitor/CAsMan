"""
Server Management for CAsMan Web Application

Provides development and production server runners.
"""

import logging
import sys

from casman.database.initialization import init_all_databases

from .app import create_app

logger = logging.getLogger(__name__)


def run_dev_server(
    host: str = "0.0.0.0",
    port: int = 5000,
    enable_scanner: bool = True,
    enable_visualization: bool = True,
) -> None:
    """Run the development server."""
    init_all_databases()
    app = create_app(enable_scanner, enable_visualization)

    logger.info("🚀 Starting CAsMan Web Application (Development Mode)")
    logger.info(f"📡 Server: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")

    if enable_scanner and enable_visualization:
        print("✓ Scanner interface: /scanner")
        print("✓ Visualization interface: /visualize")
    elif enable_scanner:
        print("✓ Scanner interface only (commissioning/repairs)")
    elif enable_visualization:
        print("✓ Visualization interface only (view chains)")

    print()
    print("Press Ctrl+C to stop")

    app.run(host=host, port=port, debug=True)


def run_production_server(
    host: str = "0.0.0.0",
    port: int = 5000,
    workers: int = 4,
    enable_scanner: bool = True,
    enable_visualization: bool = True,
) -> None:
    """Run the production server using Gunicorn."""
    try:
        import gunicorn.app.base
    except ImportError:
        logger.error("❌ Gunicorn is required for production mode")
        logger.info("💡 Install with: pip install gunicorn")
        sys.exit(1)

    init_all_databases()

    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    app = create_app(enable_scanner, enable_visualization)

    options = {
        "bind": f"{host}:{port}",
        "workers": workers,
        "worker_class": "sync",
        "accesslog": "-",
        "errorlog": "-",
        "loglevel": "info",
    }

    logger.info("🚀 Starting CAsMan Web Application (Production Mode)")
    logger.info(f"📡 Server: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    logger.info(f"⚙️  Workers: {workers}")

    if enable_scanner and enable_visualization:
        print("✓ Scanner interface: /scanner")
        print("✓ Visualization interface: /visualize")
    elif enable_scanner:
        print("✓ Scanner interface only (commissioning/repairs)")
    elif enable_visualization:
        print("✓ Visualization interface only (view chains)")

    print()
    print("Press Ctrl+C to stop")

    StandaloneApplication(app, options).run()
