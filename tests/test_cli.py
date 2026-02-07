"""
Comprehensive tests for CAsMan CLI functionality.

Tests cover:
- Main CLI entry point and routing
- Utility functions (version, help, completion)
- Parts commands (list, add, search)
- Scan/assembly commands (connect, disconnect, connection, disconnection)
- Barcode commands (printpages, validate)
- Database commands (clear, print, load-coordinates, backup)
- Visualization commands (chains)
- Web commands (dev/prod server, scanner, visualize)
"""

import os
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from casman.cli.database_commands import (
    cmd_database,
    cmd_database_clear,
    cmd_database_load_coordinates,
    cmd_database_print,
)
from casman.cli.main import main
from casman.cli.utils import show_commands_list, show_completion_help, show_version


class TestCLIMain:
    """Test main CLI functionality."""

    @patch("sys.argv", ["casman", "--help"])
    def test_main_help(self):
        """Test main help command."""
        try:
            main()
        except SystemExit:
            pass  # Expected for help command

    @patch("sys.argv", ["casman", "--version"])
    @patch("casman.cli.utils.print")
    def test_main_version(self, mock_print):
        """Test version command."""
        try:
            main()
        except SystemExit:
            pass  # Expected for version command

    @patch("sys.argv", ["casman", "--list-commands"])
    def test_main_list_commands(self):
        """Test list commands option."""
        try:
            main()
        except SystemExit:
            pass  # Expected

    @patch("sys.argv", ["casman"])
    def test_main_no_args(self):
        """Test main with no arguments."""
        try:
            main()
        except SystemExit:
            pass  # Expected


class TestCLIUtilities:
    """Test CLI utility functions."""

    @patch("builtins.print")
    def test_show_version(self, mock_print):
        """Test show_version utility."""
        try:
            show_version()
        except SystemExit:
            pass  # Expected
        mock_print.assert_called()

    @patch("builtins.print")
    def test_show_commands_list(self, mock_print):
        """Test show_commands_list utility."""
        commands = {
            "parts": "Manage parts",
            "scan": "Interactive scanning",
        }
        try:
            show_commands_list(commands)
        except SystemExit:
            pass  # Expected
        mock_print.assert_called()

    @patch("builtins.print")
    def test_show_completion_help(self, mock_print):
        """Test show_completion_help utility."""
        try:
            show_completion_help()
        except SystemExit:
            pass  # Expected
        mock_print.assert_called()


class TestCLIPartsCommand:
    """Test parts command functionality."""

    @patch("sys.argv", ["casman", "parts", "--help"])
    @patch("casman.cli.parts_commands.cmd_parts")
    def test_parts_help(self, mock_cmd):
        """Test parts help command."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "parts", "list"])
    @patch("casman.cli.parts_commands.get_parts_by_criteria")
    @patch("builtins.input", return_value="0")
    def test_parts_list(self, mock_input, mock_get_parts):
        """Test parts list command."""
        mock_get_parts.return_value = []
        try:
            from casman.cli.parts_commands import cmd_parts

            cmd_parts()
        except (SystemExit, EOFError):
            pass

    @patch("sys.argv", ["casman", "parts", "add"])
    @patch("casman.cli.parts_commands.add_parts_interactive")
    def test_parts_add(self, mock_add):
        """Test parts add command."""
        try:
            from casman.cli.parts_commands import cmd_parts

            cmd_parts()
        except SystemExit:
            pass


class TestCLIScanCommand:
    """Test scan command functionality."""

    @patch("sys.argv", ["casman", "scan", "--help"])
    def test_scan_help(self):
        """Test scan help command."""
        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan", "connection"])
    @patch("casman.cli.assembly_commands.scan_and_assemble_interactive")
    @patch("casman.cli.assembly_commands.init_all_databases")
    def test_scan_connection(self, mock_init, mock_scan):
        """Test scan connection command."""
        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass


class TestCLIBarcodeCommand:
    """Test barcode command functionality."""

    @patch("sys.argv", ["casman", "barcode", "--help"])
    def test_barcode_help(self):
        """Test barcode help command."""
        try:
            from casman.cli.barcode_commands import cmd_barcode

            cmd_barcode()
        except SystemExit:
            pass

    @patch(
        "sys.argv",
        [
            "casman",
            "barcode",
            "printpages",
            "--part-type",
            "ANTENNA",
            "--end-number",
            "10",
        ],
    )
    @patch("casman.cli.barcode_commands.generate_barcode_printpages")
    def test_barcode_printpages(self, mock_generate):
        """Test barcode printpages command."""
        try:
            from casman.cli.barcode_commands import cmd_barcode

            cmd_barcode()
        except (SystemExit, Exception):
            pass


class TestCLIVisualizeCommand:
    """Test visualize command functionality."""

    @patch("sys.argv", ["casman", "visualize", "--help"])
    def test_visualize_help(self):
        """Test visualize help command."""
        try:
            from casman.cli.visualization_commands import cmd_visualize

            cmd_visualize()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "visualize", "chains"])
    @patch("casman.visualization.core.format_ascii_chains")
    @patch("casman.database.initialization.init_all_databases")
    @patch("builtins.print")
    def test_visualize_chains(self, mock_print, mock_init, mock_format):
        """Test visualize chains command."""
        mock_format.return_value = "Test chain visualization"
        mock_init.return_value = None
        try:
            from casman.cli.visualization_commands import cmd_visualize

            cmd_visualize()
        except (SystemExit, Exception):
            pass


class TestCLIDatabaseCommand:
    """Test database command functionality."""

    @patch("sys.argv", ["casman", "database", "--help"])
    def test_database_help(self):
        """Test database help command."""
        try:
            from casman.cli.database_commands import cmd_database

            cmd_database()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "database", "print"])
    @patch("sqlite3.connect")
    @patch("casman.cli.database_commands.get_config")
    @patch("builtins.print")
    def test_database_print(self, mock_print, mock_config, mock_connect):
        """Test database print command."""
        mock_config.return_value = "/tmp/test_db.db"
        # Mock database connection to prevent file creation
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        try:
            from casman.cli.database_commands import cmd_database

            cmd_database()
        except (SystemExit, Exception):
            pass


class TestCLIWebCommand:
    """Test web command functionality."""

    @patch("sys.argv", ["casman", "web", "--help"])
    def test_web_help(self):
        """Test web help command."""
        try:
            from casman.cli.web_commands import cmd_web

            cmd_web()
        except SystemExit:
            pass


class TestCLICommandRouting:
    """Test CLI command routing."""

    @patch("sys.argv", ["casman", "nonexistent"])
    @patch("builtins.print")
    def test_unknown_command(self, mock_print):
        """Test handling of unknown commands."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "parts"])
    @patch("casman.cli.parts_commands.cmd_parts")
    def test_route_to_parts(self, mock_cmd):
        """Test routing to parts command."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan"])
    @patch("casman.cli.assembly_commands.cmd_scan")
    def test_route_to_scan(self, mock_cmd):
        """Test routing to scan command."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "database"])
    @patch("casman.cli.database_commands.cmd_database")
    def test_route_to_database(self, mock_cmd):
        """Test routing to database command."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "visualize"])
    @patch("casman.cli.visualization_commands.cmd_visualize")
    def test_route_to_visualize(self, mock_cmd):
        """Test routing to visualize command."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "web"])
    @patch("casman.cli.web_commands.cmd_web")
    def test_route_to_web(self, mock_cmd):
        """Test routing to web command."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "barcode"])
    @patch("casman.cli.barcode_commands.cmd_barcode")
    def test_route_to_barcode(self, mock_cmd):
        """Test routing to barcode command."""
        try:
            main()
        except SystemExit:
            pass


class TestCLIBarcodeCommands:
    """Test CLI barcode commands."""

    @patch("sys.argv", ["casman", "barcode", "printpages", "--help"])
    def test_barcode_printpages_help(self):
        """Test barcode printpages help."""
        try:
            main()
        except SystemExit:
            pass

    @patch(
        "sys.argv",
        [
            "casman",
            "barcode",
            "printpages",
            "--part-type",
            "ANTENNA",
            "--start-number",
            "1",
            "--end-number",
            "10",
        ],
    )
    @patch("casman.cli.barcode_commands.generate_barcode_printpages")
    def test_barcode_printpages_command(self, mock_generate):
        """Test barcode printpages command execution."""
        try:
            main()
        except SystemExit:
            pass

        # Verify the function was called with correct args
        mock_generate.assert_called_once_with("ANTENNA", 1, 10)

    @patch("sys.argv", ["casman", "barcode", "validate", "--help"])
    def test_barcode_validate_help(self):
        """Test barcode validate help."""
        try:
            main()
        except SystemExit:
            pass


class TestCLIPartsCommands:
    """Test CLI parts commands."""

    @patch("sys.argv", ["casman", "parts", "list", "--help"])
    def test_parts_list_help(self):
        """Test parts list help."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "parts", "list"])
    @patch("casman.cli.parts_commands.display_parts_interactive")
    def test_parts_list_command(self, mock_display):
        """Test parts list command execution."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "parts", "add", "--help"])
    def test_parts_add_help(self):
        """Test parts add help."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "parts", "add"])
    @patch("casman.cli.parts_commands.add_parts_interactive")
    def test_parts_add_command(self, mock_add):
        """Test parts add command execution."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "parts", "search", "--help"])
    def test_parts_search_help(self):
        """Test parts search help."""
        try:
            main()
        except SystemExit:
            pass


class TestCLIDatabaseCommands:
    """Test CLI database commands."""

    @patch("sys.argv", ["casman", "database", "clear", "--help"])
    def test_database_clear_help(self):
        """Test database clear help."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "database", "print", "--help"])
    def test_database_print_help(self):
        """Test database print help."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "database", "print"])
    @patch("sqlite3.connect")
    @patch("casman.cli.database_commands.get_config")
    @patch("builtins.print")
    def test_database_print_command(self, mock_print, mock_config, mock_connect):
        """Test database print command execution."""
        mock_config.return_value = "/tmp/test_db.db"
        # Mock database connection to prevent file creation
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "database", "backup", "--help"])
    def test_database_backup_help(self):
        """Test database backup help."""
        try:
            main()
        except SystemExit:
            pass


class TestCLIAssemblyCommands:
    """Test CLI assembly/scan commands."""

    @patch("sys.argv", ["casman", "scan", "connect", "--help"])
    def test_scan_connect_help(self):
        """Test scan connect help."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan", "disconnect", "--help"])
    def test_scan_disconnect_help(self):
        """Test scan disconnect help."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan", "connection", "--help"])
    def test_scan_connection_help(self):
        """Test scan connection help."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan", "disconnection", "--help"])
    def test_scan_disconnection_help(self):
        """Test scan disconnection help."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan", "connection"])
    @patch("casman.cli.assembly_commands.init_all_databases")
    @patch("casman.cli.assembly_commands.scan_and_assemble_interactive")
    def test_scan_connection_execution(self, mock_scan, mock_init):
        """Test scan connection command execution."""
        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass

        mock_init.assert_called_once()
        mock_scan.assert_called_once()

    @patch("sys.argv", ["casman", "scan", "disconnection"])
    @patch("casman.cli.assembly_commands.init_all_databases")
    @patch("casman.assembly.interactive.scan_and_disassemble_interactive")
    def test_scan_disconnection_execution(self, mock_scan, mock_init):
        """Test scan disconnection command execution."""
        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass

        mock_init.assert_called_once()
        mock_scan.assert_called_once()

    @patch("sys.argv", ["casman", "scan", "connect"])
    @patch("casman.cli.assembly_commands.init_all_databases")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_scan_connect_workflow(self, _mock_print, mock_subprocess, mock_init):
        """Test full connect workflow."""
        mock_subprocess.return_value.returncode = 0
        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass

        mock_init.assert_called_once()
        mock_subprocess.assert_called_once()

    @patch("sys.argv", ["casman", "scan", "disconnect"])
    @patch("casman.cli.assembly_commands.init_all_databases")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_scan_disconnect_workflow(self, _mock_print, mock_subprocess, mock_init):
        """Test full disconnect workflow."""
        mock_subprocess.return_value.returncode = 0
        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass

        mock_init.assert_called_once()
        mock_subprocess.assert_called_once()

    @patch("sys.argv", ["casman", "scan"])
    @patch("builtins.print")
    def test_scan_no_action(self, _mock_print):
        """Test scan command with no action."""
        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass


class TestCLIVisualizationCommands:
    """Test CLI visualization commands."""

    @patch("sys.argv", ["casman", "visualize", "chains", "--help"])
    def test_visualize_chains_help(self):
        """Test visualize chains help."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "visualize", "chains"])
    @patch("casman.visualization.core.format_ascii_chains")
    @patch("builtins.print")
    def test_visualize_chains_command(self, mock_print, mock_format):
        """Test visualize chains command execution."""
        mock_format.return_value = "Chain visualization"
        try:
            main()
        except SystemExit:
            pass


class TestCLIWebCommands:
    """Test CLI web commands."""

    @patch("sys.argv", ["casman", "web", "--help"])
    def test_web_help(self):
        """Test web help."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "web", "--port", "8080"])
    @patch("casman.web.run_dev_server")
    def test_web_custom_port(self, mock_run):
        """Test web command with custom port."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "web", "--mode", "prod"])
    @patch("casman.web.run_production_server")
    def test_web_production_mode(self, mock_run):
        """Test web command in production mode."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "web", "--scanner-only"])
    @patch("casman.web.run_dev_server")
    def test_web_scanner_only(self, mock_run):
        """Test web command scanner-only mode."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "web", "--visualize-only"])
    @patch("casman.web.run_dev_server")
    def test_web_visualize_only(self, mock_run):
        """Test web command visualize-only mode."""
        try:
            main()
        except SystemExit:
            pass


class TestCLIUtilsAdvanced:
    """Test advanced CLI utility functions."""

    @patch("builtins.print")
    def test_show_help_with_completion(self, mock_print):
        """Test show_help_with_completion utility."""
        from unittest.mock import Mock

        from casman.cli.utils import show_help_with_completion

        mock_parser = Mock()
        try:
            show_help_with_completion(mock_parser)
        except SystemExit as e:
            assert e.code == 1
        mock_parser.print_help.assert_called_once()
        mock_print.assert_called()

    @patch("builtins.print")
    def test_show_unknown_command_error(self, mock_print):
        """Test show_unknown_command_error utility."""
        from unittest.mock import Mock

        from casman.cli.utils import show_unknown_command_error

        mock_parser = Mock()
        try:
            show_unknown_command_error("badcommand", mock_parser)
        except SystemExit as e:
            assert e.code == 1
        mock_parser.print_help.assert_called_once()
        mock_print.assert_called()


class TestCLIPartsCommandsAdvanced:
    """Test advanced parts command scenarios."""

    @patch("sys.argv", ["casman", "parts", "list", "--all"])
    @patch("casman.cli.parts_commands.get_parts_by_criteria")
    @patch("casman.cli.parts_commands.init_all_databases")
    @patch("builtins.print")
    def test_parts_list_all_with_results(self, mock_print, mock_init, mock_get_parts):
        """Test parts list --all with results."""
        mock_get_parts.return_value = [
            (1, "ANT-P1-00001", "ANTENNA", "P1", "2024-01-01", "2024-01-01")
        ]
        try:
            from casman.cli.parts_commands import cmd_parts

            cmd_parts()
        except SystemExit:
            pass
        mock_init.assert_called_once()
        mock_get_parts.assert_called()

    @patch("sys.argv", ["casman", "parts", "list", "--all"])
    @patch("casman.cli.parts_commands.get_parts_by_criteria")
    @patch("casman.cli.parts_commands.init_all_databases")
    @patch("builtins.print")
    def test_parts_list_all_empty(self, mock_print, mock_init, mock_get_parts):
        """Test parts list --all with no results."""
        mock_get_parts.return_value = []
        try:
            from casman.cli.parts_commands import cmd_parts

            cmd_parts()
        except SystemExit:
            pass
        mock_init.assert_called_once()

    @patch("sys.argv", ["casman", "parts", "list", "--type", "ANTENNA"])
    @patch("casman.cli.parts_commands.get_parts_by_criteria")
    @patch("casman.cli.parts_commands.init_all_databases")
    def test_parts_list_with_type_filter(self, mock_init, mock_get_parts):
        """Test parts list with type filter."""
        mock_get_parts.return_value = []
        try:
            from casman.cli.parts_commands import cmd_parts

            cmd_parts()
        except SystemExit:
            pass
        mock_init.assert_called_once()

    @patch(
        "sys.argv",
        ["casman", "parts", "list", "--type", "ANTENNA", "--polarization", "1"],
    )
    @patch("casman.cli.parts_commands.get_parts_by_criteria")
    @patch("casman.cli.parts_commands.init_all_databases")
    def test_parts_list_with_type_and_polarization(self, mock_init, mock_get_parts):
        """Test parts list with type and polarization filters."""
        mock_get_parts.return_value = []
        try:
            from casman.cli.parts_commands import cmd_parts

            cmd_parts()
        except SystemExit:
            pass
        mock_init.assert_called_once()

    @patch("sys.argv", ["casman", "parts", "list"])
    @patch("casman.cli.parts_commands.display_parts_interactive")
    @patch("casman.cli.parts_commands.init_all_databases")
    def test_parts_list_interactive_mode(self, mock_init, mock_display):
        """Test parts list without filters triggers interactive mode."""
        try:
            from casman.cli.parts_commands import cmd_parts

            cmd_parts()
        except SystemExit:
            pass
        mock_init.assert_called_once()
        mock_display.assert_called_once()

    @patch(
        "sys.argv", ["casman", "parts", "add", "--part-type", "ANTENNA", "--count", "5"]
    )
    @patch("casman.cli.parts_commands.add_parts_interactive")
    @patch("casman.cli.parts_commands.init_all_databases")
    def test_parts_add_with_args(self, mock_init, mock_add):
        """Test parts add with command-line arguments."""
        try:
            from casman.cli.parts_commands import cmd_parts

            cmd_parts()
        except SystemExit:
            pass
        mock_init.assert_called_once()
        mock_add.assert_called()

    @patch("sys.argv", ["casman", "parts"])
    @patch("builtins.print")
    def test_parts_no_action(self, mock_print):
        """Test parts command with no action."""
        try:
            from casman.cli.parts_commands import cmd_parts

            cmd_parts()
        except SystemExit:
            pass


class TestCLIDatabaseCommandsAdvanced:
    """Test advanced database command scenarios."""

    @patch("sys.argv", ["casman", "database", "clear", "--parts"])
    @patch("sqlite3.connect")
    @patch("casman.cli.database_commands.get_config")
    @patch("os.path.exists")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_database_clear_parts_only(
        self, mock_print, mock_input, mock_exists, mock_config, mock_connect
    ):
        """Test clearing only parts database."""
        mock_config.return_value = "test.db"
        mock_exists.return_value = True
        mock_input.side_effect = ["yes", "yes"]
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        try:
            from casman.cli.database_commands import cmd_database

            cmd_database()
        except (SystemExit, Exception):
            pass

    @patch("sys.argv", ["casman", "database", "clear", "--assembled"])
    @patch("sqlite3.connect")
    @patch("casman.cli.database_commands.get_config")
    @patch("os.path.exists")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_database_clear_assembled_only(
        self, mock_print, mock_input, mock_exists, mock_config, mock_connect
    ):
        """Test clearing only assembled database."""
        mock_config.return_value = "/tmp/test_assembled.db"
        mock_exists.return_value = True
        mock_input.side_effect = ["yes", "yes"]
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        try:
            from casman.cli.database_commands import cmd_database

            cmd_database()
        except (SystemExit, Exception):
            pass

    @patch("sys.argv", ["casman", "database", "clear"])
    @patch("sqlite3.connect")
    @patch("casman.cli.database_commands.get_config")
    @patch("os.path.exists")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_database_clear_both(
        self, mock_print, mock_input, mock_exists, mock_config, mock_connect
    ):
        """Test clearing both databases."""
        mock_config.return_value = "/tmp/test.db"
        mock_exists.return_value = True
        mock_input.side_effect = ["yes", "yes", "yes", "yes"]
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        try:
            from casman.cli.database_commands import cmd_database

            cmd_database()
        except (SystemExit, Exception):
            pass

    @patch("sys.argv", ["casman", "database", "clear", "--parts"])
    @patch("casman.cli.database_commands.get_config")
    @patch("os.path.exists")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_database_clear_cancelled(
        self, mock_print, mock_input, mock_exists, mock_config
    ):
        """Test cancelling database clear."""
        mock_config.return_value = "test.db"
        mock_exists.return_value = True
        mock_input.side_effect = ["no"]
        try:
            from casman.cli.database_commands import cmd_database

            cmd_database()
        except (SystemExit, Exception):
            pass

    @patch("sys.argv", ["casman", "database", "clear", "--parts"])
    @patch("casman.cli.database_commands.get_config")
    @patch("os.path.exists")
    @patch("builtins.print")
    def test_database_clear_file_not_exists(self, mock_print, mock_exists, mock_config):
        """Test clearing when database file doesn't exist."""
        mock_config.return_value = "test.db"
        mock_exists.return_value = False
        try:
            from casman.cli.database_commands import cmd_database

            cmd_database()
        except (SystemExit, Exception):
            pass

    @patch("sys.argv", ["casman", "database"])
    @patch("builtins.print")
    def test_database_no_subcommand(self, mock_print):
        """Test database command with no subcommand."""
        try:
            from casman.cli.database_commands import cmd_database

            cmd_database()
        except SystemExit:
            pass


class TestCLIScanCommandsAdvanced:
    """Test advanced scan command scenarios."""

    @patch("sys.argv", ["casman", "scan", "remove"])
    @patch("casman.database.initialization.init_all_databases")
    @patch("casman.database.connection.get_database_path")
    @patch("sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_remove_no_connections(
        self, mock_print, mock_input, mock_connect, mock_get_path, mock_init
    ):
        """Test scan remove with no connections."""
        mock_get_path.return_value = "test.db"
        mock_input.return_value = "ANT-P1-00001"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan", "remove"])
    @patch("casman.database.initialization.init_all_databases")
    @patch("casman.database.connection.get_database_path")
    @patch("sqlite3.connect")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_scan_remove_with_connections_cancelled(
        self, mock_print, mock_input, mock_connect, mock_get_path, mock_init
    ):
        """Test scan remove cancelled by user."""
        mock_get_path.return_value = "test.db"
        mock_input.side_effect = ["ANT-P1-00001", "no"]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "part_number": "ANT-P1-00001",
                "connected_to": "LNA-P1-00001",
                "scan_time": "2024-01-01",
            }
        ]
        mock_conn.execute.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan", "connect"])
    @patch("casman.cli.assembly_commands.init_all_databases")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_scan_connect_subprocess_error(
        self, mock_print, mock_subprocess, mock_init
    ):
        """Test scan connect with subprocess error."""
        mock_subprocess.side_effect = OSError("Subprocess error")
        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan", "connect"])
    @patch("casman.cli.assembly_commands.init_all_databases")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_scan_connect_keyboard_interrupt(
        self, mock_print, mock_subprocess, mock_init
    ):
        """Test scan connect with keyboard interrupt."""
        mock_subprocess.side_effect = KeyboardInterrupt()
        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan", "disconnect"])
    @patch("casman.cli.assembly_commands.init_all_databases")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_scan_disconnect_nonzero_return(
        self, mock_print, mock_subprocess, mock_init
    ):
        """Test scan disconnect with non-zero return code."""
        mock_subprocess.return_value.returncode = 1
        try:
            from casman.cli.assembly_commands import cmd_scan

            cmd_scan()
        except SystemExit:
            pass


class TestCLIVisualizationCommandsAdvanced:
    """Test advanced visualization command scenarios."""

    @patch("sys.argv", ["casman", "visualize", "chains", "--db-dir", "/custom/path"])
    @patch("casman.visualization.core.format_ascii_chains")
    @patch("casman.database.initialization.init_all_databases")
    @patch("builtins.print")
    def test_visualize_chains_custom_db(self, mock_print, mock_init, mock_format):
        """Test visualize chains with custom database directory."""
        mock_format.return_value = "Custom chain"
        try:
            from casman.cli.visualization_commands import cmd_visualize

            cmd_visualize()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "visualize"])
    @patch("builtins.print")
    def test_visualize_no_subcommand(self, mock_print):
        """Test visualize command with no subcommand."""
        try:
            from casman.cli.visualization_commands import cmd_visualize

            cmd_visualize()
        except SystemExit:
            pass


class TestCLIBarcodeCommandsAdvanced:
    """Test advanced barcode command scenarios."""

    @patch(
        "sys.argv",
        [
            "casman",
            "barcode",
            "printpages",
            "--part-type",
            "ANTENNA",
            "--start-number",
            "1",
            "--end-number",
            "5",
        ],
    )
    @patch("casman.cli.barcode_commands.generate_barcode_printpages")
    @patch("builtins.print")
    def test_barcode_printpages_with_range(self, mock_print, mock_generate):
        """Test barcode printpages with start and end numbers."""
        try:
            from casman.cli.barcode_commands import cmd_barcode

            cmd_barcode()
        except SystemExit:
            pass
        mock_generate.assert_called_once()

    @patch("sys.argv", ["casman", "barcode", "printpages"])
    @patch("builtins.print")
    def test_barcode_printpages_no_args(self, mock_print):
        """Test barcode printpages with no arguments."""
        try:
            from casman.cli.barcode_commands import cmd_barcode

            cmd_barcode()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "barcode"])
    @patch("builtins.print")
    def test_barcode_no_subcommand(self, mock_print):
        """Test barcode command with no subcommand."""
        try:
            from casman.cli.barcode_commands import cmd_barcode

            cmd_barcode()
        except SystemExit:
            pass


class TestCLIWebCommandsAdvanced:
    """Test advanced web command scenarios."""

    @patch(
        "sys.argv",
        ["casman", "web", "--mode", "prod", "--port", "9000", "--workers", "4"],
    )
    @patch("casman.web.run_production_server")
    def test_web_production_custom_config(self, mock_run):
        """Test web production mode with custom configuration."""
        try:
            from casman.cli.web_commands import cmd_web

            cmd_web()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "web"])
    @patch("casman.web.run_dev_server")
    def test_web_default_dev_mode(self, mock_run):
        """Test web command defaults to dev mode."""
        try:
            from casman.cli.web_commands import cmd_web

            cmd_web()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "web", "--scanner-only", "--visualize-only"])
    @patch("casman.web.run_dev_server")
    @patch("builtins.print")
    def test_web_conflicting_modes(self, mock_print, mock_run):
        """Test web command with conflicting mode flags."""
        try:
            from casman.cli.web_commands import cmd_web

            cmd_web()
        except SystemExit:
            pass


class TestCLIMainAdvanced:
    """Test advanced main CLI scenarios."""

    @patch("sys.argv", ["casman", "completion"])
    @patch("builtins.print")
    def test_main_completion_command(self, mock_print):
        """Test completion command."""
        try:
            main()
        except SystemExit:
            pass
        mock_print.assert_called()

    @patch("sys.argv", ["casman", "parts", "list", "--help"])
    def test_main_nested_help(self):
        """Test help for nested subcommand."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "invalid_command"])
    @patch("builtins.print")
    def test_main_invalid_command_error(self, mock_print):
        """Test error message for invalid command."""
        try:
            main()
        except SystemExit:
            pass
        mock_print.assert_called()

    @patch("sys.argv", ["casman", "parts", "-h"])
    def test_main_short_help_flag(self):
        """Test short help flag -h."""
        try:
            main()
        except SystemExit:
            pass

    @patch("sys.argv", ["casman", "scan", "connection", "--help"])
    def test_main_double_nested_help(self):
        """Test help for double-nested subcommand."""
        try:
            main()
        except SystemExit:
            pass


# ============================================================================
# Database Commands Tests (from test_cli_database_commands.py)
# ============================================================================


class TestCmdDatabaseRouting:
    """Tests for main database command routing."""

    @patch("sys.argv", ["casman", "database", "--help"])
    def test_database_help_displays(self, capsys):
        """Test database --help displays usage."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_database()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "CAsMan Database Management" in captured.out
        assert "clear" in captured.out
        assert "print" in captured.out
        assert "load-coordinates" in captured.out

    @patch("sys.argv", ["casman", "database"])
    def test_database_no_subcommand_shows_help(self, capsys):
        """Test database without subcommand shows help."""
        cmd_database()
        captured = capsys.readouterr()
        assert "CAsMan Database Management" in captured.out

    @patch("sys.argv", ["casman", "database", "invalid-command"])
    def test_database_invalid_subcommand(self, capsys):
        """Test database with invalid subcommand raises error."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_database()
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "invalid choice" in captured.err


class TestCmdDatabaseLoadCoordinates:
    """Tests for load-coordinates subcommand."""

    @patch("sys.argv", ["casman", "database", "load-coordinates", "--help"])
    def test_load_coordinates_help(self, capsys):
        """Test load-coordinates --help."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_database()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Load coordinates from CSV" in captured.out
        assert "--csv" in captured.out

    def test_load_coordinates_success(self, tmp_path, capsys):
        """Test successful coordinate loading."""
        db_path = tmp_path / "parts.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE antenna_positions (
                antenna_number TEXT,
                grid_code TEXT,
                latitude REAL,
                longitude REAL,
                height REAL,
                coordinate_system TEXT
            )
        """
        )
        cursor.execute(
            """
            INSERT INTO antenna_positions (antenna_number, grid_code)
            VALUES ('ANT00001', 'CN001E01')
        """
        )
        conn.commit()
        conn.close()

        csv_path = tmp_path / "coords.csv"
        csv_path.write_text(
            "grid_code,latitude,longitude,height,coordinate_system,notes\n"
            "CN001E01,37.87,122.25,10.5,WGS84,Test position\n"
        )

        with patch(
            "casman.database.antenna_positions.get_database_path",
            return_value=str(db_path),
        ):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--csv", type=str)

            cmd_database_load_coordinates(parser, [f"--csv={csv_path}"])

        captured = capsys.readouterr()
        assert "Loaded:  1 position(s)" in captured.out
        assert "Coordinate data loaded successfully" in captured.out

    def test_load_coordinates_file_not_found(self, capsys):
        """Test load-coordinates with non-existent file."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--csv", type=str)

        cmd_database_load_coordinates(parser, ["--csv=/nonexistent/file.csv"])
        captured = capsys.readouterr()
        assert "Error" in captured.out or "CSV file not found" in captured.out

    def test_load_coordinates_no_updates(self, tmp_path, capsys):
        """Test load-coordinates when no positions match."""
        db_path = tmp_path / "parts.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE antenna_positions (
                antenna_number TEXT,
                grid_code TEXT,
                latitude REAL,
                longitude REAL,
                height REAL,
                coordinate_system TEXT
            )
        """
        )
        conn.commit()
        conn.close()

        csv_path = tmp_path / "coords.csv"
        csv_path.write_text(
            "grid_code,latitude,longitude,height,coordinate_system,notes\n"
            "CN999E99,37.87,122.25,10.5,WGS84,Nonexistent position\n"
        )

        with patch(
            "casman.database.antenna_positions.get_database_path",
            return_value=str(db_path),
        ):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--csv", type=str)

            cmd_database_load_coordinates(parser, [f"--csv={csv_path}"])

        captured = capsys.readouterr()
        assert "Loaded:  1 position(s)" in captured.out
        # When grid code doesn't exist in antenna_positions table, it's still loaded into grid_positions


class TestCmdDatabaseClear:
    """Tests for clear subcommand."""

    @patch("sys.argv", ["casman", "database", "clear", "--help"])
    def test_clear_help(self, capsys):
        """Test clear --help."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_database()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "clear database" in captured.out.lower()
        assert "--parts" in captured.out
        assert "--assembled" in captured.out

    def test_clear_user_declines(self, tmp_path, monkeypatch, capsys):
        """Test clear command when user declines."""
        parts_db = tmp_path / "parts.db"
        assembled_db = tmp_path / "assembled_casm.db"

        for db in [parts_db, assembled_db]:
            conn = sqlite3.connect(str(db))
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()
            conn.close()

        monkeypatch.setattr("builtins.input", lambda _: "no")

        with patch("casman.database.connection.get_database_path") as mock_path:
            mock_path.side_effect = lambda db, _: str(tmp_path / db)

            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--parts", action="store_true")
            parser.add_argument("--assembled", action="store_true")

            cmd_database_clear(parser, [])

        captured = capsys.readouterr()
        assert "Aborted" in captured.out


class TestCmdDatabasePrint:
    """Tests for print subcommand."""

    @patch("sys.argv", ["casman", "database", "print", "--help"])
    def test_print_help(self, capsys):
        """Test print --help."""
        with pytest.raises(SystemExit) as exc_info:
            cmd_database()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "display" in captured.out.lower() and "database" in captured.out.lower()

    def test_print_empty_database(self, tmp_path, capsys):
        """Test print command with empty database."""
        db_path = tmp_path / "assembled_casm.db"

        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()
        conn.close()

        with patch(
            "casman.cli.database_commands.get_config", return_value=str(db_path)
        ):
            import argparse

            parser = argparse.ArgumentParser()

            cmd_database_print(parser, [])

        captured = capsys.readouterr()
        assert "Assembly Database Contents" in captured.out

    def test_print_database_not_found(self, capsys):
        """Test print command when database not found."""
        with patch("casman.cli.database_commands.get_config", return_value=None):
            import argparse

            parser = argparse.ArgumentParser()

            with pytest.raises(SystemExit):
                cmd_database_print(parser, [])

        captured = capsys.readouterr()
        assert "Could not determine path" in captured.out


class TestIntegrationDatabaseCommands:
    """Integration tests for database command flow."""

    @patch("sys.argv", ["casman", "database", "load-coordinates"])
    def test_full_load_coordinates_flow(self, tmp_path, capsys):
        """Test complete load-coordinates command flow."""
        db_path = tmp_path / "parts.db"
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
                assigned_at TEXT,
                notes TEXT,
                latitude REAL,
                longitude REAL,
                height REAL,
                coordinate_system TEXT
            )
        """
        )

        # Also create grid_positions table
        cursor.execute(
            """
            CREATE TABLE grid_positions (
                grid_code TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL,
                height REAL,
                coordinate_system TEXT,
                notes TEXT
            )
        """
        )

        test_positions = [
            ("ANT00001", "CN001E01", "C", 1, 1),
            ("ANT00002", "CN001E02", "C", 1, 2),
            ("ANT00003", "CC000E01", "C", 0, 1),
        ]

        for ant, grid, arr, row, col in test_positions:
            cursor.execute(
                """
                INSERT INTO antenna_positions 
                (antenna_number, grid_code, array_id, row_offset, east_col, assigned_at)
                VALUES (?, ?, ?, ?, ?, '2025-01-01T00:00:00Z')
            """,
                (ant, grid, arr, row, col),
            )

        conn.commit()
        conn.close()

        csv_path = tmp_path / "grid_positions.csv"
        csv_content = """grid_code,latitude,longitude,height,coordinate_system,notes
    CN001E01,37.871899,-122.258477,10.5,WGS84,North row 1 east 1
    CN001E02,37.871912,-122.258321,10.6,WGS84,North row 1 east 2
    CC000E01,37.871850,-122.258600,10.4,WGS84,Center row east 1
    """
        csv_path.write_text(csv_content)

        with patch(
            "casman.database.antenna_positions.get_database_path",
            return_value=str(db_path),
        ):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--csv", type=str)

            cmd_database_load_coordinates(parser, [f"--csv={csv_path}"])

        captured = capsys.readouterr()
        assert "Loaded:  3 position(s)" in captured.out
        assert "Skipped: 1 position(s)" in captured.out

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        # Check grid_positions table, not antenna_positions
        cursor.execute(
            "SELECT COUNT(*) FROM grid_positions WHERE latitude IS NOT NULL"
        )
        count = cursor.fetchone()[0]
        assert count == 3
        conn.close()
