"""Tests for the visualization module."""

import os
import sqlite3

import pytest

from casman.database import init_assembled_db
from casman.visualization import (
    format_ascii_chains,
    get_chain_summary,
    get_visualization_data,
)


class TestVisualization:
    """Test visualization functionality."""

    def test_format_ascii_chains_empty(self) -> None:
        """Test formatting ASCII chains with empty database."""
        result = format_ascii_chains()
        assert "No assembly connections found." in result

    def test_format_ascii_chains_with_data(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test formatting ASCII chains with sample data."""
        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", db_path)
        init_assembled_db(temporary_directory)
        # Insert test data
        conn = sqlite3.connect(os.path.join(temporary_directory, "assembled_casm.db"))
        cursor = conn.cursor()

        test_connections = [
            ("ANTP1-00001", "LNAP1-00001", "2024-01-01 10:00:00"),
            ("LNAP1-00001", "BACP1-00001", "2024-01-01 10:01:00"),
            ("BACP1-00001", None, "2024-01-01 10:02:00"),
        ]

        for connection in test_connections:
            cursor.execute(
                "INSERT INTO assembly (part_number, connected_to, scan_time) VALUES (?, ?, ?)",
                connection,
            )

        conn.commit()
        conn.close()

        # Test formatting chains
        result = format_ascii_chains()

        assert "CASM Assembly Connections:" in result
        assert "ANTP1-00001 ---> LNAP1-00001 ---> BACP1-00001" in result

    def test_get_visualization_data_empty(self) -> None:
        """Test getting visualization data with empty database."""
        data = get_visualization_data()

        assert "nodes" in data
        assert "links" in data
        assert not data["nodes"]
        assert not data["links"]

    def test_get_visualization_data_with_data(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting visualization data with sample data."""
        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", db_path)
        init_assembled_db(temporary_directory)
        # Insert test data
        conn = sqlite3.connect(os.path.join(temporary_directory, "assembled_casm.db"))
        cursor = conn.cursor()

        test_connections = [
            ("ANTP1-00001", None, "2024-01-01 10:00:00"),
            ("LNAP1-00001", "ANTP1-00001", "2024-01-01 10:01:00"),
            ("BACP1-00001", "LNAP1-00001", "2024-01-01 10:02:00"),
        ]

        for connection in test_connections:
            cursor.execute(
                "INSERT INTO assembly (part_number, connected_to, scan_time) VALUES (?, ?, ?)",
                connection,
            )

        conn.commit()
        conn.close()

        # Test getting visualization data
        data = get_visualization_data()

        assert "nodes" in data
        assert "links" in data

        # Check nodes
        node_ids = [node["id"] for node in data["nodes"]]
        assert "ANTP1-00001" in node_ids
        assert "LNAP1-00001" in node_ids
        assert "BACP1-00001" in node_ids
        assert len(data["nodes"]) == 3

        # Check that each node has required fields
        for node in data["nodes"]:
            assert "id" in node
            assert "label" in node

        # Check links
        assert len(data["links"]) == 2

        # Verify specific connections
        link_pairs = [(link["source"], link["target"]) for link in data["links"]]
        assert ("LNAP1-00001", "ANTP1-00001") in link_pairs
        assert ("BACP1-00001", "LNAP1-00001") in link_pairs

    def test_get_chain_summary_empty(self) -> None:
        """Test getting chain summary with empty database."""
        summary = get_chain_summary()

        expected_keys = [
            "total_parts",
            "total_connections",
            "total_chains",
            "longest_chain",
            "average_chain_length",
        ]
        for key in expected_keys:
            assert key in summary

        assert summary["total_parts"] == 0
        assert summary["total_connections"] == 0
        assert summary["total_chains"] == 0
        assert summary["longest_chain"] == 0
        assert summary["average_chain_length"] == 0

    def test_get_chain_summary_with_data(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting chain summary with sample data."""
        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", db_path)
        init_assembled_db(temporary_directory)
        # Insert test data - create a longer chain
        conn = sqlite3.connect(os.path.join(temporary_directory, "assembled_casm.db"))
        cursor = conn.cursor()

        test_connections = [
            ("ANTP1-00001", None, "2024-01-01 10:00:00"),
            ("LNAP1-00001", "ANTP1-00001", "2024-01-01 10:01:00"),
            ("BACP1-00001", "LNAP1-00001", "2024-01-01 10:02:00"),
            ("ANTP1-00002", "BACP1-00001", "2024-01-01 10:03:00"),
            # Separate chain
            ("LNAP1-00002", None, "2024-01-01 10:04:00"),
            ("BACP1-00002", "LNAP1-00002", "2024-01-01 10:05:00"),
        ]

        for connection in test_connections:
            cursor.execute(
                "INSERT INTO assembly (part_number, connected_to, scan_time) VALUES (?, ?, ?)",
                connection,
            )

        conn.commit()
        conn.close()

        # Test getting summary
        summary = get_chain_summary()

        assert summary["total_parts"] == 6
        assert summary["total_connections"] == 4  # 4 non-null connections
        assert summary["total_chains"] >= 1
        # At least 3 parts in longest chain
        assert summary["longest_chain"] >= 3
        assert summary["average_chain_length"] > 0

    def test_visualization_data_node_structure(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that visualization data nodes have correct structure."""
        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", db_path)
        init_assembled_db(temporary_directory)
        # Insert minimal test data
        conn = sqlite3.connect(os.path.join(temporary_directory, "assembled_casm.db"))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO assembly (part_number, connected_to, scan_time) VALUES (?, ?, ?)",
            ("ANTP1-00001", None, "2024-01-01 10:00:00"),
        )
        conn.commit()
        conn.close()

        # Test node structure
        data = get_visualization_data()

        assert len(data["nodes"]) == 1
        node = data["nodes"][0]

        # Check required fields
        assert node["id"] == "ANTP1-00001"
        assert node["label"] == "ANTP1-00001"

    def test_visualization_data_link_structure(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that visualization data links have correct structure."""
        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", db_path)
        init_assembled_db(temporary_directory)
        # Insert test data with connection
        conn = sqlite3.connect(os.path.join(temporary_directory, "assembled_casm.db"))
        cursor = conn.cursor()

        test_connections = [
            ("ANTP1-00001", None, "2024-01-01 10:00:00"),
            ("LNAP1-00001", "ANTP1-00001", "2024-01-01 10:01:00"),
        ]

        for connection in test_connections:
            cursor.execute(
                "INSERT INTO assembly (part_number, connected_to, scan_time) VALUES (?, ?, ?)",
                connection,
            )

        conn.commit()
        conn.close()

        # Test link structure
        data = get_visualization_data()

        assert len(data["links"]) == 1
        link = data["links"][0]

        # Check required fields
        assert "source" in link
        assert "target" in link
        assert link["source"] == "LNAP1-00001"
        assert link["target"] == "ANTP1-00001"
