"""Tests for the CLI module."""

from io import StringIO
from unittest.mock import Mock, patch

import pytest

from casman.cli import (cmd_assemble, cmd_barcode, cmd_parts, cmd_scan,
                        cmd_visualize, main)


class TestCLI:
    """Test command-line interface functionality."""

    def test_main_no_args(self) -> None:
        """Test main function with no arguments shows help."""
        with patch('sys.argv', ['casman']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit):
                    main()

                output = mock_stdout.getvalue()
                assert 'usage:' in output.lower() or 'help' in output.lower()

    def test_main_help(self) -> None:
        """Test main function with help argument."""
        with patch('sys.argv', ['casman', '--help']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit):
                    main()

                output = mock_stdout.getvalue()
                assert 'usage:' in output.lower()

    def test_main_version(self) -> None:
        """Test main function with version argument."""
        with patch('sys.argv', ['casman', '--version']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit):
                    main()

                output = mock_stdout.getvalue()
                assert any(word in output.lower()
                           for word in ['version', 'casman'])

    @patch('casman.cli.main.cmd_parts')
    def test_main_parts_command(self, mock_cmd_parts: Mock) -> None:
        """Test main function with parts command."""
        with patch('sys.argv', ['casman', 'parts']):
            main()

            # Should have called parts command
            mock_cmd_parts.assert_called_once()

    @patch('casman.cli.main.cmd_scan')
    def test_main_scan_command(self, mock_cmd_scan: Mock) -> None:
        """Test main function with scan command."""
        with patch('sys.argv', ['casman', 'scan']):
            main()

            mock_cmd_scan.assert_called_once()

    @patch('casman.cli.main.cmd_visualize')
    def test_main_visualize_command(self, mock_cmd_visualize: Mock) -> None:
        """Test main function with visualize command."""
        with patch('sys.argv', ['casman', 'visualize']):
            main()

            mock_cmd_visualize.assert_called_once()

    @patch('casman.cli.main.cmd_barcode')
    def test_main_barcode_command(self, mock_cmd_barcode: Mock) -> None:
        """Test main function with barcode command."""
        with patch('sys.argv', ['casman', 'barcode']):
            main()

            mock_cmd_barcode.assert_called_once()

    @patch('casman.cli.main.cmd_assemble')
    def test_main_assemble_command(self, mock_cmd_assemble: Mock) -> None:
        """Test main function with assemble command."""
        with patch('sys.argv', ['casman', 'assemble']):
            main()

            mock_cmd_assemble.assert_called_once()

    @patch('casman.cli.parts_commands.add_parts_interactive')
    @patch('casman.cli.parts_commands.init_all_databases')
    @patch('sys.argv', ['casman', 'parts', 'add'])
    def test_cmd_parts_add(
            self,
            mock_init_db: Mock,
            mock_add_interactive: Mock) -> None:
        """Test parts command with add action."""
        cmd_parts()
        mock_init_db.assert_called_once()
        mock_add_interactive.assert_called_once()

    @patch('casman.cli.parts_commands.get_parts_by_criteria')
    @patch('casman.cli.parts_commands.init_all_databases')
    @patch('sys.argv', ['casman', 'parts', 'list', '--type', 'ANTENNA'])
    def test_cmd_parts_list(
            self,
            mock_init_db: Mock,
            mock_get_parts: Mock) -> None:
        """Test parts command with list action."""
        mock_get_parts.return_value = [
            (1, 'ANTP1-00001', 'ANTENNA', 'X', '2024-01-01', '2024-01-01'),
            (2, 'ANTP1-00002', 'ANTENNA', 'Y', '2024-01-01', '2024-01-01'),
        ]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cmd_parts()

            output = mock_stdout.getvalue()
            assert 'ANTP1-00001' in output
            mock_init_db.assert_called_once()
            mock_get_parts.assert_called_once_with('ANTENNA', None)

    @patch('casman.cli.parts_commands.add_parts_interactive')
    @patch('casman.cli.parts_commands.init_all_databases')
    @patch('sys.argv', ['casman', 'parts', 'add'])
    def test_cmd_parts_interactive(
            self,
            mock_init_db: Mock,
            mock_interactive: Mock) -> None:
        """Test parts command with interactive mode."""
        cmd_parts()
        mock_init_db.assert_called_once()
        mock_interactive.assert_called_once()

    @patch('casman.cli.assembly_commands.get_assembly_stats')
    @patch('casman.cli.assembly_commands.init_all_databases')
    @patch('sys.argv', ['casman', 'scan', 'stats'])
    def test_cmd_scan_stats(
            self,
            mock_init_db: Mock,
            mock_get_stats: Mock) -> None:
        """Test scan command with stats action."""
        mock_get_stats.return_value = {
            'total_scans': 10,
            'unique_parts': 5,
            'connected_parts': 3,
            'latest_scan': '2024-01-01 10:00:00'
        }

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cmd_scan()

            output = mock_stdout.getvalue()
            assert 'Assembly Statistics:' in output
            assert '10' in output  # total_scans
            mock_init_db.assert_called_once()
            mock_get_stats.assert_called_once()

    @patch('casman.visualization.format_ascii_chains')
    @patch('casman.database.init_all_databases')
    @patch('sys.argv', ['casman', 'visualize', 'chains'])
    def test_cmd_visualize_chains(
            self,
            mock_init_db: Mock,
            mock_format: Mock) -> None:
        """Test visualize command with chains action."""
        mock_format.return_value = "Test ASCII output"

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cmd_visualize()

            output = mock_stdout.getvalue()
            assert 'Test ASCII output' in output
            mock_init_db.assert_called_once()
            mock_format.assert_called_once()

    @patch('casman.cli.barcode_commands.generate_barcode_printpages')
    @patch(
        'sys.argv', ['casman', 'barcode', 'printpages',
                     '--part-type', 'ANTENNA', '--end-number', '5']
    )
    def test_cmd_barcode_printpages(
            self, mock_generate_printpages: Mock) -> None:
        """Test barcode command for generating printpages."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cmd_barcode()

            output = mock_stdout.getvalue()
            assert 'Generated barcode printpages' in output
            mock_generate_printpages.assert_called_once_with('ANTENNA', 1, 5)

    def test_basic_cli_module_import(self) -> None:
        """Test that CLI module can be imported and has expected functions."""
        # Check that functions exist
        assert callable(main)
        assert callable(cmd_parts)
        assert callable(cmd_scan)
        assert callable(cmd_visualize)
        assert callable(cmd_barcode)
        assert callable(cmd_assemble)
