"""
R2 Quota tracking to enforce Cloudflare free tier limits.

Tracks:
- Storage: 10 GB limit
- Class A operations (writes): 1 million/month limit
- Class B operations (reads): 10 million/month limit
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class QuotaExceededError(Exception):
    """Raised when R2 quota limits are exceeded."""
    pass


class QuotaTracker:
    """Track R2 API usage to prevent exceeding free tier limits."""
    
    def __init__(self, db_dir: Optional[str] = None):
        if db_dir is None:
            from casman.database.connection import get_database_path
            db_dir = os.path.dirname(get_database_path("parts.db"))
        
        self.quota_file = os.path.join(db_dir, ".r2_quota_tracker.json")
        self.data = self._load()
        
    def _load(self) -> dict:
        """Load quota tracking data."""
        if os.path.exists(self.quota_file):
            try:
                with open(self.quota_file, "r") as f:
                    data = json.load(f)
                    # Check if we need to reset monthly counters
                    last_reset = datetime.fromisoformat(data.get("last_reset", datetime.utcnow().isoformat()))
                    now = datetime.utcnow()
                    # Reset if in a new month
                    if last_reset.month != now.month or last_reset.year != now.year:
                        logger.info("Resetting monthly quota counters")
                        data["class_a_ops_month"] = 0
                        data["class_b_ops_month"] = 0
                        data["last_reset"] = now.isoformat()
                        self._save_data(data)
                    return data
            except Exception as e:
                logger.warning(f"Could not load quota tracker: {e}")
        
        return {
            "total_storage_bytes": 0,
            "class_a_ops_month": 0,  # Writes (PUT, POST, LIST, DELETE)
            "class_b_ops_month": 0,  # Reads (GET, HEAD)
            "last_reset": datetime.utcnow().isoformat(),
            "backups_this_month": 0,
            "restores_this_month": 0,
        }
    
    def _save_data(self, data: dict):
        """Save data to file."""
        try:
            with open(self.quota_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save quota tracker: {e}")
    
    def _save(self):
        """Save quota tracking data."""
        self._save_data(self.data)
    
    def record_backup(self, size_bytes: int, num_files: int = 2):
        """Record a backup operation (Class A: PUT + metadata)."""
        # Each backup: 1 PUT for DB + 1 PUT for metadata + potential LIST/DELETE for cleanup
        class_a_ops = num_files + 2  # PUT operations + potential LIST + DELETE
        
        self.data["class_a_ops_month"] += class_a_ops
        self.data["backups_this_month"] += 1
        self.data["total_storage_bytes"] += size_bytes
        self._save()
        logger.debug(f"Recorded backup: {class_a_ops} Class A ops, {size_bytes} bytes")
    
    def record_restore(self):
        """Record a restore operation (Class B: GET)."""
        # Each restore: 1 GET for DB file + 1 GET for metadata
        class_b_ops = 2
        
        self.data["class_b_ops_month"] += class_b_ops
        self.data["restores_this_month"] += 1
        self._save()
        logger.debug(f"Recorded restore: {class_b_ops} Class B ops")
    
    def record_list(self, num_requests: int = 1):
        """Record a list operation (Class A: LIST)."""
        self.data["class_a_ops_month"] += num_requests
        self._save()
        logger.debug(f"Recorded list: {num_requests} Class A ops")
    
    def record_sync_check(self, num_files: int = 2):
        """Record sync check operations (Class B: HEAD requests)."""
        self.data["class_b_ops_month"] += num_files
        self._save()
        logger.debug(f"Recorded sync check: {num_files} Class B ops")
    
    def check_quota(self, quota_limits: dict, operation: str = "backup") -> bool:
        """Check if operation would exceed quota limits.
        
        Parameters
        ----------
        quota_limits : dict
            Dictionary with quota limit configuration.
        operation : str
            Type of operation: 'backup', 'restore', 'list', 'sync'
        
        Returns
        -------
        bool
            True if operation is allowed, False otherwise.
            
        Raises
        ------
        QuotaExceededError
            If quota would be exceeded.
        """
        # Storage check
        storage_gb = self.data["total_storage_bytes"] / (1024**3)
        storage_usage = storage_gb / quota_limits["storage_gb"]
        
        # Class A ops check (writes)
        class_a_usage = self.data["class_a_ops_month"] / quota_limits["class_a_operations"]
        
        # Class B ops check (reads)
        class_b_usage = self.data["class_b_ops_month"] / quota_limits["class_b_operations"]
        
        # Determine which quotas this operation affects
        if operation in ["backup"]:
            check_usage = max(storage_usage, class_a_usage)
            quota_type = "storage/Class A operations"
        elif operation in ["restore", "sync"]:
            check_usage = class_b_usage
            quota_type = "Class B operations"
        elif operation == "list":
            check_usage = class_a_usage
            quota_type = "Class A operations"
        else:
            check_usage = max(storage_usage, class_a_usage, class_b_usage)
            quota_type = "storage/operations"
        
        # Block if at block threshold
        if check_usage >= quota_limits["block_threshold"]:
            error_msg = (
                f"R2 quota limit reached: {check_usage*100:.1f}% of {quota_type} used. "
                f"Operation '{operation}' blocked to prevent exceeding free tier limits. "
                f"Storage: {storage_gb:.2f}/{quota_limits['storage_gb']} GB, "
                f"Class A: {self.data['class_a_ops_month']}/{quota_limits['class_a_operations']:,}, "
                f"Class B: {self.data['class_b_ops_month']}/{quota_limits['class_b_operations']:,}"
            )
            logger.error(error_msg)
            raise QuotaExceededError(error_msg)
        
        # Warn if at warn threshold
        if check_usage >= quota_limits["warn_threshold"]:
            logger.warning(
                f"⚠ R2 quota warning: {check_usage*100:.1f}% of {quota_type} used. "
                f"Storage: {storage_gb:.2f}/{quota_limits['storage_gb']} GB, "
                f"Class A: {self.data['class_a_ops_month']}/{quota_limits['class_a_operations']:,}, "
                f"Class B: {self.data['class_b_ops_month']}/{quota_limits['class_b_operations']:,}"
            )
        
        return True
    
    def get_usage_summary(self, quota_limits: dict) -> dict:
        """Get current quota usage summary."""
        storage_gb = self.data["total_storage_bytes"] / (1024**3)
        
        return {
            "storage_gb": storage_gb,
            "storage_limit_gb": quota_limits["storage_gb"],
            "storage_percent": (storage_gb / quota_limits["storage_gb"]) * 100,
            "class_a_ops": self.data["class_a_ops_month"],
            "class_a_limit": quota_limits["class_a_operations"],
            "class_a_percent": (self.data["class_a_ops_month"] / quota_limits["class_a_operations"]) * 100,
            "class_b_ops": self.data["class_b_ops_month"],
            "class_b_limit": quota_limits["class_b_operations"],
            "class_b_percent": (self.data["class_b_ops_month"] / quota_limits["class_b_operations"]) * 100,
            "backups_this_month": self.data["backups_this_month"],
            "restores_this_month": self.data["restores_this_month"],
            "last_reset": self.data["last_reset"],
        }
