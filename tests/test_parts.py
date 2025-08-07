"""Tests for the parts module."""

# Standard library imports
import os
import sqlite3
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest

from casman.database import init_parts_db

# Project imports
from casman.parts import (
    PART_TYPES,
    generate_part_numbers,
    get_last_part_number,
    read_parts,
)


@pytest.fixture(autouse=True)
def set_casman_parts_db_env(
    temporary_directory: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fixture to set CASMAN_PARTS_DB environment variable to a temp DB for isolation."""
    db_path = os.path.join(temporary_directory, "parts.db")
    os.makedirs(temporary_directory, exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)
    monkeypatch.setenv("CASMAN_PARTS_DB", db_path)


class TestParts:
    """Test parts functionality in the parts module."""

    def test_part_types_constant(self) -> None:
        """Test that PART_TYPES is a non-empty dict with correct structure."""
        assert isinstance(PART_TYPES, dict)
        assert len(PART_TYPES) > 0
        for key, (name, abbrev) in PART_TYPES.items():
            assert isinstance(key, int)
            assert isinstance(name, str)
            assert isinstance(abbrev, str)
            assert len(name) > 0
            assert len(abbrev) > 0

    def test_get_last_part_number_empty_db(self, temporary_directory: str) -> None:
        """Test get_last_part_number returns None for empty DB."""
        init_parts_db(temporary_directory)
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parts")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='parts'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        result = get_last_part_number("ANTENNA")
        assert result is None

    def test_get_last_part_number_with_data(self, temporary_directory: str) -> None:
        """
        Test get_last_part_number returns correct values with data present.
        Ensures that the function returns the last part number for each type \
            and None for missing types.
        """
        init_parts_db(temporary_directory)
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parts")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='parts'")
        except sqlite3.OperationalError:
            pass
        # Insert test data
        test_parts = [
            (
                "ANTP1-00001",
                "ANTENNA",
                "X",
                "2024-01-01 10:00:00",
                "2024-01-01 10:00:00",
            ),
            (
                "ANTP1-00002",
                "ANTENNA",
                "Y",
                "2024-01-01 10:01:00",
                "2024-01-01 10:01:00",
            ),
            ("LNAP1-00001", "LNA", "X", "2024-01-01 10:02:00", "2024-01-01 10:02:00"),
        ]
        for part in test_parts:
            cursor.execute(
                # Insert each test part into the database
                "INSERT INTO parts (part_number, part_type, \
                    polarization, date_created, date_modified) "
                "VALUES (?, ?, ?, ?, ?)",
                part,
            )
        conn.commit()
        conn.close()
        # Check last part numbers for each type
        last_antenna = get_last_part_number("ANTENNA")
        assert last_antenna == "ANTP1-00002"
        last_lna = get_last_part_number("LNA")
        assert last_lna == "LNAP1-00001"
        last_missing = get_last_part_number("NONEXISTENT")
        assert last_missing is None

    @patch("casman.parts.generation.generate_barcode")
    def test_generate_part_numbers_new_type(
        self, mock_generate_barcode: MagicMock, temporary_directory: str
    ) -> None:
        """
        Test generating part numbers for a new part type.
        Ensures that the correct number and format of part numbers
        are generated and barcodes are created.
        """
        init_parts_db(temporary_directory)
        mock_generate_barcode.return_value = None
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parts")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='parts'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        # Generate new part numbers
        new_parts = generate_part_numbers("ANTENNA", 3, "1")
        assert len(new_parts) == 3
        assert new_parts[0] == "ANT-P1-00001"
        assert new_parts[1] == "ANT-P1-00002"
        assert new_parts[2] == "ANT-P1-00003"
        assert mock_generate_barcode.call_count == 3

    @patch("casman.parts.generation.generate_barcode")
    def test_generate_part_numbers_existing_type(
        self, mock_generate_barcode: MagicMock, temporary_directory: str
    ) -> None:
        """Test generating part numbers for an existing part type."""
        init_parts_db(temporary_directory)
        mock_generate_barcode.return_value = None
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parts")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='parts'")
        except sqlite3.OperationalError:
            pass
        # Insert an existing part
        cursor.execute(
            "INSERT INTO parts (part_number, part_type, polarization, date_created, date_modified) "
            "VALUES (?, ?, ?, ?, ?)",
            ("LNA-P1-00005", "LNA", "1", "2024-01-01", "2024-01-01"),
        )
        conn.commit()
        conn.close()
        new_parts = generate_part_numbers("LNA", 2, "1")
        assert len(new_parts) == 2
        assert new_parts[0] == "LNA-P1-00006"
        assert new_parts[1] == "LNA-P1-00007"

    def test_generate_part_numbers_invalid_type(self) -> None:
        """Test that ValueError is raised for unknown part type."""
        with pytest.raises(ValueError, match="Unknown part type"):
            generate_part_numbers("INVALID_TYPE", 1, "1")

    def test_read_parts_empty_db(self, temporary_directory: str) -> None:
        """Test read_parts returns empty list for empty DB."""
        init_parts_db(temporary_directory)
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parts")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='parts'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        parts = read_parts()
        assert parts == []

    def test_read_parts_with_data(self, temporary_directory: str) -> None:
        """Test read_parts returns correct data when DB has parts."""
        init_parts_db(temporary_directory)
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parts")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='parts'")
        except sqlite3.OperationalError:
            pass
        # Insert test data
        test_parts = [
            ("ANT-P1-00001", "ANTENNA", "1", "2024-01-01", "2024-01-01"),
            ("LNA-P1-00001", "LNA", "2", "2024-01-01", "2024-01-01"),
            ("BAC-P1-00001", "BACBOARD", "1", "2024-01-01", "2024-01-01"),
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
        parts = read_parts()
        assert len(parts) == 3
        for part in parts:
            assert part[1] in ["ANT-P1-00001", "LNA-P1-00001", "BAC-P1-00001"]
            assert part[2] in ["ANTENNA", "LNA", "BACBOARD"]
            assert len(part) >= 6

    def test_generate_part_numbers_zero_count(self) -> None:
        """Test generate_part_numbers returns empty list for zero count."""
        result = generate_part_numbers("ANTENNA", 0, "1")
        assert not result

    def test_generate_part_numbers_negative_count(self) -> None:
        """Test generate_part_numbers returns empty list for negative count."""
        result = generate_part_numbers("ANTENNA", -1, "1")
        assert not result

    @patch("casman.parts.generation.generate_barcode")
    def test_generate_part_numbers_database_persistence(
        self, mock_generate_barcode: MagicMock, temporary_directory: str
    ) -> None:
        """Test that generated part numbers are persisted in the database."""
        init_parts_db(temporary_directory)
        mock_generate_barcode.return_value = None
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parts")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='parts'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        new_parts = generate_part_numbers("BACBOARD", 2, "V")
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT part_number, part_type, polarization FROM parts ORDER BY id"
        )
        saved_parts = cursor.fetchall()
        conn.close()
        assert len(saved_parts) == 2
        assert saved_parts[0] == ("BAC-PV-00001", "BACBOARD", "V")
        assert saved_parts[1] == ("BAC-PV-00002", "BACBOARD", "V")
        assert new_parts == ["BAC-PV-00001", "BAC-PV-00002"]

    def test_part_number_format(self, temporary_directory: str) -> None:
        """Test that generated part numbers have the correct format for all types."""
        init_parts_db(temporary_directory)
        conn = sqlite3.connect(os.path.join(temporary_directory, "parts.db"))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parts")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='parts'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        # Patch barcode generation for all types
        with patch("casman.parts.generation.generate_barcode"):
            for _, (part_type, abbrev) in PART_TYPES.items():
                new_parts = generate_part_numbers(part_type, 1, "1")
                assert len(new_parts) == 1
                part_number = new_parts[0]
                expected_prefix = f"{abbrev}-P1-"
                assert part_number.startswith(expected_prefix)
                number_part = part_number[len(expected_prefix) :]
                assert len(number_part) == 5
                assert number_part.isdigit()
