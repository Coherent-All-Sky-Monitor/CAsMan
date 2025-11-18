"""Comprehensive tests for CAsMan assembly functionality."""

import sqlite3
from unittest.mock import patch, MagicMock

from casman.assembly.chains import build_connection_chains, print_assembly_chains
from casman.assembly.connections import (
    record_assembly_connection,
    record_assembly_disconnection,
)
from casman.assembly.data import get_assembly_connections
from casman.assembly.interactive import (
    validate_connection_rules,
    validate_chain_directionality,
    check_existing_connections,
    check_target_connections,
    validate_part_in_database,
    validate_snap_part,
    VALID_NEXT_CONNECTIONS,
)
from casman.assembly import main


class TestAssemblyConnections:
    """Test assembly connection recording functions."""

    @patch("casman.assembly.connections.get_database_path")
    @patch("casman.assembly.connections.init_assembled_db")
    @patch("casman.assembly.connections.sqlite3.connect")
    def test_record_assembly_connection_success(
        self, mock_connect, mock_init, mock_get_path
    ):
        """Test successful assembly connection recording."""
        mock_get_path.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_connect.return_value.__exit__.return_value = None

        result = record_assembly_connection(
            "ANT-P1-00001",
            "ANTENNA",
            "P1",
            "2024-01-01 10:00:00",
            "LNA-P1-00001",
            "LNA",
            "P1",
            "2024-01-01 10:05:00",
        )

        assert result is True
        mock_init.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch("casman.assembly.connections.get_database_path")
    @patch("casman.assembly.connections.init_assembled_db")
    @patch("casman.assembly.connections.sqlite3.connect")
    def test_record_assembly_connection_with_status(
        self, mock_connect, _mock_init, mock_get_path
    ):
        """Test recording connection with custom status."""
        mock_get_path.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_connect.return_value.__exit__.return_value = None

        result = record_assembly_connection(
            "ANT00001P1",
            "ANTENNA",
            "P1",
            "2024-01-01 10:00:00",
            "LNA00001P1",
            "LNA",
            "P1",
            "2024-01-01 10:05:00",
            connection_status="disconnected",
        )

        assert result is True
        # Verify the status was passed correctly
        call_args = mock_cursor.execute.call_args[0]
        assert "disconnected" in call_args[1]

    @patch("casman.assembly.connections.get_database_path")
    @patch("casman.assembly.connections.init_assembled_db")
    @patch("casman.assembly.connections.sqlite3.connect")
    def test_record_assembly_connection_database_error(
        self, mock_connect, _mock_init, mock_get_path
    ):
        """Test handling of database errors."""
        mock_get_path.return_value = "test.db"
        mock_connect.side_effect = sqlite3.Error("Database error")

        result = record_assembly_connection(
            "ANT00001P1",
            "ANTENNA",
            "P1",
            "2024-01-01 10:00:00",
            "LNA00001P1",
            "LNA",
            "P1",
            "2024-01-01 10:05:00",
        )

        assert result is False

    @patch("casman.assembly.connections.record_assembly_connection")
    def test_record_assembly_disconnection(self, mock_record):
        """Test assembly disconnection recording."""
        mock_record.return_value = True

        result = record_assembly_disconnection(
            "ANT00001P1",
            "ANTENNA",
            "P1",
            "2024-01-01 10:00:00",
            "LNA00001P1",
            "LNA",
            "P1",
            "2024-01-01 10:10:00",
        )

        assert result is True
        mock_record.assert_called_once()
        # Verify it was called with disconnected status
        call_kwargs = mock_record.call_args[1]
        assert call_kwargs["connection_status"] == "disconnected"

    @patch("casman.assembly.connections.get_database_path")
    @patch("casman.assembly.connections.init_assembled_db")
    @patch("casman.assembly.connections.sqlite3.connect")
    def test_record_assembly_connection_value_error(
        self, mock_connect, _mock_init, mock_get_path
    ):
        """Test handling of value errors."""
        mock_get_path.return_value = "test.db"
        mock_connect.side_effect = ValueError("Invalid value")

        result = record_assembly_connection(
            "ANT00001P1",
            "ANTENNA",
            "P1",
            "2024-01-01 10:00:00",
            "LNA00001P1",
            "LNA",
            "P1",
            "2024-01-01 10:05:00",
        )

        assert result is False


class TestAssemblyData:
    """Test assembly data retrieval functions."""

    @patch("casman.assembly.data.get_database_path")
    @patch("casman.assembly.data.sqlite3.connect")
    def test_get_assembly_connections_success(self, mock_connect, mock_get_path):
        """Test successful retrieval of assembly connections."""
        mock_get_path.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("ANT00001P1", "LNA00001P1", "2024-01-01 10:00:00", "ANTENNA", "P1"),
            ("LNA00001P1", "CXS00001P1", "2024-01-01 10:05:00", "LNA", "P1"),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_connect.return_value.__exit__.return_value = None

        connections = get_assembly_connections()

        assert len(connections) == 2
        assert connections[0][0] == "ANT00001P1"
        assert connections[0][1] == "LNA00001P1"

    @patch("casman.assembly.data.get_database_path")
    @patch("casman.assembly.data.sqlite3.connect")
    def test_get_assembly_connections_empty(self, mock_connect, mock_get_path):
        """Test retrieval with no connections."""
        mock_get_path.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_connect.return_value.__exit__.return_value = None

        connections = get_assembly_connections()

        assert connections == []

    @patch("casman.assembly.data.get_database_path")
    @patch("casman.assembly.data.sqlite3.connect")
    def test_get_assembly_connections_database_error(
        self, mock_connect, mock_get_path
    ):
        """Test handling of database errors."""
        mock_get_path.return_value = "test.db"
        mock_connect.side_effect = sqlite3.Error("Database error")

        connections = get_assembly_connections()

        assert connections == []

    @patch("casman.assembly.data.get_database_path")
    @patch("casman.assembly.data.sqlite3.connect")
    def test_get_assembly_connections_with_custom_dir(
        self, mock_connect, mock_get_path
    ):
        """Test retrieval with custom database directory."""
        mock_get_path.return_value = "custom/test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_connect.return_value.__exit__.return_value = None

        get_assembly_connections(db_dir="custom")

        mock_get_path.assert_called_with("assembled_casm.db", "custom")


class TestAssemblyChains:
    """Test assembly chain building and printing functions."""

    @patch("casman.assembly.chains.get_assembly_connections")
    def test_build_connection_chains_simple(self, mock_get_connections):
        """Test building simple connection chains."""
        mock_get_connections.return_value = [
            ("ANT00001P1", "LNA00001P1", "2024-01-01 10:00:00", "ANTENNA", "P1"),
            ("LNA00001P1", "CXS00001P1", "2024-01-01 10:05:00", "LNA", "P1"),
        ]

        chains = build_connection_chains()

        assert "ANT00001P1" in chains
        assert "LNA00001P1" in chains
        assert "LNA00001P1" in chains["ANT00001P1"]
        assert "CXS00001P1" in chains["LNA00001P1"]

    @patch("casman.assembly.chains.get_assembly_connections")
    def test_build_connection_chains_empty(self, mock_get_connections):
        """Test building chains with no connections."""
        mock_get_connections.return_value = []

        chains = build_connection_chains()

        assert chains == {}

    @patch("casman.assembly.chains.get_assembly_connections")
    def test_build_connection_chains_no_duplicates(self, mock_get_connections):
        """Test that duplicate connections are not added."""
        mock_get_connections.return_value = [
            ("ANT00001P1", "LNA00001P1", "2024-01-01 10:00:00", "ANTENNA", "P1"),
            ("ANT00001P1", "LNA00001P1", "2024-01-01 10:05:00", "ANTENNA", "P1"),
        ]

        chains = build_connection_chains()

        assert len(chains["ANT00001P1"]) == 1

    @patch("casman.assembly.chains.build_connection_chains")
    @patch("builtins.print")
    def test_print_assembly_chains_with_connections(self, mock_print, mock_build):
        """Test printing assembly chains."""
        mock_build.return_value = {
            "ANT00001P1": ["LNA00001P1"],
            "LNA00001P1": ["CXS00001P1"],
        }

        print_assembly_chains()

        # Verify print was called
        assert mock_print.call_count > 0
        # Check that header was printed
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Assembly Chains:" in str(call) for call in calls)

    @patch("casman.assembly.chains.build_connection_chains")
    @patch("builtins.print")
    def test_print_assembly_chains_empty(self, mock_print, mock_build):
        """Test printing with no chains."""
        mock_build.return_value = {}

        print_assembly_chains()

        # Should print "No assembly connections found."
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("No assembly connections found" in str(call) for call in calls)

    @patch("casman.assembly.chains.build_connection_chains")
    @patch("builtins.print")
    def test_print_assembly_chains_multiple_chains(self, mock_print, mock_build):
        """Test printing multiple independent chains."""
        mock_build.return_value = {
            "ANT00001P1": ["LNA00001P1"],
            "ANT00002P1": ["LNA00002P1"],
        }

        print_assembly_chains()

        assert mock_print.call_count > 0

    @patch("casman.assembly.chains.build_connection_chains")
    @patch("builtins.print")
    def test_print_assembly_chains_circular_reference(self, mock_print, mock_build):
        """Test printing chains with circular references."""
        mock_build.return_value = {
            "ANT00001P1": ["LNA00001P1"],
            "LNA00001P1": ["ANT00001P1"],  # Circular reference
        }

        print_assembly_chains()

        assert mock_print.call_count > 0

    @patch("casman.assembly.chains.build_connection_chains")
    @patch("builtins.print")
    def test_print_assembly_chains_with_custom_db_dir(self, mock_print, mock_build):
        """Test printing chains with custom database directory."""
        mock_build.return_value = {
            "ANT00001P1": ["LNA00001P1"],
        }

        print_assembly_chains(db_dir="/custom/path")

        assert mock_print.call_count > 0
        mock_build.assert_called_once_with("/custom/path")

    @patch("casman.assembly.chains.get_assembly_connections")
    def test_build_connection_chains_with_custom_db_dir(self, mock_get_connections):
        """Test building chains with custom database directory."""
        mock_get_connections.return_value = [
            ("ANT00001P1", "LNA00001P1", "2024-01-01 10:00:00", "ANTENNA", "P1"),
        ]

        chains = build_connection_chains(db_dir="/custom/path")

        assert "ANT00001P1" in chains
        mock_get_connections.assert_called_once_with("/custom/path")


class TestAssemblyInteractive:
    """Test interactive assembly validation functions."""

    def test_validate_connection_rules_valid(self):
        """Test valid connection rules."""
        # ANTENNA -> LNA is valid
        is_valid, error = validate_connection_rules(
            "ANT00001P1", "ANTENNA", "LNA00001P1", "LNA"
        )
        assert is_valid is True
        assert error == ""

    def test_validate_connection_rules_invalid(self):
        """Test invalid connection rules."""
        # ANTENNA -> SNAP is invalid (skips intermediate parts)
        is_valid, error = validate_connection_rules(
            "ANT00001P1", "ANTENNA", "SNAP1A00", "SNAP"
        )
        assert is_valid is False
        assert "can only connect to" in error

    def test_validate_connection_rules_terminal_part(self):
        """Test connection from terminal part."""
        # SNAP cannot connect to anything
        is_valid, _ = validate_connection_rules(
            "SNAP1A00", "SNAP", "ANT00001P1", "ANTENNA"
        )
        assert is_valid is False

    def test_validate_chain_directionality_antenna_outgoing_valid(self):
        """Test ANTENNA can make outgoing connections."""
        is_valid, error = validate_chain_directionality("ANTENNA", "outgoing")
        assert is_valid is True
        assert error == ""

    def test_validate_chain_directionality_antenna_incoming_invalid(self):
        """Test ANTENNA cannot receive incoming connections."""
        is_valid, error = validate_chain_directionality("ANTENNA", "incoming")
        assert is_valid is False
        assert "ANTENNA" in error
        assert "outgoing" in error

    def test_validate_chain_directionality_snap_incoming_valid(self):
        """Test SNAP can receive incoming connections."""
        is_valid, error = validate_chain_directionality("SNAP", "incoming")
        assert is_valid is True
        assert error == ""

    def test_validate_chain_directionality_snap_outgoing_invalid(self):
        """Test SNAP cannot make outgoing connections."""
        is_valid, error = validate_chain_directionality("SNAP", "outgoing")
        assert is_valid is False
        assert "SNAP" in error
        assert "incoming" in error

    def test_validate_chain_directionality_middle_part(self):
        """Test middle parts can make both connections."""
        is_valid, _ = validate_chain_directionality("LNA", "outgoing")
        assert is_valid is True

        is_valid, _ = validate_chain_directionality("LNA", "incoming")
        assert is_valid is True

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_existing_connections_none(self, mock_connect, mock_config):
        """Test checking part with no existing connections."""
        mock_config.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [[], []]  # No outgoing, no incoming
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        can_connect, error, connections = check_existing_connections("ANT00001P1")

        assert can_connect is True
        assert error == ""
        assert connections == []

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_existing_connections_outgoing_exists(
        self, mock_connect, mock_config
    ):
        """Test checking part with existing outgoing connection."""
        mock_config.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [("LNA00001P1", "LNA")],  # Outgoing connection exists
            [],
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        can_connect, error, connections = check_existing_connections("ANT00001P1")

        assert can_connect is False
        assert "already connects to" in error
        assert len(connections) == 1

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_existing_connections_incoming_exists(
        self, mock_connect, mock_config
    ):
        """Test checking part with existing incoming connection."""
        mock_config.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [],  # No outgoing
            [("ANT00001P1", "ANTENNA")],  # Incoming connection exists
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        can_connect, error, _ = check_existing_connections("LNA00001P1")

        assert can_connect is False
        assert "incoming connection" in error

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_existing_connections_database_error(
        self, mock_connect, mock_config
    ):
        """Test handling database errors."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = sqlite3.Error("Database error")

        can_connect, error, _ = check_existing_connections("ANT00001P1")

        assert can_connect is False
        assert "Database error" in error

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_target_connections_available(self, mock_connect, mock_config):
        """Test checking target part that can accept connection."""
        mock_config.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []  # No incoming connections
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        can_accept, error = check_target_connections("LNA00001P1")

        assert can_accept is True
        assert error == ""

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_target_connections_already_connected(
        self, mock_connect, mock_config
    ):
        """Test checking target part that already has incoming connection."""
        mock_config.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("ANT00001P1",)
        ]  # Already has incoming
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        can_accept, error = check_target_connections("LNA00001P1")

        assert can_accept is False
        assert "already has an incoming connection" in error

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_target_connections_database_error(self, mock_connect, mock_config):
        """Test handling database errors."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = sqlite3.Error("Database error")

        can_accept, error = check_target_connections("LNA00001P1")

        assert can_accept is False
        assert "Database error" in error

    @patch("casman.assembly.interactive.validate_snap_part")
    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_validate_part_in_database_regular_part(
        self, mock_connect, mock_config, _mock_snap
    ):
        """Test validating regular part in database."""
        mock_config.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("ANTENNA", "P1")
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        is_valid, part_type, polarization = validate_part_in_database("ANT00001P1")

        assert is_valid is True
        assert part_type == "ANTENNA"
        assert polarization == "P1"

    @patch("casman.assembly.interactive.validate_snap_part")
    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_validate_part_in_database_snap_part(
        self, _mock_connect, _mock_config, mock_snap
    ):
        """Test validating SNAP part."""
        mock_snap.return_value = (True, "SNAP", "ADC0")

        is_valid, part_type, _ = validate_part_in_database(
            "SNAP1A00_ADC0"
        )

        assert is_valid is True
        assert part_type == "SNAP"
        mock_snap.assert_called_once_with("SNAP1A00_ADC0")

    @patch("casman.assembly.interactive.validate_snap_part")
    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_validate_part_in_database_not_found(
        self, mock_connect, mock_config, mock_snap
    ):
        """Test validating non-existent part."""
        mock_snap.return_value = (False, None, None)
        mock_config.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        is_valid, part_type, _ = validate_part_in_database("INVALID-00001")

        assert is_valid is False
        assert part_type == ""

    def test_validate_snap_part_valid(self):
        """Test validating valid SNAP part."""
        # Valid format: SNAP<crate 1-4><slot A-K><port 00-11>
        is_valid, part_type, polarization = validate_snap_part("SNAP1A00")

        assert is_valid is True
        assert part_type == "SNAP"
        assert polarization == "N/A"

    def test_validate_snap_part_invalid_format(self):
        """Test SNAP part with invalid format."""
        is_valid, _, _ = validate_snap_part("INVALID")

        assert is_valid is False

    def test_validate_snap_part_not_in_valid_format(self):
        """Test SNAP part not in valid format."""
        # Invalid crate number (5 > 4)
        is_valid, _, _ = validate_snap_part("SNAP5A00")

        assert is_valid is False

    def test_validate_snap_part_with_adc_suffix(self):
        """Test SNAP part with _ADC suffix."""
        # This should fail pattern match since _ADC is not in the pattern
        is_valid, _, _ = validate_snap_part("SNAP1A00_ADC0")

        assert is_valid is False

    def test_validate_snap_part_edge_cases(self):
        """Test SNAP part edge cases."""
        # Valid edge cases
        assert validate_snap_part("SNAP4K11")[0] is True  # Max values
        assert validate_snap_part("SNAP1A00")[0] is True  # Min values

        # Invalid edge cases
        assert validate_snap_part("SNAP0A00")[0] is False  # Crate 0
        assert validate_snap_part("SNAP1L00")[0] is False  # Slot L
        assert validate_snap_part("SNAP1A12")[0] is False  # Port 12

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_validate_part_in_database_with_snap_adc_suffix(
        self, mock_connect, mock_config
    ):
        """Test validating SNAP part with _ADC suffix."""
        mock_config.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # SNAP parts with _ADC suffix should use validate_snap_part
        is_valid, _, _ = validate_part_in_database(
            "SNAP1A00_ADC0"
        )

        # This should fail because the suffix doesn't match the pattern
        assert is_valid is False

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_validate_part_in_database_error_handling(
        self, mock_connect, mock_config
    ):
        """Test error handling in validate_part_in_database."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = sqlite3.Error("Connection failed")

        is_valid, part_type, polarization = validate_part_in_database("ANT00001P1")

        assert is_valid is False
        assert part_type == ""
        assert polarization == ""

    def test_validate_snap_part_exception_handling(self):
        """Test exception handling in validate_snap_part."""
        # Valid input shouldn't raise exceptions
        is_valid, _, _ = validate_snap_part("SNAP1A00")
        assert is_valid is True

        # Invalid input should be handled gracefully
        is_valid, _, _ = validate_snap_part("INVALID")
        assert is_valid is False

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_existing_connections_os_error(self, mock_connect, mock_config):
        """Test handling of OSError in check_existing_connections."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = OSError("File not found")

        can_connect, error, _ = check_existing_connections("ANT00001P1")

        assert can_connect is False
        assert "Database error" in error

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_target_connections_os_error(self, mock_connect, mock_config):
        """Test handling of OSError in check_target_connections."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = OSError("File not found")

        can_accept, error = check_target_connections("LNA00001P1")

        assert can_accept is False
        assert "Database error" in error

    def test_validate_snap_part_various_valid_formats(self):
        """Test various valid SNAP part formats."""
        # Test different valid combinations
        valid_parts = [
            "SNAP1A00",  # Min values
            "SNAP4K11",  # Max values
            "SNAP2E05",  # Middle values
            "SNAP3B10",  # Another valid combo
        ]
        
        for part in valid_parts:
            is_valid, part_type, _ = validate_snap_part(part)
            assert is_valid is True, f"Expected {part} to be valid"
            assert part_type == "SNAP"

    def test_validate_snap_part_various_invalid_formats(self):
        """Test various invalid SNAP part formats."""
        invalid_parts = [
            "SNAP0A00",  # Crate 0 (too low)
            "SNAP5A00",  # Crate 5 (too high)
            "SNAP1Z00",  # Slot Z (too high)
            "SNAP1A12",  # Port 12 (too high)
            "SNAP1A99",  # Port 99 (way too high)
            "SNAP_1A00",  # Underscore
            "snap1a00",  # Lowercase
        ]
        
        for part in invalid_parts:
            is_valid, _, _ = validate_snap_part(part)
            assert is_valid is False, f"Expected {part} to be invalid"


class TestAssemblyMain:
    """Test main entry point function."""

    @patch("sys.argv", ["casman-scan", "--help"])
    @patch("builtins.print")
    def test_main_help_flag(self, mock_print):
        """Test main function with help flag."""
        main()

        # Verify help text was printed
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Interactive Assembly Scanner" in str(call) for call in calls)

    @patch("sys.argv", ["casman-scan", "-h"])
    @patch("builtins.print")
    def test_main_help_short_flag(self, mock_print):
        """Test main function with short help flag."""
        main()

        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Interactive Assembly Scanner" in str(call) for call in calls)

    @patch("sys.argv", ["casman-scan"])
    @patch("casman.assembly.scan_and_assemble_interactive")
    def test_main_launches_scanner(self, mock_scanner):
        """Test main function launches interactive scanner."""
        main()

        mock_scanner.assert_called_once()


class TestValidNextConnections:
    """Test VALID_NEXT_CONNECTIONS mapping."""

    def test_valid_next_connections_exists(self):
        """Test that VALID_NEXT_CONNECTIONS mapping is created."""
        assert isinstance(VALID_NEXT_CONNECTIONS, dict)
        assert len(VALID_NEXT_CONNECTIONS) > 0

    def test_antenna_connects_to_lna(self):
        """Test ANTENNA connects to LNA."""
        assert "ANTENNA" in VALID_NEXT_CONNECTIONS
        assert "LNA" in VALID_NEXT_CONNECTIONS["ANTENNA"]

    def test_snap_has_no_outgoing(self):
        """Test SNAP (terminal) has no outgoing connections."""
        assert "SNAP" in VALID_NEXT_CONNECTIONS
        assert VALID_NEXT_CONNECTIONS["SNAP"] == []

    def test_each_part_has_one_next(self):
        """Test each non-terminal part connects to exactly one next part."""
        for part_type, next_parts in VALID_NEXT_CONNECTIONS.items():
            if part_type != "SNAP":  # SNAP is terminal
                assert len(next_parts) <= 1  # At most one next connection
