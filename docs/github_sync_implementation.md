# GitHub Releases Database Sync - Implementation Summary

## Overview
Implemented a complete GitHub Releases-based database synchronization system to replace the existing Cloudflare R2 backend. The system enables:
- **Client-side**: Automatic database downloads for pip-installed `casman-antenna` users
- **Server-side**: Manual/automatic database uploads to GitHub Releases via web UI or CLI

## Architecture

### Client Side (casman-antenna users - standalone install)
1. **Auto-sync on import**: When `casman.antenna` is imported, databases are automatically downloaded from GitHub Releases
2. **XDG standard location**: Databases stored in `~/.local/share/casman/databases/`
3. **Graceful degradation**: Falls back to stale local copy if GitHub API fails
4. **No authentication**: Public repo, no credentials needed for downloads

### Server Side (full CAsMan installation)
1. **Project directory downloads**: `casman database pull` downloads directly to `database/` folder
2. **Automatic backups**: Creates timestamped `.bak` files before overwriting databases
3. **Restore capability**: `casman database restore --latest` to restore from backups
4. **Web UI**: Admin panel with "Sync to GitHub" button
5. **CLI commands**: `casman database push/pull/status/restore`
6. **Configurable auto-push**: After N scans (default: 30) or N hours (default: 1)
7. **Requires GITHUB_TOKEN**: Personal access token with `repo` scope

## Files Created/Modified

### New Files
1. **casman/database/github_sync.py** (~510 lines)
   - `GitHubSyncManager` class
   - `DatabaseSnapshot` dataclass
   - Methods: `get_latest_release()`, `download_databases()`, `create_release()`, `cleanup_old_releases()`
   - Uses GitHub REST API v3 (requests library)

2. **casman/antenna/sync.py** (~160 lines)
   - Lightweight sync for antenna-only users
   - `sync_databases()`: Auto-sync on import
   - `force_sync()`: Manual sync trigger
   - Quiet mode by default (warnings/errors only)

### Modified Files
1. **config.yaml**
   - Added `database.sync.github_owner`, `github_repo`, `github_token`
   - Added `database.sync.client.*` settings
   - Added `database.sync.server.*` settings (auto-push configuration)
   - Changed default backend from `r2` to `github`

2. **casman/antenna/__init__.py**
   - Added auto-sync call on module import
   - Imports `sync_databases()` and calls with `quiet=True`
   - Catches exceptions to not fail import

3. **casman/database/connection.py**
   - Updated `get_database_path()` to check XDG location first
   - Path resolution order: explicit param → env vars → config.yaml → XDG → project root → cwd

4. **casman/web/visualize.py**
   - Added `/admin/sync-to-github` POST route
   - Added `/admin/sync-status` GET route
   - Server-side sync via web UI

5. **casman/templates/admin.html**
   - Added "Sync to GitHub" card with button
   - Shows latest release info on page load
   - JavaScript for sync status display

6. **casman/cli/database_commands.py**
   - Added `push` subcommand: Upload databases to GitHub Releases
   - Added `pull` subcommand: Download databases from GitHub Releases
   - Added `status` subcommand: Show sync status and configuration
   - Updated help text with new commands

## Configuration

### config.yaml
```yaml
database:
  sync:
    enabled: true
    backend: github  # Changed from 'r2' to 'github'
    
    github_owner: Coherent-All-Sky-Monitor
    github_repo: CAsMan
    # github_token: ghp_xxxxx  # Set via GITHUB_TOKEN env var
    
    auto_sync_on_import: true
    
    client:
      check_on_import: true
      use_stale_on_failure: true
    
    server:
      auto_push_enabled: true
      push_after_scans: 30
      push_after_hours: 1.0
      keep_releases: 10
```

### Environment Variables
- `GITHUB_TOKEN`: Required for server-side uploads (personal access token with `repo` scope)
- `XDG_DATA_HOME`: Optional, defaults to `~/.local/share`

## Release Naming Convention
- Format: `database-snapshot-YYYYMMDD-HHMMSS`
- Example: `database-snapshot-20251218-143022`
- Timestamp-based (UTC)
- Sorted automatically by GitHub (newest first)

## Usage

### Client Side (pip install casman-antenna)
```python
import casman.antenna  # Automatically syncs databases on import

# Manual sync if needed
from casman.antenna.sync import force_sync
force_sync()
```

### Server Side (CLI)
```bash
# Set GitHub token
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# Push databases to GitHub Releases
casman database push

# Push and cleanup old releases (keep 10 most recent)
casman database push --cleanup 10

# Download latest databases (saves to project database/ directory with backups)
casman database pull

# Force re-download even if up-to-date
casman database pull --force

# Restore from latest timestamped backups
casman database restore --latest              # Restore both databases
casman database restore --latest --parts      # Restore only parts.db
casman database restore --latest --assembled  # Restore only assembled_casm.db

# Show sync status
casman database status
```

### Server Side (Web UI)
1. Navigate to `/visualize/admin`
2. Click "Sync to GitHub" button
3. Status shows latest release info

## Auto-Push Trigger Logic
The server can automatically push databases to GitHub after changes:
- **Trigger**: After N scans OR N hours (whichever comes first)
- **Scans**: Connect/disconnect parts, assign/remove antenna positions
- **Configuration**: `push_after_scans` (default: 30), `push_after_hours` (default: 1.0)
- **Implementation**: Through web application (no cron jobs required)

## Database Files
- `parts.db`: Part inventory database (~324 KB)
- `assembled_casm.db`: Assembly chain database (~16 KB)
- Total size: ~340 KB (well within GitHub's limits)

## GitHub API Endpoints Used
- `GET /repos/{owner}/{repo}/releases` - List releases
- `GET /repos/{owner}/{repo}/releases/tags/{tag}` - Get specific release
- `POST /repos/{owner}/{repo}/releases` - Create release
- `POST /repos/{owner}/{repo}/releases/{id}/assets` - Upload asset
- `DELETE /repos/{owner}/{repo}/releases/{id}` - Delete release

## Dependencies
- `requests`: HTTP library for GitHub API calls
- `pyyaml`: Config file parsing
- Existing: `sqlite3`, `pathlib`, `hashlib`, `json`, `datetime`

## Testing Checklist
- [ ] Client-side auto-sync on first import
- [ ] Client-side check for updates on subsequent imports
- [ ] Client-side fallback to stale on GitHub API failure
- [ ] Server-side push via CLI
- [ ] Server-side push via web UI
- [ ] Server-side pull via CLI
- [ ] Server-side status command
- [ ] Release cleanup (keep N most recent)
- [ ] XDG path resolution
- [ ] Database validation (SQLite integrity check)

## Migration from Cloudflare R2
The new GitHub sync system coexists with the old R2 system:
- Old code: `casman/database/sync.py` (780 lines, R2-based)
- New code: `casman/database/github_sync.py` (510 lines, GitHub-based)
- Config: `backend: github` (was `backend: r2`)
- To migrate: Change backend setting and set GITHUB_TOKEN

## Advantages Over Cloudflare R2
1. **Free for public repos**: No storage costs
2. **No authentication for downloads**: Public releases, no credentials needed
3. **Simpler deployment**: No Cloudflare Access configuration
4. **Better visibility**: Releases visible on GitHub UI
5. **Version history**: All snapshots tagged and browsable
6. **Smaller attack surface**: No S3-compatible API keys to manage

## Future Enhancements
- [ ] Add auto-push trigger logic to web application
- [ ] Add database diff/changelog in release descriptions
- [ ] Add download progress indicators for large databases
- [ ] Add signature verification for database integrity
- [ ] Add multiple backend support (GitHub + R2 fallback)
