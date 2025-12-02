"""
Comprehensive tests for CLI database commands.

Tests cover:
- Database command help and routing
- Clear command with various options
- Print command
- Load coordinates command
- Error handling and validation
"""

import os
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from casman.cli.database_commands import (
    cmd_database,
    cmd_database_clear,
    cmd_database_load_coordinates,
    cmd_database_print,
)


class TestCmdDatabaseRouting:
    """Tests for main database command routing."""

    @patch("sys.argv", ["casman", "database", "--help"])
    def test_database_help_displays(self, capsys):
        """Test database --help displays usage."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_database()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "CAsMan Database Management" in captured.out
        assert "clear" in captured.out
        assert "print" in captured.out
        assert "load-coordinates" in captured.out

    @patch("sys.argv", ["casman", "database"])
    def test_database_no_subcommand_shows_help(self, capsys):
        """Test database without subcommand shows help."""
        cmd_database()
        captured = capsys.readouterr()
        assert "CAsMan Database Management" in captured.out

    @patch("sys.argv", ["casman", "database", "invalid-command"])
    def test_database_invalid_subcommand(self, capsys):
        """Test database with invalid subcommand raises error."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_database()
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "invalid choice" in captured.err


class TestCmdDatabaseLoadCoordinates:
    """Tests for load-coordinates subcommand."""

    @patch("sys.argv", ["casman", "database", "load-coordinates", "--help"])
    def test_load_coordinates_help(self, capsys):
        """Test load-coordinates --help."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_database()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Load geographic coordinates" in captured.out
        assert "--csv" in captured.out

    def test_load_coordinates_success(self, tmp_path, capsys):
        """Test successful coordinate loading."""
        # Create test database
        db_path = tmp_path / "parts.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create antenna_positions table
        cursor.execute(
            """
            CREATE TABLE antenna_positions (
                antenna_number TEXT,
                grid_code TEXT,
                latitude REAL,
                longitude REAL,
                height REAL,
                coordinate_system TEXT
            )
        """
        )
        cursor.execute(
            """
            INSERT INTO antenna_positions (antenna_number, grid_code)
            VALUES ('ANT00001', 'CN001E00')
        """
        )
        conn.commit()
        conn.close()

        # Create test CSV
        csv_path = tmp_path / "coords.csv"
        csv_path.write_text(
            "grid_code,latitude,longitude,height,coordinate_system,notes\n"
            "CN001E00,37.87,122.25,10.5,WGS84,Test position\n"
        )

        # Mock get_database_path to return our test database
        with patch(
            "casman.database.antenna_positions.get_database_path",
            return_value=str(db_path),
        ):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--csv", type=str)

            cmd_database_load_coordinates(parser, [f"--csv={csv_path}"])

        captured = capsys.readouterr()
        assert "Updated: 1 position" in captured.out
        assert "Coordinate data loaded successfully" in captured.out

    def test_load_coordinates_file_not_found(self, capsys):
        """Test load-coordinates with non-existent file."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--csv", type=str)

        cmd_database_load_coordinates(parser, ["--csv=/nonexistent/file.csv"])
        captured = capsys.readouterr()
        assert "Error" in captured.out or "CSV file not found" in captured.out

    def test_load_coordinates_no_updates(self, tmp_path, capsys):
        """Test load-coordinates when no positions match."""
        # Create test database with no matching positions
        db_path = tmp_path / "parts.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE antenna_positions (
                antenna_number TEXT,
                grid_code TEXT,
                latitude REAL,
                longitude REAL,
                height REAL,
                coordinate_system TEXT
            )
        """
        )
        conn.commit()
        conn.close()

        # Create test CSV
        csv_path = tmp_path / "coords.csv"
        csv_path.write_text(
            "grid_code,latitude,longitude,height,coordinate_system,notes\n"
            "CN999E99,37.87,122.25,10.5,WGS84,Nonexistent position\n"
        )

        with patch(
            "casman.database.antenna_positions.get_database_path",
            return_value=str(db_path),
        ):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--csv", type=str)

            cmd_database_load_coordinates(parser, [f"--csv={csv_path}"])

        captured = capsys.readouterr()
        assert "Updated: 0 position" in captured.out
        assert "No positions were updated" in captured.out


class TestCmdDatabaseClear:
    """Tests for clear subcommand."""

    @patch("sys.argv", ["casman", "database", "clear", "--help"])
    def test_clear_help(self, capsys):
        """Test clear --help."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_database()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "clear database" in captured.out.lower()
        assert "--parts" in captured.out
        assert "--assembled" in captured.out

    def test_clear_user_declines(self, tmp_path, monkeypatch, capsys):
        """Test clear command when user declines."""
        # Create test databases
        parts_db = tmp_path / "parts.db"
        assembled_db = tmp_path / "assembled_casm.db"

        for db in [parts_db, assembled_db]:
            conn = sqlite3.connect(str(db))
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()
            conn.close()

        # Mock user input to decline
        monkeypatch.setattr("builtins.input", lambda _: "no")

        with patch("casman.database.connection.get_database_path") as mock_path:
            mock_path.side_effect = lambda db, _: str(tmp_path / db)

            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--parts", action="store_true")
            parser.add_argument("--assembled", action="store_true")

            cmd_database_clear(parser, [])

        captured = capsys.readouterr()
        assert "Aborted" in captured.out


class TestCmdDatabasePrint:
    """Tests for print subcommand."""

    @patch("sys.argv", ["casman", "database", "print", "--help"])
    def test_print_help(self, capsys):
        """Test print --help."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_database()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "display" in captured.out.lower() and "database" in captured.out.lower()

    def test_print_empty_database(self, tmp_path, capsys):
        """Test print command with empty database."""
        db_path = tmp_path / "assembled_casm.db"

        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()
        conn.close()

        with patch(
            "casman.cli.database_commands.get_config", return_value=str(db_path)
        ):
            import argparse

            parser = argparse.ArgumentParser()

            cmd_database_print(parser, [])

        captured = capsys.readouterr()
        assert "Assembly Database Contents" in captured.out

    def test_print_database_not_found(self, capsys):
        """Test print command when database not found."""
        with patch("casman.cli.database_commands.get_config", return_value=None):
            import argparse

            parser = argparse.ArgumentParser()

            with pytest.raises(SystemExit):
                cmd_database_print(parser, [])

        captured = capsys.readouterr()
        assert "Could not determine path" in captured.out


class TestIntegrationDatabaseCommands:
    """Integration tests for database command flow."""

    @patch("sys.argv", ["casman", "database", "load-coordinates"])
    def test_full_load_coordinates_flow(self, tmp_path, capsys):
        """Test complete load-coordinates command flow."""
        # Create realistic test setup
        db_path = tmp_path / "parts.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE antenna_positions (
                id INTEGER PRIMARY KEY,
                antenna_number TEXT UNIQUE,
                grid_code TEXT UNIQUE,
                array_id TEXT,
                row_offset INTEGER,
                east_col INTEGER,
                assigned_at TEXT,
                notes TEXT,
                latitude REAL,
                longitude REAL,
                height REAL,
                coordinate_system TEXT
            )
        """
        )

        # Insert test positions
        test_positions = [
            ("ANT00001", "CN001E00", "C", 1, 0),
            ("ANT00002", "CN001E01", "C", 1, 1),
            ("ANT00003", "CC000E00", "C", 0, 0),
        ]

        for ant, grid, arr, row, col in test_positions:
            cursor.execute(
                """
                INSERT INTO antenna_positions 
                (antenna_number, grid_code, array_id, row_offset, east_col, assigned_at)
                VALUES (?, ?, ?, ?, ?, '2025-01-01T00:00:00Z')
            """,
                (ant, grid, arr, row, col),
            )

        conn.commit()
        conn.close()

        # Create CSV with coordinates
        csv_path = tmp_path / "grid_positions.csv"
        csv_content = """grid_code,latitude,longitude,height,coordinate_system,notes
CN001E00,37.871899,-122.258477,10.5,WGS84,North row 1 east 0
CN001E01,37.871912,-122.258321,10.6,WGS84,North row 1 east 1
CC000E00,37.871850,-122.258600,10.4,WGS84,Center row east 0
"""
        csv_path.write_text(csv_content)

        with patch(
            "casman.database.antenna_positions.get_database_path",
            return_value=str(db_path),
        ):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--csv", type=str)

            cmd_database_load_coordinates(parser, [f"--csv={csv_path}"])

        captured = capsys.readouterr()
        assert "Updated: 3 position(s)" in captured.out
        assert "Skipped: 0 position(s)" in captured.out

        # Verify coordinates were loaded
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM antenna_positions WHERE latitude IS NOT NULL"
        )
        count = cursor.fetchone()[0]
        assert count == 3
        conn.close()
