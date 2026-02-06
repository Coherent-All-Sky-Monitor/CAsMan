"""
GitHub Releases-based database synchronization for CAsMan.

Provides database sync using GitHub Releases:
- Download databases from GitHub Releases (client-side)
- Upload databases to GitHub Releases (server-side)
- Timestamp-based release naming
- Fallback to stale local copy on failure
- No authentication required for public repos
"""

import hashlib
import json
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests

from casman.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class DatabaseSnapshot:
    """Metadata for a database snapshot on GitHub Releases."""

    release_name: str  # e.g., "database-snapshot-20251218-143022"
    timestamp: datetime
    checksum: str
    size_bytes: int
    download_url: str
    assets: List[str]  # List of database filenames (parts.db, assembled_casm.db)

    def to_dict(self) -> dict:
        return {
            "release_name": self.release_name,
            "timestamp": self.timestamp.isoformat(),
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "download_url": self.download_url,
            "assets": self.assets,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DatabaseSnapshot":
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class GitHubSyncManager:
    """Manages database synchronization with GitHub Releases."""

    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        github_token: Optional[str] = None,
        local_db_dir: Optional[Path] = None,
    ):
        """
        Initialize GitHub sync manager.

        Args:
            repo_owner: GitHub repository owner (e.g., "Coherent-All-Sky-Monitor")
            repo_name: GitHub repository name (e.g., "CAsMan")
            github_token: Optional GitHub personal access token (required for uploads)
            local_db_dir: Local database directory (defaults to XDG standard location)
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        self.api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

        # Determine local database directory
        if local_db_dir:
            self.local_db_dir = Path(local_db_dir)
        else:
            # Prefer project database directory when running in full project environment
            project_db_dir = self._detect_project_db_dir()
            if project_db_dir is not None:
                self.local_db_dir = project_db_dir
            else:
                # Fallback to XDG standard location: ~/.local/share/casman/databases/
                xdg_data_home = os.environ.get("XDG_DATA_HOME")
                if xdg_data_home:
                    base_dir = Path(xdg_data_home)
                else:
                    base_dir = Path.home() / ".local" / "share"
                self.local_db_dir = base_dir / "casman" / "databases"

        self.local_db_dir.mkdir(parents=True, exist_ok=True)

        # Track last sync check
        self.last_check_file = self.local_db_dir / ".last_sync_check"
        self.metadata_file = self.local_db_dir / ".sync_metadata.json"

    def _detect_project_db_dir(self) -> Optional[Path]:
        """
        Detect the project's database directory by scanning upward for a repository root
        that contains both 'pyproject.toml' and a 'database' folder.

        Returns:
            Path to project database directory if found, else None.
        """
        try:
            current = Path(__file__).resolve()
            for parent in [current.parent] + list(current.parents):
                # Go up to possible repo root (two levels above casman/database)
                # and check for pyproject.toml and database directory
                # We consider both parent and its parents during the walk
                repo_root = parent
                pyproject = repo_root / "pyproject.toml"
                database_dir = repo_root / "database"
                if pyproject.exists() and database_dir.exists() and database_dir.is_dir():
                    return database_dir
            # Also check CWD fallback
            cwd_db = Path(os.getcwd()) / "database"
            if (Path(os.getcwd()) / "pyproject.toml").exists() and cwd_db.exists():
                return cwd_db
        except Exception:
            pass
        return None

    def _get_headers(self, include_auth: bool = False) -> Dict[str, str]:
        """Get HTTP headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CAsMan-Database-Sync",
        }
        if include_auth and self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_latest_release(self) -> Optional[DatabaseSnapshot]:
        """
        Get the latest database snapshot from GitHub Releases.

        Returns:
            DatabaseSnapshot if found, None otherwise
        """
        try:
            # Get all releases sorted by date
            url = f"{self.api_base}/releases"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()

            releases = response.json()

            # Find the most recent database snapshot release
            for release in releases:
                tag_name = release.get("tag_name", "")
                if tag_name.startswith("database-snapshot-"):
                    # Parse timestamp from tag name
                    timestamp_str = tag_name.replace("database-snapshot-", "")
                    try:
                        timestamp = datetime.strptime(
                            timestamp_str, "%Y%m%d-%H%M%S"
                        ).replace(tzinfo=timezone.utc)
                    except ValueError:
                        logger.warning(f"Invalid timestamp format in release: {tag_name}")
                        continue

                    # Extract asset information
                    assets = []
                    total_size = 0
                    download_urls = {}

                    for asset in release.get("assets", []):
                        asset_name = asset["name"]
                        if asset_name.endswith(".db"):
                            assets.append(asset_name)
                            total_size += asset["size"]
                            download_urls[asset_name] = asset[
                                "browser_download_url"
                            ]

                    if not assets:
                        continue

                    # Use release description for checksum if available
                    body = release.get("body", "")
                    checksum = ""
                    if "SHA256:" in body:
                        checksum = body.split("SHA256:")[1].strip().split()[0]

                    return DatabaseSnapshot(
                        release_name=tag_name,
                        timestamp=timestamp,
                        checksum=checksum,
                        size_bytes=total_size,
                        download_url=release["html_url"],
                        assets=assets,
                    )

            return None

        except requests.RequestException as e:
            logger.error(f"Failed to fetch releases from GitHub: {e}")
            return None

    def download_databases(
        self, snapshot: Optional[DatabaseSnapshot] = None, force: bool = False
    ) -> bool:
        """
        Download databases from GitHub Releases.

        Args:
            snapshot: Specific snapshot to download (defaults to latest)
            force: Force download even if local copy exists and is up-to-date

        Returns:
            True if download successful, False otherwise
        """
        try:
            # Get snapshot to download
            if snapshot is None:
                snapshot = self.get_latest_release()
                if snapshot is None:
                    logger.warning("No database snapshots found on GitHub Releases")
                    return False

            # Check if we already have this version
            if not force and self._is_local_up_to_date(snapshot):
                logger.info("Local databases are already up-to-date")
                return True

            logger.info(f"Downloading database snapshot: {snapshot.release_name}")

            # Get release details to get asset download URLs
            url = f"{self.api_base}/releases/tags/{snapshot.release_name}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            release_data = response.json()

            # Download each database asset
            success = True
            for asset in release_data.get("assets", []):
                asset_name = asset["name"]
                if not asset_name.endswith(".db"):
                    continue

                download_url = asset["browser_download_url"]
                local_path = self.local_db_dir / asset_name

                logger.info(f"Downloading {asset_name}...")
                try:
                    # Download to temporary file first
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        tmp_path = Path(tmp_file.name)
                        response = requests.get(
                            download_url, headers=self._get_headers(), timeout=30
                        )
                        response.raise_for_status()
                        tmp_file.write(response.content)

                    # Verify it's a valid SQLite database
                    if not self._verify_sqlite_db(tmp_path):
                        logger.error(f"Downloaded file is not a valid SQLite database: {asset_name}")
                        tmp_path.unlink()
                        success = False
                        continue

                    # Backup existing local database before overwrite
                    try:
                        if local_path.exists():
                            ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
                            backup_path = local_path.with_name(f"{local_path.name}.{ts}.bak")
                            shutil.copy2(str(local_path), str(backup_path))
                            logger.info(f"Backup created: {backup_path}")
                    except Exception as be:
                        logger.warning(f"Failed to create backup for {local_path.name}: {be}")

                    # Move to final location
                    shutil.move(str(tmp_path), str(local_path))
                    logger.info(f"Successfully downloaded {asset_name}")

                except Exception as e:
                    logger.error(f"Failed to download {asset_name}: {e}")
                    if tmp_path.exists():
                        tmp_path.unlink()
                    success = False

            if success:
                # Update metadata
                self._save_sync_metadata(snapshot)
                self._update_last_check()
                logger.info("Database sync completed successfully")

            return success

        except Exception as e:
            logger.error(f"Failed to download databases: {e}")
            return False

    def _verify_sqlite_db(self, file_path: Path) -> bool:
        """Verify that a file is a valid SQLite database."""
        try:
            import sqlite3

            conn = sqlite3.connect(str(file_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            cursor.fetchall()
            conn.close()
            return True
        except Exception:
            return False

    def _is_local_up_to_date(self, remote_snapshot: DatabaseSnapshot) -> bool:
        """Check if local databases are up-to-date with remote snapshot."""
        try:
            if not self.metadata_file.exists():
                return False

            with open(self.metadata_file, "r") as f:
                local_metadata = json.load(f)

            local_timestamp = datetime.fromisoformat(local_metadata.get("timestamp", ""))
            return local_timestamp >= remote_snapshot.timestamp

        except Exception:
            return False

    def _save_sync_metadata(self, snapshot: DatabaseSnapshot):
        """Save sync metadata to local file."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(snapshot.to_dict(), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save sync metadata: {e}")

    def _update_last_check(self):
        """Update the last sync check timestamp."""
        try:
            with open(self.last_check_file, "w") as f:
                f.write(datetime.now(timezone.utc).isoformat())
        except Exception as e:
            logger.warning(f"Failed to update last check timestamp: {e}")

    def get_last_check_time(self) -> Optional[datetime]:
        """Get the timestamp of the last sync check."""
        try:
            if self.last_check_file.exists():
                with open(self.last_check_file, "r") as f:
                    return datetime.fromisoformat(f.read().strip())
        except Exception:
            pass
        return None

    def create_release(
        self, db_paths: List[Path], description: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a new GitHub Release with database snapshots.

        Args:
            db_paths: List of database file paths to upload
            description: Optional release description

        Returns:
            Release tag name if successful, None otherwise
        """
        if not self.github_token:
            logger.error("GitHub token required for creating releases")
            return None

        try:
            # Generate release name with timestamp
            timestamp = datetime.now(timezone.utc)
            tag_name = f"database-snapshot-{timestamp.strftime('%Y%m%d-%H%M%S')}"

            # Calculate total checksum
            checksums = []
            for db_path in db_paths:
                if db_path.exists():
                    checksums.append(self._calculate_checksum(db_path))

            combined_checksum = hashlib.sha256(
                "".join(checksums).encode()
            ).hexdigest()

            # Create release description
            if description is None:
                description = f"Automated database snapshot\nTimestamp: {timestamp.isoformat()}\n"

            description += f"\nSHA256: {combined_checksum}\n"
            description += "\nDatabases:\n"
            for db_path in db_paths:
                if db_path.exists():
                    size_mb = db_path.stat().st_size / (1024 * 1024)
                    description += f"- {db_path.name} ({size_mb:.2f} MB)\n"

            # Create the release
            url = f"{self.api_base}/releases"
            payload = {
                "tag_name": tag_name,
                "name": f"Database Snapshot {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                "body": description,
                "draft": False,
                "prerelease": False,
            }

            response = requests.post(
                url, headers=self._get_headers(include_auth=True), json=payload, timeout=30
            )
            response.raise_for_status()
            release_data = response.json()

            logger.info(f"Created release: {tag_name}")

            # Upload database files as assets
            upload_url = release_data["upload_url"].replace("{?name,label}", "")

            for db_path in db_paths:
                if not db_path.exists():
                    logger.warning(f"Database file not found: {db_path}")
                    continue

                logger.info(f"Uploading {db_path.name}...")

                with open(db_path, "rb") as f:
                    headers = self._get_headers(include_auth=True)
                    headers["Content-Type"] = "application/x-sqlite3"

                    asset_url = f"{upload_url}?name={db_path.name}"
                    asset_response = requests.post(
                        asset_url, headers=headers, data=f, timeout=60
                    )
                    asset_response.raise_for_status()

                logger.info(f"Successfully uploaded {db_path.name}")

            logger.info(f"Release {tag_name} created successfully")
            return tag_name

        except requests.RequestException as e:
            logger.error(f"Failed to create GitHub release: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating release: {e}")
            return None

    def cleanup_old_releases(self, keep_count: int = 10) -> int:
        """
        Delete old database snapshot releases, keeping only the most recent ones.

        Args:
            keep_count: Number of recent snapshots to keep

        Returns:
            Number of releases deleted
        """
        if not self.github_token:
            logger.error("GitHub token required for deleting releases")
            return 0

        try:
            # Get all database snapshot releases
            url = f"{self.api_base}/releases"
            response = requests.get(
                url, headers=self._get_headers(include_auth=True), timeout=10
            )
            response.raise_for_status()

            releases = response.json()

            # Filter and sort database snapshots
            snapshots = []
            for release in releases:
                tag_name = release.get("tag_name", "")
                if tag_name.startswith("database-snapshot-"):
                    try:
                        timestamp_str = tag_name.replace("database-snapshot-", "")
                        timestamp = datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")
                        snapshots.append((timestamp, release))
                    except ValueError:
                        continue

            # Sort by timestamp (newest first)
            snapshots.sort(key=lambda x: x[0], reverse=True)

            # Delete old releases
            deleted_count = 0
            for timestamp, release in snapshots[keep_count:]:
                release_id = release["id"]
                tag_name = release["tag_name"]

                logger.info(f"Deleting old release: {tag_name}")

                delete_url = f"{self.api_base}/releases/{release_id}"
                delete_response = requests.delete(
                    delete_url, headers=self._get_headers(include_auth=True), timeout=10
                )

                if delete_response.status_code == 204:
                    deleted_count += 1
                    logger.info(f"Deleted release: {tag_name}")
                else:
                    logger.warning(
                        f"Failed to delete release {tag_name}: {delete_response.status_code}"
                    )

            logger.info(f"Cleaned up {deleted_count} old releases")
            return deleted_count

        except requests.RequestException as e:
            logger.error(f"Failed to cleanup old releases: {e}")
            return 0


def get_github_sync_manager() -> Optional[GitHubSyncManager]:
    """
    Get a GitHubSyncManager instance from config.

    Returns:
        GitHubSyncManager if configured, None otherwise
    """
    try:
        # Get GitHub repo info from config
        repo_owner = get_config("database.sync.github_owner", "Coherent-All-Sky-Monitor")
        repo_name = get_config("database.sync.github_repo", "CAsMan")

        # Get optional GitHub token (required for server-side uploads)
        github_token = get_config("database.sync.github_token")
        if not github_token:
            github_token = os.environ.get("GITHUB_TOKEN")

        return GitHubSyncManager(
            repo_owner=repo_owner, repo_name=repo_name, github_token=github_token
        )

    except Exception as e:
        logger.error(f"Failed to create GitHub sync manager: {e}")
        return None
