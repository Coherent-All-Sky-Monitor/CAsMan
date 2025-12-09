"""
Database backup and synchronization module for CAsMan.

Provides cloud backup/restore functionality with support for:
- Cloudflare R2 
- Versioned backups with timestamps
- Zero data loss guarantees
- Offline-first operation with graceful degradation
- Multi-user safety with conflict detection
"""

import hashlib
import json
import logging
import os
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from casman.config import get_config
from casman.database.quota import QuotaTracker, QuotaExceededError

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a database backup."""

    filename: str
    timestamp: datetime
    checksum: str
    size_bytes: int
    db_name: str
    record_count: Optional[int] = None
    operation: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "timestamp": self.timestamp.isoformat(),
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "db_name": self.db_name,
            "record_count": self.record_count,
            "operation": self.operation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackupMetadata":
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class SyncConfig:
    """Configuration for database synchronization."""

    enabled: bool = True
    backend: str = "r2"  # 'r2', 's3', or 'disabled'
    auto_sync_on_import: bool = False  # Only on install, not every import
    cache_ttl_seconds: int = 3600  # 1 hour
    keep_versions: int = 10
    backup_on_scan_count: int = 10  # Backup every N scans
    backup_on_hours: float = 24.0  # Backup every N hours

    # R2/S3 configuration
    account_id: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    bucket_name: str = "casman-databases"
    endpoint: Optional[str] = None
    region: str = "auto"
    
    # R2 Free Tier Quota Limits
    quota_limits: Optional[dict] = None

    @classmethod
    def from_config(cls) -> "SyncConfig":
        """Load sync configuration from config.yaml and environment."""
        config_data = {}

        # Load from config.yaml
        db_sync = get_config("database.sync")
        if db_sync:
            config_data.update(db_sync)

        r2_config = get_config("r2")
        if r2_config:
            config_data.update(r2_config)

        # Override with environment variables (higher priority)
        env_mapping = {
            "R2_ACCOUNT_ID": "account_id",
            "R2_ACCESS_KEY_ID": "access_key_id",
            "R2_SECRET_ACCESS_KEY": "secret_access_key",
            "R2_BUCKET_NAME": "bucket_name",
            "R2_ENDPOINT": "endpoint",
            "CASMAN_SYNC_ENABLED": "enabled",
            "CASMAN_SYNC_BACKEND": "backend",
        }

        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Handle boolean conversion
                if config_key == "enabled":
                    value = value.lower() in ("true", "1", "yes")
                config_data[config_key] = value
        
        # Set default quota limits if not specified
        if "quota_limits" not in config_data or config_data["quota_limits"] is None:
            config_data["quota_limits"] = {
                "storage_gb": 10.0,
                "class_a_operations": 1000000,
                "class_b_operations": 10000000,
                "warn_threshold": 0.8,
                "block_threshold": 0.95,
            }

        return cls(**{k: v for k, v in config_data.items() if k in cls.__annotations__})


class DatabaseSyncManager:
    """Manages database backup and synchronization."""

    def __init__(self, config: Optional[SyncConfig] = None, db_dir: Optional[str] = None):
        self.config = config or SyncConfig.from_config()
        self._backend = None
        self._metadata_cache: Dict[str, BackupMetadata] = {}
        self.quota_tracker = QuotaTracker(db_dir) if self.config.backend == "r2" else None

    @property
    def backend(self):
        """Lazy-load the storage backend."""
        if self._backend is None and self.config.enabled:
            if self.config.backend in ("r2", "s3"):
                try:
                    import boto3
                    from botocore.exceptions import BotoCoreError, ClientError

                    # Build endpoint URL
                    if self.config.backend == "r2":
                        if not self.config.endpoint:
                            endpoint = f"https://{self.config.account_id}.r2.cloudflarestorage.com"
                        else:
                            endpoint = self.config.endpoint
                    else:
                        endpoint = None

                    self._backend = boto3.client(
                        "s3",
                        endpoint_url=endpoint,
                        aws_access_key_id=self.config.access_key_id,
                        aws_secret_access_key=self.config.secret_access_key,
                        region_name=self.config.region,
                    )
                    logger.info(
                        f"Initialized {self.config.backend.upper()} backend for bucket: {self.config.bucket_name}"
                    )
                except ImportError:
                    logger.warning(
                        "boto3 not installed. Install with: pip install boto3"
                    )
                    self.config.enabled = False
                except Exception as e:
                    logger.warning(f"Failed to initialize storage backend: {e}")
                    self.config.enabled = False

        return self._backend

    def _calculate_checksum(self, filepath: str) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_record_count(self, db_path: str, db_name: str) -> Optional[int]:
        """Get the number of records in the main table of a database."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Determine table name based on database
            if "parts" in db_name.lower():
                table = "parts"
            elif "assembled" in db_name.lower():
                table = "assembled_casm"
            else:
                return None

            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.warning(f"Could not get record count for {db_name}: {e}")
            return None

    def _get_backup_key(self, db_name: str, timestamp: Optional[datetime] = None) -> str:
        """Generate S3 key for a backup."""
        if timestamp is None:
            timestamp = datetime.now(UTC)
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"backups/{db_name}/{timestamp_str}_{db_name}"

    def _get_metadata_key(self, backup_key: str) -> str:
        """Generate S3 key for backup metadata."""
        return f"{backup_key}.metadata.json"

    def backup_database(
        self,
        db_path: str,
        db_name: str,
        operation: Optional[str] = None,
        quiet: bool = False,
    ) -> Optional[BackupMetadata]:
        """
        Backup a database to cloud storage.

        Parameters
        ----------
        db_path : str
            Path to the database file to backup.
        db_name : str
            Name of the database (e.g., 'parts.db').
        operation : str, optional
            Description of the operation that triggered this backup.
        quiet : bool, default False
            If True, suppress log messages.

        Returns
        -------
        BackupMetadata or None
            Metadata about the backup, or None if backup failed/disabled.
        """
        if not self.config.enabled:
            if not quiet:
                logger.debug("Database sync is disabled")
            return None

        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return None

        try:
            # Ensure backend is initialized
            if self.backend is None:
                logger.warning("Storage backend not available")
                return None
            
            # Check quota limits before backup (R2 only)
            if self.quota_tracker:
                try:
                    self.quota_tracker.check_quota(self.config.quota_limits, "backup")
                except QuotaExceededError as e:
                    logger.error(f"Backup blocked: {e}")
                    if not quiet:
                        print(f"✗ {e}")
                    return None

            # Calculate metadata
            timestamp = datetime.now(UTC)
            checksum = self._calculate_checksum(db_path)
            size_bytes = os.path.getsize(db_path)
            record_count = self._get_record_count(db_path, db_name)

            metadata = BackupMetadata(
                filename=db_name,
                timestamp=timestamp,
                checksum=checksum,
                size_bytes=size_bytes,
                db_name=db_name,
                record_count=record_count,
                operation=operation,
            )

            # Generate backup key
            backup_key = self._get_backup_key(db_name, timestamp)
            metadata_key = self._get_metadata_key(backup_key)

            # Upload database file
            if not quiet:
                logger.info(f"Backing up {db_name} to {self.config.backend.upper()}...")

            self.backend.upload_file(
                db_path, self.config.bucket_name, backup_key
            )

            # Upload metadata
            self.backend.put_object(
                Bucket=self.config.bucket_name,
                Key=metadata_key,
                Body=json.dumps(metadata.to_dict(), indent=2),
                ContentType="application/json",
            )

            if not quiet:
                logger.info(
                    f"✓ Backup complete: {backup_key} ({size_bytes / 1024:.1f} KB, {record_count} records)"
                )
            
            # Record quota usage (R2 only)
            if self.quota_tracker:
                self.quota_tracker.record_backup(size_bytes, num_files=2)

            # Cleanup old backups
            self._cleanup_old_backups(db_name)

            return metadata

        except Exception as e:
            logger.error(f"Backup failed for {db_name}: {e}")
            return None

    def _cleanup_old_backups(self, db_name: str):
        """Remove old backups beyond keep_versions limit."""
        try:
            # List all backups for this database
            prefix = f"backups/{db_name}/"
            response = self.backend.list_objects_v2(
                Bucket=self.config.bucket_name, Prefix=prefix
            )

            if "Contents" not in response:
                return

            # Filter to only .db files (not metadata)
            backups = [
                obj
                for obj in response["Contents"]
                if obj["Key"].endswith(".db")
            ]

            # Sort by modification time (oldest first)
            backups.sort(key=lambda x: x["LastModified"])

            # Delete oldest backups if we exceed keep_versions
            to_delete = backups[: -self.config.keep_versions]
            for backup in to_delete:
                logger.info(f"Removing old backup: {backup['Key']}")
                self.backend.delete_object(
                    Bucket=self.config.bucket_name, Key=backup["Key"]
                )
                # Also delete metadata
                metadata_key = self._get_metadata_key(backup["Key"])
                self.backend.delete_object(
                    Bucket=self.config.bucket_name, Key=metadata_key
                )

        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")

    def list_backups(
        self, db_name: Optional[str] = None
    ) -> List[Tuple[str, BackupMetadata]]:
        """
        List available backups.

        Parameters
        ----------
        db_name : str, optional
            Filter backups for a specific database.

        Returns
        -------
        List[Tuple[str, BackupMetadata]]
            List of (backup_key, metadata) tuples, sorted by timestamp (newest first).
        """
        if not self.config.enabled or self.backend is None:
            logger.warning("Storage backend not available")
            return []
        
        # Check quota limits before list (R2 only)
        if self.quota_tracker:
            try:
                self.quota_tracker.check_quota(self.config.quota_limits, "list")
            except QuotaExceededError as e:
                logger.error(f"List operation blocked: {e}")
                return []

        try:
            prefix = f"backups/{db_name}/" if db_name else "backups/"
            response = self.backend.list_objects_v2(
                Bucket=self.config.bucket_name, Prefix=prefix
            )

            if "Contents" not in response:
                return []

            backups = []
            for obj in response["Contents"]:
                key = obj["Key"]
                if not key.endswith(".db"):
                    continue

                # Try to load metadata
                metadata_key = self._get_metadata_key(key)
                try:
                    meta_response = self.backend.get_object(
                        Bucket=self.config.bucket_name, Key=metadata_key
                    )
                    meta_data = json.loads(meta_response["Body"].read())
                    metadata = BackupMetadata.from_dict(meta_data)
                except Exception as e:
                    # Create basic metadata from object info
                    logger.debug(f"No metadata for {key}: {e}")
                    metadata = BackupMetadata(
                        filename=os.path.basename(key),
                        timestamp=obj["LastModified"],
                        checksum="unknown",
                        size_bytes=obj["Size"],
                        db_name=db_name or "unknown",
                    )

                backups.append((key, metadata))

            # Sort by timestamp, newest first
            backups.sort(key=lambda x: x[1].timestamp, reverse=True)
            
            # Record quota usage (R2 only)
            if self.quota_tracker:
                self.quota_tracker.record_list(num_requests=1)
            
            return backups

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    def restore_database(
        self, backup_key: str, dest_path: str, create_backup: bool = True
    ) -> bool:
        """
        Restore a database from a backup.

        Parameters
        ----------
        backup_key : str
            S3 key of the backup to restore.
        dest_path : str
            Destination path for the restored database.
        create_backup : bool, default True
            If True, backup the current database before restoring.

        Returns
        -------
        bool
            True if restore succeeded, False otherwise.
        """
        if not self.config.enabled or self.backend is None:
            logger.error("Storage backend not available")
            return False
        
        # Check quota limits before restore (R2 only)
        if self.quota_tracker:
            try:
                self.quota_tracker.check_quota(self.config.quota_limits, "restore")
            except QuotaExceededError as e:
                logger.error(f"Restore blocked: {e}")
                return False

        try:
            # Backup current database if it exists and requested
            if create_backup and os.path.exists(dest_path):
                db_name = os.path.basename(dest_path)
                logger.info(f"Creating backup of current {db_name} before restore...")
                self.backup_database(dest_path, db_name, operation="pre-restore")

            # Download to temporary file first
            temp_path = f"{dest_path}.tmp"
            logger.info(f"Downloading backup: {backup_key}")

            self.backend.download_file(
                self.config.bucket_name, backup_key, temp_path
            )

            # Verify it's a valid SQLite database
            try:
                conn = sqlite3.connect(temp_path)
                conn.execute("SELECT 1")
                conn.close()
            except Exception as e:
                logger.error(f"Downloaded file is not a valid SQLite database: {e}")
                os.remove(temp_path)
                return False

            # Atomic move
            shutil.move(temp_path, dest_path)
            logger.info(f"✓ Database restored to {dest_path}")
            
            # Record quota usage (R2 only)
            if self.quota_tracker:
                self.quota_tracker.record_restore()
            
            return True

        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def sync_from_remote(
        self, db_path: str, db_name: str, force: bool = False, quiet: bool = False
    ) -> bool:
        """
        Sync a local database from the remote (download if newer).

        Parameters
        ----------
        db_path : str
            Path to local database.
        db_name : str
            Name of the database.
        force : bool, default False
            Force download even if local is up to date.
        quiet : bool, default False
            Suppress log messages.

        Returns
        -------
        bool
            True if sync occurred, False otherwise.
        """
        if not self.config.enabled or self.backend is None:
            if not quiet:
                logger.debug("Storage backend not available for sync")
            return False
        
        # Check quota limits before sync (R2 only)
        if self.quota_tracker and not force:
            try:
                self.quota_tracker.check_quota(self.config.quota_limits, "sync")
            except QuotaExceededError as e:
                if not quiet:
                    logger.error(f"Sync blocked: {e}")
                return False

        try:
            # Get latest remote backup
            backups = self.list_backups(db_name)
            if not backups:
                if not quiet:
                    logger.info(f"No remote backups found for {db_name}")
                return False

            latest_key, latest_metadata = backups[0]

            # Check if we need to sync
            if not force and os.path.exists(db_path):
                local_checksum = self._calculate_checksum(db_path)
                if local_checksum == latest_metadata.checksum:
                    if not quiet:
                        logger.info(f"Local {db_name} is up to date")
                    return False

            # Download latest version
            if not quiet:
                logger.info(f"Syncing {db_name} from remote...")
            
            # Record quota usage for check (R2 only)
            if self.quota_tracker:
                self.quota_tracker.record_sync_check(num_files=1)
            
            return self.restore_database(latest_key, db_path, create_backup=False)

        except Exception as e:
            if not quiet:
                logger.warning(f"Sync failed for {db_name}: {e}")
            return False

    def check_needs_sync(self, db_path: str, db_name: str) -> bool:
        """
        Check if a local database needs to be synced from remote.

        Parameters
        ----------
        db_path : str
            Path to local database.
        db_name : str
            Name of the database.

        Returns
        -------
        bool
            True if sync is needed, False otherwise.
        """
        if not self.config.enabled or self.backend is None:
            return False

        try:
            # Get latest remote backup
            backups = self.list_backups(db_name)
            if not backups:
                return False

            _, latest_metadata = backups[0]

            # If local doesn't exist, need sync
            if not os.path.exists(db_path):
                return True

            # Compare checksums
            local_checksum = self._calculate_checksum(db_path)
            return local_checksum != latest_metadata.checksum

        except Exception as e:
            logger.debug(f"Could not check sync status: {e}")
            return False

    def maintain_storage_class(self) -> Dict[str, any]:
        """
        Perform maintenance to keep objects in Standard storage class.
        
        Touches all backup objects by reading their metadata (HEAD request)
        to prevent automatic transition to Infrequent Access storage.
        
        Should be called at least once per month to ensure objects remain
        in the free tier eligible Standard storage class.
        
        Returns
        -------
        dict
            Summary of maintenance operation including objects touched.
        """
        if not self.config.enabled or self.backend is None:
            return {
                "success": False,
                "error": "Storage backend not available",
                "objects_touched": 0,
            }
        
        # Check quota limits for Class B operations (HEAD requests)
        if self.quota_tracker:
            try:
                self.quota_tracker.check_quota(self.config.quota_limits, "sync")
            except QuotaExceededError as e:
                return {
                    "success": False,
                    "error": f"Quota exceeded: {e}",
                    "objects_touched": 0,
                }
        
        try:
            # List all backup objects
            response = self.backend.list_objects_v2(
                Bucket=self.config.bucket_name, Prefix="backups/"
            )
            
            if "Contents" not in response:
                return {
                    "success": True,
                    "objects_touched": 0,
                    "message": "No backups found",
                }
            
            objects_touched = 0
            for obj in response["Contents"]:
                key = obj["Key"]
                
                # Touch object with HEAD request to maintain access pattern
                try:
                    self.backend.head_object(
                        Bucket=self.config.bucket_name,
                        Key=key
                    )
                    objects_touched += 1
                    logger.debug(f"Touched {key} to maintain Standard storage class")
                except Exception as e:
                    logger.warning(f"Failed to touch {key}: {e}")
            
            # Record quota usage (1 LIST + N HEAD requests)
            if self.quota_tracker:
                self.quota_tracker.record_list(num_requests=1)  # LIST operation
                self.quota_tracker.record_sync_check(num_files=objects_touched)  # HEAD operations
            
            logger.info(
                f"Storage class maintenance complete: touched {objects_touched} objects"
            )
            
            return {
                "success": True,
                "objects_touched": objects_touched,
                "message": f"Touched {objects_touched} objects to maintain Standard storage",
            }
            
        except Exception as e:
            logger.error(f"Storage class maintenance failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "objects_touched": 0,
            }


class ScanTracker:
    """Tracks scan operations to trigger time/count-based backups."""

    def __init__(self, db_dir: Optional[str] = None):
        if db_dir is None:
            from casman.database.connection import get_database_path

            db_dir = os.path.dirname(get_database_path("parts.db"))

        self.tracker_file = os.path.join(db_dir, ".scan_tracker.json")
        self.data = self._load()

    def _load(self) -> dict:
        """Load tracker data from file."""
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load scan tracker: {e}")

        return {
            "last_backup_time": None,
            "scans_since_backup": 0,
        }

    def _save(self):
        """Save tracker data to file."""
        try:
            with open(self.tracker_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save scan tracker: {e}")

    def record_scan(self):
        """Record a scan operation."""
        self.data["scans_since_backup"] += 1
        self._save()

    def reset_after_backup(self):
        """Reset counters after a backup."""
        self.data["last_backup_time"] = datetime.now(UTC).isoformat()
        self.data["scans_since_backup"] = 0
        self._save()

    def should_backup(self, config: SyncConfig) -> bool:
        """
        Check if a backup should be triggered based on scan count or time.

        Parameters
        ----------
        config : SyncConfig
            Sync configuration with thresholds.

        Returns
        -------
        bool
            True if backup should be triggered.
        """
        # Check scan count threshold
        if self.data["scans_since_backup"] >= config.backup_on_scan_count:
            logger.info(
                f"Backup triggered: {self.data['scans_since_backup']} scans since last backup"
            )
            return True

        # Check time threshold (only if there have been scans)
        if self.data["scans_since_backup"] > 0 and self.data["last_backup_time"]:
            last_backup = datetime.fromisoformat(self.data["last_backup_time"])
            hours_since = (datetime.now(UTC) - last_backup).total_seconds() / 3600

            if hours_since >= config.backup_on_hours:
                logger.info(
                    f"Backup triggered: {hours_since:.1f} hours since last backup"
                )
                return True

        return False
