"""
Comprehensive tests for the visualization module.

This module tests all visualization functions including:
- ASCII chain formatting
- Chain summary statistics
- Duplicate connection detection
- Main entry points
"""

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from casman.visualization.core import (
    format_ascii_chains,
    get_chain_summary,
    get_duplicate_connections,
    _calculate_chain_length,
    main as core_main,
)
from casman.visualization import main as package_main


class TestFormatAsciiChains:
    """Test ASCII chain formatting functionality."""

    @patch("casman.visualization.core.get_duplicate_connections")
    @patch("casman.visualization.core.build_connection_chains")
    def test_format_ascii_chains_with_connections(
        self, mock_build_chains, mock_get_duplicates
    ):
        """Test formatting ASCII chains with valid connections."""
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1"],
            "LNA00001P1": ["CXS00001P1"],
        }
        mock_get_duplicates.return_value = {}

        result = format_ascii_chains()

        assert "CASM Assembly Connections:" in result
        assert "ANT00001P1" in result
        assert "LNA00001P1" in result
        assert "CXS00001P1" in result
        assert "--->" in result

    @patch("casman.visualization.core.get_duplicate_connections")
    @patch("casman.visualization.core.build_connection_chains")
    def test_format_ascii_chains_empty(self, mock_build_chains, mock_get_duplicates):
        """Test formatting when no chains exist."""
        mock_build_chains.return_value = {}
        mock_get_duplicates.return_value = {}

        result = format_ascii_chains()

        assert result == "No assembly connections found."

    @patch("casman.visualization.core.get_duplicate_connections")
    @patch("casman.visualization.core.build_connection_chains")
    def test_format_ascii_chains_with_duplicates(
        self, mock_build_chains, mock_get_duplicates
    ):  # noqa: E501
        """Test formatting chains with duplicate connections."""
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1"],
        }
        mock_get_duplicates.return_value = {
            "ANT00001P1": [
                ("LNA00001P1", "2024-01-01 10:00:00", "2024-01-01 10:05:00"),
                ("LNA00002P1", "2024-01-01 11:00:00", "2024-01-01 11:05:00"),
            ]
        }

        result = format_ascii_chains()

        assert "DUPLICATE CONNECTIONS DETECTED:" in result
        assert "ANT00001P1" in result
        assert "2 database entries" in result
        assert "LNA00001P1" in result
        assert "LNA00002P1" in result

    @patch("casman.visualization.core.get_duplicate_connections")
    @patch("casman.visualization.core.build_connection_chains")
    def test_format_ascii_chains_with_custom_db_dir(
        self, mock_build_chains, mock_get_duplicates
    ):
        """Test formatting chains with custom database directory."""
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1"],
        }
        mock_get_duplicates.return_value = {}

        result = format_ascii_chains(db_dir="/custom/path")

        assert "CASM Assembly Connections:" in result
        mock_build_chains.assert_called_once_with("/custom/path")
        mock_get_duplicates.assert_called_once_with("/custom/path")

    @patch("casman.visualization.core.get_duplicate_connections")
    @patch("casman.visualization.core.build_connection_chains")
    def test_format_ascii_chains_multiple_starting_points(
        self, mock_build_chains, mock_get_duplicates
    ):
        """Test formatting chains with multiple independent starting points."""
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1"],
            "ANT00002P1": ["LNA00002P1"],
        }
        mock_get_duplicates.return_value = {}

        result = format_ascii_chains()

        assert "ANT00001P1" in result
        assert "ANT00002P1" in result
        assert "LNA00001P1" in result
        assert "LNA00002P1" in result

    @patch("casman.visualization.core.get_duplicate_connections")
    @patch("casman.visualization.core.build_connection_chains")
    def test_format_ascii_chains_no_starting_points(
        self, mock_build_chains, mock_get_duplicates
    ):
        """Test formatting chains when all parts are connected (circular)."""
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1"],
            "LNA00001P1": ["ANT00001P1"],  # Circular reference
        }
        mock_get_duplicates.return_value = {}

        result = format_ascii_chains()

        assert "CASM Assembly Connections:" in result
        # Should still handle the circular case gracefully

    @patch("casman.visualization.core.get_duplicate_connections")
    @patch("casman.visualization.core.build_connection_chains")
    def test_format_ascii_chains_branching(
        self, mock_build_chains, mock_get_duplicates
    ):
        """Test formatting chains with branching connections."""
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1", "LNA00002P1"],  # Branches to two parts
        }
        mock_get_duplicates.return_value = {}

        result = format_ascii_chains()

        assert "ANT00001P1" in result
        assert "LNA00001P1" in result or "LNA00002P1" in result

    @patch("casman.visualization.core.get_duplicate_connections")
    @patch("casman.visualization.core.build_connection_chains")
    def test_format_ascii_chains_already_printed_parts(
        self, mock_build_chains, mock_get_duplicates
    ):
        """Test formatting when parts are already printed (circular or revisited)."""
        # This tests the case where current_part is already in printed_parts
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1"],
            "LNA00001P1": ["CXS00001P1"],
            "CXS00001P1": ["LNA00001P1"],  # Points back to already visited
        }
        mock_get_duplicates.return_value = {}

        result = format_ascii_chains()

        assert "CASM Assembly Connections:" in result
        # Should handle the circular reference without infinite loop


class TestGetDuplicateConnections:
    """Test duplicate connection detection."""

    @patch("casman.database.connection.get_database_path")
    @patch("sqlite3.connect")
    def test_get_duplicate_connections_with_duplicates(
        self, mock_connect, mock_get_path
    ):
        """Test detecting duplicate connections."""
        mock_get_path.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("ANT00001P1", "LNA00001P1", "2024-01-01 10:00:00", "2024-01-01 10:05:00"),
            ("ANT00001P1", "LNA00002P1", "2024-01-01 11:00:00", "2024-01-01 11:05:00"),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = lambda self: self
        mock_conn.__exit__ = lambda self, *args: None
        mock_connect.return_value = mock_conn

        duplicates = get_duplicate_connections()

        assert "ANT00001P1" in duplicates
        assert len(duplicates["ANT00001P1"]) == 2
        assert duplicates["ANT00001P1"][0] == (
            "LNA00001P1",
            "2024-01-01 10:00:00",
            "2024-01-01 10:05:00",
        )
        mock_get_path.assert_called_once_with("assembled_casm.db", None)

    @patch("casman.database.connection.get_database_path")
    @patch("sqlite3.connect")
    def test_get_duplicate_connections_no_duplicates(
        self, mock_connect, mock_get_path
    ):
        """Test when no duplicate connections exist."""
        mock_get_path.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("ANT00001P1", "LNA00001P1", "2024-01-01 10:00:00", "2024-01-01 10:05:00"),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = lambda self: self
        mock_conn.__exit__ = lambda self, *args: None
        mock_connect.return_value = mock_conn

        duplicates = get_duplicate_connections()

        assert duplicates == {}

    @patch("casman.database.connection.get_database_path")
    @patch("sqlite3.connect")
    def test_get_duplicate_connections_with_custom_db_dir(
        self, mock_connect, mock_get_path
    ):
        """Test detecting duplicates with custom database directory."""
        mock_get_path.return_value = "/custom/path/assembled_casm.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = lambda self: self
        mock_conn.__exit__ = lambda self, *args: None
        mock_connect.return_value = mock_conn

        duplicates = get_duplicate_connections(db_dir="/custom/path")

        assert duplicates == {}
        mock_get_path.assert_called_once_with("assembled_casm.db", "/custom/path")

    @patch("casman.database.connection.get_database_path")
    @patch("sqlite3.connect")
    def test_get_duplicate_connections_database_error(
        self, mock_connect, mock_get_path
    ):
        """Test handling database errors."""
        mock_get_path.return_value = "test.db"
        mock_connect.side_effect = sqlite3.Error("Database error")

        duplicates = get_duplicate_connections()

        assert duplicates == {}

    @patch("casman.database.connection.get_database_path")
    @patch("sqlite3.connect")
    def test_get_duplicate_connections_with_none_values(
        self, mock_connect, mock_get_path
    ):
        """Test handling None values in database records."""
        mock_get_path.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("ANT00001P1", None, None, None),
            ("ANT00001P1", "LNA00001P1", None, "2024-01-01 10:05:00"),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = lambda self: self
        mock_conn.__exit__ = lambda self, *args: None
        mock_connect.return_value = mock_conn

        duplicates = get_duplicate_connections()

        assert "ANT00001P1" in duplicates
        assert len(duplicates["ANT00001P1"]) == 2
        # None values should be converted to "None" strings
        assert duplicates["ANT00001P1"][0][0] == "None"


class TestGetChainSummary:
    """Test chain summary statistics."""

    @patch("casman.visualization.core.build_connection_chains")
    def test_get_chain_summary_with_chains(self, mock_build_chains):
        """Test getting summary statistics with chains."""
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1"],
            "LNA00001P1": ["CXS00001P1"],
            "CXS00001P1": ["BAC00001P1"],
        }

        summary = get_chain_summary()

        assert summary["total_parts"] == 3
        assert summary["total_connections"] == 3
        assert summary["total_chains"] == 1
        assert summary["average_chain_length"] > 0
        assert summary["longest_chain"] == 4  # ANT->LNA->CXS->BAC

    @patch("casman.visualization.core.build_connection_chains")
    def test_get_chain_summary_empty(self, mock_build_chains):
        """Test getting summary with no chains."""
        mock_build_chains.return_value = {}

        summary = get_chain_summary()

        assert summary["total_parts"] == 0
        assert summary["total_connections"] == 0
        assert summary["total_chains"] == 0
        assert summary["average_chain_length"] == 0.0
        assert summary["longest_chain"] == 0

    @patch("casman.visualization.core.build_connection_chains")
    def test_get_chain_summary_multiple_chains(self, mock_build_chains):
        """Test getting summary with multiple independent chains."""
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1"],
            "LNA00001P1": ["CXS00001P1"],
            "ANT00002P1": ["LNA00002P1"],
        }

        summary = get_chain_summary()

        assert summary["total_parts"] == 3
        assert summary["total_connections"] == 3
        assert summary["total_chains"] == 2
        assert summary["average_chain_length"] > 0
        assert summary["longest_chain"] == 3  # ANT->LNA->CXS

    @patch("casman.visualization.core.build_connection_chains")
    def test_get_chain_summary_with_custom_db_dir(self, mock_build_chains):
        """Test getting summary with custom database directory."""
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1"],
        }

        summary = get_chain_summary(db_dir="/custom/path")

        assert summary["total_parts"] == 1
        assert summary["total_connections"] == 1
        mock_build_chains.assert_called_once_with("/custom/path")

    @patch("casman.visualization.core.build_connection_chains")
    def test_get_chain_summary_single_part_no_connections(self, mock_build_chains):
        """Test summary with parts but no connections."""
        mock_build_chains.return_value = {
            "ANT00001P1": [],
        }

        summary = get_chain_summary()

        assert summary["total_parts"] == 1
        assert summary["total_connections"] == 0
        assert summary["total_chains"] == 1
        assert summary["longest_chain"] == 1

    @patch("casman.visualization.core.build_connection_chains")
    def test_get_chain_summary_branching_chains(self, mock_build_chains):
        """Test summary with branching chains."""
        mock_build_chains.return_value = {
            "ANT00001P1": ["LNA00001P1", "LNA00002P1"],  # Branches
            "LNA00001P1": ["CXS00001P1"],
        }

        summary = get_chain_summary()

        # total_parts counts keys in chains dict, not all parts mentioned
        assert summary["total_parts"] == 2  # ANT00001P1, LNA00001P1
        assert summary["total_connections"] == 3  # ANT has 2 connections, LNA has 1


class TestGetChainSummaryEdgeCases:
    """Test edge cases in chain summary calculation."""

    @patch("casman.visualization.core.build_connection_chains")
    def test_get_chain_summary_all_visited(self, mock_build_chains):
        """Test summary when all parts are already visited (empty chain_lengths)."""
        # Create a scenario where _calculate_chain_length returns 0
        mock_build_chains.return_value = {
            "ANT00001P1": [],
        }

        summary = get_chain_summary()

        # With no connections, should still count the part
        assert summary["total_parts"] == 1
        assert summary["total_chains"] == 1


class TestCalculateChainLength:
    """Test chain length calculation helper function."""

    def test_calculate_chain_length_simple(self):
        """Test calculating length of simple chain."""
        chains = {
            "ANT00001P1": ["LNA00001P1"],
            "LNA00001P1": ["CXS00001P1"],
        }
        visited = set()

        length = _calculate_chain_length("ANT00001P1", chains, visited)

        assert length == 3
        assert "ANT00001P1" in visited
        assert "LNA00001P1" in visited
        assert "CXS00001P1" in visited

    def test_calculate_chain_length_single_part(self):
        """Test calculating length of single part with no connections."""
        chains = {
            "ANT00001P1": [],
        }
        visited = set()

        length = _calculate_chain_length("ANT00001P1", chains, visited)

        assert length == 1

    def test_calculate_chain_length_already_visited(self):
        """Test calculating length when part is already visited."""
        chains = {
            "ANT00001P1": ["LNA00001P1"],
        }
        visited = {"ANT00001P1"}

        length = _calculate_chain_length("ANT00001P1", chains, visited)

        assert length == 0

    def test_calculate_chain_length_branching(self):
        """Test calculating length with branching (follows first connection)."""
        chains = {
            "ANT00001P1": ["LNA00001P1", "LNA00002P1"],
            "LNA00001P1": ["CXS00001P1"],
        }
        visited = set()

        length = _calculate_chain_length("ANT00001P1", chains, visited)

        # Should follow first connection path
        assert length == 3  # ANT -> LNA00001P1 -> CXS00001P1

    def test_calculate_chain_length_circular_reference(self):
        """Test calculating length with circular reference."""
        chains = {
            "ANT00001P1": ["LNA00001P1"],
            "LNA00001P1": ["ANT00001P1"],
        }
        visited = set()

        length = _calculate_chain_length("ANT00001P1", chains, visited)

        # Should stop at circular reference
        assert length == 2  # ANT -> LNA, then stops


class TestCoreMain:
    """Test the core visualization main function."""

    @patch("builtins.input")
    @patch("casman.visualization.core.format_ascii_chains")
    @patch("builtins.print")
    def test_core_main_choice_1(self, mock_print, mock_format, mock_input):
        """Test main function with choice 1 (show ASCII chains)."""
        mock_input.return_value = "1"
        mock_format.return_value = "Chain output"

        core_main()

        mock_format.assert_called_once()
        # Check that print was called with the chain output
        print_calls = [str(c) for c in mock_print.call_args_list]
        assert any("Chain output" in str(c) for c in print_calls)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_core_main_invalid_choice(self, mock_print, mock_input):
        """Test main function with invalid choice."""
        mock_input.return_value = "99"

        core_main()

        print_calls = [str(c) for c in mock_print.call_args_list]
        assert any("Invalid choice" in str(c) for c in print_calls)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_core_main_value_error(self, mock_print, mock_input):
        """Test main function with non-numeric input."""
        mock_input.return_value = "abc"

        core_main()

        print_calls = [str(c) for c in mock_print.call_args_list]
        assert any("Invalid input" in str(c) for c in print_calls)


class TestPackageMain:
    """Test the package-level main function."""

    @patch("builtins.input")
    @patch("casman.visualization.cli_main")
    @patch("builtins.print")
    def test_package_main_choice_1(self, _mock_print, mock_cli_main, mock_input):
        """Test package main with choice 1."""
        mock_input.return_value = "1"

        package_main()

        mock_cli_main.assert_called_once()

    @patch("builtins.input")
    @patch("casman.visualization.cli_main")
    @patch("builtins.print")
    def test_package_main_empty_choice(self, _mock_print, mock_cli_main, mock_input):
        """Test package main with empty choice (defaults to 1)."""
        mock_input.return_value = ""

        package_main()

        mock_cli_main.assert_called_once()

    @patch("builtins.input")
    @patch("builtins.print")
    def test_package_main_invalid_choice(self, mock_print, mock_input):
        """Test package main with invalid choice."""
        mock_input.return_value = "99"

        package_main()

        print_calls = [str(c) for c in mock_print.call_args_list]
        assert any("Invalid option" in str(c) for c in print_calls)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_package_main_keyboard_interrupt(self, mock_print, mock_input):
        """Test package main handling KeyboardInterrupt."""
        mock_input.side_effect = KeyboardInterrupt()

        package_main()

        print_calls = [str(c) for c in mock_print.call_args_list]
        assert any("Goodbye" in str(c) for c in print_calls)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_package_main_eof_error(self, mock_print, mock_input):
        """Test package main handling EOFError."""
        mock_input.side_effect = EOFError()

        package_main()

        print_calls = [str(c) for c in mock_print.call_args_list]
        assert any("Goodbye" in str(c) for c in print_calls)

    @patch("sys.argv", ["prog", "--web"])
    @patch("builtins.print")
    def test_package_main_web_flag(self, mock_print):
        """Test package main with --web flag."""
        package_main()

        print_calls = [str(c) for c in mock_print.call_args_list]
        assert any("Web visualization not available" in str(c) for c in print_calls)
