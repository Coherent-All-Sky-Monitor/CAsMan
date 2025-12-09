"""
CAsMan - CASM Assembly Manager

A collection of scripts to manage and visualize the sequence of parts
in the CASM assembly process.
"""

import logging
import os

__version__ = "1.2.0"
__author__ = "CASM Team"

logger = logging.getLogger(__name__)


def _auto_sync_on_install():
    """
    Auto-sync databases on package install/import if configured.
    
    This runs once when the package is first imported to sync databases
    from remote storage. Fails gracefully if sync is not configured or
    offline.
    """
    # Check if this is the first import (use marker file)
    import tempfile
    marker_file = os.path.join(tempfile.gettempdir(), ".casman_synced")
    
    # Skip if already synced in this session
    if os.path.exists(marker_file):
        return
    
    try:
        from casman.database.sync import DatabaseSyncManager, SyncConfig
        from casman.database.connection import get_database_path
        
        config = SyncConfig.from_config()
        
        # Only auto-sync if explicitly enabled and configured
        if not config.enabled or not config.auto_sync_on_import:
            return
        
        sync_manager = DatabaseSyncManager(config)
        
        # Check if backend is available
        if sync_manager.backend is None:
            logger.debug("Database sync backend not available, skipping auto-sync")
            return
        
        # Try to sync both databases
        for db_name in ["parts.db", "assembled_casm.db"]:
            try:
                db_path = get_database_path(db_name)
                if sync_manager.check_needs_sync(db_path, db_name):
                    logger.info(f"Auto-syncing {db_name} on package import...")
                    sync_manager.sync_from_remote(db_path, db_name, quiet=True)
            except Exception as e:
                logger.debug(f"Could not auto-sync {db_name}: {e}")
        
        # Mark as synced for this session
        with open(marker_file, 'w') as f:
            f.write("synced")
            
    except Exception as e:
        # Fail silently - this is not critical
        logger.debug(f"Auto-sync failed: {e}")


# Run auto-sync on import (only if environment variable is set)
# This prevents sync on every import, only on explicit install/first use
if os.environ.get("CASMAN_AUTO_SYNC_ON_INSTALL", "").lower() in ("true", "1", "yes"):
    _auto_sync_on_install()
