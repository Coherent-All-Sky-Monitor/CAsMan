"""
Tests for multi-array grid system functionality.

Tests cover:
- Loading array configurations dynamically
- Array name lookups by ID
- Validation against different array bounds
- Grid code parsing with multiple arrays
"""

import pytest

from casman.antenna.grid import (
    load_array_layout,
    get_array_name_for_id,
    load_core_layout,
    parse_grid_code,
    validate_components,
    format_grid_code,
)


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

    def test_load_array_missing_fields(self):
        """Test that missing required fields raise KeyError."""
        # This would only happen if config.yaml is malformed
        # We can't easily test this without mocking the config
        pass


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

    def test_empty_id(self):
        """Test with empty string."""
        name = get_array_name_for_id("")
        assert name is None

    def test_lowercase_id(self):
        """Test that lowercase IDs don't match (case-sensitive)."""
        name = get_array_name_for_id("c")
        assert name is None


class TestMultiArrayValidation:
    """Tests for validation with multiple arrays."""

    def test_validate_core_within_bounds(self):
        """Test validation within core array bounds."""
        # Should not raise
        validate_components("C", 10, 3, enforce_bounds=True)

    def test_validate_core_at_max_bounds(self):
        """Test validation at core array boundary."""
        # Should not raise - north row 21, east column 6
        validate_components("C", 21, 6, enforce_bounds=True)
        validate_components("C", -21, 6, enforce_bounds=True)

    def test_validate_core_beyond_bounds_with_expansion(self):
        """Test validation beyond core bounds when expansion allowed."""
        # Should not raise because core has allow_expansion=true
        validate_components("C", 50, 10, enforce_bounds=True)

    def test_validate_without_enforcement(self):
        """Test validation skips array-specific bounds check."""
        # Should not raise even for unknown array
        validate_components("X", 100, 50, enforce_bounds=False)

    def test_validate_unknown_array_with_enforcement(self):
        """Test that unknown arrays pass validation (no config to check)."""
        # Should not raise - unknown arrays have no bounds to enforce
        validate_components("X", 10, 5, enforce_bounds=True)


class TestMultiArrayParsing:
    """Tests for parsing grid codes with different arrays."""

    def test_parse_core_array(self):
        """Test parsing core array grid code."""
        pos = parse_grid_code("CN010E03")
        assert pos.array_id == "C"
        assert pos.row_offset == 10
        assert pos.east_col == 3

    def test_parse_hypothetical_outrigger(self):
        """Test parsing outrigger array code (if configured)."""
        # This would work if outriggers are configured in config.yaml
        pos = parse_grid_code("ON005E02", enforce_bounds=False)
        assert pos.array_id == "O"
        assert pos.row_offset == 5
        assert pos.east_col == 2

    def test_parse_different_array_letters(self):
        """Test parsing various array IDs."""
        for letter in "ABDEFGHIJKLMNOPQRSTUVWXYZ":  # Skip C since it's core
            code = f"{letter}N001E01"
            pos = parse_grid_code(code, enforce_bounds=False)
            assert pos.array_id == letter


class TestMultiArrayFormatting:
    """Tests for formatting grid codes with different arrays."""

    def test_format_core_array(self):
        """Test formatting core array grid code."""
        code = format_grid_code("C", "N", 10, 3)
        assert code == "CN010E03"

    def test_format_different_arrays(self):
        """Test formatting with different array IDs."""
        code_a = format_grid_code("A", "N", 5, 2)
        assert code_a == "AN005E02"
        
        code_o = format_grid_code("O", "S", 10, 4)
        assert code_o == "OS010E04"


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
        assert south == 21
        assert east == 6

    def test_validate_against_loaded_bounds(self):
        """Test validation uses loaded array bounds."""
        # Load core bounds
        _, north, south, east, expand = load_array_layout("core")
        
        # Validate within bounds
        validate_components("C", north, east, enforce_bounds=True)  # Max north, max east
        validate_components("C", -south, east, enforce_bounds=True)  # Max south, max east
        
        # With expansion, beyond bounds should also work
        if expand:
            validate_components("C", north + 10, east + 5, enforce_bounds=True)


class TestErrorHandling:
    """Tests for error conditions in multi-array system."""

    def test_load_array_with_empty_name(self):
        """Test loading array with empty name."""
        with pytest.raises(KeyError):
            load_array_layout("")

    def test_load_array_with_none(self):
        """Test loading array with None."""
        with pytest.raises((KeyError, TypeError)):
            load_array_layout(None)

    def test_get_array_name_with_none(self):
        """Test getting array name with None."""
        name = get_array_name_for_id(None)
        assert name is None
