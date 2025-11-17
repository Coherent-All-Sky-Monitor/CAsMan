"""Simplified tests for CAsMan CLI functionality."""

from unittest.mock import patch

from casman.cli.main import main


class TestCLI:
    """Test CLI functionality."""

    @patch('sys.argv', ['casman', '--help'])
    @patch('casman.cli.main.argparse.ArgumentParser.print_help')
    def test_main_help(self, mock_help):
        """Test main help command."""
        try:
            main()
        except SystemExit:
            pass  # Expected for help command
        mock_help.assert_called_once()

    @patch('sys.argv', ['casman', '--version'])
    @patch('builtins.print')
    def test_main_version(self, mock_print):
        """Test version command."""
        try:
            main()
        except SystemExit:
            pass  # Expected for version command
        mock_print.assert_called_once()
