"""Tests for the database module."""

import os
import sqlite3

import pytest

from casman.database import (
    get_database_path,
    get_parts_by_criteria,
    init_all_databases,
    init_assembled_db,
    init_parts_db,
)


class TestDatabase:
    """Test database functionality."""

    def test_get_database_path_default(self) -> None:
        """Test getting database path with default location."""
        path = get_database_path("test.db")
        assert path.endswith("database/test.db")
        assert "test.db" in path

    def test_init_parts_db(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test initializing parts database."""
        db_path = os.path.join(temporary_directory, "parts.db")
        monkeypatch.setenv("CASMAN_PARTS_DB", db_path)
        init_parts_db(temporary_directory)
        init_parts_db()

        db_path = os.path.join(temporary_directory, "parts.db")
        assert os.path.exists(db_path)

        # Check table structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='parts'"
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "parts"
        conn.close()

    def test_init_assembled_db(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test initializing assembled database."""
        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", db_path)
        init_assembled_db(temporary_directory)
        init_assembled_db()

        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        assert os.path.exists(db_path)

        # Check table structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='assembly'"
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "assembly"
        conn.close()

    def test_init_all_databases(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test initializing all databases."""
        parts_db = os.path.join(temporary_directory, "parts.db")
        assembled_db = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_PARTS_DB", parts_db)
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", assembled_db)
        init_all_databases(temporary_directory)
        init_all_databases()

        parts_path = os.path.join(temporary_directory, "parts.db")
        assembled_path = os.path.join(temporary_directory, "assembled_casm.db")

        assert os.path.exists(parts_path)
        assert os.path.exists(assembled_path)

    def test_get_parts_by_criteria_empty(self) -> None:
        """Test getting parts from empty database."""
        init_parts_db()
        parts = get_parts_by_criteria()
        assert parts == []

    def test_get_parts_by_criteria_with_data(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting parts with sample data."""
        db_path = os.path.join(temporary_directory, "parts.db")
        monkeypatch.setenv("CASMAN_PARTS_DB", db_path)
        init_parts_db(temporary_directory)
        # Insert test data
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()

        test_parts = [
            (
                "ANTP1-00001",
                "ANTENNA",
                "X",
                "2024-01-01 10:00:00",
                "2024-01-01 10:00:00",
            ),
            ("LNAP1-00001", "LNA", "Y", "2024-01-01 10:00:00", "2024-01-01 10:00:00"),
            (
                "BACP1-00001",
                "BACBOARD",
                "H",
                "2024-01-01 10:00:00",
                "2024-01-01 10:00:00",
            ),
        ]

        for part in test_parts:
            cursor.execute(
                "INSERT INTO parts \
                    (part_number, part_type, polarization, date_created, date_modified) "
                "VALUES (?, ?, ?, ?, ?)",
                part,
            )

        conn.commit()
        conn.close()

        # Test getting all parts
        all_parts = get_parts_by_criteria()
        assert len(all_parts) == 3

        # Test filtering by part type
        antenna_parts = get_parts_by_criteria(part_type="ANTENNA")
        assert len(antenna_parts) == 1
        assert antenna_parts[0][1] == "ANTP1-00001"  # part_number

        # Test filtering by polarization
        x_parts = get_parts_by_criteria(polarization="X")
        assert len(x_parts) == 1
        assert x_parts[0][3] == "X"  # polarization

        # Test filtering by both
        filtered_parts = get_parts_by_criteria(part_type="LNA", polarization="Y")
        assert len(filtered_parts) == 1
        assert filtered_parts[0][1] == "LNAP1-00001"

    def test_database_schema_parts(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test parts database schema."""
        db_path = os.path.join(temporary_directory, "parts.db")
        monkeypatch.setenv("CASMAN_PARTS_DB", db_path)
        init_parts_db(temporary_directory)
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()

        # Check column information
        cursor.execute("PRAGMA table_info(parts)")
        columns = cursor.fetchall()

        expected_columns = [
            "id",
            "part_number",
            "part_type",
            "polarization",
            "date_created",
            "date_modified",
        ]
        actual_columns = [col[1] for col in columns]

        for expected_col in expected_columns:
            assert expected_col in actual_columns

        conn.close()

    def test_database_schema_assembly(
        self, temporary_directory: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test assembly database schema."""
        db_path = os.path.join(temporary_directory, "assembled_casm.db")
        monkeypatch.setenv("CASMAN_ASSEMBLED_DB", db_path)
        init_assembled_db(temporary_directory)
        conn = sqlite3.connect(os.path.join(temporary_directory, "assembled_casm.db"))
        cursor = conn.cursor()

        # Check column information
        cursor.execute("PRAGMA table_info(assembly)")
        columns = cursor.fetchall()

        expected_columns = [
            "id",
            "part_number",
            "part_type",
            "polarization",
            "scan_time",
            "connected_to",
            "connected_to_type",
            "connected_polarization",
            "connected_scan_time",
        ]
        actual_columns = [col[1] for col in columns]

        for expected_col in expected_columns:
            assert expected_col in actual_columns

        conn.close()
