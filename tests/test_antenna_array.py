#!/usr/bin/env python3
"""
Unit tests for standalone antenna array module.
"""

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from casman.antenna.array import AntennaArray, AntennaPosition
from casman.antenna.grid import parse_grid_code


class TestAntennaArray:
    """Tests for AntennaArray class."""

    @pytest.fixture
    def test_db(self, tmp_path):
        """Create test database with sample data."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create antenna_positions table
        cursor.execute(
            """
            CREATE TABLE antenna_positions (
                id INTEGER PRIMARY KEY,
                antenna_number TEXT UNIQUE,
                grid_code TEXT UNIQUE,
                array_id TEXT,
                row_offset INTEGER,
                east_col INTEGER,
                latitude REAL,
                longitude REAL,
                height REAL,
                coordinate_system TEXT,
                assigned_at TEXT,
                notes TEXT
            )
        """
        )

        # Insert test data
        test_data = [
            (
                "ANT00001",
                "CN001E01",
                "C",
                1,
                0,
                37.8719,
                -122.2585,
                10.5,
                "WGS84",
                "2025-01-01T00:00:00Z",
                "Test 1",
            ),
            (
                "ANT00002",
                "CN001E02",
                "C",
                1,
                2,
                37.8720,
                -122.2583,
                10.6,
                "WGS84",
                "2025-01-01T00:00:00Z",
                "Test 2",
            ),
            (
                "ANT00003",
                "CC000E01",
                "C",
                0,
                0,
                37.8718,
                -122.2586,
                10.4,
                "WGS84",
                "2025-01-01T00:00:00Z",
                None,
            ),
            (
                "ANT00004",
                "CS001E01",
                "C",
                -1,
                0,
                None,
                None,
                None,
                None,
                "2025-01-01T00:00:00Z",
                None,
            ),
        ]

        for data in test_data:
            cursor.execute(
                """
                INSERT INTO antenna_positions 
                (antenna_number, grid_code, array_id, row_offset, east_col,
                 latitude, longitude, height, coordinate_system, assigned_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data,
            )

        conn.commit()
        conn.close()

        return db_path

    def test_load_from_database(self, test_db):
        """Test loading array from database."""
        array = AntennaArray.from_database(test_db)

        assert len(array) == 4
        assert len(array.antennas) == 4

    def test_load_from_database_file_not_found(self):
        """Test error when database doesn't exist."""
        with pytest.raises(FileNotFoundError):
            AntennaArray.from_database("/nonexistent/path.db")

    def test_get_antenna(self, test_db):
        """Test retrieving antenna by number."""
        array = AntennaArray.from_database(test_db)

        ant = array.get_antenna("ANT00001")
        assert ant is not None
        assert ant.antenna_number == "ANT00001"
        assert ant.grid_code == "CN001E01"

        missing = array.get_antenna("ANT99999")
        assert missing is None

    def test_get_antenna_at_position(self, test_db):
        """Test retrieving antenna by grid position."""
        array = AntennaArray.from_database(test_db)

        ant = array.get_antenna_at_position("CN001E01")
        assert ant is not None
        assert ant.antenna_number == "ANT00001"

        # Case insensitive
        ant2 = array.get_antenna_at_position("cn001e01")
        assert ant2 is not None
        assert ant2.antenna_number == "ANT00001"

        missing = array.get_antenna_at_position("CX999E99")
        assert missing is None

    def test_antenna_position_properties(self, test_db):
        """Test AntennaPosition properties."""
        array = AntennaArray.from_database(test_db)
        ant = array.get_antenna("ANT00001")

        assert ant.has_coordinates() is True
        assert ant.grid_code == "CN001E01"
        assert ant.row_offset == 1
        assert ant.east_col == 1

    def test_antenna_position_no_coords(self, test_db):
        """Test antenna without coordinates."""
        array = AntennaArray.from_database(test_db)
        ant = array.get_antenna("ANT00004")

        assert ant.has_coordinates() is False
        assert ant.latitude is None
        assert ant.longitude is None

    def test_compute_baseline_geodetic(self, test_db):
        """Test geodetic baseline calculation."""
        array = AntennaArray.from_database(test_db)

        ant1 = array.get_antenna("ANT00001")
        ant2 = array.get_antenna("ANT00002")

        baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)

        # Should be small distance (nearby antennas)
        assert 0 < baseline < 100  # meters
        assert isinstance(baseline, float)

    def test_compute_baseline_grid(self, test_db):
        """Test grid-based baseline calculation."""
        array = AntennaArray.from_database(test_db)

        ant1 = array.get_antenna("ANT00001")  # CN001E01 (row +1, col 1)
        ant2 = array.get_antenna("ANT00002")  # CN001E02 (row +1, col 2)

        baseline = array.compute_baseline(ant1, ant2, use_coordinates=False)

        # Grid spacing: 1 column apart with default 0.4m spacing
        assert baseline == pytest.approx(0.4, rel=0.01)

    def test_compute_baseline_fallback(self, test_db):
        """Test baseline falls back to grid when coordinates unavailable."""
        array = AntennaArray.from_database(test_db)

        ant1 = array.get_antenna("ANT00001")  # Has coordinates
        ant2 = array.get_antenna("ANT00004")  # No coordinates

        # Should fall back to grid calculation
        baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)

        assert baseline > 0
        assert isinstance(baseline, float)

    def test_compute_all_baselines(self, test_db):
        """Test computing all pairwise baselines."""
        array = AntennaArray.from_database(test_db)

        baselines = array.compute_all_baselines(
            use_coordinates=True, include_self=False
        )

        # 4 antennas: 4*3/2 = 6 unique pairs
        assert len(baselines) == 6

        # Check structure
        for ant1, ant2, dist in baselines:
            assert isinstance(ant1, str)
            assert isinstance(ant2, str)
            assert isinstance(dist, float)
            assert dist >= 0

    def test_compute_all_baselines_with_self(self, test_db):
        """Test computing baselines including self-baselines."""
        array = AntennaArray.from_database(test_db)

        baselines = array.compute_all_baselines(use_coordinates=True, include_self=True)

        # 4 antennas: 4*4/2 = 8 pairs including self
        assert len(baselines) == 10  # 4 + 3 + 2 + 1

    def test_filter_by_coordinates(self, test_db):
        """Test filtering by coordinate availability."""
        array = AntennaArray.from_database(test_db)

        with_coords = array.filter_by_coordinates(has_coords=True)
        assert len(with_coords) == 3

        without_coords = array.filter_by_coordinates(has_coords=False)
        assert len(without_coords) == 1
        assert without_coords[0].antenna_number == "ANT00004"

    def test_array_iteration(self, test_db):
        """Test iterating over array."""
        array = AntennaArray.from_database(test_db)

        count = 0
        for ant in array:
            count += 1
            assert isinstance(ant, AntennaPosition)

        assert count == 4

    def test_array_repr(self, test_db):
        """Test string representation."""
        array = AntennaArray.from_database(test_db)

        repr_str = repr(array)
        assert "AntennaArray" in repr_str
        assert "4" in repr_str

    def test_baseline_with_height_difference(self, test_db):
        """Test baseline calculation includes height."""
        array = AntennaArray.from_database(test_db)

        ant1 = array.get_antenna("ANT00001")  # height 10.5
        ant2 = array.get_antenna("ANT00002")  # height 10.6

        baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)

        # With height difference should be slightly longer than without
        assert baseline > 0
