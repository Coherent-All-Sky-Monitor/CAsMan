"""
Tests for the assembly connections module.

These tests specifically target the connections recording functionality
to improve code coverage.
"""

import os
import sqlite3
import tempfile
from unittest.mock import patch

from casman.assembly.connections import record_assembly_connection


class TestAssemblyConnections:
    """Test assembly connection recording functionality."""

    def test_record_assembly_connection_success(self) -> None:
        """Test successful recording of assembly connection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            success = record_assembly_connection(
                part_number="ANT-P1-00001",
                part_type="ANTENNA",
                polarization="P1",
                scan_time="2024-01-01 10:00:00",
                connected_to="LNA-P1-00001",
                connected_to_type="LNA",
                connected_polarization="P1",
                connected_scan_time="2024-01-01 10:05:00",
                db_dir=temp_dir,
            )

            assert success is True

            # Verify the record was inserted using get_database_path
            from casman.database import get_database_path
            db_path = get_database_path("assembled_casm.db", temp_dir)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM assembly WHERE part_number = ?", ("ANT-P1-00001",))
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[1] == "ANT-P1-00001"  # part_number is column 1 (id is column 0)
            assert result[5] == "LNA-P1-00001"  # connected_to is column 5

    def test_record_assembly_connection_with_null_connection(self) -> None:
        """Test recording connection with no connected part (source part)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            success = record_assembly_connection(
                part_number="ANT-P1-00001",
                part_type="ANTENNA",
                polarization="P1",
                scan_time="2024-01-01 10:00:00",
                connected_to="",
                connected_to_type="",
                connected_polarization="",
                connected_scan_time="",
                db_dir=temp_dir,
            )

            assert success is True

    def test_record_assembly_connection_database_error(self) -> None:
        """Test handling of database errors during connection recording."""
        with patch("casman.assembly.connections.get_database_path", return_value="/nonexistent/path.db"):
            success = record_assembly_connection(
                part_number="ANT-P1-00001",
                part_type="ANTENNA",
                polarization="P1",
                scan_time="2024-01-01 10:00:00",
                connected_to="LNA-P1-00001",
                connected_to_type="LNA",
                connected_polarization="P1",
                connected_scan_time="2024-01-01 10:05:00",
            )

            assert success is False

    def test_record_assembly_connection_value_error(self) -> None:
        """Test handling of value errors during connection recording."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with invalid scan_time format to trigger ValueError
            with patch("sqlite3.connect") as mock_connect:
                mock_connect.side_effect = ValueError("Invalid timestamp format")
                
                success = record_assembly_connection(
                    part_number="ANT-P1-00001",
                    part_type="ANTENNA",
                    polarization="P1",
                    scan_time="invalid-time",
                    connected_to="LNA-P1-00001",
                    connected_to_type="LNA",
                    connected_polarization="P1",
                    connected_scan_time="2024-01-01 10:05:00",
                    db_dir=temp_dir,
                )

                assert success is False

    def test_record_assembly_connection_type_error(self) -> None:
        """Test handling of type errors during connection recording."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("sqlite3.connect") as mock_connect:
                mock_connect.side_effect = TypeError("Invalid parameter type")
                
                success = record_assembly_connection(
                    part_number="ANT-P1-00001",
                    part_type="ANTENNA",
                    polarization="P1",
                    scan_time="2024-01-01 10:00:00",
                    connected_to="LNA-P1-00001",
                    connected_to_type="LNA",
                    connected_polarization="P1",
                    connected_scan_time="2024-01-01 10:05:00",
                    db_dir=temp_dir,
                )

                assert success is False

    def test_record_assembly_connection_with_custom_db_dir(self) -> None:
        """Test recording connection with custom database directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_db_dir = os.path.join(temp_dir, "custom_db")
            os.makedirs(custom_db_dir, exist_ok=True)
            
            success = record_assembly_connection(
                part_number="ANT-P1-00001",
                part_type="ANTENNA",
                polarization="P1",
                scan_time="2024-01-01 10:00:00",
                connected_to="LNA-P1-00001",
                connected_to_type="LNA",
                connected_polarization="P1",
                connected_scan_time="2024-01-01 10:05:00",
                db_dir=custom_db_dir,
            )

            assert success is True

    def test_record_assembly_connection_without_db_dir(self) -> None:
        """Test recording connection without specifying db_dir (uses default)."""
        # This tests the default path behavior
        with patch("casman.assembly.connections.init_assembled_db") as mock_init:
            with patch("casman.assembly.connections.get_database_path"):
                with patch("sqlite3.connect") as mock_connect:
                    mock_context_manager = mock_connect.return_value.__enter__.return_value
                    mock_cursor = mock_context_manager.cursor.return_value
                    
                    success = record_assembly_connection(
                        part_number="ANT-P1-00001",
                        part_type="ANTENNA",
                        polarization="P1",
                        scan_time="2024-01-01 10:00:00",
                        connected_to="LNA-P1-00001",
                        connected_to_type="LNA",
                        connected_polarization="P1",
                        connected_scan_time="2024-01-01 10:05:00",
                    )

                    assert success is True
                    mock_init.assert_called_once_with(None)
                    mock_cursor.execute.assert_called_once()
