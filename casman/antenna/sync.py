"""
Lightweight database synchronization for casman-antenna package.

This module provides auto-sync functionality for antenna-only users
who install casman-antenna via pip. It automatically downloads the latest
databases from GitHub Releases on import.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def sync_databases(quiet: bool = True) -> bool:
    """
    Synchronize databases from GitHub Releases.

    This function is called automatically when the antenna module is imported.
    It downloads the latest databases if they're not already up-to-date.

    Args:
        quiet: If True, suppress informational logging (keeps errors/warnings)

    Returns:
        True if sync successful or local databases are up-to-date, False otherwise
    """
    try:
        # Import here to avoid circular dependencies
        from casman.database.github_sync import get_github_sync_manager

        # Set logging level temporarily if quiet mode
        if quiet:
            original_level = logger.level
            logger.setLevel(logging.WARNING)

        try:
            # Get sync manager
            sync_manager = get_github_sync_manager()
            if sync_manager is None:
                logger.warning("Could not initialize GitHub sync manager")
                return False

            # Check if we have local databases
            has_local_dbs = _check_local_databases(sync_manager.local_db_dir)

            if not has_local_dbs:
                # First time: Download databases
                logger.info("First-time sync: downloading databases from GitHub...")
                success = sync_manager.download_databases()

                if not success:
                    logger.error(
                        "Failed to download databases. "
                        "Please check your internet connection or download manually."
                    )
                    return False

                logger.info("Database sync completed successfully")
                return True

            else:
                # Check for updates (always check on import as per user request)
                latest_release = sync_manager.get_latest_release()

                if latest_release is None:
                    # No releases found or GitHub API failed
                    # Use stale local copy (graceful degradation)
                    logger.debug("Using local databases (GitHub API unavailable)")
                    return True

                # Check if we need to update
                if sync_manager._is_local_up_to_date(latest_release):
                    logger.debug("Local databases are up-to-date")
                    return True

                # Download updated databases
                logger.info(f"Updating databases to {latest_release.release_name}...")
                success = sync_manager.download_databases(snapshot=latest_release)

                if not success:
                    # Use stale local copy on failure
                    logger.warning(
                        "Failed to download database updates. Using local copy."
                    )
                    return True  # Still return True since we have local databases

                logger.info("Database sync completed successfully")
                return True

        finally:
            # Restore logging level
            if quiet:
                logger.setLevel(original_level)

    except Exception as e:
        logger.error(f"Unexpected error during database sync: {e}")
        # Try to continue with local databases if they exist
        try:
            from casman.database.github_sync import get_github_sync_manager

            sync_manager = get_github_sync_manager()
            if sync_manager and _check_local_databases(sync_manager.local_db_dir):
                logger.info("Using local databases after sync error")
                return True
        except Exception:
            pass

        return False


def _check_local_databases(db_dir: Path) -> bool:
    """
    Check if local databases exist and are valid.

    Args:
        db_dir: Database directory path

    Returns:
        True if valid databases exist, False otherwise
    """
    try:
        # Check for essential database files
        parts_db = db_dir / "parts.db"
        assembled_db = db_dir / "assembled_casm.db"

        # Both databases should exist
        if not parts_db.exists() or not assembled_db.exists():
            return False

        # Check if they're non-empty
        if parts_db.stat().st_size == 0 or assembled_db.stat().st_size == 0:
            return False

        # Optional: Verify they're valid SQLite databases
        import sqlite3

        for db_path in [parts_db, assembled_db]:
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                cursor.fetchall()
                conn.close()
            except Exception:
                return False

        return True

    except Exception:
        return False


def force_sync() -> bool:
    """
    Force download of databases from GitHub Releases.

    This function can be called manually to force a database update,
    ignoring the local version check.

    Returns:
        True if sync successful, False otherwise
    """
    try:
        from casman.database.github_sync import get_github_sync_manager

        sync_manager = get_github_sync_manager()
        if sync_manager is None:
            logger.error("Could not initialize GitHub sync manager")
            return False

        logger.info("Force syncing databases from GitHub...")
        return sync_manager.download_databases(force=True)

    except Exception as e:
        logger.error(f"Failed to force sync databases: {e}")
        return False
