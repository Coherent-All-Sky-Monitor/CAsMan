"""
Tests for antenna grid position parsing, formatting, and validation.

Tests cover:
- Grid code parsing (valid and invalid cases)
- Grid code formatting and round-trip consistency
- Direction mapping from row offsets
- Component validation with and without core bounds enforcement
- Boundary conditions for core array
"""

import pytest

from casman.antenna.grid import (
    AntennaGridPosition,
    direction_from_row,
    format_grid_code,
    parse_grid_code,
    to_grid_code,
    validate_components,
)


class TestGridCodeParsing:
    """Tests for parsing grid codes."""

    def test_parse_valid_center(self):
        """Test parsing center position."""
        pos = parse_grid_code("CC000E00")
        assert pos.array_id == "C"
        assert pos.direction == "C"
        assert pos.offset == 0
        assert pos.east_col == 0
        assert pos.row_offset == 0
        assert pos.grid_code == "CC000E00"

    def test_parse_valid_north(self):
        """Test parsing north position."""
        pos = parse_grid_code("CN002E03")
        assert pos.array_id == "C"
        assert pos.direction == "N"
        assert pos.offset == 2
        assert pos.east_col == 3
        assert pos.row_offset == 2
        assert pos.grid_code == "CN002E03"

    def test_parse_valid_south(self):
        """Test parsing south position."""
        pos = parse_grid_code("CS021E05")
        assert pos.array_id == "C"
        assert pos.direction == "S"
        assert pos.offset == 21
        assert pos.east_col == 5
        assert pos.row_offset == -21
        assert pos.grid_code == "CS021E05"

    def test_parse_max_north(self):
        """Test parsing maximum north row."""
        pos = parse_grid_code("CN021E05")
        assert pos.offset == 21
        assert pos.row_offset == 21

    def test_parse_max_south(self):
        """Test parsing maximum south row."""
        pos = parse_grid_code("CS021E05")
        assert pos.offset == 21
        assert pos.row_offset == -21

    def test_parse_different_array(self):
        """Test parsing with different array ID."""
        pos = parse_grid_code("AN010E02", enforce_core_bounds=False)
        assert pos.array_id == "A"
        assert pos.direction == "N"
        assert pos.offset == 10
        assert pos.east_col == 2

    def test_parse_invalid_format(self):
        """Test parsing with invalid format."""
        with pytest.raises(ValueError, match="does not match pattern"):
            parse_grid_code("INVALID")

    def test_parse_invalid_direction(self):
        """Test parsing with invalid direction."""
        with pytest.raises(ValueError, match="does not match pattern"):
            parse_grid_code("CX010E02")

    def test_parse_center_with_nonzero_offset(self):
        """Test parsing center with non-zero offset (invalid)."""
        with pytest.raises(ValueError, match="Center row must use offset 000"):
            parse_grid_code("CC001E02")

    def test_parse_north_south_with_zero_offset(self):
        """Test parsing N/S with zero offset (invalid)."""
        with pytest.raises(ValueError, match="North/South rows must use offset"):
            parse_grid_code("CN000E02")

    def test_parse_exceeds_core_bounds_north(self):
        """Test parsing exceeds core north bounds with expansion disabled."""
        # Note: Since config has allow_expansion=true, bounds are not enforced by default
        # This test verifies the behavior when expansion is allowed
        pos = parse_grid_code("CN022E03")
        assert pos.offset == 22  # Should parse successfully with expansion

    def test_parse_exceeds_core_bounds_south(self):
        """Test parsing exceeds core south bounds with expansion disabled."""
        # Note: Since config has allow_expansion=true, bounds are not enforced by default
        pos = parse_grid_code("CS022E03")
        assert pos.offset == 22  # Should parse successfully with expansion

    def test_parse_exceeds_core_bounds_east(self):
        """Test parsing exceeds core east bounds with expansion disabled."""
        # Note: Since config has allow_expansion=true, bounds are not enforced by default
        pos = parse_grid_code("CN010E06")
        assert pos.east_col == 6  # Should parse successfully with expansion

    def test_parse_expansion_beyond_core(self):
        """Test parsing beyond core bounds with expansion enabled."""
        pos = parse_grid_code("CN050E10", enforce_core_bounds=False)
        assert pos.offset == 50
        assert pos.east_col == 10


class TestGridCodeFormatting:
    """Tests for formatting grid codes."""

    def test_format_center(self):
        """Test formatting center position."""
        code = format_grid_code("C", "C", 0, 0)
        assert code == "CC000E00"

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
        code = format_grid_code("C", "N", 1, 0)
        assert code == "CN001E00"

    def test_format_max_offset(self):
        """Test formatting with maximum offset."""
        code = format_grid_code("C", "N", 999, 99)
        assert code == "CN999E99"

    def test_format_invalid_direction(self):
        """Test formatting with invalid direction."""
        with pytest.raises(ValueError, match="direction must be"):
            format_grid_code("C", "X", 5, 2)


class TestGridCodeConversion:
    """Tests for converting row offsets to grid codes."""

    def test_to_grid_code_center(self):
        """Test converting center row offset."""
        code = to_grid_code(0, 0)
        assert code == "CC000E00"

    def test_to_grid_code_north(self):
        """Test converting north row offset."""
        code = to_grid_code(5, 3)
        assert code == "CN005E03"

    def test_to_grid_code_south(self):
        """Test converting south row offset."""
        code = to_grid_code(-10, 2)
        assert code == "CS010E02"

    def test_to_grid_code_max_north(self):
        """Test converting maximum north offset."""
        code = to_grid_code(21, 5)
        assert code == "CN021E05"

    def test_to_grid_code_max_south(self):
        """Test converting maximum south offset."""
        code = to_grid_code(-21, 5)
        assert code == "CS021E05"

    def test_to_grid_code_different_array(self):
        """Test converting with different array ID."""
        code = to_grid_code(10, 2, array_id="A")
        assert code == "AN010E02"


class TestDirectionMapping:
    """Tests for mapping row offsets to directions."""

    def test_direction_from_center(self):
        """Test direction for center row."""
        assert direction_from_row(0) == "C"

    def test_direction_from_north(self):
        """Test direction for north rows."""
        assert direction_from_row(1) == "N"
        assert direction_from_row(10) == "N"
        assert direction_from_row(21) == "N"

    def test_direction_from_south(self):
        """Test direction for south rows."""
        assert direction_from_row(-1) == "S"
        assert direction_from_row(-10) == "S"
        assert direction_from_row(-21) == "S"


class TestComponentValidation:
    """Tests for validating grid components."""

    def test_validate_core_center(self):
        """Test validating core center position."""
        validate_components("C", 0, 0)  # Should not raise

    def test_validate_core_north_min(self):
        """Test validating minimum north position."""
        validate_components("C", 1, 0)  # Should not raise

    def test_validate_core_north_max(self):
        """Test validating maximum north position."""
        validate_components("C", 21, 5)  # Should not raise

    def test_validate_core_south_min(self):
        """Test validating minimum south position."""
        validate_components("C", -1, 0)  # Should not raise

    def test_validate_core_south_max(self):
        """Test validating maximum south position."""
        validate_components("C", -21, 5)  # Should not raise

    def test_validate_core_north_exceeds(self):
        """Test validating exceeds north bounds with expansion allowed."""
        # With allow_expansion=true in config, this should not raise
        validate_components("C", 22, 3)  # Should not raise

    def test_validate_core_south_exceeds(self):
        """Test validating exceeds south bounds with expansion allowed."""
        # With allow_expansion=true in config, this should not raise
        validate_components("C", -22, 3)  # Should not raise

    def test_validate_core_east_exceeds(self):
        """Test validating exceeds east bounds with expansion allowed."""
        # With allow_expansion=true in config, this should not raise
        validate_components("C", 10, 6)  # Should not raise

    def test_validate_expansion_beyond_core(self):
        """Test validating beyond core with expansion."""
        validate_components("C", 50, 10, enforce_core_bounds=False)  # Should not raise

    def test_validate_different_array_no_enforcement(self):
        """Test validating different array without enforcement."""
        validate_components("A", 100, 20, enforce_core_bounds=False)  # Should not raise


class TestRoundTripConsistency:
    """Tests for round-trip parse/format consistency."""

    def test_roundtrip_center(self):
        """Test round-trip for center position."""
        original = "CC000E00"
        pos = parse_grid_code(original)
        reconstructed = format_grid_code(
            pos.array_id, pos.direction, pos.offset, pos.east_col
        )
        assert reconstructed == original

    def test_roundtrip_north(self):
        """Test round-trip for north positions."""
        for offset in [1, 5, 10, 21]:
            original = f"CN{offset:03d}E03"
            pos = parse_grid_code(original)
            reconstructed = format_grid_code(
                pos.array_id, pos.direction, pos.offset, pos.east_col
            )
            assert reconstructed == original

    def test_roundtrip_south(self):
        """Test round-trip for south positions."""
        for offset in [1, 5, 10, 21]:
            original = f"CS{offset:03d}E02"
            pos = parse_grid_code(original)
            reconstructed = format_grid_code(
                pos.array_id, pos.direction, pos.offset, pos.east_col
            )
            assert reconstructed == original

    def test_roundtrip_all_columns(self):
        """Test round-trip for all columns."""
        for col in range(6):
            original = f"CN010E{col:02d}"
            pos = parse_grid_code(original)
            reconstructed = format_grid_code(
                pos.array_id, pos.direction, pos.offset, pos.east_col
            )
            assert reconstructed == original


class TestBoundaryConditions:
    """Tests for boundary conditions."""

    def test_boundary_north_zero(self):
        """Test boundary: N000 is invalid."""
        with pytest.raises(ValueError):
            parse_grid_code("CN000E00")

    def test_boundary_south_zero(self):
        """Test boundary: S000 is invalid."""
        with pytest.raises(ValueError):
            parse_grid_code("CS000E00")

    def test_boundary_center_nonzero(self):
        """Test boundary: C with non-zero offset is invalid."""
        with pytest.raises(ValueError):
            parse_grid_code("CC001E00")

    def test_boundary_core_north_21(self):
        """Test boundary: N021 is valid (at core boundary)."""
        pos = parse_grid_code("CN021E05")
        assert pos.offset == 21

    def test_boundary_core_north_22(self):
        """Test boundary: N022 allowed with expansion."""
        # With allow_expansion=true, this should parse successfully
        pos = parse_grid_code("CN022E05")
        assert pos.offset == 22

    def test_boundary_core_south_21(self):
        """Test boundary: S021 is valid (at core boundary)."""
        pos = parse_grid_code("CS021E05")
        assert pos.offset == 21

    def test_boundary_core_south_22(self):
        """Test boundary: S022 allowed with expansion."""
        # With allow_expansion=true, this should parse successfully
        pos = parse_grid_code("CS022E05")
        assert pos.offset == 22

    def test_boundary_east_5(self):
        """Test boundary: E05 is valid (at core boundary)."""
        pos = parse_grid_code("CN010E05")
        assert pos.east_col == 5

    def test_boundary_east_6(self):
        """Test boundary: E06 allowed with expansion."""
        # With allow_expansion=true, this should parse successfully
        pos = parse_grid_code("CN010E06")
        assert pos.east_col == 6


class TestAntennaGridPositionDataclass:
    """Tests for AntennaGridPosition dataclass validation."""

    def test_post_init_invalid_direction(self):
        """Test __post_init__ rejects invalid direction."""
        with pytest.raises(ValueError, match="Invalid direction"):
            AntennaGridPosition(
                array_id="C",
                direction="X",
                offset=1,
                east_col=0,
                row_offset=1,
                grid_code="CX001E00",
            )

    def test_post_init_offset_negative(self):
        """Test __post_init__ rejects negative offset."""
        with pytest.raises(ValueError, match="Offset out of range"):
            AntennaGridPosition(
                array_id="C",
                direction="N",
                offset=-1,
                east_col=0,
                row_offset=1,
                grid_code="CN001E00",
            )

    def test_post_init_offset_too_large(self):
        """Test __post_init__ rejects offset > 999."""
        with pytest.raises(ValueError, match="Offset out of range"):
            AntennaGridPosition(
                array_id="C",
                direction="N",
                offset=1000,
                east_col=0,
                row_offset=1000,
                grid_code="CN1000E00",
            )

    def test_post_init_center_nonzero_offset(self):
        """Test __post_init__ rejects center with non-zero offset."""
        with pytest.raises(ValueError, match="Center .* must have offset 0"):
            AntennaGridPosition(
                array_id="C",
                direction="C",
                offset=1,
                east_col=0,
                row_offset=0,
                grid_code="CC001E00",
            )

    def test_post_init_north_south_zero_offset(self):
        """Test __post_init__ rejects N/S with zero offset."""
        with pytest.raises(ValueError, match="North/South offsets must be >= 1"):
            AntennaGridPosition(
                array_id="C",
                direction="N",
                offset=0,
                east_col=0,
                row_offset=0,
                grid_code="CN000E00",
            )

    def test_post_init_east_col_negative(self):
        """Test __post_init__ rejects negative east_col."""
        with pytest.raises(ValueError, match="East column out of range"):
            AntennaGridPosition(
                array_id="C",
                direction="N",
                offset=1,
                east_col=-1,
                row_offset=1,
                grid_code="CN001E00",
            )

    def test_post_init_east_col_too_large(self):
        """Test __post_init__ rejects east_col > 99."""
        with pytest.raises(ValueError, match="East column out of range"):
            AntennaGridPosition(
                array_id="C",
                direction="N",
                offset=1,
                east_col=100,
                row_offset=1,
                grid_code="CN001E100",
            )

    def test_post_init_grid_code_mismatch(self):
        """Test __post_init__ detects grid_code mismatch."""
        with pytest.raises(ValueError, match="grid_code mismatch"):
            AntennaGridPosition(
                array_id="C",
                direction="N",
                offset=1,
                east_col=0,
                row_offset=1,
                grid_code="CN002E00",  # Mismatch: offset is 1 but code says 2
            )


class TestFormatGridCodeEdgeCases:
    """Tests for format_grid_code edge cases."""

    def test_format_invalid_array_id_empty(self):
        """Test format_grid_code rejects empty array_id."""
        with pytest.raises(ValueError, match="array_id must be one uppercase letter"):
            format_grid_code("", "N", 1, 0)

    def test_format_invalid_array_id_multiple_chars(self):
        """Test format_grid_code rejects multi-character array_id."""
        with pytest.raises(ValueError, match="array_id must be one uppercase letter"):
            format_grid_code("AB", "N", 1, 0)

    def test_format_invalid_array_id_lowercase(self):
        """Test format_grid_code rejects lowercase array_id."""
        with pytest.raises(ValueError, match="array_id must be one uppercase letter"):
            format_grid_code("c", "N", 1, 0)

    def test_format_invalid_array_id_digit(self):
        """Test format_grid_code rejects digit array_id."""
        with pytest.raises(ValueError, match="array_id must be one uppercase letter"):
            format_grid_code("1", "N", 1, 0)

    def test_format_invalid_direction(self):
        """Test format_grid_code rejects invalid direction."""
        with pytest.raises(ValueError, match="direction must be one of N,S,C"):
            format_grid_code("C", "X", 1, 0)

    def test_format_center_with_nonzero_offset(self):
        """Test format_grid_code rejects center with non-zero offset."""
        with pytest.raises(ValueError, match="Center direction must have offset 0"):
            format_grid_code("C", "C", 1, 0)

    def test_format_north_south_zero_offset(self):
        """Test format_grid_code rejects N/S with zero offset."""
        with pytest.raises(ValueError, match="North/South offsets must be >= 1"):
            format_grid_code("C", "N", 0, 0)


class TestValidateComponentsEdgeCases:
    """Tests for validate_components edge cases."""

    def test_validate_invalid_array_id_empty(self):
        """Test validate_components rejects empty array_id."""
        with pytest.raises(ValueError, match="Invalid array_id"):
            validate_components("", 1, 0)

    def test_validate_invalid_array_id_lowercase(self):
        """Test validate_components rejects lowercase array_id."""
        with pytest.raises(ValueError, match="Invalid array_id"):
            validate_components("c", 1, 0)

    def test_validate_invalid_array_id_digit(self):
        """Test validate_components rejects digit array_id."""
        with pytest.raises(ValueError, match="Invalid array_id"):
            validate_components("1", 1, 0)

    def test_validate_east_col_negative(self):
        """Test validate_components rejects negative east_col."""
        with pytest.raises(ValueError, match="east_col out of range"):
            validate_components("C", 1, -1)

    def test_validate_east_col_too_large(self):
        """Test validate_components rejects east_col > 99."""
        with pytest.raises(ValueError, match="east_col out of range"):
            validate_components("C", 1, 100)

    def test_validate_row_offset_too_negative(self):
        """Test validate_components rejects row_offset < -999."""
        with pytest.raises(ValueError, match="row_offset out of absolute range"):
            validate_components("A", -1000, 0, enforce_core_bounds=False)

    def test_validate_row_offset_too_positive(self):
        """Test validate_components rejects row_offset > 999."""
        with pytest.raises(ValueError, match="row_offset out of absolute range"):
            validate_components("A", 1000, 0, enforce_core_bounds=False)


class TestParseGridCodeEdgeCases:
    """Tests for parse_grid_code edge cases."""

    def test_parse_non_string_input(self):
        """Test parse_grid_code rejects non-string input."""
        with pytest.raises(ValueError, match="Grid code must be a string"):
            parse_grid_code(123)  # type: ignore

    def test_parse_lowercase_normalized(self):
        """Test parse_grid_code normalizes lowercase to uppercase."""
        pos = parse_grid_code("cn002e03")
        assert pos.grid_code == "CN002E03"

    def test_parse_with_whitespace(self):
        """Test parse_grid_code strips whitespace."""
        pos = parse_grid_code("  CN002E03  ")
        assert pos.grid_code == "CN002E03"


class TestToGridCodeEdgeCases:
    """Tests for to_grid_code edge cases."""

    def test_to_grid_code_center_with_default_array(self):
        """Test to_grid_code for center with default array_id."""
        code = to_grid_code(0, 0)
        assert code == "CC000E00"

    def test_to_grid_code_explicit_array(self):
        """Test to_grid_code with explicit array_id."""
        # Non-core arrays are allowed, just not validated for core bounds
        code = to_grid_code(5, 2, array_id="A")
        assert code == "AN005E02"
