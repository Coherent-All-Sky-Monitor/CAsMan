"""
Tests for CAsMan web scanner blueprint.
"""

import json
import sqlite3
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from casman.web import create_app
from casman.web.scanner import (
    ALL_PART_TYPES,
    format_snap_part,
    get_existing_connections,
    get_part_details,
    scanner_bp,
    validate_connection_sequence,
    validate_snap_part,
)


@pytest.fixture
def app():
    """Create test Flask app."""
    test_app = create_app(enable_scanner=True, enable_visualization=False)
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

    # Create parts table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS parts (
            part_number TEXT PRIMARY KEY,
            part_type TEXT NOT NULL,
            polarization TEXT NOT NULL,
            barcode_path TEXT
        )
    """
    )

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

    # Add sample data
    cursor.execute(
        """
        INSERT INTO parts (part_number, part_type, polarization)
        VALUES 
            ('ANT00001P1', 'ANTENNA', '1'),
            ('LNA00001P1', 'LNA', '1'),
            ('BAC00001P1', 'BACBOARD', '1')
    """
    )

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    import os

    os.unlink(db_path)


class TestHelperFunctions:
    """Test scanner helper functions."""

    def test_validate_snap_part_valid(self):
        """Test SNAP part validation with valid inputs."""
        assert validate_snap_part("SNAP1A00") is True
        assert validate_snap_part("SNAP4K11") is True
        assert validate_snap_part("SNAP2E05") is True

    def test_validate_snap_part_invalid(self):
        """Test SNAP part validation with invalid inputs."""
        assert validate_snap_part("SNAP5A00") is False  # Invalid chassis
        assert validate_snap_part("SNAP1Z00") is False  # Invalid slot
        assert validate_snap_part("SNAP1A12") is False  # Invalid port
        assert validate_snap_part("SNAP1") is False  # Too short
        assert validate_snap_part("ANTENNA") is False  # Wrong format

    def test_validate_connection_sequence_valid(self):
        """Test valid connection sequences."""
        valid, msg = validate_connection_sequence("ANTENNA", "LNA")
        assert valid is True
        assert msg == ""

        valid, msg = validate_connection_sequence("LNA", "COAXSHORT")
        assert valid is True

        valid, msg = validate_connection_sequence("BACBOARD", "SNAP")
        assert valid is True

    def test_validate_connection_sequence_invalid(self):
        """Test invalid connection sequences."""
        valid, msg = validate_connection_sequence("ANTENNA", "SNAP")
        assert valid is False
        assert "ANTENNA" in msg and "LNA" in msg

        valid, msg = validate_connection_sequence("LNA", "BACBOARD")
        assert valid is False

    def test_validate_connection_sequence_invalid_type(self):
        """Test connection sequence with invalid part type."""
        valid, msg = validate_connection_sequence("INVALID", "LNA")
        assert valid is False
        assert "Invalid part type" in msg

    def test_format_snap_part(self):
        """Test SNAP part number formatting."""
        assert format_snap_part(1, "A", 0) == "SNAP1A00"
        assert format_snap_part(4, "K", 11) == "SNAP4K11"
        assert format_snap_part(2, "E", 5) == "SNAP2E05"

    def test_get_part_details(self, temp_db):
        """Test getting part details from database."""
        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            result = get_part_details("ANT00001P1")
            assert result is not None
            assert result[0] == "ANTENNA"
            assert result[1] == "1"

    def test_get_part_details_not_found(self, temp_db):
        """Test getting details for non-existent part."""
        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            result = get_part_details("INVALID")
            assert result is None

    def test_get_part_details_db_error(self):
        """Test get_part_details with database error."""
        with patch(
            "casman.web.scanner.get_database_path", return_value="/invalid/path.db"
        ):
            result = get_part_details("ANT00001P1")
            assert result is None

    def test_get_existing_connections_empty(self, temp_db):
        """Test getting connections when none exist."""
        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            result = get_existing_connections("ANT00001P1")
            assert result == []

    def test_get_existing_connections_with_data(self, temp_db):
        """Test getting existing connections."""
        # Add connection to database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, polarization, scan_time, 
             connected_to, connected_to_type, connected_polarization, 
             connected_scan_time, connection_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "ANT00001P1",
                "ANTENNA",
                "1",
                "2025-01-01 00:00:00",
                "LNA00001P1",
                "LNA",
                "1",
                "2025-01-01 00:00:01",
                "connected",
            ),
        )
        conn.commit()
        conn.close()

        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            result = get_existing_connections("ANT00001P1")
            assert len(result) == 1
            assert result[0]["part_number"] == "ANT00001P1"
            assert result[0]["connected_to"] == "LNA00001P1"

    def test_get_existing_connections_only_latest_status(self, temp_db):
        """Test that only connections with latest status 'connected' are returned."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Add connected then disconnected
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, polarization, scan_time, 
             connected_to, connected_to_type, connected_polarization, 
             connected_scan_time, connection_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "ANT00001P1",
                "ANTENNA",
                "1",
                "2025-01-01 00:00:00",
                "LNA00001P1",
                "LNA",
                "1",
                "2025-01-01 00:00:01",
                "connected",
            ),
        )

        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, polarization, scan_time, 
             connected_to, connected_to_type, connected_polarization, 
             connected_scan_time, connection_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "ANT00001P1",
                "ANTENNA",
                "1",
                "2025-01-01 00:10:00",
                "LNA00001P1",
                "LNA",
                "1",
                "2025-01-01 00:10:01",
                "disconnected",
            ),
        )

        conn.commit()
        conn.close()

        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            result = get_existing_connections("ANT00001P1")
            # Should return empty since latest status is disconnected
            assert len(result) == 0

    def test_all_part_types_loaded(self):
        """Test that ALL_PART_TYPES is populated."""
        assert isinstance(ALL_PART_TYPES, list)
        assert len(ALL_PART_TYPES) > 0


class TestScannerRoutes:
    """Test scanner blueprint routes."""

    def test_scanner_index(self, client):
        """Test scanner index page."""
        response = client.get("/scanner/")
        assert response.status_code == 200
        assert b"scanner" in response.data.lower()

    def test_validate_part_missing_part_number(self, client):
        """Test validate-part with missing part number."""
        response = client.post("/scanner/api/validate-part", json={})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "required" in data["error"].lower()

    def test_validate_part_snap_valid(self, client):
        """Test validating valid SNAP part."""
        response = client.post(
            "/scanner/api/validate-part", json={"part_number": "SNAP1A00"}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["part_type"] == "SNAP"
        assert data["polarization"] == "N/A"

    def test_validate_part_snap_invalid(self, client):
        """Test validating invalid SNAP part."""
        response = client.post(
            "/scanner/api/validate-part", json={"part_number": "SNAP9Z99"}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Invalid SNAP format" in data["error"]

    def test_validate_part_from_database(self, client, temp_db):
        """Test validating part from database."""
        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            response = client.post(
                "/scanner/api/validate-part", json={"part_number": "ANT00001P1"}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["part_type"] == "ANTENNA"
            assert data["polarization"] == "1"

    def test_validate_part_not_found(self, client, temp_db):
        """Test validating non-existent part."""
        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            response = client.post(
                "/scanner/api/validate-part", json={"part_number": "INVALID123"}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is False
            assert "not found" in data["error"].lower()

    def test_get_connections_missing_part(self, client):
        """Test get-connections with missing part number."""
        response = client.post("/scanner/api/get-connections", json={})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False

    def test_get_connections_success(self, client, temp_db):
        """Test get-connections with valid part."""
        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            response = client.post(
                "/scanner/api/get-connections", json={"part_number": "ANT00001P1"}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "connections" in data
            assert "count" in data

    def test_check_snap_ports_missing_params(self, client):
        """Test check-snap-ports with missing parameters."""
        response = client.post("/scanner/api/check-snap-ports", json={})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "required" in data["error"].lower()

    def test_check_snap_ports_success(self, client, temp_db):
        """Test check-snap-ports with valid chassis and slot."""
        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            response = client.post(
                "/scanner/api/check-snap-ports", json={"chassis": 1, "slot": "A"}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "occupied_ports" in data

    def test_format_snap_missing_params(self, client):
        """Test format-snap with missing parameters."""
        response = client.post("/scanner/api/format-snap", json={"chassis": 1})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "required" in data["error"].lower()

    def test_format_snap_invalid_chassis(self, client):
        """Test format-snap with invalid chassis."""
        response = client.post(
            "/scanner/api/format-snap", json={"chassis": 5, "slot": "A", "port": 0}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "chassis" in data["error"].lower()

    def test_format_snap_invalid_slot(self, client):
        """Test format-snap with invalid slot."""
        response = client.post(
            "/scanner/api/format-snap", json={"chassis": 1, "slot": "Z", "port": 0}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "slot" in data["error"].lower()

    def test_format_snap_invalid_port(self, client):
        """Test format-snap with invalid port."""
        response = client.post(
            "/scanner/api/format-snap", json={"chassis": 1, "slot": "A", "port": 12}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "port" in data["error"].lower()

    def test_format_snap_success_connect_mode(self, client, temp_db):
        """Test format-snap with valid params in connect mode."""
        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            response = client.post(
                "/scanner/api/format-snap",
                json={"chassis": 1, "slot": "A", "port": 0, "action": "connect"},
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["snap_part"] == "SNAP1A00"

    def test_format_snap_success_disconnect_mode(self, client, temp_db):
        """Test format-snap in disconnect mode with connection."""
        # Add connection first
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, polarization, scan_time, 
             connected_to, connected_to_type, connected_polarization, 
             connected_scan_time, connection_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "BAC00001P1",
                "BACBOARD",
                "1",
                "2025-01-01 00:00:00",
                "SNAP1A00",
                "SNAP",
                "N/A",
                "2025-01-01 00:00:01",
                "connected",
            ),
        )
        conn.commit()
        conn.close()

        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            response = client.post(
                "/scanner/api/format-snap",
                json={"chassis": 1, "slot": "A", "port": 0, "action": "disconnect"},
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["snap_part"] == "SNAP1A00"
            assert data["connected_to"] == "BAC00001P1"

    def test_record_connection_invalid_sequence(self, client):
        """Test record-connection with invalid sequence."""
        response = client.post(
            "/scanner/api/record-connection",
            json={
                "part_number": "ANT00001P1",
                "part_type": "ANTENNA",
                "polarization": "1",
                "connected_to": "SNAP1A00",
                "connected_to_type": "SNAP",
                "connected_polarization": "N/A",
            },
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "connect to" in data["error"].lower()

    def test_record_connection_success(self, client, temp_db):
        """Test recording valid connection."""
        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            with patch(
                "casman.web.scanner.record_assembly_connection", return_value=True
            ):
                response = client.post(
                    "/scanner/api/record-connection",
                    json={
                        "part_number": "ANT00001P1",
                        "part_type": "ANTENNA",
                        "polarization": "1",
                        "connected_to": "LNA00001P1",
                        "connected_to_type": "LNA",
                        "connected_polarization": "1",
                    },
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["success"] is True
                assert "Successfully connected" in data["message"]

    def test_record_connection_failure(self, client, temp_db):
        """Test recording connection when database operation fails."""
        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            with patch(
                "casman.web.scanner.record_assembly_connection", return_value=False
            ):
                response = client.post(
                    "/scanner/api/record-connection",
                    json={
                        "part_number": "ANT00001P1",
                        "part_type": "ANTENNA",
                        "polarization": "1",
                        "connected_to": "LNA00001P1",
                        "connected_to_type": "LNA",
                        "connected_polarization": "1",
                    },
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["success"] is False

    def test_record_disconnection_success(self, client):
        """Test recording disconnection."""
        with patch(
            "casman.web.scanner.record_assembly_disconnection", return_value=True
        ):
            response = client.post(
                "/scanner/api/record-disconnection",
                json={
                    "part_number": "ANT00001P1",
                    "part_type": "ANTENNA",
                    "polarization": "1",
                    "connected_to": "LNA00001P1",
                    "connected_to_type": "LNA",
                    "connected_polarization": "1",
                },
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "Successfully disconnected" in data["message"]

    def test_record_disconnection_failure(self, client):
        """Test recording disconnection when operation fails."""
        with patch(
            "casman.web.scanner.record_assembly_disconnection", return_value=False
        ):
            response = client.post(
                "/scanner/api/record-disconnection",
                json={
                    "part_number": "ANT00001P1",
                    "part_type": "ANTENNA",
                    "polarization": "1",
                    "connected_to": "LNA00001P1",
                    "connected_to_type": "LNA",
                    "connected_polarization": "1",
                },
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is False

    def test_add_parts_missing_params(self, client):
        """Test add-parts with missing parameters."""
        response = client.post("/scanner/api/add-parts", json={"count": 5})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False

    def test_add_parts_invalid_count(self, client):
        """Test add-parts with invalid count."""
        response = client.post(
            "/scanner/api/add-parts",
            json={"part_type": "ANTENNA", "count": 0, "polarization": "1"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "greater than 0" in data["error"]

    def test_add_parts_invalid_polarization(self, client):
        """Test add-parts with invalid polarization."""
        response = client.post(
            "/scanner/api/add-parts",
            json={"part_type": "ANTENNA", "count": 5, "polarization": "3"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "polarization" in data["error"].lower()

    def test_add_parts_success(self, client):
        """Test successful parts creation."""
        with patch(
            "casman.parts.generation.generate_part_numbers",
            return_value=["ANT00001P1", "ANT00002P1"],
        ):
            response = client.post(
                "/scanner/api/add-parts",
                json={"part_type": "ANTENNA", "count": 2, "polarization": "1"},
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert len(data["parts"]) == 2
            assert data["count"] == 2

    def test_part_history_missing_part_number(self, client):
        """Test part-history with missing part number."""
        response = client.post("/scanner/api/part-history", json={})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False

    def test_part_history_success(self, client, temp_db):
        """Test getting part history."""
        # Add history records
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, connected_to, connected_to_type, 
             connection_status, scan_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                "ANT00001P1",
                "ANTENNA",
                "LNA00001P1",
                "LNA",
                "connected",
                "2025-01-01 00:00:00",
            ),
        )
        conn.commit()
        conn.close()

        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            response = client.post(
                "/scanner/api/part-history", json={"part_number": "ANT00001P1"}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "history" in data
            assert len(data["history"]) > 0

    def test_part_history_no_duplicates(self, client, temp_db):
        """Test that part history deduplicates bidirectional records."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Add bidirectional records (should be deduplicated)
        scan_time = "2025-01-01 00:00:00"
        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, connected_to, connected_to_type, 
             connection_status, scan_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            ("ANT00001P1", "ANTENNA", "LNA00001P1", "LNA", "connected", scan_time),
        )

        cursor.execute(
            """
            INSERT INTO assembly 
            (part_number, part_type, connected_to, connected_to_type, 
             connection_status, scan_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            ("LNA00001P1", "LNA", "ANT00001P1", "ANTENNA", "connected", scan_time),
        )

        conn.commit()
        conn.close()

        with patch("casman.web.scanner.get_database_path", return_value=temp_db):
            response = client.post(
                "/scanner/api/part-history", json={"part_number": "ANT00001P1"}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            # Should only have 1 record due to deduplication
            assert len(data["history"]) == 1
