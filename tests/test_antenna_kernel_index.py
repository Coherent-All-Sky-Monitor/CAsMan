"""Tests for antenna kernel index mapping functions."""

import pytest
import numpy as np

from casman.antenna.kernel_index import (
    KernelIndexArray,
    grid_to_kernel_index,
    kernel_index_to_grid,
    get_antenna_kernel_idx,
)


class TestGridToKernelIndex:
    """Tests for grid_to_kernel_index function."""

    def test_first_position(self):
        """Test first position CN021E01 maps to kernel index 0."""
        assert grid_to_kernel_index("CN021E01") == 0

    def test_first_row_positions(self):
        """Test all positions in first row (CN021)."""
        assert grid_to_kernel_index("CN021E01") == 0
        assert grid_to_kernel_index("CN021E02") == 1
        assert grid_to_kernel_index("CN021E03") == 2
        assert grid_to_kernel_index("CN021E04") == 3
        assert grid_to_kernel_index("CN021E05") == 4
        assert grid_to_kernel_index("CN021E06") == 5

    def test_second_row_positions(self):
        """Test positions in second row (CN020)."""
        assert grid_to_kernel_index("CN020E01") == 6
        assert grid_to_kernel_index("CN020E02") == 7
        assert grid_to_kernel_index("CN020E06") == 11

    def test_center_row(self):
        """Test center row (CC000)."""
        assert grid_to_kernel_index("CC000E01") == 126  # Row 21 (0-indexed)
        assert grid_to_kernel_index("CC000E06") == 131

    def test_last_mapped_positions(self):
        """Test last mapped positions (kernel index 252-255)."""
        # Kernel index 252-255 should be CS021E01-E04
        assert grid_to_kernel_index("CS021E01") == 252
        assert grid_to_kernel_index("CS021E02") == 253
        assert grid_to_kernel_index("CS021E03") == 254
        assert grid_to_kernel_index("CS021E04") == 255

    def test_unmapped_positions(self):
        """Test unmapped positions (exceeding max kernel index)."""
        # CS021E05 and CS021E06 exceed max_index=255
        assert grid_to_kernel_index("CS021E05") is None
        assert grid_to_kernel_index("CS021E06") is None

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert grid_to_kernel_index("cn021e01") == 0
        assert grid_to_kernel_index("CN021E01") == 0
        assert grid_to_kernel_index("Cn021E01") == 0

    def test_invalid_grid_code(self):
        """Test invalid grid codes."""
        assert grid_to_kernel_index("INVALID") is None
        assert grid_to_kernel_index("XX999E99") is None
        assert grid_to_kernel_index("") is None


class TestKernelIndexToGrid:
    """Tests for kernel_index_to_grid function."""

    def test_first_index(self):
        """Test kernel index 0 maps to CN021E01."""
        assert kernel_index_to_grid(0) == "CN021E01"

    def test_first_row_indices(self):
        """Test indices 0-5 map to CN021E01-E06."""
        assert kernel_index_to_grid(0) == "CN021E01"
        assert kernel_index_to_grid(1) == "CN021E02"
        assert kernel_index_to_grid(2) == "CN021E03"
        assert kernel_index_to_grid(3) == "CN021E04"
        assert kernel_index_to_grid(4) == "CN021E05"
        assert kernel_index_to_grid(5) == "CN021E06"

    def test_second_row_indices(self):
        """Test indices 6-11 map to CN020E01-E06."""
        assert kernel_index_to_grid(6) == "CN020E01"
        assert kernel_index_to_grid(7) == "CN020E02"
        assert kernel_index_to_grid(11) == "CN020E06"

    def test_center_row_indices(self):
        """Test center row indices."""
        assert kernel_index_to_grid(126) == "CC000E01"
        assert kernel_index_to_grid(131) == "CC000E06"

    def test_last_valid_indices(self):
        """Test last valid indices (252-255)."""
        assert kernel_index_to_grid(252) == "CS021E01"
        assert kernel_index_to_grid(253) == "CS021E02"
        assert kernel_index_to_grid(254) == "CS021E03"
        assert kernel_index_to_grid(255) == "CS021E04"

    def test_out_of_range_indices(self):
        """Test indices outside valid range."""
        assert kernel_index_to_grid(256) is None
        assert kernel_index_to_grid(1000) is None
        assert kernel_index_to_grid(-1) is None


class TestRoundTripConversion:
    """Tests for round-trip conversions between grid codes and kernel indices."""

    def test_round_trip_all_mapped_positions(self):
        """Test round-trip conversion for all mapped positions."""
        # Test all kernel indices 0-255
        for kernel_idx in range(256):
            grid_code = kernel_index_to_grid(kernel_idx)
            assert grid_code is not None, f"Failed to convert kernel_idx {kernel_idx}"
            
            back_to_kernel = grid_to_kernel_index(grid_code)
            assert back_to_kernel == kernel_idx, (
                f"Round-trip failed: {kernel_idx} -> {grid_code} -> {back_to_kernel}"
            )

    def test_round_trip_sample_grid_codes(self):
        """Test round-trip conversion for sample grid codes."""
        test_codes = [
            "CN021E01", "CN021E06", "CN020E01", "CN010E03",
            "CN001E01", "CC000E01", "CC000E06",
            "CS001E01", "CS010E03", "CS020E06", "CS021E04"
        ]
        
        for grid_code in test_codes:
            kernel_idx = grid_to_kernel_index(grid_code)
            assert kernel_idx is not None, f"Failed to convert {grid_code}"
            
            back_to_grid = kernel_index_to_grid(kernel_idx)
            assert back_to_grid == grid_code, (
                f"Round-trip failed: {grid_code} -> {kernel_idx} -> {back_to_grid}"
            )


class TestGetAntennaKernelIdx:
    """Tests for get_antenna_kernel_idx function."""

    def test_array_shape(self):
        """Test returned array has correct shape."""
        kernel_data = get_antenna_kernel_idx()
        
        # Should be 43 rows (21 north + 1 center + 21 south) x 6 columns
        assert kernel_data.shape == (43, 6)
        assert kernel_data.kernel_indices.shape == (43, 6)
        assert kernel_data.grid_codes.shape == (43, 6)
        assert kernel_data.antenna_numbers.shape == (43, 6)
        assert kernel_data.snap_ports.shape == (43, 6)

    def test_kernel_indices_range(self):
        """Test kernel indices are in valid range or -1."""
        kernel_data = get_antenna_kernel_idx()
        
        # All kernel indices should be -1 or in range 0-255
        valid_mask = (kernel_data.kernel_indices >= 0) & (kernel_data.kernel_indices <= 255)
        unmapped_mask = kernel_data.kernel_indices == -1
        
        assert np.all(valid_mask | unmapped_mask)

    def test_unmapped_positions(self):
        """Test that CS021E05 and CS021E06 are unmapped."""
        kernel_data = get_antenna_kernel_idx()
        
        # Last row (index 42 = CS021), last two columns (indices 4, 5 = E05, E06)
        assert kernel_data.kernel_indices[42, 4] == -1  # CS021E05
        assert kernel_data.kernel_indices[42, 5] == -1  # CS021E06

    def test_all_mapped_positions_have_grid_codes(self):
        """Test all mapped positions have valid grid codes."""
        kernel_data = get_antenna_kernel_idx()
        
        mapped_mask = kernel_data.kernel_indices >= 0
        grid_codes_at_mapped = kernel_data.grid_codes[mapped_mask]
        
        # All mapped positions should have non-empty grid codes
        assert np.all([code != "" for code in grid_codes_at_mapped])

    def test_grid_code_format(self):
        """Test grid codes follow correct format."""
        kernel_data = get_antenna_kernel_idx()
        
        # Check a few specific positions
        assert kernel_data.grid_codes[0, 0] == "CN021E01"  # First position
        assert kernel_data.grid_codes[0, 5] == "CN021E06"  # End of first row
        assert kernel_data.grid_codes[21, 0] == "CC000E01"  # Center row
        assert kernel_data.grid_codes[42, 3] == "CS021E04"  # Last mapped position

    def test_kernel_index_values(self):
        """Test specific kernel index values."""
        kernel_data = get_antenna_kernel_idx()
        
        assert kernel_data.kernel_indices[0, 0] == 0      # CN021E01
        assert kernel_data.kernel_indices[0, 5] == 5      # CN021E06
        assert kernel_data.kernel_indices[1, 0] == 6      # CN020E01
        assert kernel_data.kernel_indices[21, 0] == 126   # CC000E01
        assert kernel_data.kernel_indices[42, 3] == 255   # CS021E04

    def test_unique_kernel_indices(self):
        """Test all kernel indices are unique (no duplicates)."""
        kernel_data = get_antenna_kernel_idx()
        
        mapped_indices = kernel_data.kernel_indices[kernel_data.kernel_indices >= 0]
        unique_indices = np.unique(mapped_indices)
        
        # Should have exactly 256 unique indices (0-255)
        assert len(unique_indices) == 256
        assert np.array_equal(unique_indices, np.arange(256))


class TestKernelIndexArray:
    """Tests for KernelIndexArray container class."""

    def test_get_by_kernel_index_valid(self):
        """Test getting information by valid kernel index."""
        kernel_data = get_antenna_kernel_idx()
        
        # Get info for kernel index 0
        info = kernel_data.get_by_kernel_index(0)
        assert info is not None
        assert info['grid_code'] == 'CN021E01'
        assert info['ns'] == 0
        assert info['ew'] == 0

    def test_get_by_kernel_index_last(self):
        """Test getting information for last kernel index."""
        kernel_data = get_antenna_kernel_idx()
        
        info = kernel_data.get_by_kernel_index(255)
        assert info is not None
        assert info['grid_code'] == 'CS021E04'
        assert info['ns'] == 42
        assert info['ew'] == 3

    def test_get_by_kernel_index_invalid(self):
        """Test getting information for invalid kernel index."""
        kernel_data = get_antenna_kernel_idx()
        
        assert kernel_data.get_by_kernel_index(256) is None
        assert kernel_data.get_by_kernel_index(-1) is None
        assert kernel_data.get_by_kernel_index(1000) is None

    def test_get_by_grid_code_valid(self):
        """Test getting information by valid grid code."""
        kernel_data = get_antenna_kernel_idx()
        
        info = kernel_data.get_by_grid_code('CN021E01')
        assert info is not None
        assert info['kernel_index'] == 0
        assert info['ns'] == 0
        assert info['ew'] == 0

    def test_get_by_grid_code_unmapped(self):
        """Test getting information for unmapped grid code."""
        kernel_data = get_antenna_kernel_idx()
        
        # CS021E05 is unmapped
        info = kernel_data.get_by_grid_code('CS021E05')
        assert info is None

    def test_get_by_grid_code_case_insensitive(self):
        """Test grid code lookup is case insensitive."""
        kernel_data = get_antenna_kernel_idx()
        
        info_upper = kernel_data.get_by_grid_code('CN021E01')
        info_lower = kernel_data.get_by_grid_code('cn021e01')
        
        assert info_upper is not None
        assert info_lower is not None
        assert info_upper['kernel_index'] == info_lower['kernel_index']

    def test_get_by_grid_code_invalid(self):
        """Test getting information for invalid grid code."""
        kernel_data = get_antenna_kernel_idx()
        
        assert kernel_data.get_by_grid_code('INVALID') is None
        assert kernel_data.get_by_grid_code('XX999E99') is None

    def test_repr(self):
        """Test string representation."""
        kernel_data = get_antenna_kernel_idx()
        repr_str = repr(kernel_data)
        
        assert 'KernelIndexArray' in repr_str
        assert 'shape=(43, 6)' in repr_str
        assert 'mapped_positions=256' in repr_str


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_boundary_positions(self):
        """Test positions at array boundaries."""
        # Test corners and edges of mapped region
        test_cases = [
            ("CN021E01", 0),       # Top-left
            ("CN021E06", 5),       # Top-right
            ("CS021E01", 252),     # Bottom-left (mapped)
            ("CS021E04", 255),     # Bottom-right (last mapped)
        ]
        
        for grid_code, expected_idx in test_cases:
            kernel_idx = grid_to_kernel_index(grid_code)
            assert kernel_idx == expected_idx, f"Failed for {grid_code}"
            
            back_to_grid = kernel_index_to_grid(kernel_idx)
            assert back_to_grid == grid_code

    def test_row_major_ordering(self):
        """Test that indices follow row-major ordering."""
        kernel_data = get_antenna_kernel_idx()
        
        # For each row, kernel indices should increase left to right
        for row in range(43):
            row_indices = kernel_data.kernel_indices[row, :]
            mapped_indices = row_indices[row_indices >= 0]
            
            if len(mapped_indices) > 1:
                # Check indices are increasing
                assert np.all(mapped_indices[:-1] < mapped_indices[1:])

    def test_max_index_enforcement(self):
        """Test that max_index configuration is enforced."""
        # With max_index=255, positions beyond index 255 should not be mapped
        kernel_data = get_antenna_kernel_idx()
        
        # Count number of mapped positions
        n_mapped = np.sum(kernel_data.kernel_indices >= 0)
        assert n_mapped == 256  # Exactly 256 positions (0-255)

    def test_array_continuity(self):
        """Test that kernel indices are continuous with no gaps."""
        kernel_data = get_antenna_kernel_idx()
        
        mapped_indices = kernel_data.kernel_indices[kernel_data.kernel_indices >= 0]
        sorted_indices = np.sort(mapped_indices)
        
        # Should be exactly 0, 1, 2, ..., 255 with no gaps
        expected = np.arange(256)
        assert np.array_equal(sorted_indices, expected)


class TestConfigurationDependency:
    """Tests that verify functions depend on configuration."""

    def test_requires_enabled_config(self):
        """Test that functions check if kernel_index is enabled."""
        # For arrays without kernel_index.enabled=true, should return None or raise
        result = grid_to_kernel_index("CN021E01", array_name="nonexistent")
        assert result is None
        
        result = kernel_index_to_grid(0, array_name="nonexistent")
        assert result is None

    def test_get_antenna_kernel_idx_requires_enabled(self):
        """Test that get_antenna_kernel_idx raises error for disabled arrays."""
        with pytest.raises(ValueError, match="not enabled"):
            get_antenna_kernel_idx(array_name="nonexistent")
