"""
Tests for antenna position database operations.

Tests cover:
- Table initialization
- Antenna position assignment (success and failure cases)
- Duplicate detection and overwrite functionality
- Position lookups (by antenna and by grid code)
- Listing all positions
- Position removal
- Polarization stripping
"""

import os
import tempfile
from datetime import datetime

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
from casman.database.initialization import init_parts_db


@pytest.fixture
def temp_db_dir():
    """Create a temporary database directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize parts database in temp directory
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


class TestTableInitialization:
    """Tests for table initialization."""

    def test_table_creation(self, temp_db_dir):
        """Test that antenna_positions table is created."""
        import sqlite3

        db_path = os.path.join(temp_db_dir, "parts.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='antenna_positions'"
        )
        result = cursor.fetchone()
        assert result is not None

        # Check schema
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


class TestPositionAssignment:
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

        # Verify via get
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

        # Verify polarization was stripped
        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos["antenna_number"] == "ANT00001"

    def test_assign_duplicate_antenna(self, temp_db_dir):
        """Test assigning same antenna to different position (should raise)."""
        # First assignment
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        # Try to assign same antenna to different position (should raise ValueError)
        with pytest.raises(ValueError, match="already assigned"):
            assign_antenna_position(
                antenna_number="ANT00001",
                grid_code="CN003E04",
                db_dir=temp_db_dir,
            )

    def test_assign_duplicate_position(self, temp_db_dir):
        """Test assigning different antenna to same position (should raise)."""
        # First assignment
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        # Try to assign different antenna to same position (should raise ValueError)
        with pytest.raises(ValueError, match="occupied"):
            assign_antenna_position(
                antenna_number="ANT00002",
                grid_code="CN002E03",
                db_dir=temp_db_dir,
            )

    def test_assign_overwrite_antenna(self, temp_db_dir):
        """Test overwriting antenna position."""
        # First assignment
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        # Overwrite with new position
        result = assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN005E04",
            allow_overwrite=True,
            db_dir=temp_db_dir,
        )

        assert result["success"] is True
        assert (
            "updated" in result["message"].lower()
            or "assigned" in result["message"].lower()
        )

        # Verify new position
        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos["grid_code"] == "CN005E04"

    def test_assign_overwrite_position(self, temp_db_dir):
        """Test overwriting position with different antenna."""
        # First assignment
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        # Overwrite position with different antenna
        result = assign_antenna_position(
            antenna_number="ANT00002",
            grid_code="CN002E03",
            allow_overwrite=True,
            db_dir=temp_db_dir,
        )

        assert result["success"] is True

        # Verify new antenna at position
        pos = get_antenna_at_position("CN002E03", db_dir=temp_db_dir)
        assert pos["antenna_number"] == "ANT00002"

        # Verify old antenna no longer has position
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
            grid_code="CC000E00",
            db_dir=temp_db_dir,
        )

        assert result["success"] is True

        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos["row_offset"] == 0
        assert pos["grid_code"] == "CC000E00"

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


class TestPositionLookup:
    """Tests for looking up antenna positions."""

    def test_get_antenna_position_found(self, temp_db_dir):
        """Test getting position for assigned antenna."""
        # Assign position
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        # Retrieve position
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
        # Assign without polarization
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        # Retrieve with polarization suffix
        pos = get_antenna_position("ANT00001P1", db_dir=temp_db_dir)
        assert pos is not None
        assert pos["antenna_number"] == "ANT00001"

    def test_get_antenna_at_position_found(self, temp_db_dir):
        """Test getting antenna at assigned position."""
        # Assign position
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        # Retrieve by position
        pos = get_antenna_at_position("CN002E03", db_dir=temp_db_dir)

        assert pos is not None
        assert pos["antenna_number"] == "ANT00001"
        assert pos["grid_code"] == "CN002E03"

    def test_get_antenna_at_position_not_found(self, temp_db_dir):
        """Test getting antenna at unassigned position."""
        pos = get_antenna_at_position("CN099E05", db_dir=temp_db_dir)
        assert pos is None


class TestPositionListing:
    """Tests for listing all antenna positions."""

    def test_get_all_positions_empty(self, temp_db_dir):
        """Test getting all positions when none assigned."""
        positions = get_all_antenna_positions(db_dir=temp_db_dir)
        assert len(positions) == 0

    def test_get_all_positions_multiple(self, temp_db_dir):
        """Test getting all positions with multiple assignments."""
        # Assign multiple positions
        assign_antenna_position("ANT00001", "CN002E03", db_dir=temp_db_dir)
        assign_antenna_position("ANT00002", "CN005E04", db_dir=temp_db_dir)
        assign_antenna_position("ANT00003", "CS010E02", db_dir=temp_db_dir)

        # Retrieve all
        positions = get_all_antenna_positions(db_dir=temp_db_dir)

        assert len(positions) == 3
        antenna_numbers = {pos["antenna_number"] for pos in positions}
        assert antenna_numbers == {"ANT00001", "ANT00002", "ANT00003"}

    def test_get_all_positions_sorted(self, temp_db_dir):
        """Test that positions are sorted by row_offset DESC, east_col ASC."""
        # Assign positions in random order
        assign_antenna_position("ANT00001", "CS005E02", db_dir=temp_db_dir)  # row=-5
        assign_antenna_position("ANT00002", "CN010E01", db_dir=temp_db_dir)  # row=10
        assign_antenna_position("ANT00003", "CN010E03", db_dir=temp_db_dir)  # row=10
        assign_antenna_position("ANT00004", "CC000E00", db_dir=temp_db_dir)  # row=0

        positions = get_all_antenna_positions(db_dir=temp_db_dir)

        # Check order: N10E01, N10E03, C00E00, S05E02
        assert positions[0]["antenna_number"] == "ANT00002"  # CN010E01
        assert positions[1]["antenna_number"] == "ANT00003"  # CN010E03
        assert positions[2]["antenna_number"] == "ANT00004"  # CC000E00
        assert positions[3]["antenna_number"] == "ANT00001"  # CS005E02

    def test_get_all_positions_filter_array(self, temp_db_dir):
        """Test filtering by array_id."""
        # For this test, we need to allow expansion to use different arrays
        # Since we're using temp_db_dir, the config won't have allow_expansion
        # So we'll just verify filtering works with core array
        assign_antenna_position("ANT00001", "CN002E03", db_dir=temp_db_dir)
        assign_antenna_position("ANT00002", "CN005E04", db_dir=temp_db_dir)

        positions = get_all_antenna_positions(array_id="C", db_dir=temp_db_dir)
        assert len(positions) == 2


class TestPositionRemoval:
    """Tests for removing antenna positions."""

    def test_remove_existing_position(self, temp_db_dir):
        """Test removing an assigned position."""
        # Assign position
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        # Verify assigned
        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos is not None

        # Remove position
        result = remove_antenna_position("ANT00001", db_dir=temp_db_dir)

        assert result["success"] is True
        assert "removed" in result["message"].lower()

        # Verify removed
        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos is None

    def test_remove_nonexistent_position(self, temp_db_dir):
        """Test removing unassigned antenna (returns success=True, no rows affected)."""
        result = remove_antenna_position("ANT99999", db_dir=temp_db_dir)

        # Note: The function returns success even if antenna not found
        # This is idempotent behavior (delete operation succeeded, even if no rows deleted)
        assert result["success"] is True

    def test_remove_with_polarization(self, temp_db_dir):
        """Test removing with polarization suffix."""
        # Assign without polarization
        assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            db_dir=temp_db_dir,
        )

        # Remove with polarization suffix
        result = remove_antenna_position("ANT00001P1", db_dir=temp_db_dir)

        assert result["success"] is True

        # Verify removed
        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos is None


class TestIntegrationScenarios:
    """Integration tests for complex scenarios."""

    def test_full_lifecycle(self, temp_db_dir):
        """Test complete assignment lifecycle."""
        # Assign
        result = assign_antenna_position(
            antenna_number="ANT00001",
            grid_code="CN002E03",
            notes="Initial assignment",
            db_dir=temp_db_dir,
        )
        assert result["success"] is True

        # Verify by antenna
        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos["grid_code"] == "CN002E03"

        # Verify by position
        pos = get_antenna_at_position("CN002E03", db_dir=temp_db_dir)
        assert pos["antenna_number"] == "ANT00001"

        # Verify in list
        positions = get_all_antenna_positions(db_dir=temp_db_dir)
        assert len(positions) == 1

        # Remove
        result = remove_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert result["success"] is True

        # Verify removed
        pos = get_antenna_position("ANT00001", db_dir=temp_db_dir)
        assert pos is None

    def test_grid_coverage(self, temp_db_dir):
        """Test assigning to all positions in a small grid."""
        # Assign to first 3 rows, all columns
        assignments = [
            ("ANT00001", "CN021E00"),
            ("ANT00002", "CN021E01"),
            ("ANT00003", "CN021E02"),
            ("ANT00004", "CN020E00"),
            ("ANT00005", "CN020E01"),
            ("ANT00006", "CN020E02"),
        ]

        for antenna, grid_code in assignments:
            result = assign_antenna_position(antenna, grid_code, db_dir=temp_db_dir)
            assert result["success"] is True

        # Verify all assigned
        positions = get_all_antenna_positions(db_dir=temp_db_dir)
        assert len(positions) == 6

        # Verify no duplicates
        antenna_numbers = [pos["antenna_number"] for pos in positions]
        assert len(antenna_numbers) == len(set(antenna_numbers))

        grid_codes = [pos["grid_code"] for pos in positions]
        assert len(grid_codes) == len(set(grid_codes))
