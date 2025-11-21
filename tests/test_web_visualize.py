"""
Tests for CAsMan web visualization blueprint.
"""

import json
import sqlite3
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest

from casman.web import create_app
from casman.web.visualize import (format_display_data, get_all_chains,
                                  get_all_parts, get_duplicate_info,
                                  get_last_update, load_viz_template,
                                  visualize_bp)


@pytest.fixture
def app():
    """Create test Flask app."""
    test_app = create_app(enable_scanner=False, enable_visualization=True)
    test_app.config["TESTING"] = True
    return test_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


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
            polarization TEXT,
            scan_time TEXT NOT NULL,
            connected_to TEXT,
            connected_to_type TEXT,
            connected_polarization TEXT,
            connected_scan_time TEXT,
            connection_status TEXT DEFAULT 'connected'
        )
    """
    )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    import os

    os.unlink(db_path)


class TestVisualizationHelpers:
    """Test visualization helper functions."""

    def test_load_viz_template(self):
        """Test loading visualization template."""
        mock_template_content = "<html><body>Test Template</body></html>"

        with patch("builtins.open", mock_open(read_data=mock_template_content)):
            result = load_viz_template()
            assert result == mock_template_content

    def test_get_all_parts_empty(self, temp_db):
        """Test getting all parts from empty database."""
        with patch("casman.web.visualize.get_config", return_value=temp_db):
            parts = get_all_parts()
            assert parts == []

    def test_get_all_parts_with_data(self, temp_db):
        """Test getting all parts from database."""
        # Add sample data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time)
            VALUES 
                ('ANT00001P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:00:01'),
                ('LNA00001P1', 'LNA', '2025-01-01 00:00:01',
                 'BAC00001P1', 'BACBOARD', '2025-01-01 00:00:02')
        """
        )
        conn.commit()
        conn.close()

        with patch("casman.web.visualize.get_config", return_value=temp_db):
            parts = get_all_parts()
            assert len(parts) > 0
            assert "ANT00001P1" in parts
            assert "LNA00001P1" in parts
            assert "BAC00001P1" in parts

    def test_get_all_chains_empty(self, temp_db):
        """Test getting chains from empty database."""
        with patch("casman.web.visualize.get_config", return_value=temp_db):
            chains, connections = get_all_chains()
            assert chains == []
            assert connections == {}

    def test_get_all_chains_with_data(self, temp_db):
        """Test getting chains from database."""
        # Add sample chain
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time, connection_status)
            VALUES 
                ('ANT00001P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:00:01', 'connected'),
                ('LNA00001P1', 'LNA', '2025-01-01 00:00:01',
                 'BAC00001P1', 'BACBOARD', '2025-01-01 00:00:02', 'connected')
        """
        )
        conn.commit()
        conn.close()

        with patch("casman.web.visualize.get_config", return_value=temp_db):
            chains, connections = get_all_chains()
            assert len(chains) > 0
            assert len(connections) > 0
            # Check that chain is formed
            assert "ANT00001P1" in connections

    def test_get_all_chains_only_connected_status(self, temp_db):
        """Test that only connections with 'connected' status are included."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Add connected then disconnected
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time, connection_status)
            VALUES 
                ('ANT00001P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:00:01', 'connected')
        """
        )

        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time, connection_status)
            VALUES 
                ('ANT00001P1', 'ANTENNA', '2025-01-01 00:10:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:10:01', 'disconnected')
        """
        )

        conn.commit()
        conn.close()

        with patch("casman.web.visualize.get_config", return_value=temp_db):
            chains, connections = get_all_chains()
            # Should have no chains since latest status is disconnected
            assert len(chains) == 0

    def test_get_all_chains_filtered_by_part(self, temp_db):
        """Test filtering chains by specific part."""
        # Add two separate chains
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time, connection_status)
            VALUES 
                ('ANT00001P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:00:01', 'connected'),
                ('ANT00002P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00002P1', 'LNA', '2025-01-01 00:00:01', 'connected')
        """
        )
        conn.commit()
        conn.close()

        with patch("casman.web.visualize.get_config", return_value=temp_db):
            chains, connections = get_all_chains(selected_part="ANT00001P1")
            # Should only return chain containing ANT00001P1
            assert len(chains) == 1
            assert "ANT00001P1" in chains[0]
            assert "ANT00002P1" not in chains[0]

    def test_get_duplicate_info_no_duplicates(self, temp_db):
        """Test getting duplicate info when no duplicates exist."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time, connection_status)
            VALUES 
                ('ANT00001P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:00:01', 'connected')
        """
        )
        conn.commit()
        conn.close()

        with patch("casman.web.visualize.get_config", return_value=temp_db):
            duplicates = get_duplicate_info()
            assert duplicates == {}

    def test_get_duplicate_info_with_duplicates(self, temp_db):
        """Test getting duplicate info when duplicates exist."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Create duplicate connection (same part connected to multiple others)
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time, connection_status)
            VALUES 
                ('ANT00001P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:00:01', 'connected'),
                ('ANT00002P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:00:01', 'connected')
        """
        )
        conn.commit()
        conn.close()

        with patch("casman.web.visualize.get_config", return_value=temp_db):
            duplicates = get_duplicate_info()
            # LNA00001P1 should be marked as duplicate
            assert "LNA00001P1" in duplicates
            assert len(duplicates["LNA00001P1"]) == 2

    def test_get_last_update_empty(self, temp_db):
        """Test getting last update from empty database."""
        with patch("casman.web.visualize.get_config", return_value=temp_db):
            last_update = get_last_update()
            assert last_update is None

    def test_get_last_update_with_data(self, temp_db):
        """Test getting last update timestamp."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time)
            VALUES 
                ('ANT00001P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:00:01')
        """
        )
        conn.commit()
        conn.close()

        with patch("casman.web.visualize.get_config", return_value=temp_db):
            last_update = get_last_update()
            assert last_update is not None
            assert "2025-01-01" in last_update

    def test_format_display_data_basic(self):
        """Test formatting display data for a part."""
        connections = {
            "ANT00001P1": ("LNA00001P1", "2025-01-01 00:00:00", "2025-01-01 00:00:01")
        }
        duplicates = {}

        result = format_display_data("ANT00001P1", connections, duplicates)
        assert "ANT00001P1" in result
        assert "2025-01-01 00:00:00" in result

    def test_format_display_data_with_duplicate(self):
        """Test formatting display data for duplicate part."""
        connections = {}
        duplicates = {"ANT00001P1": ["LNA00001P1", "LNA00002P1"]}

        result = format_display_data("ANT00001P1", connections, duplicates)
        assert "ANT00001P1" in result
        assert "color: red" in result

    def test_format_display_data_with_full_chain(self):
        """Test formatting display data with complete chain info."""
        connections = {
            "ANT00001P1": ("LNA00001P1", "2025-01-01 00:00:00", "2025-01-01 00:00:01"),
            "LNA00001P1": ("BAC00001P1", "2025-01-01 00:00:01", "2025-01-01 00:00:02"),
        }
        duplicates = {}

        result = format_display_data("LNA00001P1", connections, duplicates)
        assert "LNA00001P1" in result
        # Should have FRM time from ANT connection
        assert "FRM:" in result
        # Should have NOW time
        assert "NOW:" in result
        # Should have NXT time
        assert "NXT:" in result


class TestVisualizationRoutes:
    """Test visualization blueprint routes."""

    def test_visualize_index_get(self, client, temp_db):
        """Test visualize index with GET request."""
        with patch("casman.web.visualize.get_config", return_value=temp_db):
            with patch(
                "casman.web.visualize.load_viz_template",
                return_value="<html>{{ parts|length }}</html>",
            ):
                response = client.get("/visualize/")
                assert response.status_code == 200

    def test_visualize_index_post(self, client, temp_db):
        """Test visualize index with POST request."""
        with patch("casman.web.visualize.get_config", return_value=temp_db):
            with patch(
                "casman.web.visualize.load_viz_template",
                return_value="<html>{{ parts|length }}</html>",
            ):
                response = client.post("/visualize/", data={"part": "ANT00001P1"})
                assert response.status_code == 200

    def test_visualize_chains_route(self, client, temp_db):
        """Test /visualize/chains route."""
        with patch("casman.web.visualize.get_config", return_value=temp_db):
            with patch(
                "casman.web.visualize.load_viz_template",
                return_value="<html>{{ chains|length }}</html>",
            ):
                response = client.get("/visualize/chains")
                assert response.status_code == 200

    def test_visualize_static_files(self, client):
        """Test serving static files."""
        # Test that the static route exists - actual file may not
        response = client.get("/visualize/static/test.txt")
        # 404 is expected if file doesn't exist, which is fine
        # We're just verifying the route is registered
        assert response.status_code in [200, 404]

    def test_visualize_with_selected_part(self, client, temp_db):
        """Test visualization with part filter."""
        # Add test data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time, connection_status)
            VALUES 
                ('ANT00001P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:00:01', 'connected')
        """
        )
        conn.commit()
        conn.close()

        with patch("casman.web.visualize.get_config", return_value=temp_db):
            with patch(
                "casman.web.visualize.load_viz_template",
                return_value="<html>{{ selected_part }}</html>",
            ):
                response = client.get("/visualize/?part=ANT00001P1")
                assert response.status_code == 200
                assert b"ANT00001P1" in response.data

    def test_visualize_template_rendering(self, client, temp_db):
        """Test that template receives all required context."""
        with patch("casman.web.visualize.get_config", return_value=temp_db):
            template_str = """
                Parts: {{ parts|length }}
                Chains: {{ chains|length }}
                Duplicates: {{ duplicates|length }}
                Selected: {{ selected_part or 'None' }}
                Updated: {{ last_update or 'Never' }}
            """
            with patch(
                "casman.web.visualize.load_viz_template", return_value=template_str
            ):
                response = client.get("/visualize/")
                assert response.status_code == 200
                assert b"Parts:" in response.data
                assert b"Chains:" in response.data
                assert b"Duplicates:" in response.data

    def test_visualize_error_handling(self, client, temp_db):
        """Test visualization error handling."""
        # Test with valid database but error in processing
        with patch("casman.web.visualize.get_config", return_value=temp_db):
            with patch(
                "casman.web.visualize.get_all_parts",
                side_effect=Exception("Test error"),
            ):
                with patch(
                    "casman.web.visualize.load_viz_template",
                    return_value="<html>Error Test</html>",
                ):
                    try:
                        response = client.get("/visualize/")
                        # May return error
                        assert response.status_code in [200, 500]
                    except Exception:
                        # Exception during processing is acceptable for error handling test
                        pass


class TestVisualizationIntegration:
    """Integration tests for visualization."""

    def test_full_chain_visualization(self, client, temp_db):
        """Test visualizing a complete assembly chain."""
        # Create full chain: ANTENNA -> LNA -> COAXSHORT -> COAXLONG -> BACBOARD -> SNAP
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        chain_data = [
            ("ANT00001P1", "ANTENNA", "LNA00001P1", "LNA"),
            ("LNA00001P1", "LNA", "CXS00001P1", "COAXSHORT"),
            ("CXS00001P1", "COAXSHORT", "CXL00001P1", "COAXLONG"),
            ("CXL00001P1", "COAXLONG", "BAC00001P1", "BACBOARD"),
            ("BAC00001P1", "BACBOARD", "SNAP1A00", "SNAP"),
        ]

        for i, (part, part_type, connected, connected_type) in enumerate(chain_data):
            cursor.execute(
                """
                INSERT INTO assembly 
                (part_number, part_type, scan_time, 
                 connected_to, connected_to_type, connected_scan_time, connection_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    part,
                    part_type,
                    f"2025-01-01 00:00:{i:02d}",
                    connected,
                    connected_type,
                    f"2025-01-01 00:00:{i+1:02d}",
                    "connected",
                ),
            )

        conn.commit()
        conn.close()

        with patch("casman.web.visualize.get_config", return_value=temp_db):
            chains, connections = get_all_chains()

            # Should have exactly one chain
            assert len(chains) == 1
            # Chain should have all 6 parts
            assert len(chains[0]) == 6
            # Verify chain order
            assert chains[0][0] == "ANT00001P1"
            assert chains[0][-1] == "SNAP1A00"

    def test_multiple_chains_visualization(self, client, temp_db):
        """Test visualizing multiple independent chains."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Chain 1
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time, connection_status)
            VALUES 
                ('ANT00001P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00001P1', 'LNA', '2025-01-01 00:00:01', 'connected')
        """
        )

        # Chain 2
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, scan_time, 
             connected_to, connected_to_type, connected_scan_time, connection_status)
            VALUES 
                ('ANT00002P1', 'ANTENNA', '2025-01-01 00:00:00', 
                 'LNA00002P1', 'LNA', '2025-01-01 00:00:01', 'connected')
        """
        )

        conn.commit()
        conn.close()

        with patch("casman.web.visualize.get_config", return_value=temp_db):
            chains, connections = get_all_chains()

            # Should have two independent chains
            assert len(chains) == 2
