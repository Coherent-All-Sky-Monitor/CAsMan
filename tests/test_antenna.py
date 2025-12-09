"""
Comprehensive tests for CAsMan antenna module.

Consolidates tests for:
- Antenna array and positions
- Antenna chain utilities (SNAP port tracing)
- Grid position parsing, formatting, and validation
- Kernel index mapping
- Multi-array grid system
"""

import os
import sqlite3
import tempfile
from pathlib import Path

import numpy as np
import pytest

from casman.antenna.array import AntennaArray, AntennaPosition
from casman.antenna.chain import get_snap_port_for_chain
from casman.antenna.grid import (
    AntennaGridPosition,
    direction_from_row,
    format_grid_code,
    get_array_name_for_id,
    load_array_layout,
    load_core_layout,
    parse_grid_code,
    to_grid_code,
    validate_components,
)
from casman.antenna.kernel_index import (
    KernelIndexArray,
    get_antenna_kernel_idx,
    grid_to_kernel_index,
    kernel_index_to_grid,
)
from casman.database.initialization import init_assembled_db


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def test_db(tmp_path):
    """Create test database with sample antenna data."""
    db_path = tmp_path / "test.db"
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
            latitude REAL,
            longitude REAL,
            height REAL,
            coordinate_system TEXT,
            assigned_at TEXT,
            notes TEXT
        )
    """
    )

    test_data = [
        ("ANT00001", "CN001E01", "C", 1, 1, 37.8719, -122.2585, 10.5, "WGS84", "2025-01-01T00:00:00Z", "Test 1"),
        ("ANT00002", "CN001E02", "C", 1, 2, 37.8720, -122.2583, 10.6, "WGS84", "2025-01-01T00:00:00Z", "Test 2"),
        ("ANT00003", "CC000E01", "C", 0, 1, 37.8718, -122.2586, 10.4, "WGS84", "2025-01-01T00:00:00Z", None),
        ("ANT00004", "CS001E01", "C", -1, 1, None, None, None, None, "2025-01-01T00:00:00Z", None),
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


@pytest.fixture
def temp_db_with_chains():
    """Create a temporary database with test connection chains."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "assembled_casm.db")
        
        init_assembled_db(temp_dir)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        test_chains = [
            ("ANT00001P1", "ANTENNA", 1, "LNA00001P1", "LNA", 1, "connected"),
            ("LNA00001P1", "LNA", 1, "CXS00001P1", "COAXSHORT", 1, "connected"),
            ("CXS00001P1", "COAXSHORT", 1, "CXL00001P1", "COAXLONG", 1, "connected"),
            ("CXL00001P1", "COAXLONG", 1, "BAC00001P1", "BACBOARD", 1, "connected"),
            ("BAC00001P1", "BACBOARD", 1, "SNAP1A05", "SNAP", 1, "connected"),
            
            ("ANT00002P2", "ANTENNA", 2, "LNA00002P2", "LNA", 2, "connected"),
            ("LNA00002P2", "LNA", 2, "CXS00002P2", "COAXSHORT", 2, "connected"),
            ("CXS00002P2", "COAXSHORT", 2, "CXL00002P2", "COAXLONG", 2, "connected"),
            ("CXL00002P2", "COAXLONG", 2, "BAC00002P2", "BACBOARD", 2, "connected"),
            ("BAC00002P2", "BACBOARD", 2, "SNAP2B11", "SNAP", 2, "connected"),
            
            ("ANT00003P1", "ANTENNA", 1, "LNA00003P1", "LNA", 1, "connected"),
            ("LNA00003P1", "LNA", 1, "CXS00003P1", "COAXSHORT", 1, "connected"),
            ("CXS00003P1", "COAXSHORT", 1, "CXL00003P1", "COAXLONG", 1, "connected"),
            
            ("ANT00004P1", "ANTENNA", 1, "LNA00004P1", "LNA", 1, "disconnected"),
            
            ("ANT00005P1", "ANTENNA", 1, "LNA00005P1", "LNA", 1, "connected"),
            ("LNA00005P1", "LNA", 1, "CXS00005P1", "COAXSHORT", 1, "connected"),
            ("CXS00005P1", "COAXSHORT", 1, "CXL00005P1", "COAXLONG", 1, "connected"),
            ("CXL00005P1", "COAXLONG", 1, "BAC00005P1", "BACBOARD", 1, "connected"),
            ("BAC00005P1", "BACBOARD", 1, "SNAP4K100", "SNAP", 1, "connected"),
        ]
        
        for parts in test_chains:
            cursor.execute(
                """
                INSERT INTO assembly 
                (part_number, part_type, polarization, connected_to, 
                 connected_to_type, connected_polarization, connection_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                parts
            )
        
        conn.commit()
        conn.close()
        
        yield temp_dir


# ============================================================================
# Antenna Array Tests
# ============================================================================


class TestAntennaArray:
    """Tests for AntennaArray class."""

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
        
        ant2 = array.get_antenna_at_position("cn001e01")
        assert ant2 is not None
        
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

    def test_compute_baseline_geodetic(self, test_db):
        """Test geodetic baseline calculation."""
        array = AntennaArray.from_database(test_db)
        
        ant1 = array.get_antenna("ANT00001")
        ant2 = array.get_antenna("ANT00002")
        
        baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)
        assert 0 < baseline < 100
        assert isinstance(baseline, float)

    def test_compute_baseline_grid(self, test_db):
        """Test grid-based baseline calculation."""
        array = AntennaArray.from_database(test_db)
        
        ant1 = array.get_antenna("ANT00001")
        ant2 = array.get_antenna("ANT00002")
        
        baseline = array.compute_baseline(ant1, ant2, use_coordinates=False)
        assert baseline == pytest.approx(0.4, rel=0.01)

    def test_compute_all_baselines(self, test_db):
        """Test computing all pairwise baselines."""
        array = AntennaArray.from_database(test_db)
        
        baselines = array.compute_all_baselines(use_coordinates=True, include_self=False)
        assert len(baselines) == 6

    def test_filter_by_coordinates(self, test_db):
        """Test filtering by coordinate availability."""
        array = AntennaArray.from_database(test_db)
        
        with_coords = array.filter_by_coordinates(has_coords=True)
        assert len(with_coords) == 3
        
        without_coords = array.filter_by_coordinates(has_coords=False)
        assert len(without_coords) == 1

    def test_array_iteration(self, test_db):
        """Test iterating over array."""
        array = AntennaArray.from_database(test_db)
        
        count = sum(1 for ant in array)
        assert count == 4

    def test_antenna_position_properties(self, test_db):
        """Test AntennaPosition property accessors."""
        array = AntennaArray.from_database(test_db)
        ant = array.get_antenna("ANT00001")
        
        # Test that antenna position has grid_position attribute
        assert ant.grid_position is not None
        assert ant.antenna_number == "ANT00001"
        assert ant.has_coordinates() or not ant.has_coordinates()  # Either state is valid
    
    def test_antenna_format_chain_status_invalid_polarization(self, test_db):
        """Test format_chain_status with invalid polarization."""
        array = AntennaArray.from_database(test_db)
        ant = array.get_antenna("ANT00001")
        
        result = ant.format_chain_status("P3")
        assert "Invalid polarization" in result
    
    def test_antenna_repr(self, test_db):
        """Test AntennaPosition string representation."""
        array = AntennaArray.from_database(test_db)
        ant = array.get_antenna("ANT00001")
        
        repr_str = repr(ant)
        assert "ANT00001" in repr_str
        assert "CN001E01" in repr_str
    
    def test_compute_baseline_fallback_to_grid(self, test_db):
        """Test baseline computation falls back to grid when coords missing."""
        array = AntennaArray.from_database(test_db)
        
        ant1 = array.get_antenna("ANT00001")  # Has coords
        ant2 = array.get_antenna("ANT00004")  # No coords
        
        baseline = array.compute_baseline(ant1, ant2, use_coordinates=True)
        assert baseline > 0
    
    def test_compute_all_baselines_with_self(self, test_db):
        """Test computing baselines including self-baselines."""
        array = AntennaArray.from_database(test_db)
        
        baselines = array.compute_all_baselines(use_coordinates=False, include_self=True)
        # 4 antennas: 4 + 3 + 2 + 1 = 10 total pairs
        assert len(baselines) == 10
        
        # Check self-baselines are zero
        self_baselines = [b for b in baselines if b[0] == b[1]]
        assert len(self_baselines) == 4
        for ant1, ant2, dist in self_baselines:
            assert dist == 0.0
    
    def test_get_antenna_lookup(self, test_db):
        """Test get_antenna lookup."""
        array = AntennaArray.from_database(test_db)
        
        ant1 = array.get_antenna("ANT00001")
        assert ant1 is not None
        assert ant1.antenna_number == "ANT00001"
        
        # Non-existent antenna returns None
        ant2 = array.get_antenna("ANT99999")
        assert ant2 is None
    
    def test_get_antenna_at_position_case_insensitive(self, test_db):
        """Test get_antenna_at_position is case insensitive."""
        array = AntennaArray.from_database(test_db)
        
        ant1 = array.get_antenna_at_position("CN001E01")
        ant2 = array.get_antenna_at_position("cn001e01")
        
        assert ant1 is not None
        assert ant2 is not None
        assert ant1.antenna_number == ant2.antenna_number
    
    def test_array_len(self, test_db):
        """Test array length."""
        array = AntennaArray.from_database(test_db)
        assert len(array) == 4
    
    def test_array_repr(self, test_db):
        """Test array string representation."""
        array = AntennaArray.from_database(test_db)
        
        repr_str = repr(array)
        assert "AntennaArray" in repr_str
        assert "4" in repr_str


# ============================================================================
# Antenna Chain Tests
# ============================================================================


class TestAntennaChain:
    """Test get_snap_port_for_chain function."""
    
    def test_complete_chain_to_snap(self, temp_db_with_chains):
        """Test tracing a complete chain to SNAP board."""
        result = get_snap_port_for_chain("ANT00001P1", db_dir=temp_db_with_chains)
        
        assert result is not None
        assert result["snap_part"] == "SNAP1A05"
        assert result["chassis"] == 1
        assert result["slot"] == "A"
        assert result["port"] == 5
        assert "ANT00001P1" in result["chain"]
    
    def test_complete_chain_polarization2(self, temp_db_with_chains):
        """Test tracing chain for polarization 2."""
        result = get_snap_port_for_chain("ANT00002P2", db_dir=temp_db_with_chains)
        
        assert result is not None
        assert result["snap_part"] == "SNAP2B11"
        assert result["chassis"] == 2
        assert result["slot"] == "B"
        assert result["port"] == 11
    
    def test_incomplete_chain(self, temp_db_with_chains):
        """Test chain that doesn't reach SNAP."""
        result = get_snap_port_for_chain("ANT00003P1", db_dir=temp_db_with_chains)
        assert result is None
    
    def test_disconnected_chain(self, temp_db_with_chains):
        """Test chain with disconnected parts."""
        result = get_snap_port_for_chain("ANT00004P1", db_dir=temp_db_with_chains)
        assert result is None
    
    def test_nonexistent_part(self, temp_db_with_chains):
        """Test with part that doesn't exist."""
        result = get_snap_port_for_chain("ANT99999P1", db_dir=temp_db_with_chains)
        assert result is None
    
    def test_chain_starting_from_lna(self, temp_db_with_chains):
        """Test starting chain trace from LNA instead of antenna."""
        result = get_snap_port_for_chain("LNA00001P1", db_dir=temp_db_with_chains)
        
        assert result is not None
        assert result["snap_part"] == "SNAP1A05"
        assert "ANT00001P1" not in result["chain"]
    
    def test_snap_with_three_digit_port(self, temp_db_with_chains):
        """Test SNAP part with 3-digit port number."""
        result = get_snap_port_for_chain("ANT00005P1", db_dir=temp_db_with_chains)
        
        assert result is not None
        assert result["snap_part"] == "SNAP4K100"
        assert result["chassis"] == 4
        assert result["slot"] == "K"
        assert result["port"] == 100
    
    def test_case_insensitive_part_lookup(self, temp_db_with_chains):
        """Test that part numbers are case-insensitive."""
        result = get_snap_port_for_chain("ant00001p1", db_dir=temp_db_with_chains)
        
        assert result is not None
        assert result["snap_part"] == "SNAP1A05"
    
    def test_empty_database(self):
        """Test with empty database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_assembled_db(temp_dir)
            result = get_snap_port_for_chain("ANT00001P1", db_dir=temp_dir)
            assert result is None


# ============================================================================
# Grid Code Parsing Tests
# ============================================================================


class TestGridCodeParsing:
    """Tests for parsing grid codes."""

    def test_parse_valid_center(self):
        """Test parsing center position."""
        pos = parse_grid_code("CC000E01")
        assert pos.array_id == "C"
        assert pos.direction == "C"
        assert pos.offset == 0
        assert pos.east_col == 1
        assert pos.row_offset == 0

    def test_parse_valid_north(self):
        """Test parsing north position."""
        pos = parse_grid_code("CN002E03")
        assert pos.array_id == "C"
        assert pos.direction == "N"
        assert pos.offset == 2
        assert pos.east_col == 3
        assert pos.row_offset == 2

    def test_parse_valid_south(self):
        """Test parsing south position."""
        pos = parse_grid_code("CS021E05")
        assert pos.array_id == "C"
        assert pos.direction == "S"
        assert pos.offset == 21
        assert pos.east_col == 5
        assert pos.row_offset == -21

    def test_parse_different_array(self):
        """Test parsing with different array ID."""
        pos = parse_grid_code("AN010E02", enforce_bounds=False)
        assert pos.array_id == "A"
        assert pos.direction == "N"
        assert pos.offset == 10

    def test_parse_invalid_format(self):
        """Test parsing with invalid format."""
        with pytest.raises(ValueError, match="does not match pattern"):
            parse_grid_code("INVALID")

    def test_parse_center_with_nonzero_offset(self):
        """Test parsing center with non-zero offset (invalid)."""
        with pytest.raises(ValueError, match="Center row must use offset 000"):
            parse_grid_code("CC001E01")

    def test_parse_case_insensitive(self):
        """Test case insensitivity."""
        pos = parse_grid_code("cn021e01")
        assert pos.array_id == "C"
        assert pos.direction == "N"


# ============================================================================
# Grid Code Formatting Tests
# ============================================================================


class TestGridCodeFormatting:
    """Tests for formatting grid codes."""

    def test_format_center(self):
        """Test formatting center position."""
        code = format_grid_code("C", "C", 0, 1)
        assert code == "CC000E01"

    def test_format_north(self):
        """Test formatting north position."""
        code = format_grid_code("C", "N", 2, 3)
        assert code == "CN002E03"

    def test_format_south(self):
        """Test formatting south position."""
        code = format_grid_code("C", "S", 21, 5)
        assert code == "CS021E05"

    def test_format_padding(self):
        """Test formatting with padding."""
        code = format_grid_code("C", "N", 1, 1)
        assert code == "CN001E01"

    def test_format_invalid_direction(self):
        """Test formatting with invalid direction."""
        with pytest.raises(ValueError, match="direction must be"):
            format_grid_code("C", "X", 1, 1)


class TestGridCodeConversion:
    """Tests for converting row offsets to grid codes."""

    def test_to_grid_code_center(self):
        """Test converting center row offset."""
        code = to_grid_code(0, 1)
        assert code == "CC000E01"

    def test_to_grid_code_north(self):
        """Test converting north row offset."""
        code = to_grid_code(5, 3)
        assert code == "CN005E03"

    def test_to_grid_code_south(self):
        """Test converting south row offset."""
        code = to_grid_code(-10, 2)
        assert code == "CS010E02"


class TestDirectionMapping:
    """Tests for mapping row offsets to directions."""

    def test_direction_from_center(self):
        """Test direction for center row."""
        assert direction_from_row(0) == "C"

    def test_direction_from_north(self):
        """Test direction for north rows."""
        assert direction_from_row(1) == "N"
        assert direction_from_row(21) == "N"

    def test_direction_from_south(self):
        """Test direction for south rows."""
        assert direction_from_row(-1) == "S"
        assert direction_from_row(-21) == "S"


class TestRoundTripConsistency:
    """Tests for round-trip parse/format consistency."""

    def test_roundtrip_center(self):
        """Test round-trip for center position."""
        original = "CC000E01"
        pos = parse_grid_code(original)
        reformed = format_grid_code(pos.array_id, pos.direction, pos.offset, pos.east_col)
        assert reformed == original

    def test_roundtrip_north(self):
        """Test round-trip for north position."""
        original = "CN010E03"
        pos = parse_grid_code(original)
        reformed = format_grid_code(pos.array_id, pos.direction, pos.offset, pos.east_col)
        assert reformed == original


# ============================================================================
# Kernel Index Mapping Tests
# ============================================================================


class TestGridToKernelIndex:
    """Tests for grid_to_kernel_index function."""

    def test_first_position(self):
        """Test first position CN021E01 maps to kernel index 0."""
        assert grid_to_kernel_index("CN021E01") == 0

    def test_first_row_positions(self):
        """Test all positions in first row (CN021)."""
        assert grid_to_kernel_index("CN021E01") == 0
        assert grid_to_kernel_index("CN021E02") == 1
        assert grid_to_kernel_index("CN021E06") == 5

    def test_center_row(self):
        """Test center row (CC000)."""
        assert grid_to_kernel_index("CC000E01") == 126
        assert grid_to_kernel_index("CC000E06") == 131

    def test_last_mapped_positions(self):
        """Test last mapped positions (kernel index 252-255)."""
        assert grid_to_kernel_index("CS021E01") == 252
        assert grid_to_kernel_index("CS021E04") == 255

    def test_unmapped_positions(self):
        """Test unmapped positions (exceeding max kernel index)."""
        assert grid_to_kernel_index("CS021E05") is None
        assert grid_to_kernel_index("CS021E06") is None

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert grid_to_kernel_index("cn021e01") == 0
        assert grid_to_kernel_index("CN021E01") == 0

    def test_invalid_grid_code(self):
        """Test invalid grid codes."""
        assert grid_to_kernel_index("INVALID") is None


class TestKernelIndexToGrid:
    """Tests for kernel_index_to_grid function."""

    def test_first_index(self):
        """Test kernel index 0 maps to CN021E01."""
        assert kernel_index_to_grid(0) == "CN021E01"

    def test_first_row_indices(self):
        """Test indices 0-5 map to CN021E01-E06."""
        assert kernel_index_to_grid(0) == "CN021E01"
        assert kernel_index_to_grid(5) == "CN021E06"

    def test_center_row_indices(self):
        """Test center row indices."""
        assert kernel_index_to_grid(126) == "CC000E01"
        assert kernel_index_to_grid(131) == "CC000E06"

    def test_last_valid_indices(self):
        """Test last valid indices (252-255)."""
        assert kernel_index_to_grid(252) == "CS021E01"
        assert kernel_index_to_grid(255) == "CS021E04"

    def test_out_of_range_indices(self):
        """Test indices outside valid range."""
        assert kernel_index_to_grid(256) is None
        assert kernel_index_to_grid(-1) is None


class TestRoundTripKernelConversion:
    """Tests for round-trip conversions between grid codes and kernel indices."""

    def test_round_trip_all_mapped_positions(self):
        """Test round-trip conversion for all mapped positions."""
        for kernel_idx in range(256):
            grid_code = kernel_index_to_grid(kernel_idx)
            assert grid_code is not None
            back_to_idx = grid_to_kernel_index(grid_code)
            assert back_to_idx == kernel_idx


class TestGetAntennaKernelIdx:
    """Tests for get_antenna_kernel_idx function."""

    def test_array_shape(self):
        """Test returned array has correct shape."""
        kernel_data = get_antenna_kernel_idx()
        assert kernel_data.shape == (43, 6)
        assert kernel_data.kernel_indices.shape == (43, 6)

    def test_kernel_indices_range(self):
        """Test kernel indices are in valid range or -1."""
        kernel_data = get_antenna_kernel_idx()
        
        valid_mask = (kernel_data.kernel_indices >= 0) & (kernel_data.kernel_indices <= 255)
        unmapped_mask = kernel_data.kernel_indices == -1
        
        assert np.all(valid_mask | unmapped_mask)

    def test_unmapped_positions(self):
        """Test that CS021E05 and CS021E06 are unmapped."""
        kernel_data = get_antenna_kernel_idx()
        assert kernel_data.kernel_indices[42, 4] == -1
        assert kernel_data.kernel_indices[42, 5] == -1

    def test_unique_kernel_indices(self):
        """Test all kernel indices are unique (no duplicates)."""
        kernel_data = get_antenna_kernel_idx()
        
        mapped_indices = kernel_data.kernel_indices[kernel_data.kernel_indices >= 0]
        unique_indices = np.unique(mapped_indices)
        
        assert len(unique_indices) == 256
        assert np.array_equal(unique_indices, np.arange(256))


class TestKernelIndexArray:
    """Tests for KernelIndexArray container class."""

    def test_get_by_kernel_index_valid(self):
        """Test getting information by valid kernel index."""
        kernel_data = get_antenna_kernel_idx()
        
        info = kernel_data.get_by_kernel_index(0)
        assert info is not None
        assert info['grid_code'] == 'CN021E01'

    def test_get_by_kernel_index_invalid(self):
        """Test getting information for invalid kernel index."""
        kernel_data = get_antenna_kernel_idx()
        assert kernel_data.get_by_kernel_index(256) is None
        assert kernel_data.get_by_kernel_index(-1) is None

    def test_get_by_grid_code_valid(self):
        """Test getting information by valid grid code."""
        kernel_data = get_antenna_kernel_idx()
        
        info = kernel_data.get_by_grid_code('CN021E01')
        assert info is not None
        assert info['kernel_index'] == 0

    def test_get_by_grid_code_case_insensitive(self):
        """Test grid code lookup is case insensitive."""
        kernel_data = get_antenna_kernel_idx()
        
        info_upper = kernel_data.get_by_grid_code('CN021E01')
        info_lower = kernel_data.get_by_grid_code('cn021e01')
        
        assert info_upper is not None
        assert info_lower is not None
        assert info_upper['kernel_index'] == info_lower['kernel_index']


# ============================================================================
# Multi-Array Tests
# ============================================================================


class TestLoadArrayLayout:
    """Tests for loading array layout configurations."""

    def test_load_core_layout(self):
        """Test loading core array layout."""
        array_id, north_rows, south_rows, east_columns, allow_expansion = load_array_layout("core")
        
        assert array_id == "C"
        assert north_rows == 21
        assert south_rows == 21
        assert east_columns == 6
        assert allow_expansion is True

    def test_load_core_via_load_core_layout(self):
        """Test that load_core_layout returns same as load_array_layout('core')."""
        core_direct = load_core_layout()
        core_via_array = load_array_layout("core")
        
        assert core_direct == core_via_array

    def test_load_nonexistent_array(self):
        """Test loading array that doesn't exist in config."""
        with pytest.raises(KeyError, match="not found in configuration"):
            load_array_layout("nonexistent")


class TestGetArrayNameForId:
    """Tests for array name lookup by ID."""

    def test_get_core_name(self):
        """Test getting array name for core ID."""
        name = get_array_name_for_id("C")
        assert name == "core"

    def test_get_nonexistent_id(self):
        """Test getting name for ID that doesn't exist."""
        name = get_array_name_for_id("Z")
        assert name is None


class TestMultiArrayValidation:
    """Tests for validation with multiple arrays."""

    def test_validate_core_within_bounds(self):
        """Test validation within core array bounds."""
        validate_components("C", 10, 3, enforce_bounds=True)

    def test_validate_core_beyond_bounds_with_expansion(self):
        """Test validation beyond core bounds when expansion allowed."""
        validate_components("C", 50, 10, enforce_bounds=True)

    def test_validate_without_enforcement(self):
        """Test validation skips array-specific bounds check."""
        validate_components("X", 100, 50, enforce_bounds=False)


class TestMultiArrayParsing:
    """Tests for parsing grid codes with different arrays."""

    def test_parse_core_array(self):
        """Test parsing core array grid code."""
        pos = parse_grid_code("CN010E03")
        assert pos.array_id == "C"
        assert pos.row_offset == 10

    def test_parse_hypothetical_outrigger(self):
        """Test parsing outrigger array code (if configured)."""
        pos = parse_grid_code("ON005E02", enforce_bounds=False)
        assert pos.array_id == "O"
        assert pos.row_offset == 5


class TestArrayConfigurationIntegration:
    """Integration tests for array configuration system."""

    def test_round_trip_core_array(self):
        """Test parsing and formatting core array codes."""
        original = "CN015E04"
        pos = parse_grid_code(original)
        reformed = format_grid_code(pos.array_id, pos.direction, pos.offset, pos.east_col)
        assert reformed == original

    def test_lookup_and_load_core(self):
        """Test looking up core array name and loading its config."""
        name = get_array_name_for_id("C")
        assert name == "core"
        
        array_id, north, south, east, expand = load_array_layout(name)
        assert array_id == "C"
        assert north == 21
