"""
Tests for CAsMan web application factory and configuration.
"""

import os
import sqlite3
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from casman.web.app import APP_CONFIG, configure_apps, create_app


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Initialize database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create assembly table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS assembly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT NOT NULL,
            part_type TEXT NOT NULL,
            scan_time TEXT NOT NULL,
            connected_to TEXT,
            connected_to_type TEXT,
            connected_scan_time TEXT,
            connection_status TEXT DEFAULT 'connected'
        )
    """
    )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    os.unlink(db_path)


class TestAppConfiguration:
    """Test application configuration functions."""

    def test_configure_apps_default(self):
        """Test default app configuration."""
        configure_apps()
        assert APP_CONFIG["enable_scanner"] is True
        assert APP_CONFIG["enable_visualization"] is True

    def test_configure_apps_scanner_only(self):
        """Test scanner-only configuration."""
        configure_apps(enable_scanner=True, enable_visualization=False)
        assert APP_CONFIG["enable_scanner"] is True
        assert APP_CONFIG["enable_visualization"] is False

    def test_configure_apps_visualization_only(self):
        """Test visualization-only configuration."""
        configure_apps(enable_scanner=False, enable_visualization=True)
        assert APP_CONFIG["enable_scanner"] is False
        assert APP_CONFIG["enable_visualization"] is True

    def test_configure_apps_none_enabled(self):
        """Test configuration with both disabled."""
        configure_apps(enable_scanner=False, enable_visualization=False)
        assert APP_CONFIG["enable_scanner"] is False
        assert APP_CONFIG["enable_visualization"] is False


class TestAppCreation:
    """Test Flask application creation."""

    def test_create_app_default(self):
        """Test creating app with default configuration."""
        app = create_app()
        assert isinstance(app, Flask)
        assert "scanner" in app.blueprints
        assert "visualize" in app.blueprints

    def test_create_app_scanner_only(self):
        """Test creating app with scanner only."""
        app = create_app(enable_scanner=True, enable_visualization=False)
        assert isinstance(app, Flask)
        assert "scanner" in app.blueprints
        assert "visualize" not in app.blueprints

    def test_create_app_visualization_only(self):
        """Test creating app with visualization only."""
        app = create_app(enable_scanner=False, enable_visualization=True)
        assert isinstance(app, Flask)
        assert "scanner" not in app.blueprints
        assert "visualize" in app.blueprints

    def test_create_app_template_folder(self):
        """Test that app has correct template folder."""
        app = create_app()
        assert app.template_folder is not None
        assert "templates" in app.template_folder

    def test_create_app_static_folder(self):
        """Test that app has correct static folder."""
        app = create_app()
        assert app.static_folder is not None

    @patch("casman.web.app.HAS_CORS", True)
    @patch("casman.web.app.CORS")
    def test_create_app_with_cors(self, mock_cors):
        """Test app creation with CORS enabled."""
        app = create_app()
        mock_cors.assert_called_once_with(app)

    @patch("casman.web.app.HAS_CORS", False)
    def test_create_app_without_cors(self):
        """Test app creation without CORS available."""
        app = create_app()
        # Should create app successfully even without CORS
        assert isinstance(app, Flask)

    def test_home_route_both_apps(self):
        """Test home route with both apps enabled."""
        app = create_app(enable_scanner=True, enable_visualization=True)
        client = app.test_client()
        response = client.get("/")
        # Should show home page with both links
        assert response.status_code == 200

    def test_home_route_scanner_only(self):
        """Test home route with scanner only - should redirect."""
        app = create_app(enable_scanner=True, enable_visualization=False)
        client = app.test_client()
        response = client.get("/")
        # Should redirect to scanner
        assert response.status_code == 302
        assert "/scanner" in response.location

    def test_home_route_visualization_only(self):
        """Test home route with visualization only - should redirect."""
        app = create_app(enable_scanner=False, enable_visualization=True)
        client = app.test_client()
        response = client.get("/")
        # Should redirect to visualize
        assert response.status_code == 302
        assert "/visualize" in response.location

    def test_jinja_env_format_display_data(self):
        """Test that format_display_data is added to jinja environment."""
        app = create_app(enable_visualization=True)
        assert "format_display_data" in app.jinja_env.globals


class TestAppIntegration:
    """Integration tests for the complete app."""

    def test_app_runs_without_errors(self, temp_db):
        """Test that app can be created and accessed without errors."""
        app = create_app()
        client = app.test_client()

        # Test home page
        response = client.get("/")
        assert response.status_code == 200

        # Test scanner index
        response = client.get("/scanner/")
        assert response.status_code == 200

        # Test visualize index with mocked database
        with patch("casman.web.visualize.get_config", return_value=temp_db):
            with patch(
                "casman.web.visualize.load_viz_template",
                return_value="<html>Test</html>",
            ):
                response = client.get("/visualize/")
                assert response.status_code == 200

    def test_scanner_routes_registered(self):
        """Test that all scanner routes are registered."""
        app = create_app(enable_scanner=True)

        # Get all registered routes
        routes = [str(rule) for rule in app.url_map.iter_rules()]

        # Check key scanner routes are present
        assert any("/scanner/" in route for route in routes)
        assert any("/scanner/api/validate-part" in route for route in routes)
        assert any("/scanner/api/record-connection" in route for route in routes)

    def test_visualize_routes_registered(self):
        """Test that all visualize routes are registered."""
        app = create_app(enable_visualization=True)

        # Get all registered routes
        routes = [str(rule) for rule in app.url_map.iter_rules()]

        # Check key visualize routes are present
        assert any("/visualize/" in route for route in routes)
        assert any("/visualize/chains" in route for route in routes)
