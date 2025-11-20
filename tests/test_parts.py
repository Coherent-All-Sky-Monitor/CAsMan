"""Simplified tests for CAsMan parts functionality."""

import pytest
from unittest.mock import patch, MagicMock

from casman.parts.validation import (
    validate_part_number,
    validate_part_type,
    validate_polarization,
    get_part_info,
)
from casman.parts.part import Part, create_part
from casman.parts.search import (
    search_parts,
    get_all_parts,
    search_by_prefix,
    get_part_statistics,
    find_part,
    get_recent_parts,
)


class TestPartsValidation:
    """Test parts validation functions."""

    def test_validate_part_number(self):
        """Test part number validation."""
        assert validate_part_number("ANT00001P1")
        assert validate_part_number("LNA00123P2")
        assert not validate_part_number("INVALID")
        assert not validate_part_number(None)

    def test_validate_part_type(self):
        """Test part type validation."""
        assert validate_part_type("ANTENNA")
        assert validate_part_type("LNA")
        assert not validate_part_type("INVALID_TYPE")
        assert not validate_part_type(None)

    def test_validate_polarization(self):
        """Test polarization validation."""
        assert validate_polarization("P1")
        assert validate_polarization("P2")
        assert validate_polarization("PV")
        assert not validate_polarization("INVALID")
        assert not validate_polarization(None)

    def test_get_part_info(self):
        """Test part info extraction."""
        info = get_part_info("ANT00001P1")
        assert info is not None
        assert info["prefix"] == "ANT"
        assert info["part_type"] == "ANTENNA"
        assert info["polarization"] == "P1"
        assert info["number"] == "00001"

        assert get_part_info("INVALID") is None


class TestPartClass:
    """Test the Part class."""

    def test_part_initialization(self):
        """Test creating a Part instance."""
        part = Part("ANT00001P1")
        assert part.part_number == "ANT00001P1"
        assert part.part_type == "ANTENNA"
        assert part.polarization == "P1"
        assert part.prefix == "ANT"
        assert part.number == "00001"

    def test_part_initialization_with_explicit_values(self):
        """Test creating a Part with explicit type and polarization."""
        part = Part("LNA00042P2", part_type="LNA", polarization="P2")
        assert part.part_number == "LNA00042P2"
        assert part.part_type == "LNA"
        assert part.polarization == "P2"

    def test_part_initialization_invalid_part_number(self):
        """Test that invalid part numbers raise ValueError."""
        with pytest.raises(ValueError, match="Invalid part number format"):
            Part("INVALID")

    def test_part_initialization_mismatched_type(self):
        """Test that mismatched part type raises ValueError."""
        with pytest.raises(ValueError, match="doesn't match part number"):
            Part("ANT00001P1", part_type="LNA")

    def test_part_initialization_mismatched_polarization(self):
        """Test that mismatched polarization raises ValueError."""
        with pytest.raises(ValueError, match="doesn't match part number"):
            Part("ANT00001P1", polarization="P2")

    def test_part_equality(self):
        """Test Part equality comparison."""
        part1 = Part("ANT00001P1")
        part2 = Part("ANT00001P1")
        part3 = Part("ANT00002P1")
        
        assert part1 == part2
        assert part1 != part3

    def test_part_hash(self):
        """Test that Part instances can be hashed."""
        part1 = Part("ANT00001P1")
        part2 = Part("ANT00001P1")
        
        # Same part numbers should have same hash
        assert hash(part1) == hash(part2)
        
        # Can be used in sets
        parts_set = {part1, part2}
        assert len(parts_set) == 1

    def test_part_to_dict(self):
        """Test converting Part to dictionary."""
        part = Part("LNA00123P2")
        part_dict = part.to_dict()
        
        assert part_dict["part_number"] == "LNA00123P2"
        assert part_dict["part_type"] == "LNA"
        assert part_dict["polarization"] == "P2"
        assert part_dict["prefix"] == "LNA"
        assert part_dict["number"] == "00123"
        assert "date_created" in part_dict
        assert "date_modified" in part_dict

    def test_part_from_dict(self):
        """Test creating Part from dictionary."""
        data = {
            "part_number": "ANT00001P1",
            "part_type": "ANTENNA",
            "polarization": "P1",
            "date_created": "2024-01-01 00:00:00",
            "date_modified": "2024-01-01 00:00:00",
        }
        part = Part.from_dict(data)
        
        assert part.part_number == "ANT00001P1"
        assert part.part_type == "ANTENNA"
        assert part.polarization == "P1"

    def test_part_from_database_row(self):
        """Test creating Part from database row."""
        row = (1, "LNA00042P2", "LNA", "P2", "2024-01-01 00:00:00", "2024-01-01 00:00:00")
        part = Part.from_database_row(row)
        
        assert part.part_number == "LNA00042P2"
        assert part.part_type == "LNA"
        assert part.polarization == "P2"

    def test_part_from_database_row_invalid(self):
        """Test that invalid database row raises ValueError."""
        with pytest.raises(ValueError, match="Invalid database row format"):
            Part.from_database_row((1, "ANT00001P1"))

    def test_part_is_valid(self):
        """Test Part validation."""
        valid_part = Part("ANT00001P1")
        assert valid_part.is_valid()

    def test_part_get_barcode_filename(self):
        """Test getting barcode filename."""
        part = Part("ANT00001P1")
        assert part.get_barcode_filename() == "ANT00001P1.png"

    def test_part_update_modified_time(self):
        """Test updating modified time."""
        part = Part("ANT00001P1")
        original_time = part.date_modified
        
        # Sleep for 1 second to ensure timestamp changes (resolution is 1 second)
        import time
        time.sleep(1.1)
        
        part.update_modified_time()
        assert part.date_modified != original_time

    def test_create_part_convenience_function(self):
        """Test the create_part convenience function."""
        part = create_part("ANT00001P1")
        assert isinstance(part, Part)
        assert part.part_number == "ANT00001P1"

    def test_part_string_representation(self):
        """Test Part string representations."""
        part = Part("ANT00001P1")
        
        # Test __str__
        assert "ANT00001P1" in str(part)
        assert "ANTENNA" in str(part)
        
        # Test __repr__
        assert "part_number='ANT00001P1'" in repr(part)


class TestPartSearch:
    """Test parts search functionality."""

    @patch("casman.parts.search.sqlite3.connect")
    @patch("casman.parts.search.get_database_path")
    def test_search_parts_by_type(self, mock_get_path, mock_connect):
        """Test searching parts by type."""
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),
            (2, "ANT00002P1", "ANTENNA", "P1", "2024-01-02", "2024-01-02"),
        ]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        results = search_parts(part_type="ANTENNA")
        
        assert len(results) == 2
        assert all(isinstance(p, Part) for p in results)
        assert all(p.part_type == "ANTENNA" for p in results)

    @patch("casman.parts.search.sqlite3.connect")
    @patch("casman.parts.search.get_database_path")
    def test_search_parts_with_pattern(self, mock_get_path, mock_connect):
        """Test searching parts with pattern."""
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),
        ]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        results = search_parts(part_number_pattern="ANT%")
        
        assert len(results) == 1
        assert results[0].part_number == "ANT00001P1"

    @patch("casman.parts.search.sqlite3.connect")
    @patch("casman.parts.search.get_database_path")
    def test_search_parts_with_date_filter(self, mock_get_path, mock_connect):
        """Test searching parts with date filters."""
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-15", "2024-01-15"),
        ]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        results = search_parts(created_after="2024-01-01", created_before="2024-01-31")
        
        assert len(results) == 1

    @patch("casman.parts.search.search_parts")
    def test_get_all_parts(self, mock_search):
        """Test getting all parts."""
        mock_search.return_value = [Part("ANT00001P1"), Part("LNA00042P2")]
        
        results = get_all_parts()
        
        assert len(results) == 2
        mock_search.assert_called_once_with(db_dir=None)

    @patch("casman.parts.search.search_parts")
    def test_search_by_prefix(self, mock_search):
        """Test searching by prefix."""
        mock_search.return_value = [Part("ANT00001P1"), Part("ANT00002P1")]
        
        results = search_by_prefix("ANT")
        
        assert len(results) == 2
        mock_search.assert_called_once_with(part_number_pattern="ANT-%", db_dir=None)

    @patch("casman.parts.search.sqlite3.connect")
    @patch("casman.parts.search.get_database_path")
    def test_get_part_statistics(self, mock_get_path, mock_connect):
        """Test getting part statistics."""
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        
        # Mock multiple query results
        mock_cursor.fetchone.side_effect = [
            (42,),  # Total parts count
            ("ANT00042P1", "2024-01-15"),  # Latest part
        ]
        mock_cursor.fetchall.side_effect = [
            [("ANTENNA", 20), ("LNA", 22)],  # Parts by type
            [("P1", 25), ("P2", 17)],  # Parts by polarization
        ]
        
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        stats = get_part_statistics()
        
        assert stats["total_parts"] == 42
        assert stats["parts_by_type"]["ANTENNA"] == 20
        assert stats["parts_by_type"]["LNA"] == 22
        assert stats["parts_by_polarization"]["P1"] == 25
        assert stats["latest_part"]["part_number"] == "ANT00042P1"

    @patch("casman.parts.search.search_parts")
    def test_find_part(self, mock_search):
        """Test finding a specific part."""
        mock_search.return_value = [Part("ANT00001P1")]
        
        result = find_part("ANT00001P1")
        
        assert result is not None
        assert result.part_number == "ANT00001P1"
        mock_search.assert_called_once_with(part_number_pattern="ANT00001P1", limit=1, db_dir=None)

    @patch("casman.parts.search.search_parts")
    def test_find_part_not_found(self, mock_search):
        """Test finding a part that doesn't exist."""
        mock_search.return_value = []
        
        result = find_part("NOTEXIST00001P1")
        
        assert result is None

    @patch("casman.parts.search.search_parts")
    def test_get_recent_parts(self, mock_search):
        """Test getting recent parts."""
        mock_search.return_value = [Part("ANT00005P1"), Part("ANT00004P1"), Part("ANT00003P1")]
        
        results = get_recent_parts(count=3)
        
        assert len(results) == 3
        mock_search.assert_called_once_with(limit=3, db_dir=None)

    def test_search_parts_invalid_type(self):
        """Test that invalid part type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid part type"):
            search_parts(part_type="INVALID_TYPE")

    def test_search_parts_invalid_polarization(self):
        """Test that invalid polarization raises ValueError."""
        with pytest.raises(ValueError, match="Invalid polarization"):
            search_parts(polarization="INVALID")

    @patch("casman.parts.search.sqlite3.connect")
    @patch("casman.parts.search.get_database_path")
    def test_search_parts_with_invalid_row(self, mock_get_path, mock_connect):
        """Test handling of invalid database rows."""
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        # Return invalid row (too few fields)
        mock_cursor.fetchall.return_value = [
            (1, "INVALID"),  # Invalid row
            (2, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),  # Valid row
        ]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        # Should skip invalid row and return only valid one
        results = search_parts()
        
        assert len(results) == 1
        assert results[0].part_number == "ANT00001P1"


class TestPartsDB:
    """Test parts database utilities."""

    @patch("casman.parts.db.get_parts_by_criteria")
    def test_read_parts_no_filters(self, mock_get_parts):
        """Test reading all parts."""
        from casman.parts.db import read_parts
        
        mock_get_parts.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),
        ]
        
        results = read_parts()
        
        assert len(results) == 1
        mock_get_parts.assert_called_once_with(None, None, None)

    @patch("casman.parts.db.get_parts_by_criteria")
    def test_read_parts_with_filters(self, mock_get_parts):
        """Test reading parts with type and polarization filters."""
        from casman.parts.db import read_parts
        
        mock_get_parts.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),
        ]
        
        results = read_parts(part_type="ANTENNA", polarization="P1", db_dir="/custom")
        
        assert len(results) == 1
        mock_get_parts.assert_called_once_with("ANTENNA", "P1", "/custom")


class TestPartsGeneration:
    """Test parts generation functionality."""

    @patch("casman.parts.generation.sqlite3.connect")
    @patch("casman.parts.generation.get_database_path")
    def test_get_last_part_number(self, mock_get_path, mock_connect):
        """Test getting last part number."""
        from casman.parts.generation import get_last_part_number
        
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("ANT00042P1",)
        mock_connect.return_value.cursor.return_value = mock_cursor
        mock_connect.return_value.close = MagicMock()
        
        result = get_last_part_number("ANTENNA")
        
        assert result == "ANT00042P1"
        mock_cursor.execute.assert_called_once()

    @patch("casman.parts.generation.sqlite3.connect")
    @patch("casman.parts.generation.get_database_path")
    def test_get_last_part_number_none(self, mock_get_path, mock_connect):
        """Test getting last part number when none exists."""
        from casman.parts.generation import get_last_part_number
        
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connect.return_value.cursor.return_value = mock_cursor
        mock_connect.return_value.close = MagicMock()
        
        result = get_last_part_number("ANTENNA")
        
        assert result is None

    @patch("casman.parts.generation.generate_barcode")
    @patch("casman.parts.generation.init_parts_db")
    @patch("casman.parts.generation.sqlite3.connect")
    @patch("casman.parts.generation.get_database_path")
    def test_generate_part_numbers(self, mock_get_path, mock_connect, mock_init, mock_barcode):
        """Test generating new part numbers."""
        from casman.parts.generation import generate_part_numbers
        
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        # First call returns None (no existing parts), subsequent calls are for inserts
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        results = generate_part_numbers("ANTENNA", 3, "1")
        
        assert len(results) == 3
        assert results[0] == "ANT00001P1"
        assert results[1] == "ANT00002P1"
        assert results[2] == "ANT00003P1"
        mock_init.assert_called_once()
        assert mock_barcode.call_count == 3

    @patch("casman.parts.generation.generate_barcode")
    @patch("casman.parts.generation.init_parts_db")
    @patch("casman.parts.generation.sqlite3.connect")
    @patch("casman.parts.generation.get_database_path")
    def test_generate_part_numbers_no_existing(self, mock_get_path, mock_connect, mock_init, mock_barcode):
        """Test generating part numbers when none exist."""
        from casman.parts.generation import generate_part_numbers
        
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # No existing parts
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        results = generate_part_numbers("ANTENNA", 2, "1")
        
        assert len(results) == 2
        assert results[0] == "ANT00001P1"
        assert results[1] == "ANT00002P1"

    def test_generate_part_numbers_invalid_type(self):
        """Test that invalid part type raises ValueError."""
        from casman.parts.generation import generate_part_numbers
        
        with pytest.raises(ValueError, match="Unknown part type"):
            generate_part_numbers("INVALID_TYPE", 1, "1")

    @patch("casman.parts.generation.generate_barcode")
    @patch("casman.parts.generation.init_parts_db")
    @patch("casman.parts.generation.sqlite3.connect")
    def test_generate_part_numbers_with_custom_db_dir(self, mock_connect, mock_init, mock_barcode):
        """Test generating part numbers with custom database directory."""
        from casman.parts.generation import generate_part_numbers
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        results = generate_part_numbers("ANTENNA", 1, "1", db_dir="/custom/path")
        
        assert len(results) == 1
        # Should use custom path
        mock_connect.assert_called_with("/custom/path/parts.db")

    @patch("casman.parts.generation.sqlite3.connect")
    def test_get_last_part_number_with_custom_db_dir(self, mock_connect):
        """Test getting last part number with custom database directory."""
        from casman.parts.generation import get_last_part_number
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("ANT00001P1",)
        mock_connect.return_value.cursor.return_value = mock_cursor
        mock_connect.return_value.close = MagicMock()
        
        result = get_last_part_number("ANTENNA", db_dir="/custom/path")
        
        assert result == "ANT00001P1"
        mock_connect.assert_called_with("/custom/path/parts.db")

    @patch("casman.parts.generation.generate_barcode")
    @patch("casman.parts.generation.init_parts_db")
    @patch("casman.parts.generation.sqlite3.connect")
    @patch("casman.parts.generation.get_database_path")
    def test_generate_part_numbers_with_invalid_last_number(self, mock_get_path, mock_connect, mock_init, mock_barcode):
        """Test generating part numbers when last part number format is invalid."""
        from casman.parts.generation import generate_part_numbers
        
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        # Return invalid part number format (triggers ValueError/IndexError in split)
        mock_cursor.fetchone.return_value = ("INVALID_FORMAT",)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        results = generate_part_numbers("ANTENNA", 1, "1")
        
        # Should start from 1 when parsing fails
        assert len(results) == 1
        assert results[0] == "ANT00001P1"


class TestPartsTypes:
    """Test parts type loading."""

    @patch("casman.parts.types.get_config")
    def test_load_part_types_dict(self, mock_get_config):
        """Test loading part types from config as dict."""
        from casman.parts.types import load_part_types
        
        mock_get_config.return_value = {
            "1": ["ANTENNA", "ANT"],
            "2": ["LNA", "LNA"],
        }
        
        result = load_part_types()
        
        assert result == {
            1: ("ANTENNA", "ANT"),
            2: ("LNA", "LNA"),
        }

    @patch("casman.parts.types.get_config")
    def test_load_part_types_string(self, mock_get_config):
        """Test loading part types from config as string (literal eval)."""
        from casman.parts.types import load_part_types
        
        mock_get_config.return_value = '{1: ["ANTENNA", "ANT"], 2: ["LNA", "LNA"]}'
        
        result = load_part_types()
        
        assert 1 in result
        assert 2 in result

    @patch("casman.parts.types.get_config")
    def test_load_part_types_none(self, mock_get_config):
        """Test that missing PART_TYPES raises RuntimeError."""
        from casman.parts.types import load_part_types
        
        mock_get_config.return_value = None
        
        with pytest.raises(RuntimeError, match="PART_TYPES not defined"):
            load_part_types()


class TestPartsValidationExtended:
    """Extended tests for parts validation."""

    def test_validate_part_number_edge_cases(self):
        """Test part number validation edge cases."""
        # Valid formats
        assert validate_part_number("CXS00001P1")  # 3-letter prefix
        assert validate_part_number("BAC00001P1")  # BAC prefix
        assert validate_part_number("LNA00042P2")  # Different polarization
        
        # Invalid formats
        assert not validate_part_number("A00001P1")  # Prefix too short
        assert not validate_part_number("TOOLONG00001P1")  # Prefix too long
        assert not validate_part_number("ANT0001P1")  # Number too short
        assert not validate_part_number("ANT000001P1")  # Number too long
        assert not validate_part_number("ANT00001X1")  # Missing P
        assert not validate_part_number(123)  # Not a string
        assert not validate_part_number("")  # Empty string
        assert not validate_part_number("AAAAA")  # No digits at all

    def test_validate_part_type_edge_cases(self):
        """Test part type validation edge cases."""
        assert validate_part_type("COAXSHORT")
        assert validate_part_type("COAXLONG")
        assert validate_part_type("BACBOARD")
        assert not validate_part_type(None)
        assert not validate_part_type(123)
        assert not validate_part_type("")

    def test_validate_polarization_edge_cases(self):
        """Test polarization validation edge cases."""
        assert validate_polarization("P1")
        assert validate_polarization("P2")
        assert validate_polarization("PV")
        assert validate_polarization("PH")  # Any P + alphanumeric
        assert not validate_polarization("1")  # Missing P
        assert not validate_polarization("V")  # Missing P
        assert not validate_polarization("P")  # P alone
        assert not validate_polarization(None)
        assert not validate_polarization(123)

    def test_get_part_info_various_formats(self):
        """Test getting part info from various formats."""
        # 3-letter prefix
        info = get_part_info("CXS00001P1")
        assert info["prefix"] == "CXS"
        assert info["number"] == "00001"
        assert info["polarization"] == "P1"
        
        # Different polarization
        info = get_part_info("LNA00042P2")
        assert info["prefix"] == "LNA"
        assert info["number"] == "00042"
        assert info["polarization"] == "P2"

    def test_get_part_info_no_p_in_number(self):
        """Test get_part_info when part number doesn't have P after digits."""
        # This is an invalid format but test the None path
        info = get_part_info("INVALIDFORMAT")
        assert info is None

    def test_normalize_part_number(self):
        """Test normalizing part numbers."""
        from casman.parts.validation import normalize_part_number
        
        # Already normalized
        assert normalize_part_number("ANT00001P1") == "ANT00001P1"
        
        # Invalid returns None
        assert normalize_part_number("INVALID") is None
        assert normalize_part_number("") is None


class TestPartClassExtended:
    """Extended tests for Part class."""

    def test_part_initialization_with_timestamps(self):
        """Test creating Part with explicit timestamps."""
        part = Part(
            "ANT00001P1",
            date_created="2024-01-01 00:00:00",
            date_modified="2024-01-02 00:00:00",
        )
        assert part.date_created == "2024-01-01 00:00:00"
        assert part.date_modified == "2024-01-02 00:00:00"

    def test_part_from_dict_minimal(self):
        """Test creating Part from minimal dictionary."""
        data = {
            "part_number": "LNA00042P1",
        }
        part = Part.from_dict(data)
        assert part.part_number == "LNA00042P1"
        assert part.part_type == "LNA"

    def test_part_get_barcode_filename(self):
        """Test getting barcode filename."""
        part = Part("ANT00001P1")
        filename = part.get_barcode_filename()
        assert filename == "ANT00001P1.png"

    def test_part_inequality_with_non_part(self):
        """Test Part inequality with non-Part object."""
        part = Part("ANT00001P1")
        assert part != "ANT00001P1"
        assert part != 123
        assert part is not None

    def test_part_initialization_with_mismatched_type(self):
        """Test creating Part with mismatched part type."""
        with pytest.raises(ValueError, match="doesn't match part number"):
            Part("ANT00001P1", part_type="LNA")

    def test_part_initialization_with_mismatched_polarization(self):
        """Test creating Part with mismatched polarization."""
        with pytest.raises(ValueError, match="doesn't match part number"):
            Part("ANT00001P1", polarization="P2")

    def test_part_from_database_row_invalid(self):
        """Test creating Part from invalid database row."""
        with pytest.raises(ValueError, match="Invalid database row format"):
            Part.from_database_row((1, "ANT00001P1"))  # Too few fields

    def test_part_initialization_with_invalid_type(self):
        """Test creating Part with explicitly invalid part type."""
        with pytest.raises(ValueError, match="Invalid part type"):
            Part("ANT00001P1", part_type="INVALID_TYPE")

    def test_part_initialization_with_invalid_polarization(self):
        """Test creating Part with explicitly invalid polarization."""
        with pytest.raises(ValueError, match="Invalid polarization"):
            Part("ANT00001P1", polarization="INVALID")


class TestSearchPartsExtended:
    """Extended search tests."""

    @patch("casman.parts.search.sqlite3.connect")
    @patch("casman.parts.search.get_database_path")
    def test_search_parts_with_limit(self, mock_get_path, mock_connect):
        """Test searching with limit parameter."""
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),
        ]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        results = search_parts(limit=5)
        
        assert len(results) == 1
        # Verify LIMIT was added to query
        query_call = mock_cursor.execute.call_args[0][0]
        assert "LIMIT" in query_call

    @patch("casman.parts.search.sqlite3.connect")
    @patch("casman.parts.search.get_database_path")
    def test_search_parts_by_polarization(self, mock_get_path, mock_connect):
        """Test searching by polarization."""
        mock_get_path.return_value = "test.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2024-01-01", "2024-01-01"),
        ]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        results = search_parts(polarization="P1")
        
        assert len(results) == 1
        # Verify polarization pattern was used
        query_call = mock_cursor.execute.call_args[0][0]
        assert "LIKE" in query_call

    @patch("casman.parts.search.search_parts")
    def test_get_all_parts_with_custom_db_dir(self, mock_search):
        """Test getting all parts with custom db directory."""
        mock_search.return_value = [Part("ANT00001P1")]
        
        results = get_all_parts(db_dir="/custom/path")
        
        assert len(results) == 1
        mock_search.assert_called_once_with(db_dir="/custom/path")

    @patch("casman.parts.search.search_parts")
    def test_search_by_prefix_with_custom_db_dir(self, mock_search):
        """Test searching by prefix with custom db directory."""
        mock_search.return_value = [Part("LNA00001P1")]
        
        results = search_by_prefix("LNA", db_dir="/custom/path")
        
        assert len(results) == 1
        mock_search.assert_called_once_with(part_number_pattern="LNA-%", db_dir="/custom/path")

    @patch("casman.parts.search.sqlite3.connect")
    @patch("casman.parts.search.get_database_path")
    def test_get_part_statistics_with_custom_db_dir(self, mock_get_path, mock_connect):
        """Test getting statistics with custom db directory."""
        mock_get_path.return_value = "/custom/path/parts.db"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [(10,), ("ANT00010P1", "2024-01-15")]
        mock_cursor.fetchall.side_effect = [[("ANTENNA", 10)], [("P1", 10)]]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        stats = get_part_statistics(db_dir="/custom/path")
        
        assert stats["total_parts"] == 10
        mock_get_path.assert_called_once_with("parts.db", "/custom/path")

    @patch("casman.parts.search.search_parts")
    def test_find_part_with_custom_db_dir(self, mock_search):
        """Test finding part with custom db directory."""
        mock_search.return_value = [Part("ANT00001P1")]
        
        result = find_part("ANT00001P1", db_dir="/custom/path")
        
        assert result is not None
        mock_search.assert_called_once_with(
            part_number_pattern="ANT00001P1", limit=1, db_dir="/custom/path"
        )

    @patch("casman.parts.search.search_parts")
    def test_get_recent_parts_with_custom_db_dir(self, mock_search):
        """Test getting recent parts with custom db directory."""
        mock_search.return_value = [Part("ANT00001P1")]
        
        results = get_recent_parts(count=5, db_dir="/custom/path")
        
        assert len(results) == 1
        mock_search.assert_called_once_with(limit=5, db_dir="/custom/path")


class TestPartsInteractive:
    """Test interactive parts management functions."""

    @patch("casman.parts.interactive.read_parts")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_display_parts_all_types(self, _mock_print, mock_input, mock_read):
        """Test displaying all parts."""
        mock_input.side_effect = ["0", ""]  # Type=ALL, Polarization=ALL
        mock_read.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2025-01-01", "2025-01-01")
        ]

        from casman.parts.interactive import display_parts_interactive
        display_parts_interactive()

        mock_read.assert_called_once_with(None, None)

    @patch("casman.parts.interactive.read_parts")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_display_parts_by_type_number(self, _mock_print, mock_input, mock_read):
        """Test displaying parts by type number."""
        mock_input.side_effect = ["1", "1"]  # Type=1 (ANTENNA), Polarization=1
        mock_read.return_value = [
            (1, "ANT00001P1", "ANTENNA", "P1", "2025-01-01", "2025-01-01")
        ]

        from casman.parts.interactive import display_parts_interactive
        display_parts_interactive()

        mock_read.assert_called_once_with("ANTENNA", "1")

    @patch("casman.parts.interactive.read_parts")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_display_parts_by_alias(self, _mock_print, mock_input, mock_read):
        """Test displaying parts by alias."""
        mock_input.side_effect = ["ANT", ""]  # Type=ANT alias, Polarization=ALL
        mock_read.return_value = []

        from casman.parts.interactive import display_parts_interactive
        display_parts_interactive()

        mock_read.assert_called_once_with("ANTENNA", None)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_display_parts_invalid_type(self, mock_print, mock_input):
        """Test handling invalid part type selection."""
        mock_input.side_effect = ["99"]  # Invalid type number

        from casman.parts.interactive import display_parts_interactive
        display_parts_interactive()

        assert any(
            "Invalid selection" in str(call)
            for call in mock_print.call_args_list
        )

    @patch("builtins.input")
    @patch("builtins.print")
    def test_display_parts_invalid_input(self, mock_print, mock_input):
        """Test handling invalid input format."""
        mock_input.side_effect = ["invalid"]  # Invalid input

        from casman.parts.interactive import display_parts_interactive
        display_parts_interactive()

        assert any(
            "Invalid input" in str(call)
            for call in mock_print.call_args_list
        )

    @patch("casman.parts.interactive.read_parts")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_display_parts_no_results(self, mock_print, mock_input, mock_read):
        """Test displaying message when no parts found."""
        mock_input.side_effect = ["1", "1"]
        mock_read.return_value = []

        from casman.parts.interactive import display_parts_interactive
        display_parts_interactive()

        assert any(
            "No parts found" in str(call)
            for call in mock_print.call_args_list
        )

    @patch("casman.parts.interactive.generate_part_numbers")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_parts_single_type(self, mock_print, mock_input, mock_generate):
        """Test adding parts for single type."""
        mock_input.side_effect = ["1", "5", "1"]  # Type=ANTENNA, Count=5, Pol=1
        mock_generate.return_value = ["ANT-P1-00001", "ANT-P1-00002", "ANT-P1-00003", "ANT-P1-00004", "ANT-P1-00005"]

        from casman.parts.interactive import add_parts_interactive
        add_parts_interactive()

        mock_generate.assert_called_once()
        assert any(
            "Successfully created" in str(call)
            for call in mock_print.call_args_list
        )

    @patch("casman.parts.interactive.generate_part_numbers")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_parts_all_types(self, mock_print, mock_input, mock_generate):
        """Test adding parts for all types."""
        mock_input.side_effect = ["0", "3", "1"]  # Type=ALL, Count=3, Pol=1
        mock_generate.return_value = ["PART-P1-00001", "PART-P1-00002", "PART-P1-00003"]

        from casman.parts.interactive import add_parts_interactive
        add_parts_interactive()

        # Should call generate for each type (excluding SNAP)
        assert mock_generate.call_count == 5  # 6 types - 1 SNAP

    @patch("casman.parts.interactive.generate_part_numbers")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_parts_by_alias(self, _mock_print, mock_input, mock_generate):
        """Test adding parts using alias."""
        mock_input.side_effect = ["LNA", "2", "2"]  # Type=LNA alias, Count=2, Pol=2
        mock_generate.return_value = ["LNA-P2-00001", "LNA-P2-00002"]

        from casman.parts.interactive import add_parts_interactive
        add_parts_interactive()

        mock_generate.assert_called_once()

    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_parts_invalid_type(self, mock_print, mock_input):
        """Test handling invalid type selection."""
        mock_input.side_effect = ["99"]  # Invalid type

        from casman.parts.interactive import add_parts_interactive
        add_parts_interactive()

        assert any(
            "Invalid selection" in str(call)
            for call in mock_print.call_args_list
        )

    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_parts_invalid_count_zero(self, mock_print, mock_input):
        """Test handling zero count."""
        mock_input.side_effect = ["1", "0"]  # Type=ANTENNA, Count=0

        from casman.parts.interactive import add_parts_interactive
        add_parts_interactive()

        assert any(
            "must be greater than 0" in str(call)
            for call in mock_print.call_args_list
        )

    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_parts_invalid_count_negative(self, mock_print, mock_input):
        """Test handling negative count."""
        mock_input.side_effect = ["1", "-5"]  # Type=ANTENNA, Count=-5

        from casman.parts.interactive import add_parts_interactive
        add_parts_interactive()

        assert any(
            "must be greater than 0" in str(call)
            for call in mock_print.call_args_list
        )

    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_parts_invalid_count_format(self, mock_print, mock_input):
        """Test handling non-numeric count."""
        mock_input.side_effect = ["1", "abc"]  # Type=ANTENNA, Count=invalid

        from casman.parts.interactive import add_parts_interactive
        add_parts_interactive()

        assert any(
            "Invalid input" in str(call)
            for call in mock_print.call_args_list
        )

    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_parts_invalid_polarization(self, mock_print, mock_input):
        """Test handling invalid polarization."""
        mock_input.side_effect = ["1", "5", "3"]  # Pol=3 (invalid)

        from casman.parts.interactive import add_parts_interactive
        add_parts_interactive()

        assert any(
            "Invalid polarization" in str(call)
            for call in mock_print.call_args_list
        )

    @patch("casman.parts.interactive.generate_part_numbers")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_parts_database_error(self, mock_print, mock_input, mock_generate):
        """Test handling database error during part generation."""
        mock_input.side_effect = ["1", "5", "1"]
        mock_generate.side_effect = Exception("Database error")

        from casman.parts.interactive import add_parts_interactive
        
        # The function doesn't catch exceptions, so we expect it to propagate
        try:
            add_parts_interactive()
            assert False, "Expected exception to be raised"
        except Exception as e:
            assert "Database error" in str(e)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_parts_main_function(self, mock_print, mock_input):
        """Test main function for parts CLI."""
        mock_input.side_effect = ["3"]  # Invalid choice

        from casman.parts.interactive import main
        main()

        assert any(
            "Invalid choice" in str(call)
            for call in mock_print.call_args_list
        )
