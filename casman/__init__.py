"""
CAsMan - CASM Assembly Manager

A collection of scripts to manage and visualize the sequence of parts
in the CASM assembly process.
"""

import logging
import os

__version__ = "1.5.2"
__author__ = "CASM Team"

logger = logging.getLogger(__name__)


def _auto_sync_on_install():
    """
    Auto-sync databases from GitHub Releases on package install/import if configured.
    
    This runs once when the package is first imported to sync databases
    from GitHub Releases. Fails gracefully if sync is not configured or offline.
    """
    # Check if this is the first import (use marker file)
    import tempfile
    marker_file = os.path.join(tempfile.gettempdir(), ".casman_synced")
    
    # Skip if already synced in this session
    if os.path.exists(marker_file):
        return
    
    try:
        from casman.database.github_sync import get_github_sync_manager
        from casman.config import get_config
        
        # Check if auto-sync enabled
        auto_sync = get_config("database.sync.auto_sync_on_import")
        if not auto_sync:
            return
        
        sync_manager = get_github_sync_manager()
        if sync_manager is None:
            logger.debug("GitHub sync not configured, skipping auto-sync")
            return
        
        # Get latest release and download databases
        latest_release = sync_manager.get_latest_release()
        if latest_release:
            logger.info(f"Auto-syncing databases from GitHub Releases on package import...")
            sync_manager.download_databases(snapshot=latest_release)
        
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
