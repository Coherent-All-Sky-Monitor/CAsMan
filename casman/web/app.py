"""
Flask application factory and configuration.
"""

import logging
import os

from flask import Flask, redirect, render_template

from .scanner import scanner_bp
from .visualize import format_display_data, visualize_bp

try:
    from flask_cors import CORS

    HAS_CORS = True
except ImportError:
    HAS_CORS = False


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuration for which apps to serve
APP_CONFIG = {
    "enable_scanner": True,
    "enable_visualization": True,
}


def configure_apps(
    enable_scanner: bool = True, enable_visualization: bool = True
) -> None:
    """Configure which applications to enable."""
    APP_CONFIG["enable_scanner"] = enable_scanner
    APP_CONFIG["enable_visualization"] = enable_visualization


def create_app(enable_scanner: bool = True, enable_visualization: bool = True) -> Flask:
    """Create and configure the unified Flask application."""
    configure_apps(enable_scanner, enable_visualization)

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )

    # Enable CORS for mobile browser access
    if HAS_CORS:
        CORS(app)
        logger.info("CORS enabled for cross-origin requests")
    else:
        logger.warning(
            "CORS not available - mobile browsers may have issues. Install with: pip install flask-cors"
        )

    if APP_CONFIG["enable_scanner"]:
        app.register_blueprint(scanner_bp)

    if APP_CONFIG["enable_visualization"]:
        app.register_blueprint(visualize_bp)
        app.jinja_env.globals.update(format_display_data=format_display_data)

    @app.route("/")
    def home():
        """Home page with links to available interfaces."""
        enabled_apps = []
        if APP_CONFIG["enable_scanner"]:
            enabled_apps.append(
                (
                    "Scanner",
                    "/scanner",
                    "Connect/Disconnect parts (commissioning & repairs)",
                )
            )
        if APP_CONFIG["enable_visualization"]:
            enabled_apps.append(
                (
                    "Visualization",
                    "/visualize",
                    "View assembly chains and connections",
                )
            )
            enabled_apps.append(
                (
                    "Admin",
                    "/visualize/admin",
                    "Database management and CSV loading",
                )
            )

        if len(enabled_apps) == 1:
            return redirect(enabled_apps[0][1])

        return render_template("home.html", enabled_apps=enabled_apps)

    return app
