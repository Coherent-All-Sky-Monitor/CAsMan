"""Comprehensive tests for CAsMan assembly functionality."""

import sqlite3
from unittest.mock import MagicMock, patch

from casman.assembly import main
from casman.assembly.chains import (build_connection_chains,
                                    print_assembly_chains)
from casman.assembly.connections import (record_assembly_connection,
                                         record_assembly_disconnection)
from casman.assembly.data import get_assembly_connections
from casman.assembly.interactive import (VALID_NEXT_CONNECTIONS,
                                         check_existing_connections,
                                         check_target_connections,
                                         scan_and_assemble_interactive,
                                         scan_and_disassemble_interactive,
                                         validate_chain_directionality,
                                         validate_connection_rules,
                                         validate_part_in_database,
                                         validate_snap_part)


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
    def test_get_assembly_connections_database_error(self, mock_connect, mock_get_path):
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
    def test_check_existing_connections_database_error(self, mock_connect, mock_config):
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
        mock_cursor.fetchall.return_value = [("ANT00001P1",)]  # Already has incoming
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

        is_valid, part_type, _ = validate_part_in_database("SNAP1A00_ADC0")

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
        # Valid format: SNAP<chassis 1-4><slot A-K><port 00-11>
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
        # Invalid chassis number (5 > 4)
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
        is_valid, _, _ = validate_part_in_database("SNAP1A00_ADC0")

        # This should fail because the suffix doesn't match the pattern
        assert is_valid is False

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_validate_part_in_database_error_handling(self, mock_connect, mock_config):
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
    """Test legacy main entry point function."""

    @patch("sys.argv", ["casman", "--help"])
    @patch("builtins.print")
    def test_main_help_flag(self, mock_print):
        """Test main function with help flag."""
        main()

        # Verify help text was printed
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Assembly Scanner" in str(call) for call in calls)

    @patch("sys.argv", ["casman", "-h"])
    @patch("builtins.print")
    def test_main_help_short_flag(self, mock_print):
        """Test main function with short help flag."""
        main()

        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Assembly Scanner" in str(call) for call in calls)

    @patch("sys.argv", ["casman"])
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


class TestInteractiveAssemblyScanning:
    """Test interactive assembly scanning workflows."""

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("casman.assembly.interactive.check_target_connections")
    @patch("casman.assembly.connections.record_assembly_connection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_assemble_quit_immediately(
        self,
        _mock_print,
        mock_input,
        _mock_record,
        _mock_check_target,
        _mock_check_existing,
        _mock_validate,
    ):
        """Test quitting scanner immediately."""
        mock_input.side_effect = ["quit"]

        scan_and_assemble_interactive()

        # Should only ask for first part and then quit
        assert mock_input.call_count == 1

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_assemble_empty_input(
        self, _mock_print, mock_input, _mock_validate
    ):
        """Test handling empty input."""
        mock_input.side_effect = ["", "quit"]

        scan_and_assemble_interactive()

        # Should ask again after empty input
        assert mock_input.call_count == 2

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_assemble_invalid_part(
        self, mock_print, mock_input, mock_validate
    ):
        """Test handling invalid part number."""
        mock_validate.return_value = (False, "", "")
        mock_input.side_effect = ["INVALID-001", "quit"]

        scan_and_assemble_interactive()

        # Should print error message
        assert any("not found" in str(call) for call in mock_print.call_args_list)

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("casman.assembly.interactive.validate_connection_rules")
    @patch("casman.assembly.interactive.validate_chain_directionality")
    @patch("casman.assembly.interactive.check_target_connections")
    @patch("casman.assembly.connections.record_assembly_connection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_assemble_successful_connection(
        self,
        _mock_print,
        mock_input,
        mock_record,
        mock_check_target,
        mock_check_dir,
        mock_check_rules,
        mock_check_existing,
        mock_validate,
    ):
        """Test successful connection recording."""
        # Setup mocks for successful connection
        mock_validate.side_effect = [
            (True, "ANTENNA", "P1"),  # First part
            (True, "LNA", "P1"),  # Second part
        ]
        mock_check_existing.return_value = (True, "", [])
        mock_check_rules.return_value = (True, "")
        mock_check_dir.side_effect = [(True, ""), (True, "")]
        mock_check_target.return_value = (True, "")

        mock_input.side_effect = ["ANT-P1-00001", "LNA-P1-00001", "quit"]

        scan_and_assemble_interactive()

        # Should record the connection
        mock_record.assert_called_once()

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("casman.assembly.connections.record_assembly_connection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_assemble_existing_connection(
        self, _mock_print, mock_input, _mock_record, mock_check_existing, mock_validate
    ):
        """Test handling existing connection error - function continues without crashing."""
        mock_validate.return_value = (True, "ANTENNA", "P1")
        mock_check_existing.return_value = (
            False,
            "Part already connects to another part",
            [("LNA-P1-00001", "LNA")],
        )

        mock_input.side_effect = ["ANT-P1-00001", "quit"]

        # Should not crash when handling existing connection
        scan_and_assemble_interactive()

        # Test passes if no exception is raised
        assert mock_input.called

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("casman.assembly.interactive.validate_chain_directionality")
    @patch("casman.assembly.connections.record_assembly_connection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_assemble_directionality_error(
        self,
        _mock_print,
        mock_input,
        _mock_record,
        mock_check_dir,
        mock_check_existing,
        mock_validate,
    ):
        """Test handling directionality validation error - function continues without crashing."""
        mock_validate.return_value = (True, "SNAP", "N/A")
        mock_check_existing.return_value = (True, "", [])
        mock_check_dir.return_value = (False, "SNAP cannot make outgoing connections")

        mock_input.side_effect = ["SNAP1A00", "quit"]

        # Should not crash when handling directionality error
        scan_and_assemble_interactive()

        # Test passes if no exception is raised
        assert mock_input.called

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("casman.assembly.interactive.validate_chain_directionality")
    @patch("casman.assembly.interactive.validate_connection_rules")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_assemble_connection_rules_error(
        self,
        mock_print,
        mock_input,
        mock_check_rules,
        mock_check_dir,
        mock_check_existing,
        mock_validate,
    ):
        """Test handling connection rules validation error."""
        mock_validate.side_effect = [
            (True, "ANTENNA", "P1"),
            (True, "SNAP", "N/A"),
        ]
        mock_check_existing.return_value = (True, "", [])
        mock_check_dir.return_value = (True, "")
        mock_check_rules.return_value = (False, "ANTENNA can only connect to LNA")

        mock_input.side_effect = ["ANT-P1-00001", "SNAP1A00", "quit"]

        scan_and_assemble_interactive()

        # Should print connection rules error
        assert any(
            "can only connect to" in str(call) for call in mock_print.call_args_list
        )


class TestInteractiveDisassemblyScanning:
    """Test interactive disassembly scanning workflows."""

    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_disassemble_quit_immediately(self, _mock_print, mock_input):
        """Test quitting disassembly scanner immediately."""
        mock_input.side_effect = ["quit"]

        scan_and_disassemble_interactive()

        assert mock_input.call_count == 1

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_disassemble_empty_input(
        self, _mock_print, mock_input, _mock_validate
    ):
        """Test handling empty input in disassembly."""
        mock_input.side_effect = ["", "quit"]

        scan_and_disassemble_interactive()

        assert mock_input.call_count == 2

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("casman.assembly.connections.record_assembly_disconnection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_disassemble_invalid_part(
        self, _mock_print, mock_input, _mock_record, mock_connect, mock_config
    ):
        """Test handling part with no connections in disassembly."""
        mock_config.return_value = "test.db"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []  # No connections
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        mock_input.side_effect = ["INVALID-001", "quit"]

        # Should not crash when part has no connections
        scan_and_disassemble_interactive()

        # Verify database was queried
        mock_connect.assert_called()

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("casman.assembly.connections.record_assembly_disconnection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_disassemble_no_connection(
        self, _mock_print, mock_input, _mock_record, mock_connect, mock_config
    ):
        """Test disassembly when part has no connection - function handles gracefully."""
        mock_config.return_value = "test.db"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []  # No connections found
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        mock_input.side_effect = ["ANT-P1-00001", "quit"]

        # Should handle no connections gracefully without crashing
        scan_and_disassemble_interactive()

        # Verify database was queried for connections
        mock_cursor.fetchall.assert_called()

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("casman.assembly.connections.record_assembly_disconnection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_disassemble_successful(
        self,
        _mock_print,
        mock_input,
        mock_record,
        mock_connect,
        mock_config,
        mock_validate,
    ):
        """Test successful disassembly."""
        mock_validate.return_value = (True, "ANTENNA", "P1")
        mock_config.return_value = "test.db"
        mock_record.return_value = True

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # fetchall returns list of tuples for connections
        mock_cursor.fetchall.return_value = [
            ("ANT-P1-00001", "ANTENNA", "P1", "LNA-P1-00001", "LNA", "P1", "2025-01-01")
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # User enters part, selects connection 1, then quits
        mock_input.side_effect = ["ANT-P1-00001", "1", "quit"]

        scan_and_disassemble_interactive()

        # Should record the disconnection
        mock_record.assert_called_once()

    def test_each_part_has_one_next(self):
        """Test each non-terminal part connects to exactly one next part."""
        for part_type, next_parts in VALID_NEXT_CONNECTIONS.items():
            if part_type != "SNAP":  # SNAP is terminal
                assert len(next_parts) <= 1  # At most one next connection


class TestBACBOARDToSNAPWorkflow:
    """Test BACBOARD to SNAP interactive workflow."""

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("casman.assembly.interactive.validate_connection_rules")
    @patch("casman.assembly.interactive.validate_chain_directionality")
    @patch("casman.assembly.interactive.check_target_connections")
    @patch("casman.assembly.connections.record_assembly_connection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_bacboard_to_snap_successful_connection(
        self,
        _mock_print,
        mock_input,
        mock_record,
        mock_check_target,
        mock_check_dir,
        mock_check_rules,
        mock_check_existing,
        mock_validate,
    ):
        """Test successful BACBOARD to SNAP connection with chassis/slot/port input."""
        # First validation returns BACBOARD
        mock_validate.return_value = (True, "BACBOARD", "P1")
        mock_check_existing.return_value = (True, "", [])
        mock_check_rules.return_value = (True, "")
        mock_check_dir.side_effect = [(True, ""), (True, "")]
        mock_check_target.return_value = (True, "")
        mock_record.return_value = True

        # User enters: BACBOARD part, chassis 2, slot B, port 5, then quits
        mock_input.side_effect = ["BAC-P1-00001", "2", "B", "5", "quit"]

        scan_and_assemble_interactive()

        # Should record connection to SNAP2B05
        mock_record.assert_called_once()
        call_kwargs = mock_record.call_args[1]
        assert call_kwargs["part_number"] == "BAC-P1-00001"
        assert call_kwargs["connected_to"] == "SNAP2B05"
        assert call_kwargs["connected_to_type"] == "SNAP"

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_bacboard_to_snap_invalid_chassis(
        self, _mock_print, mock_input, mock_check_existing, mock_validate
    ):
        """Test BACBOARD to SNAP with invalid chassis number."""
        mock_validate.return_value = (True, "BACBOARD", "P1")
        mock_check_existing.return_value = (True, "", [])

        # User enters invalid chassis (5), then valid (2), then quits during slot input
        mock_input.side_effect = ["BAC-P1-00001", "5", "2", "quit"]

        scan_and_assemble_interactive()

        # Should have asked for chassis multiple times
        assert mock_input.call_count == 4

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_bacboard_to_snap_invalid_slot(
        self, _mock_print, mock_input, mock_check_existing, mock_validate
    ):
        """Test BACBOARD to SNAP with invalid slot letter."""
        mock_validate.return_value = (True, "BACBOARD", "P1")
        mock_check_existing.return_value = (True, "", [])

        # User enters chassis 2, invalid slot (Z), then valid (B), then quits during port
        mock_input.side_effect = ["BAC-P1-00001", "2", "Z", "B", "quit"]

        scan_and_assemble_interactive()

        # Should have asked for slot multiple times
        assert mock_input.call_count == 5

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_bacboard_to_snap_invalid_port(
        self, _mock_print, mock_input, mock_check_existing, mock_validate
    ):
        """Test BACBOARD to SNAP with invalid port number."""
        mock_validate.return_value = (True, "BACBOARD", "P1")
        mock_check_existing.return_value = (True, "", [])

        # User enters chassis 2, slot B, invalid port (12), then valid (5), then quits
        mock_input.side_effect = ["BAC-P1-00001", "2", "B", "12", "5", "quit"]

        scan_and_assemble_interactive()

        # Should have asked for port multiple times
        assert mock_input.call_count == 6

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_bacboard_to_snap_quit_during_chassis(
        self, _mock_print, mock_input, mock_check_existing, mock_validate
    ):
        """Test quitting during chassis input for BACBOARD."""
        mock_validate.return_value = (True, "BACBOARD", "P1")
        mock_check_existing.return_value = (True, "", [])

        # User enters BACBOARD, then quits during chassis input
        mock_input.side_effect = ["BAC-P1-00001", "quit"]

        scan_and_assemble_interactive()

        assert mock_input.call_count == 2

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_bacboard_to_snap_quit_during_slot(
        self, _mock_print, mock_input, mock_check_existing, mock_validate
    ):
        """Test quitting during slot input for BACBOARD."""
        mock_validate.return_value = (True, "BACBOARD", "P1")
        mock_check_existing.return_value = (True, "", [])

        # User enters BACBOARD, chassis 2, then quits during slot input
        mock_input.side_effect = ["BAC-P1-00001", "2", "quit"]

        scan_and_assemble_interactive()

        assert mock_input.call_count == 3

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_bacboard_to_snap_quit_during_port(
        self, _mock_print, mock_input, mock_check_existing, mock_validate
    ):
        """Test quitting during port input for BACBOARD."""
        mock_validate.return_value = (True, "BACBOARD", "P1")
        mock_check_existing.return_value = (True, "", [])

        # User enters BACBOARD, chassis 2, slot B, then quits during port input
        mock_input.side_effect = ["BAC-P1-00001", "2", "B", "quit"]

        scan_and_assemble_interactive()

        assert mock_input.call_count == 4

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_bacboard_to_snap_non_numeric_chassis(
        self, _mock_print, mock_input, mock_check_existing, mock_validate
    ):
        """Test BACBOARD to SNAP with non-numeric chassis input."""
        mock_validate.return_value = (True, "BACBOARD", "P1")
        mock_check_existing.return_value = (True, "", [])

        # User enters invalid non-numeric chassis, then quits
        mock_input.side_effect = ["BAC-P1-00001", "abc", "quit"]

        scan_and_assemble_interactive()

        # Should handle ValueError and ask again
        assert mock_input.call_count == 3

    @patch("casman.assembly.interactive.validate_part_in_database")
    @patch("casman.assembly.interactive.check_existing_connections")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_bacboard_to_snap_non_numeric_port(
        self, _mock_print, mock_input, mock_check_existing, mock_validate
    ):
        """Test BACBOARD to SNAP with non-numeric port input."""
        mock_validate.return_value = (True, "BACBOARD", "P1")
        mock_check_existing.return_value = (True, "", [])

        # User enters chassis, slot, invalid non-numeric port, then quits
        mock_input.side_effect = ["BAC-P1-00001", "2", "B", "xyz", "quit"]

        scan_and_assemble_interactive()

        # Should handle ValueError and ask again
        assert mock_input.call_count == 5


class TestDisassemblyWorkflows:
    """Test scan_and_disassemble_interactive workflows."""

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("casman.assembly.connections.record_assembly_disconnection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_disassemble_multiple_connections_select_first(
        self, _mock_print, mock_input, mock_record, mock_connect, mock_config
    ):
        """Test disassembly with multiple connections, selecting first."""
        mock_config.return_value = "test.db"
        mock_record.return_value = True

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Return multiple connections
        mock_cursor.fetchall.return_value = [
            (
                "ANT-P1-00001",
                "ANTENNA",
                "P1",
                "LNA-P1-00001",
                "LNA",
                "P1",
                "2025-01-01 10:00:00",
            ),
            (
                "ANT-P1-00001",
                "ANTENNA",
                "P1",
                "LNA-P1-00002",
                "LNA",
                "P1",
                "2025-01-01 11:00:00",
            ),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # User enters part, selects connection 1, then quits
        mock_input.side_effect = ["ANT-P1-00001", "1", "quit"]

        scan_and_disassemble_interactive()

        # Should record disconnection of first connection
        mock_record.assert_called_once()
        assert mock_record.call_args[1]["connected_to"] == "LNA-P1-00001"

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("casman.assembly.connections.record_assembly_disconnection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_disassemble_multiple_connections_select_second(
        self, _mock_print, mock_input, mock_record, mock_connect, mock_config
    ):
        """Test disassembly with multiple connections, selecting second."""
        mock_config.return_value = "test.db"
        mock_record.return_value = True

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (
                "ANT-P1-00001",
                "ANTENNA",
                "P1",
                "LNA-P1-00001",
                "LNA",
                "P1",
                "2025-01-01 10:00:00",
            ),
            (
                "ANT-P1-00001",
                "ANTENNA",
                "P1",
                "LNA-P1-00002",
                "LNA",
                "P1",
                "2025-01-01 11:00:00",
            ),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # User enters part, selects connection 2, then quits
        mock_input.side_effect = ["ANT-P1-00001", "2", "quit"]

        scan_and_disassemble_interactive()

        # Should record disconnection of second connection
        mock_record.assert_called_once()
        assert mock_record.call_args[1]["connected_to"] == "LNA-P1-00002"

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_disassemble_invalid_selection_number(
        self, _mock_print, mock_input, mock_connect, mock_config
    ):
        """Test disassembly with invalid selection number."""
        mock_config.return_value = "test.db"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (
                "ANT-P1-00001",
                "ANTENNA",
                "P1",
                "LNA-P1-00001",
                "LNA",
                "P1",
                "2025-01-01 10:00:00",
            ),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # User enters part, invalid selection (0), then quits
        mock_input.side_effect = ["ANT-P1-00001", "0", "quit"]

        scan_and_disassemble_interactive()

        # Should ask for selection again
        assert mock_input.call_count == 3

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_disassemble_selection_out_of_range(
        self, _mock_print, mock_input, mock_connect, mock_config
    ):
        """Test disassembly with selection out of range."""
        mock_config.return_value = "test.db"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (
                "ANT-P1-00001",
                "ANTENNA",
                "P1",
                "LNA-P1-00001",
                "LNA",
                "P1",
                "2025-01-01 10:00:00",
            ),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # User enters part, selection 5 (out of range), then quits
        mock_input.side_effect = ["ANT-P1-00001", "5", "quit"]

        scan_and_disassemble_interactive()

        # Should handle out of range error
        assert mock_input.call_count == 3

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_disassemble_non_numeric_selection(
        self, _mock_print, mock_input, mock_connect, mock_config
    ):
        """Test disassembly with non-numeric selection."""
        mock_config.return_value = "test.db"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (
                "ANT-P1-00001",
                "ANTENNA",
                "P1",
                "LNA-P1-00001",
                "LNA",
                "P1",
                "2025-01-01 10:00:00",
            ),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # User enters part, non-numeric selection, then quits
        mock_input.side_effect = ["ANT-P1-00001", "abc", "quit"]

        scan_and_disassemble_interactive()

        # Should handle ValueError
        assert mock_input.call_count == 3

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_disassemble_quit_during_selection(
        self, _mock_print, mock_input, mock_connect, mock_config
    ):
        """Test quitting during connection selection."""
        mock_config.return_value = "test.db"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (
                "ANT-P1-00001",
                "ANTENNA",
                "P1",
                "LNA-P1-00001",
                "LNA",
                "P1",
                "2025-01-01 10:00:00",
            ),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # User enters part, then quits during selection
        mock_input.side_effect = ["ANT-P1-00001", "quit"]

        scan_and_disassemble_interactive()

        assert mock_input.call_count == 2

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("casman.assembly.connections.record_assembly_disconnection")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_disassemble_record_fails(
        self, _mock_print, mock_input, mock_record, mock_connect, mock_config
    ):
        """Test disassembly when record_assembly_disconnection fails."""
        mock_config.return_value = "test.db"
        mock_record.return_value = False  # Simulate failure

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (
                "ANT-P1-00001",
                "ANTENNA",
                "P1",
                "LNA-P1-00001",
                "LNA",
                "P1",
                "2025-01-01 10:00:00",
            ),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # User enters part, selects connection 1, then quits
        mock_input.side_effect = ["ANT-P1-00001", "1", "quit"]

        scan_and_disassemble_interactive()

        # Should attempt to record but fail gracefully
        mock_record.assert_called_once()

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_disassemble_database_error(
        self, _mock_print, mock_input, mock_connect, mock_config
    ):
        """Test disassembly with database error."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = sqlite3.Error("Database error")

        # User enters part, then quits
        mock_input.side_effect = ["ANT-P1-00001", "quit"]

        # Should handle database error gracefully
        scan_and_disassemble_interactive()

        assert mock_input.call_count == 2

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_disassemble_connection_as_target(
        self, _mock_print, mock_input, mock_connect, mock_config
    ):
        """Test disassembly where queried part is the target (connected_to) in connection."""
        mock_config.return_value = "test.db"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Part is connected_to, not part_number
        mock_cursor.fetchall.return_value = [
            (
                "ANT-P1-00001",
                "ANTENNA",
                "P1",
                "LNA-P1-00001",
                "LNA",
                "P1",
                "2025-01-01 10:00:00",
            ),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Query for the LNA part (which is connected_to in the record)
        mock_input.side_effect = ["LNA-P1-00001", "quit"]

        scan_and_disassemble_interactive()

        # Should find the connection even though part is target
        assert mock_cursor.fetchall.called


class TestKeyboardInterruptHandling:
    """Test keyboard interrupt handling in interactive functions."""

    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_assemble_keyboard_interrupt(self, _mock_print, mock_input):
        """Test keyboard interrupt in scan_and_assemble_interactive."""
        mock_input.side_effect = KeyboardInterrupt()

        # Should handle KeyboardInterrupt gracefully
        scan_and_assemble_interactive()

        # Test passes if no exception propagates
        assert mock_input.called

    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_disassemble_keyboard_interrupt(self, _mock_print, mock_input):
        """Test keyboard interrupt in scan_and_disassemble_interactive."""
        mock_input.side_effect = KeyboardInterrupt()

        # Should handle KeyboardInterrupt gracefully
        scan_and_disassemble_interactive()

        # Test passes if no exception propagates
        assert mock_input.called

    @patch("builtins.input")
    @patch("builtins.print")
    def test_interactive_main_keyboard_interrupt(self, _mock_print, mock_input):
        """Test keyboard interrupt in main() function."""
        from casman.assembly.interactive import main

        mock_input.side_effect = KeyboardInterrupt()

        # Should handle KeyboardInterrupt gracefully
        main()

        # Test passes if no exception propagates
        assert mock_input.called


class TestErrorHandlingPaths:
    """Test error handling paths in validation functions."""

    @patch("casman.assembly.interactive.validate_snap_part")
    @patch("casman.assembly.interactive.get_config")
    def test_validate_part_in_database_config_none(self, mock_config, _mock_snap):
        """Test validate_part_in_database when config returns None."""
        _mock_snap.return_value = (False, "", "")
        mock_config.return_value = None

        is_valid, part_type, polarization = validate_part_in_database("ANT-P1-00001")

        assert is_valid is False
        assert part_type == ""
        assert polarization == ""

    @patch("casman.assembly.interactive.get_config")
    def test_check_existing_connections_config_none(self, mock_config):
        """Test check_existing_connections when config returns None."""
        mock_config.return_value = None

        can_connect, error, _ = check_existing_connections("ANT-P1-00001")

        assert can_connect is False
        assert "Database error" in error

    @patch("casman.assembly.interactive.get_config")
    def test_check_target_connections_config_none(self, mock_config):
        """Test check_target_connections when config returns None."""
        mock_config.return_value = None

        can_accept, error = check_target_connections("LNA-P1-00001")

        assert can_accept is False
        assert "Database error" in error

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_validate_part_in_database_io_error(self, mock_connect, mock_config):
        """Test validate_part_in_database with IOError."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = IOError("I/O error")

        is_valid, part_type, polarization = validate_part_in_database("ANT-P1-00001")

        assert is_valid is False
        assert part_type == ""
        assert polarization == ""

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_existing_connections_io_error(self, mock_connect, mock_config):
        """Test check_existing_connections with IOError."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = IOError("I/O error")

        can_connect, error, _ = check_existing_connections("ANT-P1-00001")

        assert can_connect is False
        assert "Database error" in error

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    def test_check_target_connections_io_error(self, mock_connect, mock_config):
        """Test check_target_connections with IOError."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = IOError("I/O error")

        can_accept, error = check_target_connections("LNA-P1-00001")

        assert can_accept is False
        assert "Database error" in error

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_disassemble_value_error_in_connection_check(
        self, _mock_print, mock_input, mock_connect, mock_config
    ):
        """Test disassembly when ValueError occurs during connection check."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = ValueError("Invalid value")

        mock_input.side_effect = ["ANT-P1-00001", "quit"]

        # Should handle ValueError gracefully
        scan_and_disassemble_interactive()

        assert mock_input.call_count == 2

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_assemble_os_error(
        self, _mock_print, mock_input, mock_connect, mock_config
    ):
        """Test scan_and_assemble_interactive with OSError."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = OSError("File not found")

        mock_input.side_effect = ["ANT-P1-00001", "quit"]

        # Should handle OSError gracefully
        scan_and_assemble_interactive()

        # Test passes if function handles error without crashing
        assert mock_input.called

    @patch("casman.assembly.interactive.get_config")
    @patch("casman.assembly.interactive.sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_and_disassemble_os_error(
        self, _mock_print, mock_input, mock_connect, mock_config
    ):
        """Test scan_and_disassemble_interactive with OSError."""
        mock_config.return_value = "test.db"
        mock_connect.side_effect = OSError("File not found")

        mock_input.side_effect = ["ANT-P1-00001", "quit"]

        # Should handle OSError gracefully
        scan_and_disassemble_interactive()

        assert mock_input.called


class TestInteractiveMainFunction:
    """Test the main() function in interactive.py."""

    @patch("builtins.input")
    @patch("builtins.print")
    def test_main_option_2_quit(self, _mock_print, mock_input):
        """Test main function with option 2 (quit)."""
        from casman.assembly.interactive import main as interactive_main

        mock_input.side_effect = ["2"]

        interactive_main()

        assert mock_input.call_count == 1

    @patch("builtins.input")
    @patch("builtins.print")
    def test_main_option_quit_string(self, _mock_print, mock_input):
        """Test main function with 'quit' string."""
        from casman.assembly.interactive import main as interactive_main

        mock_input.side_effect = ["quit"]

        interactive_main()

        assert mock_input.call_count == 1

    @patch("casman.assembly.interactive.scan_and_assemble_interactive")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_main_option_1_scan(self, _mock_print, mock_input, mock_scan):
        """Test main function with option 1 (scan)."""
        from casman.assembly.interactive import main as interactive_main

        # User selects option 1, then quits
        mock_input.side_effect = ["1", "2"]

        interactive_main()

        mock_scan.assert_called_once()

    @patch("builtins.input")
    @patch("builtins.print")
    def test_main_invalid_option(self, mock_print, mock_input):
        """Test main function with invalid option."""
        from casman.assembly.interactive import main as interactive_main

        # User enters invalid option, then quits
        mock_input.side_effect = ["99", "2"]

        interactive_main()

        # Should print error message for invalid option
        assert any("Invalid option" in str(call) for call in mock_print.call_args_list)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_main_exception_handling(self, mock_print, mock_input):
        """Test main function exception handling."""
        from casman.assembly.interactive import main as interactive_main

        # Simulate exception by raising during input call
        def raise_then_quit(*_args):
            if mock_input.call_count == 1:
                raise RuntimeError("Test error")
            return "2"

        mock_input.side_effect = raise_then_quit

        interactive_main()

        # Should print error message
        assert any("Error" in str(call) for call in mock_print.call_args_list)
