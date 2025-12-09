"""
Tests for CLI sync commands.

These tests cover the database backup and synchronization commands
without connecting to actual cloud storage services.
"""

import sys
import tempfile
from datetime import datetime, UTC
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest


class TestSyncCommandParser:
    """Test sync command argument parsing."""
    
    def test_sync_command_help(self):
        """Test sync command shows help."""
        with patch("sys.argv", ["casman", "sync", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
            assert exc_info.value.code == 0
    
    def test_backup_subcommand_help(self):
        """Test backup subcommand shows help."""
        with patch("sys.argv", ["casman", "sync", "backup", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
            assert exc_info.value.code == 0
    
    def test_restore_subcommand_help(self):
        """Test restore subcommand shows help."""
        with patch("sys.argv", ["casman", "sync", "restore", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
            assert exc_info.value.code == 0
    
    def test_list_subcommand_help(self):
        """Test list subcommand shows help."""
        with patch("sys.argv", ["casman", "sync", "list", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
            assert exc_info.value.code == 0
    
    def test_status_subcommand_help(self):
        """Test status subcommand shows help."""
        with patch("sys.argv", ["casman", "sync", "status", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
            assert exc_info.value.code == 0


class TestBackupCommand:
    """Test backup command functionality."""
    
    def test_backup_both_databases(self):
        """Test backing up both databases."""
        with patch("sys.argv", ["casman", "sync", "backup"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                # Should successfully backup databases
                cmd_sync()
    
    def test_backup_parts_only(self):
        """Test backing up only parts.db."""
        with patch("sys.argv", ["casman", "sync", "backup", "--parts"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
    
    def test_backup_assembled_only(self):
        """Test backing up only assembled_casm.db."""
        with patch("sys.argv", ["casman", "sync", "backup", "--assembled"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
    
    def test_backup_disabled(self):
        """Test backup when sync is disabled."""
        with patch("sys.argv", ["casman", "sync", "backup"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = False
                
                from casman.cli.sync_commands import cmd_sync
                with pytest.raises(SystemExit):
                    cmd_sync()


class TestRestoreCommand:
    """Test restore command functionality."""
    
    def test_restore_with_backup_key(self):
        """Test restoring from a specific backup."""
        backup_key = "backups/parts.db/20241208_143022_parts.db"
        with patch("sys.argv", ["casman", "sync", "restore", backup_key]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
    
    def test_restore_with_dest(self):
        """Test restoring to a custom destination."""
        backup_key = "backups/parts.db/20241208_143022_parts.db"
        dest = "/custom/path/parts.db"
        with patch("sys.argv", ["casman", "sync", "restore", backup_key, "--dest", dest]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
    
    def test_restore_no_backup(self):
        """Test restore without safety backup."""
        backup_key = "backups/parts.db/20241208_143022_parts.db"
        with patch("sys.argv", ["casman", "sync", "restore", backup_key, "--no-backup"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()


class TestListCommand:
    """Test list command functionality."""
    
    def test_list_all_backups(self):
        """Test listing all backups."""
        with patch("sys.argv", ["casman", "sync", "list"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.list_backups.return_value = []
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
                
                mock_instance.list_backups.assert_called_once()
    
    def test_list_parts_backups(self):
        """Test listing only parts.db backups."""
        with patch("sys.argv", ["casman", "sync", "list", "--db", "parts.db"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.list_backups.return_value = []
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
                
                mock_instance.list_backups.assert_called_once()
    
    def test_list_assembled_backups(self):
        """Test listing only assembled_casm.db backups."""
        with patch("sys.argv", ["casman", "sync", "list", "--db", "assembled_casm.db"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.list_backups.return_value = []
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
                
                mock_instance.list_backups.assert_called_once()


class TestSyncCommand:
    """Test sync command functionality."""
    
    def test_sync_both_databases(self):
        """Test syncing both databases."""
        with patch("sys.argv", ["casman", "sync", "sync"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
    
    def test_sync_parts_only(self):
        """Test syncing only parts.db."""
        with patch("sys.argv", ["casman", "sync", "sync", "--parts"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
    
    def test_sync_assembled_only(self):
        """Test syncing only assembled_casm.db."""
        with patch("sys.argv", ["casman", "sync", "sync", "--assembled"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
    
    def test_sync_with_force(self):
        """Test syncing with force flag."""
        with patch("sys.argv", ["casman", "sync", "sync", "--force"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()


class TestStatusCommand:
    """Test status command functionality."""
    
    def test_status_display(self):
        """Test status command displays configuration."""
        with patch("sys.argv", ["casman", "sync", "status"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "r2"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()


class TestMaintainCommand:
    """Test maintain command functionality."""
    
    def test_maintain_r2_backend(self):
        """Test maintaining backup storage class for R2."""
        with patch("sys.argv", ["casman", "sync", "maintain"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.backend = "r2"
                mock_instance.maintain_storage_class.return_value = {
                    "success": True,
                    "objects_touched": 5,
                    "errors": [],
                    "message": "All objects maintained"
                }
                # Return real integers not MagicMock
                mock_instance.quota_tracker.get_usage_summary.return_value = {
                    "class_a_ops": 100,
                    "class_a_limit": 10000,
                    "class_a_percent": 1.0,
                    "class_b_ops": 200,
                    "class_b_limit": 10000,
                    "class_b_percent": 2.0,
                    "storage_usage": 1024,
                    "storage_limit": 10000000,
                    "storage_percent": 0.01,
                }
                
                from casman.cli.sync_commands import cmd_sync
                # Should complete without raising
                cmd_sync()
    
    def test_maintain_s3_backend(self):
        """Test maintain command skips S3 backend."""
        with patch("sys.argv", ["casman", "sync", "maintain"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                with pytest.raises(SystemExit) as exc_info:
                    cmd_sync()
                # Should exit with 0 as maintenance not needed
                assert exc_info.value.code == 0


class TestSyncCommandIntegration:
    """Integration tests for sync commands with mocked SyncManager."""
    
    def test_backup_workflow(self):
        """Test complete backup workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("sys.argv", ["casman", "sync", "backup"]):
                with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                    mock_instance = MagicMock()
                    mock_mgr.return_value = mock_instance
                    mock_instance.config.enabled = True
                    mock_instance.config.backend = "s3"
                    
                    from casman.cli.sync_commands import cmd_sync
                    cmd_sync()
    
    def test_restore_workflow(self):
        """Test complete restore workflow."""
        backup_key = "backups/parts.db/20241208_143022_parts.db"
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("sys.argv", ["casman", "sync", "restore", backup_key]):
                with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                    mock_instance = MagicMock()
                    mock_mgr.return_value = mock_instance
                    mock_instance.config.enabled = True
                    mock_instance.config.backend = "s3"
                    
                    from casman.cli.sync_commands import cmd_sync
                    cmd_sync()
    
    def test_sync_workflow(self):
        """Test complete sync workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("sys.argv", ["casman", "sync", "sync"]):
                with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                    mock_instance = MagicMock()
                    mock_mgr.return_value = mock_instance
                    mock_instance.config.enabled = True
                    mock_instance.config.backend = "s3"
                    
                    from casman.cli.sync_commands import cmd_sync
                    cmd_sync()
    
    def test_list_workflow(self):
        """Test complete list workflow."""
        with patch("sys.argv", ["casman", "sync", "list"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                mock_instance.list_backups.return_value = []
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_no_subcommand(self):
        """Test sync command without subcommand."""
        with patch("sys.argv", ["casman", "sync"]):
            from casman.cli.sync_commands import cmd_sync
            # Should not crash, may show help or do nothing
            cmd_sync()
    
    def test_invalid_subcommand(self):
        """Test sync command with invalid subcommand."""
        with patch("sys.argv", ["casman", "sync", "invalid"]):
            with pytest.raises(SystemExit):
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
    
    def test_backup_with_both_flags(self):
        """Test backup with both --parts and --assembled."""
        with patch("sys.argv", ["casman", "sync", "backup", "--parts", "--assembled"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                mock_instance = MagicMock()
                mock_mgr.return_value = mock_instance
                mock_instance.config.enabled = True
                mock_instance.config.backend = "s3"
                
                from casman.cli.sync_commands import cmd_sync
                cmd_sync()
    
    def test_sync_manager_not_configured(self):
        """Test sync commands when SyncManager is not configured."""
        with patch("sys.argv", ["casman", "sync", "status"]):
            with patch("casman.database.sync.DatabaseSyncManager") as mock_mgr:
                # Simulate unconfigured state
                mock_mgr.side_effect = Exception("R2 not configured")
                
                from casman.cli.sync_commands import cmd_sync
                with pytest.raises(SystemExit):
                    cmd_sync()
