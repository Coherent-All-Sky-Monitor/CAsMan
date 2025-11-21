"""
Web application module for CAsMan.

Provides Flask-based web interfaces for scanner and visualization.
"""

from .app import configure_apps, create_app
from .scanner import scanner_bp
from .server import run_dev_server, run_production_server
from .visualize import visualize_bp

__all__ = [
    "create_app",
    "configure_apps",
    "run_dev_server",
    "run_production_server",
    "scanner_bp",
    "visualize_bp",
]
