"""Tests for the assembly module."""

# Standard library imports
import os
import sqlite3
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest

# Project imports
from casman.assembly.chains import build_connection_chains
from casman.assembly.data import get_assembly_connections, get_assembly_stats
from casman.database.initialization import init_assembled_db


class TestAssembly:
    """Test assembly functionality in the assembly module."""

    # Removed all scan_part tests as scan_part no longer exists
    def test_get_assembly_connections_empty(self) -> None:
        """
        Test getting connections from an empty database.
        Should return an empty list.
        """
        connections = get_assembly_connections()
        assert connections == []

    def test_get_assembly_connections_with_data(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test getting assembly connections with sample data.
        Inserts test data and verifies the returned connections match expected tuples.
        """
        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", db_path)
        init_assembled_db(temporary_directory)
        conn = sqlite3.connect(os.path.join(temporary_directory, "assembled_casm.db"))
        cursor = conn.cursor()

        # Insert test data using full schema
        test_connections = [
            (
                "ANT-P1-00001",
                None,
                "2024-01-01 10:00:00",
                "ANTENNA",
                "P1",
                None,
                None,
                None,
            ),
            (
                "LNA-P1-00001",
                "ANT-P1-00001",
                "2024-01-01 10:01:00",
                "LNA",
                "P1",
                "ANTENNA",
                "P1",
                "2024-01-01 10:00:00",
            ),
            (
                "BAC-P1-00001",
                "LNA-P1-00001",
                "2024-01-01 10:02:00",
                "BACBOARD",
                "P1",
                "LNA",
                "P1",
                "2024-01-01 10:01:00",
            ),
        ]

        for connection in test_connections:
            cursor.execute(
                "INSERT INTO assembly (part_number, connected_to, \
                scan_time, part_type, polarization, connected_to_type, \
                    connected_polarization, connected_scan_time) \
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                connection,
            )

        conn.commit()
        conn.close()

        # Test getting connections (now returns 5-tuple: part_number,
        # connected_to, scan_time, part_type, polarization)
        connections = get_assembly_connections(temporary_directory)
        assert len(connections) == 3
        assert connections[0] == (
            "ANT-P1-00001",
            None,
            "2024-01-01 10:00:00",
            "ANTENNA",
            "P1",
        )
        assert connections[1] == (
            "LNA-P1-00001",
            "ANT-P1-00001",
            "2024-01-01 10:01:00",
            "LNA",
            "P1",
        )
        assert connections[2] == (
            "BAC-P1-00001",
            "LNA-P1-00001",
            "2024-01-01 10:02:00",
            "BACBOARD",
            "P1",
        )

    def test_build_connection_chains_empty(self) -> None:
        """
        Test building chains from an empty database.
        Should return an empty dictionary.
        """
        chains = build_connection_chains()
        assert not chains

    def test_build_connection_chains_with_data(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test building chains with sample data.
        Inserts a chain of connections and verifies the resulting chains dict.
        """
        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", db_path)
        init_assembled_db(temporary_directory)
        # Insert test data
        conn = sqlite3.connect(os.path.join(temporary_directory, "assembled_casm.db"))
        cursor = conn.cursor()

        test_connections = [
            ("ANT-P1-00001", None, "2024-01-01 10:00:00"),
            ("LNA-P1-00001", "ANT-P1-00001", "2024-01-01 10:01:00"),
            ("BAC-P1-00001", "LNA-P1-00001", "2024-01-01 10:02:00"),
            ("ANT-P1-00002", "BAC-P1-00001", "2024-01-01 10:03:00"),
        ]

        for connection in test_connections:
            # Insert each connection into the assembly table
            cursor.execute(
                "INSERT INTO assembly (part_number, connected_to, scan_time) VALUES (?, ?, ?)",
                connection,
            )

        conn.commit()
        conn.close()

        # Test building chains
        chains = build_connection_chains(temporary_directory)

        assert "ANT-P1-00001" in chains
        assert "LNA-P1-00001" in chains
        assert "BAC-P1-00001" in chains
        assert "ANT-P1-00002" in chains

        # Check connections
        assert chains["LNA-P1-00001"] == ["ANT-P1-00001"]
        assert chains["BAC-P1-00001"] == ["LNA-P1-00001"]
        assert chains["ANT-P1-00002"] == ["BAC-P1-00001"]
        assert chains["ANT-P1-00001"] == []  # No connections

    def test_get_assembly_stats_empty(self) -> None:
        """
        Test getting stats from an empty database.
        Should return all zero/None values in the stats dict.
        """
        stats = get_assembly_stats()
        expected_stats = {
            "total_scans": 0,
            "unique_parts": 0,
            "connected_parts": 0,
            "latest_scan": None,
        }
        assert stats == expected_stats

    def test_get_assembly_stats_with_data(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting stats with sample data."""
        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", db_path)
        init_assembled_db(temporary_directory)
        # Insert test data
        conn = sqlite3.connect(os.path.join(temporary_directory, "assembled_casm.db"))
        cursor = conn.cursor()

        test_connections = [
            ("ANT-P1-00001", None, "2024-01-01 10:00:00"),
            ("LNA-P1-00001", "ANT-P1-00001", "2024-01-01 10:01:00"),
            ("BAC-P1-00001", "LNA-P1-00001", "2024-01-01 10:02:00"),
            # Duplicate part, different connection
            ("ANT-P1-00001", "BAC-P1-00001", "2024-01-01 10:03:00"),
        ]

        for connection in test_connections:
            cursor.execute(
                "INSERT INTO assembly (part_number, connected_to, scan_time) VALUES (?, ?, ?)",
                connection,
            )

        conn.commit()
        conn.close()

        # Test getting stats
        stats = get_assembly_stats(temporary_directory)

        assert stats["total_scans"] == 4
        # ANTP1-00001, LNAP1-00001, BACP1-00001
        assert stats["unique_parts"] == 3
        # 3 scans have non-null connected_to
        assert stats["connected_parts"] == 3
        assert stats["latest_scan"] == "2024-01-01 10:03:00"

    @patch("casman.assembly.data.logger")
    def test_get_assembly_stats_database_error(self, mock_logger: MagicMock) -> None:
        """Test handling database error when getting stats."""
        with patch(
            "casman.assembly.data.get_database_path",
            return_value="/nonexistent/path.db",
        ):
            stats = get_assembly_stats()
            expected_stats = {
                "total_scans": 0,
                "unique_parts": 0,
                "connected_parts": 0,
                "latest_scan": None,
            }
            assert stats == expected_stats
            mock_logger.error.assert_called()

    # Removed test_multiple_scans_same_part as scan_part no longer exists
