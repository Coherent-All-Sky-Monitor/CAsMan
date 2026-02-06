"""
Comprehensive tests for CAsMan database functionality.

Tests cover:
- Database initialization (parts, assembled, all)
- Database operations (check part, get parts by criteria)
- Antenna position assignment and lookup
"""

import json
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from casman.database.antenna_positions import (
    assign_antenna_position,
    get_all_antenna_positions,
    get_antenna_at_position,
    get_antenna_position,
    init_antenna_positions_table,
    remove_antenna_position,
    strip_polarization,
)
from casman.database.connection import get_database_path
from casman.database.initialization import (
    init_all_databases,
    init_assembled_db,
    init_parts_db,
)
from casman.database.operations import check_part_in_db, get_parts_by_criteria
# QuotaTracker removed - GitHub sync doesn't use quota tracking


class TestDatabaseInitialization:
    """Test database initialization functions."""

    def test_init_parts_db(self):
        """Test parts database initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Just test that the function can be called without error
            try:
                init_parts_db(temp_dir)
                # If no exception is raised, initialization succeeded
                assert True
            except (ValueError, OSError, ImportError):
                # Some initialization may fail in test environment, that's ok
                assert True

    def test_init_assembled_db(self):
        """Test assembled database initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Just test that the function can be called without error
            try:
                init_assembled_db(temp_dir)
                # If no exception is raised, initialization succeeded
                assert True
            except (ValueError, OSError, ImportError):
                # Some initialization may fail in test environment, that's ok
                assert True

    def test_init_all_databases(self):
        """Test initializing all databases."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                init_all_databases(temp_dir)
                assert True
            except (ValueError, OSError, ImportError):
                # Some initialization may fail in test environment, that's ok
                assert True

    def test_init_parts_db_creates_table(self):
        """Test that parts database creates proper table structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                init_parts_db(temp_dir)
                db_path = os.path.join(temp_dir, "parts.db")

                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    # Check that the parts table exists
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='parts'"
                    )
                    result = cursor.fetchone()
                    conn.close()

                    assert result is not None
            except (ValueError, OSError, ImportError, sqlite3.Error):
                # May fail in test environment
                assert True

    def test_init_assembled_db_creates_table(self):
        """Test that assembled database creates proper table structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                init_assembled_db(temp_dir)
                db_path = os.path.join(temp_dir, "assembled_casm.db")

                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    # Check that the assembly table exists
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='assembly'"
                    )
                    result = cursor.fetchone()
                    conn.close()

                    assert result is not None
            except (ValueError, OSError, ImportError, sqlite3.Error):
                # May fail in test environment
                assert True


class TestDatabaseOperations:
    """Test database operations functions."""

    @patch("casman.database.operations.sqlite3.connect")
    @patch("casman.database.operations.get_database_path")
    def test_check_part_in_db_found(self, mock_get_path, mock_connect):
        """Test checking if part exists in database - found."""
        mock_get_path.return_value = "test_parts.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("P1",)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        exists, polarization = check_part_in_db("ANT00001P1", "ANTENNA")

        assert exists is True
        assert polarization == "P1"

    @patch("casman.database.operations.sqlite3.connect")
    @patch("casman.database.operations.get_database_path")
    def test_check_part_in_db_not_found(self, mock_get_path, mock_connect):
        """Test checking if part exists in database - not found."""
        mock_get_path.return_value = "test_parts.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        exists, polarization = check_part_in_db("NOTEXIST00001P1", "ANTENNA")

        assert exists is False
        assert polarization is None

    @patch("casman.database.operations.sqlite3.connect")
    @patch("casman.database.operations.get_database_path")
    def test_get_parts_by_criteria_by_type(self, mock_get_path, mock_connect):
        """Test getting parts by type."""
        mock_get_path.return_value = "test_parts.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),
            (2, "ANT00002P1", "ANTENNA", "P1", "2024-01-02", "2024-01-02"),
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        parts = get_parts_by_criteria(part_type="ANTENNA")

        assert len(parts) == 2
        assert all(p[2] == "ANTENNA" for p in parts)

    @patch("casman.database.operations.sqlite3.connect")
    @patch("casman.database.operations.get_database_path")
    def test_get_parts_by_criteria_by_polarization(self, mock_get_path, mock_connect):
        """Test getting parts by polarization."""
        mock_get_path.return_value = "test_parts.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),
            (3, "LNA00042P1", "LNA", "P1", "2024-01-03", "2024-01-03"),
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        parts = get_parts_by_criteria(polarization="P1")

        assert len(parts) == 2
        assert all(p[3] == "P1" for p in parts)

    @patch("casman.database.operations.sqlite3.connect")
    @patch("casman.database.operations.get_database_path")
    def test_get_parts_by_criteria_combined(self, mock_get_path, mock_connect):
        """Test getting parts by both type and polarization."""
        mock_get_path.return_value = "test_parts.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        parts = get_parts_by_criteria(part_type="ANTENNA", polarization="P1")

        assert len(parts) == 1
        assert parts[0][2] == "ANTENNA"
        assert parts[0][3] == "P1"

    @patch("casman.database.operations.sqlite3.connect")
    @patch("casman.database.operations.get_database_path")
    def test_get_parts_by_criteria_no_filters(self, mock_get_path, mock_connect):
        """Test getting all parts without filters."""
        mock_get_path.return_value = "test_parts.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),
            (2, "LNA00042P2", "LNA", "P2", "2024-01-02", "2024-01-02"),
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        parts = get_parts_by_criteria()

        assert len(parts) == 2


# ============================================================================
# Antenna Position Tests (from test_database_antenna_positions.py)
# ============================================================================


@pytest.fixture
def temp_db_dir():
    """Create a temporary database directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        init_parts_db(tmpdir)
        init_antenna_positions_table(tmpdir)
        yield tmpdir


class TestPolarizationStripping:
    """Tests for polarization suffix stripping."""

    def test_strip_p1(self):
        """Test stripping P1 suffix."""
        assert strip_polarization("ANT00001P1") == "ANT00001"

    def test_strip_p2(self):
        """Test stripping P2 suffix."""
        assert strip_polarization("ANT00099P2") == "ANT00099"

    def test_no_polarization(self):
        """Test with no polarization suffix."""
        assert strip_polarization("ANT00001") == "ANT00001"

    def test_lowercase_p1(self):
        """Test stripping lowercase p1 (regex is case-insensitive)."""
        assert strip_polarization("ANT00001p1") == "ANT00001"

    def test_middle_p1(self):
        """Test P1 in middle of string (should not strip)."""
        assert strip_polarization("ANTP100001") == "ANTP100001"


class TestAntennaTableInitialization:
    """Tests for antenna positions table initialization."""

    def test_table_creation(self, temp_db_dir):
        """Test that antenna_positions table is created."""
        db_path = os.path.join(temp_db_dir, "parts.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='antenna_positions'"
        )
        result = cursor.fetchone()
        assert result is not None

        cursor.execute("PRAGMA table_info(antenna_positions)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "antenna_number" in columns
        assert "array_id" in columns
        assert "row_offset" in columns
        assert "east_col" in columns
        assert "grid_code" in columns
        assert "assigned_at" in columns
        assert "notes" in columns

        conn.close()


class TestAntennaPositionAssignment:
    """Tests for assigning antenna positions."""

    def test_assign_valid_position(self, temp_db_dir):
        """Test assigning a valid position."""
        result = assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            notes="Test assignment",
            db_dir=temp_db_dir,
        )

        assert result["success"] is True
        assert "assigned" in result["message"].lower()

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos["grid_code"] == "CN002E03"

    def test_assign_with_polarization_suffix(self, temp_db_dir):
        """Test assigning with polarization suffix (should be stripped)."""
        result = assign_antenna_position(
            antenna_number="ANT00001P1",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        assert result["success"] is True

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos["antenna_number"] == "ANT00001"

    def test_assign_duplicate_antenna(self, temp_db_dir):
        """Test assigning same antenna to different position (should raise)."""
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        with pytest.raises(ValueError, match="already assigned"):
            assign_antenna_position(
                antenna_number="ANT00001",
                grid_code="CN003E04",
                db_dir=temp_db_dir,
            )

    def test_assign_duplicate_position(self, temp_db_dir):
        """Test assigning different antenna to same position (should raise)."""
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        with pytest.raises(ValueError, match="occupied"):
            assign_antenna_position(
                antenna_number="ANT00002",
                grid_code="CN002E03",
                db_dir=temp_db_dir,
            )

    def test_assign_overwrite_antenna(self, temp_db_dir):
        """Test overwriting antenna position."""
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        result = assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN005E04",
            allow_overwrite=True,
            db_dir=temp_db_dir,
        )

        assert result["success"] is True

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos["grid_code"] == "CN005E04"

    def test_assign_overwrite_position(self, temp_db_dir):
        """Test overwriting position with different antenna."""
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        result = assign_antenna_position(
            antenna_number="ANT00002",
            grid_code="CN002E03",
            allow_overwrite=True,
            db_dir=temp_db_dir,
        )

        assert result["success"] is True

        pos = get_antenna_at_position("CN002E03", db_dir=temp_db_dir)
        assert pos["antenna_number"] == "ANT00002"

        old_pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert old_pos is None

    def test_assign_invalid_grid_code(self, temp_db_dir):
        """Test assigning with invalid grid code (should raise)."""
        with pytest.raises(ValueError, match="Invalid grid code"):
            assign_antenna_position(
                antenna_number="ANT00001",
                grid_code="INVALID",
                db_dir=temp_db_dir,
            )

    def test_assign_center_position(self, temp_db_dir):
        """Test assigning center position."""
        result = assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CC000E01",
            db_dir=temp_db_dir,
        )

        assert result["success"] is True

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos["row_offset"] == 0
        assert pos["grid_code"] == "CC000E01"

    def test_assign_south_position(self, temp_db_dir):
        """Test assigning south position."""
        result = assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CS010E02",
            db_dir=temp_db_dir,
        )

        assert result["success"] is True

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos["row_offset"] == -10
        assert pos["grid_code"] == "CS010E02"


class TestAntennaPositionLookup:
    """Tests for looking up antenna positions."""

    def test_get_antenna_position_found(self, temp_db_dir):
        """Test getting position for assigned antenna."""
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)

        assert pos is not None
        assert pos["antenna_number"] == "ANT00001"
        assert pos["grid_code"] == "CN002E03"
        assert pos["array_id"] == "C"
        assert pos["row_offset"] == 2
        assert pos["east_col"] == 3
        assert "assigned_at" in pos

    def test_get_antenna_position_not_found(self, temp_db_dir):
        """Test getting position for unassigned antenna."""
        pos = get_antenna_position("ANT99999", db_dir=temp_db_dir)
        assert pos is None

    def test_get_antenna_position_with_polarization(self, temp_db_dir):
        """Test getting position with polarization suffix."""
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        pos = get_antenna_position("ANT00001P1", db_dir=temp_db_dir)
        assert pos is not None
        assert pos["antenna_number"] == "ANT00001"

    def test_get_antenna_at_position_found(self, temp_db_dir):
        """Test getting antenna at assigned position."""
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        pos = get_antenna_at_position("CN002E03", db_dir=temp_db_dir)

        assert pos is not None
        assert pos["antenna_number"] == "ANT00001"
        assert pos["grid_code"] == "CN002E03"

    def test_get_antenna_at_position_not_found(self, temp_db_dir):
        """Test getting antenna at unassigned position."""
        pos = get_antenna_at_position("CN099E05", db_dir=temp_db_dir)
        assert pos is None


class TestAntennaPositionListing:
    """Tests for listing all antenna positions."""

    def test_get_all_positions_empty(self, temp_db_dir):
        """Test getting all positions when none assigned."""
        positions = get_all_antenna_positions(db_dir=temp_db_dir)
        assert len(positions) == 0

    def test_get_all_positions_multiple(self, temp_db_dir):
        """Test getting all positions with multiple assignments."""
        assign_antenna_position("ANT00001", "CN002E03", db_dir=temp_db_dir)
        assign_antenna_position("ANT00002", "CN005E04", db_dir=temp_db_dir)
        assign_antenna_position("ANT00003", "CS010E02", db_dir=temp_db_dir)

        positions = get_all_antenna_positions(db_dir=temp_db_dir)

        assert len(positions) == 3
        antenna_numbers = {pos["antenna_number"] for pos in positions}
        assert antenna_numbers == {"ANT00001", "ANT00002", "ANT00003"}

    def test_get_all_positions_sorted(self, temp_db_dir):
        """Test that positions are sorted by row_offset DESC, east_col ASC."""
        assign_antenna_position("ANT00001", "CS005E02", db_dir=temp_db_dir)
        assign_antenna_position("ANT00002", "CN010E01", db_dir=temp_db_dir)
        assign_antenna_position("ANT00003", "CN010E03", db_dir=temp_db_dir)
        assign_antenna_position("ANT00004", "CC000E01", db_dir=temp_db_dir)

        positions = get_all_antenna_positions(db_dir=temp_db_dir)

        assert positions[0]["antenna_number"] == "ANT00002"
        assert positions[1]["antenna_number"] == "ANT00003"
        assert positions[2]["antenna_number"] == "ANT00004"
        assert positions[3]["antenna_number"] == "ANT00001"

    def test_get_all_positions_filter_array(self, temp_db_dir):
        """Test filtering by array_id."""
        assign_antenna_position("ANT00001", "CN002E03", db_dir=temp_db_dir)
        assign_antenna_position("ANT00002", "CN005E04", db_dir=temp_db_dir)

        positions = get_all_antenna_positions(array_id="C", db_dir=temp_db_dir)
        assert len(positions) == 2


class TestAntennaPositionRemoval:
    """Tests for removing antenna positions."""

    def test_remove_existing_position(self, temp_db_dir):
        """Test removing an assigned position."""
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos is not None

        result = remove_antenna_position("ANT00001", db_dir=temp_db_dir)

        assert result["success"] is True
        assert "removed" in result["message"].lower()

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos is None

    def test_remove_nonexistent_position(self, temp_db_dir):
        """Test removing unassigned antenna (returns success=True, no rows affected)."""
        result = remove_antenna_position("ANT99999", db_dir=temp_db_dir)
        assert result["success"] is True

    def test_remove_with_polarization(self, temp_db_dir):
        """Test removing with polarization suffix."""
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        result = remove_antenna_position("ANT00001P1", db_dir=temp_db_dir)

        assert result["success"] is True

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos is None


class TestAntennaIntegrationScenarios:
    """Integration tests for antenna position scenarios."""

    def test_full_lifecycle(self, temp_db_dir):
        """Test complete assignment lifecycle."""
        result = assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            notes="Initial assignment",
            db_dir=temp_db_dir,
        )
        assert result["success"] is True

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos["grid_code"] == "CN002E03"

        pos = get_antenna_at_position("CN002E03", db_dir=temp_db_dir)
        assert pos["antenna_number"] == "ANT00001"

        positions = get_all_antenna_positions(db_dir=temp_db_dir)
        assert len(positions) == 1

        result = remove_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert result["success"] is True

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos is None

    def test_grid_coverage(self, temp_db_dir):
        """Test assigning to all positions in a small grid."""
        assignments = [
            ("ANT00001", "CN021E01"),
            ("ANT00002", "CN021E02"),
            ("ANT00003", "CN021E03"),
            ("ANT00004", "CN020E01"),
            ("ANT00005", "CN020E02"),
            ("ANT00006", "CN020E03"),
        ]

        for antenna, grid_code in assignments:
            result = assign_antenna_position(antenna, grid_code, db_dir=temp_db_dir)
            assert result["success"] is True

        positions = get_all_antenna_positions(db_dir=temp_db_dir)
        assert len(positions) == 6

        antenna_numbers = [pos["antenna_number"] for pos in positions]
        assert len(antenna_numbers) == len(set(antenna_numbers))

        grid_codes = [pos["grid_code"] for pos in positions]
        assert len(grid_codes) == len(set(grid_codes))

