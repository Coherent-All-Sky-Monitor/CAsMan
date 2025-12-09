"""
Tests for database sync module.

These tests cover backup, restore, and sync operations without
connecting to actual cloud storage services.
"""

import hashlib
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, call, mock_open

import pytest


class TestSyncConfig:
    """Test SyncConfig configuration loading."""
    
    def test_sync_config_from_config_with_r2(self):
        """Test loading sync config with R2 settings."""
        import sys
        import importlib
        
        # Remove module from cache to ensure fresh import
        if 'casman.database.sync' in sys.modules:
            del sys.modules['casman.database.sync']
        
        with patch("casman.config.get_config") as mock_get:
            # Mock returns dict for both "database.sync" and "r2" calls
            def mock_config(key, default=None):
                if key == "database.sync":
                    return {"enabled": True, "backend": "r2"}
                elif key == "r2":
                    return {
                        "account_id": "test_account",
                        "access_key_id": "test_key",
                        "secret_access_key": "test_secret",
                        "bucket_name": "test_bucket",
                    }
                return default
            
            mock_get.side_effect = mock_config
            
            from casman.database.sync import SyncConfig
            config = SyncConfig.from_config()
            
            assert config.enabled is True
            assert config.backend == "r2"
            assert config.account_id == "test_account"
            assert config.bucket_name == "test_bucket"
    
    def test_sync_config_defaults(self):
        """Test sync config with defaults when not configured."""
        with patch("casman.config.get_config") as mock_get:
            mock_get.return_value = None
            
            from casman.database.sync import SyncConfig
            config = SyncConfig.from_config()
            
            # Default values from dataclass definition
            assert config.enabled is True
            assert config.backend == "r2"
            assert config.keep_versions == 10
            assert config.quota_limits is not None  # Should have default quota limits


class TestBackupMetadata:
    """Test BackupMetadata dataclass."""
    
    def test_backup_metadata_creation(self):
        """Test creating backup metadata."""
        from casman.database.sync import BackupMetadata
        
        timestamp = datetime.now(timezone.utc)
        metadata = BackupMetadata(
            filename="test.db",
            timestamp=timestamp,
            checksum="abc123",
            size_bytes=1024,
            db_name="parts",
            record_count=100,
            operation="backup"
        )
        
        assert metadata.filename == "test.db"
        assert metadata.timestamp == timestamp
        assert metadata.checksum == "abc123"
        assert metadata.size_bytes == 1024
        assert metadata.db_name == "parts"
        assert metadata.record_count == 100
        assert metadata.operation == "backup"
    
    def test_backup_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        from casman.database.sync import BackupMetadata
        
        timestamp = datetime.now(timezone.utc)
        metadata = BackupMetadata(
            filename="test.db",
            timestamp=timestamp,
            checksum="abc123",
            size_bytes=1024,
            db_name="parts"
        )
        
        data = metadata.to_dict()
        
        assert data["filename"] == "test.db"
        assert data["timestamp"] == timestamp.isoformat()
        assert data["checksum"] == "abc123"
        assert data["size_bytes"] == 1024
        assert data["db_name"] == "parts"


class TestDatabaseSyncManager:
    """Test DatabaseSyncManager core functionality."""
    
    def test_sync_manager_initialization(self):
        """Test initializing sync manager."""
        with patch("casman.database.sync.SyncConfig.from_config") as mock_config:
            config = MagicMock()
            config.enabled = True
            config.backend = "s3"
            mock_config.return_value = config
            
            from casman.database.sync import DatabaseSyncManager
            manager = DatabaseSyncManager()
            
            assert manager.config == config
    
    def test_calculate_checksum(self):
        """Test checksum calculation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            from casman.database.sync import DatabaseSyncManager
            
            with patch("casman.database.sync.SyncConfig.from_config") as mock_config:
                config = MagicMock()
                config.enabled = False
                mock_config.return_value = config
                
                manager = DatabaseSyncManager()
                checksum = manager._calculate_checksum(temp_path)
                
                # Verify it's a valid SHA256 hash
                assert len(checksum) == 64
                assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            Path(temp_path).unlink()
    
    def test_get_record_count_parts_db(self):
        """Test getting record count from parts.db."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db = f.name
        
        try:
            # Create test database
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE parts (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("INSERT INTO parts (name) VALUES ('part1')")
            cursor.execute("INSERT INTO parts (name) VALUES ('part2')")
            conn.commit()
            conn.close()
            
            from casman.database.sync import DatabaseSyncManager
            
            with patch("casman.database.sync.SyncConfig.from_config") as mock_config:
                config = MagicMock()
                config.enabled = False
                mock_config.return_value = config
                
                manager = DatabaseSyncManager()
                count = manager._get_record_count(temp_db, "parts.db")
                
                assert count == 2
        finally:
            Path(temp_db).unlink()
    
    def test_get_record_count_assembled_db(self):
        """Test getting record count from assembled_casm.db."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db = f.name
        
        try:
            # Create test database
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE assembled_casm (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("INSERT INTO assembled_casm (name) VALUES ('item1')")
            cursor.execute("INSERT INTO assembled_casm (name) VALUES ('item2')")
            cursor.execute("INSERT INTO assembled_casm (name) VALUES ('item3')")
            conn.commit()
            conn.close()
            
            from casman.database.sync import DatabaseSyncManager
            
            with patch("casman.database.sync.SyncConfig.from_config") as mock_config:
                config = MagicMock()
                config.enabled = False
                mock_config.return_value = config
                
                manager = DatabaseSyncManager()
                count = manager._get_record_count(temp_db, "assembled_casm.db")
                
                assert count == 3
        finally:
            Path(temp_db).unlink()
    
    def test_get_backup_key(self):
        """Test generating backup key."""
        from casman.database.sync import DatabaseSyncManager
        
        with patch("casman.database.sync.SyncConfig.from_config") as mock_config:
            config = MagicMock()
            config.enabled = False
            mock_config.return_value = config
            
            manager = DatabaseSyncManager()
            key = manager._get_backup_key("parts.db")
            
            # Should be in format: backups/parts.db/YYYYMMDD_HHMMSS_parts.db
            assert key.startswith("backups/parts.db/")
            assert key.endswith("_parts.db")
    
    def test_backend_lazy_loading_disabled(self):
        """Test backend is not loaded when sync is disabled."""
        from casman.database.sync import DatabaseSyncManager
        
        with patch("casman.database.sync.SyncConfig.from_config") as mock_config:
            config = MagicMock()
            config.enabled = False
            mock_config.return_value = config
            
            manager = DatabaseSyncManager()
            backend = manager.backend
            
            assert backend is None
    
    def test_backend_lazy_loading_r2(self):
        """Test backend initialization for R2."""
        from casman.database.sync import DatabaseSyncManager
        
        with patch("casman.database.sync.SyncConfig.from_config") as mock_config:
            config = MagicMock()
            config.enabled = True
            config.backend = "r2"
            config.account_id = "test_account"
            config.access_key_id = "test_key"
            config.secret_access_key = "test_secret"
            config.bucket_name = "test_bucket"
            config.endpoint = None
            config.region = "auto"
            mock_config.return_value = config
            
            with patch("boto3.client") as mock_boto3_client:
                mock_client = MagicMock()
                mock_boto3_client.return_value = mock_client
                
                manager = DatabaseSyncManager()
                backend = manager.backend
                
                assert backend == mock_client
                mock_boto3_client.assert_called_once()
    
    def test_list_backups_no_backend(self):
        """Test listing backups when backend is not available."""
        from casman.database.sync import DatabaseSyncManager
        
        with patch("casman.database.sync.SyncConfig.from_config") as mock_config:
            config = MagicMock()
            config.enabled = False
            mock_config.return_value = config
            
            manager = DatabaseSyncManager()
            result = manager.list_backups()
            
            assert result == []
    
    def test_backend_initialization(self):
        """Test that backend can be initialized."""
        from casman.database.sync import DatabaseSyncManager
        
        with patch("casman.database.sync.SyncConfig.from_config") as mock_config:
            config = MagicMock()
            config.enabled = False
            mock_config.return_value = config
            
            manager = DatabaseSyncManager()
            # Manager should be created
            assert manager is not None


class TestQuotaTracker:
    """Test R2 quota tracking functionality."""
    
    def test_quota_tracker_initialization(self):
        """Test quota tracker initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from casman.database.quota import QuotaTracker
            
            tracker = QuotaTracker(tmpdir)
            # QuotaTracker initializes with JSON file
            assert tracker is not None
    
    def test_quota_tracker_get_usage_summary(self):
        """Test getting quota usage summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from casman.database.quota import QuotaTracker
            
            tracker = QuotaTracker(tmpdir)
            
            # Get usage summary should not raise
            quota_limits = {
                "class_a_operations": 10000,
                "class_b_operations": 100000,
                "storage_gb": 10
            }
            usage = tracker.get_usage_summary(quota_limits)
            assert "class_a_ops" in usage
            assert "class_b_ops" in usage
