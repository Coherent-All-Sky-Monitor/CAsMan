# Database Backup & Synchronization

CAsMan provides a robust cloud-based database backup and synchronization system designed for zero data loss and multi-user collaboration.

## Overview

The backup/sync system provides:

- **Automatic Backups**: Triggered on part generation and scan operations
- **Versioned Storage**: Keep multiple backup versions with timestamps
- **Cloud Storage**: Cloudflare R2 (recommended) or AWS S3
- **Zero Data Loss**: Critical operations automatically backed up
- **Multi-User Safe**: Timestamp-based versioning prevents conflicts
- **Offline-First**: Graceful degradation when offline

## Architecture

```
┌─────────────────────────────────────────┐
│  Local Development/Production Machine   │
│  ┌────────────────────────────────┐    │
│  │  CAsMan Package                │    │
│  │  - parts.db (340 KB)           │    │
│  │  - assembled_casm.db (<10 MB)  │    │
│  └────────────────────────────────┘    │
│           ↕ (auto backup/sync)          │
└─────────────────────────────────────────┘
                    ↕
        ┌───────────────────────┐
        │   Cloudflare R2       │
        │   Bucket: casman-db   │
        │                       │
        │  Versioned Backups:   │
        │  - parts.db           │
        │  - assembled.db       │
        │  - timestamped copies │
        └───────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│  Field Sites / Antenna App Users       │
│  ┌────────────────────────────────┐    │
│  │  Auto-sync on install          │    │
│  │  Manual sync via CLI           │    │
│  │  Offline-capable               │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## Setup Instructions

### 1. Create Cloudflare R2 Bucket

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to **R2 Object Storage**
3. Click **Create bucket**
4. Name it `casman-databases` (or your preferred name)
5. Choose a location close to your primary site

### 2. Generate R2 API Credentials

1. In R2 dashboard, go to **Manage R2 API Tokens**
2. Click **Create API Token**
3. Set permissions: **Object Read & Write**
4. Apply to bucket: `casman-databases`
5. Save the credentials:
   - Account ID
   - Access Key ID
   - Secret Access Key

### 3. Configure CAsMan

Option A: **Environment Variables** (Recommended for security)

```bash
export R2_ACCOUNT_ID="your-account-id"
export R2_ACCESS_KEY_ID="your-access-key-id"
export R2_SECRET_ACCESS_KEY="your-secret-access-key"
export R2_BUCKET_NAME="casman-databases"
```

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# CAsMan R2 Configuration
export R2_ACCOUNT_ID="your-account-id"
export R2_ACCESS_KEY_ID="your-access-key-id"
export R2_SECRET_ACCESS_KEY="your-secret-access-key"
export R2_BUCKET_NAME="casman-databases"
```

Option B: **config.yaml** (Less secure, not recommended for production)

Edit `config.yaml`:

```yaml
r2:
  account_id: your-account-id
  access_key_id: your-access-key-id
  secret_access_key: your-secret-access-key
  bucket_name: casman-databases
```

### 4. Install boto3

```bash
pip install boto3
```

Or update requirements:

```bash
pip install -r requirements.txt
```

### 5. Verify Configuration

```bash
casman sync status
```

Expected output:

```
Database Sync Status
================================================================================

Configuration:
  Enabled:              True
  Backend:              r2
  Bucket:               casman-databases
  Keep Versions:        10
  Backup on Scans:      Every 10 scans
  Backup on Time:       Every 24.0 hours

Backend Status:
  ✓ R2 backend initialized
  Endpoint:             https://your-account.r2.cloudflarestorage.com

Local Databases:
  parts.db                 340.0 KB  ✓
  assembled_casm.db         45.2 KB  ✓

Scan Tracker:
  Scans since backup:   0
  Last backup:          Never
  Status:               OK (10 scans until backup)
```

## Usage

### Automatic Backups

Backups are triggered automatically:

1. **After Part Generation**: Every time you generate parts
   ```bash
   casman parts add ANTENNA 10 1
   # → Automatic backup after parts created
   ```

2. **After Scans**: Every 10 scans OR every 24 hours (whichever comes first)
   ```bash
   casman scan connection
   # → After 10 scans, automatic backup
   ```

**Configuration** (in `config.yaml`):

```yaml
database:
  sync:
    backup_on_scan_count: 10      # Backup every N scans
    backup_on_hours: 24.0          # Backup every N hours
```

### Manual Backup

Backup both databases:

```bash
casman sync backup
```

Backup specific database:

```bash
casman sync backup --parts           # Only parts.db
casman sync backup --assembled       # Only assembled_casm.db
```

### List Backups

View all available backups:

```bash
casman sync list
```

Filter by database:

```bash
casman sync list --db parts.db
```

Example output:

```
Available Backups (5):
================================================================================

backups/parts.db/20241208_143022_parts.db
  Database:    parts.db
  Timestamp:   2024-12-08 14:30:22 UTC
  Size:        340.5 KB
  Records:     258
  Operation:   Generated 10 ANTENNA P1 parts
  Checksum:    a3f2d8e9c1b4...

backups/parts.db/20241208_120015_parts.db
  Database:    parts.db
  Timestamp:   2024-12-08 12:00:15 UTC
  Size:        335.2 KB
  Records:     248
  Operation:   Scan-triggered backup (10 scans)
  Checksum:    b7e1c4f6a8d2...
```

### Restore from Backup

List backups first to find the key:

```bash
casman sync list
```

Restore specific backup:

```bash
casman sync restore backups/parts.db/20241208_143022_parts.db
```

**Safety Features:**
- Creates a safety backup of current database before restoring
- Validates database integrity after download
- Atomic operation (no partial restores)

Skip safety backup (not recommended):

```bash
casman sync restore <backup-key> --no-backup
```

### Sync from Remote

Download latest versions from remote storage:

```bash
casman sync sync
```

Sync specific database:

```bash
casman sync sync --parts           # Only parts.db
casman sync sync --assembled       # Only assembled_casm.db
```

Force download (even if up to date):

```bash
casman sync sync --force
```

**Smart Sync:**
- Compares checksums
- Only downloads if remote is newer
- No unnecessary bandwidth usage

### Check Sync Status

```bash
casman sync status
```

Shows:
- Configuration settings
- Backend status
- Local database status
- Remote sync status
- Scan tracker status
- R2 quota usage (if using R2)

### Maintain Storage Class (R2 Only)

**IMPORTANT**: Run at least once per month to keep backups in free tier:

```bash
casman sync maintain
```

This touches all backup objects to prevent automatic transition to Infrequent Access storage (which costs money).

**Why this matters:**
- R2 may move inactive objects to Infrequent Access storage
- Infrequent Access is NOT free tier eligible
- Has retrieval fees and minimum storage duration
- Standard storage (free tier) requires regular access

**Automate it** (recommended):
```bash
# Add to crontab - weekly on Sunday at 2am
0 2 * * 0 /path/to/casman sync maintain >> /var/log/casman-maintain.log 2>&1
```

## Configuration Options

Full configuration in `config.yaml`:

```yaml
database:
  sync:
    # Enable/disable cloud backup and sync
    enabled: true
    
    # Backend: 'r2' (Cloudflare R2), 's3' (AWS S3), or 'disabled'
    backend: r2
    
    # Auto-sync on package install (not on every import)
    auto_sync_on_import: false
    
    # Cache TTL in seconds (1 hour = 3600)
    cache_ttl_seconds: 3600
    
    # Number of backup versions to keep
    keep_versions: 10
    
    # Backup triggers
    backup_on_scan_count: 10      # Backup every N scans
    backup_on_hours: 24.0          # Backup every N hours (if scans occurred)

# Cloudflare R2 configuration
r2:
  account_id: ${R2_ACCOUNT_ID}           # Use environment variables
  access_key_id: ${R2_ACCESS_KEY_ID}
  secret_access_key: ${R2_SECRET_ACCESS_KEY}
  bucket_name: casman-databases
  region: auto
```

## Multi-User Workflow

### Scenario: Multiple People Scanning

1. **Person A** generates parts:
   ```bash
   casman parts add ANTENNA 10 1
   # → Automatic backup to R2
   ```

2. **Person B** (at different site) syncs:
   ```bash
   casman sync sync
   # → Downloads latest parts.db
   ```

3. **Person B** scans parts:
   ```bash
   casman scan connection
   # → After 10 scans, automatic backup
   ```

4. **Person A** syncs:
   ```bash
   casman sync sync
   # → Gets latest assembly data
   ```

### Best Practices

1. **Sync before major work**: `casman sync sync`
2. **Let automatic backups happen**: They trigger on critical operations
3. **Manual backup before risky operations**: `casman sync backup`
4. **Check status regularly**: `casman sync status`

## Offline Work

The system is designed to work offline:

1. **Import works offline**: Package import doesn't fail if no connection
2. **Operations continue**: Scanning and parts generation work normally
3. **Backups queue**: Will catch up when connection restored
4. **Sync is optional**: Explicit `casman sync sync` command

Enable offline mode by disabling auto-sync:

```yaml
database:
  sync:
    enabled: false  # Disable for offline work
```

Or via environment:

```bash
export CASMAN_SYNC_ENABLED=false
```

## Troubleshooting

### "Storage backend not available"

**Problem**: boto3 not installed or credentials not configured

**Solution**:
```bash
pip install boto3
export R2_ACCOUNT_ID="..."
export R2_ACCESS_KEY_ID="..."
export R2_SECRET_ACCESS_KEY="..."
```

### "No backups found"

**Problem**: No backups have been created yet

**Solution**: Create first backup manually:
```bash
casman sync backup
```

### "Sync failed (Continuing with local databases)"

**Problem**: No internet connection or R2 credentials expired

**Solution**:
- Check internet connection
- Verify credentials: `casman sync status`
- Work offline, sync later

### Backups not triggering automatically

**Problem**: Scan count or time threshold not reached

**Solution**: Check status:
```bash
casman sync status
# Shows: "5 scans until backup"
```

Or trigger manually:
```bash
casman sync backup
```

## Cost Estimation (Cloudflare R2)

For databases < 10 MB:

### Storage Costs
- **10 MB storage**: $0.00015/month ($0.015/GB)
- **10 versions × 10 MB**: $0.0015/month
- **Annual**: ~$0.02/year

### Operation Costs
- **Writes (backups)**: $4.50 per million
- **Reads (syncs)**: FREE (Class A operations)
- **Egress**: FREE (no bandwidth charges)

### Example Usage
- 100 backups/month: $0.00045/month
- Unlimited syncs: FREE
- **Total**: ~$0.02/year

**R2 is extremely cost-effective for this use case.**

## Security Best Practices

1. **Use Environment Variables**: Don't commit credentials to git
2. **Restrict R2 Token Permissions**: Only Object Read & Write
3. **Use Bucket-Specific Tokens**: Don't use account-wide tokens
4. **Rotate Credentials**: Periodically regenerate API tokens
5. **Add .gitignore**:
   ```
   # Ignore local config with credentials
   config.local.yaml
   ```

## AWS S3 (Alternative)

To use AWS S3 instead of R2:

1. **Create S3 Bucket**:
   - Name: `casman-databases`
   - Region: `us-west-2` (or closest)

2. **Configure**:
   ```yaml
   database:
     sync:
       backend: s3
   
   # AWS credentials (or use AWS CLI)
   r2:  # Same config section works for S3
     access_key_id: ${AWS_ACCESS_KEY_ID}
     secret_access_key: ${AWS_SECRET_ACCESS_KEY}
     bucket_name: casman-databases
     region: us-west-2
   ```

3. **Note**: S3 has egress fees (~$0.09/GB), unlike R2

## Antenna App Auto-Sync

For field sites using the antenna app:

1. **On Install** (one-time sync):
   ```bash
   CASMAN_AUTO_SYNC_ON_INSTALL=true pip install -e .
   # → Automatically syncs databases on first import
   ```

2. **Manual Sync** (before field work):
   ```bash
   casman sync sync
   ```

3. **Offline Work**: Package works without sync
   - Local databases are cached
   - Sync when back online

## Summary

The CAsMan database backup system provides:

✅ **Zero Data Loss**: Automatic backups on critical operations  
✅ **Multi-User Safe**: Versioned backups prevent conflicts  
✅ **Affordable**: ~$0.02/year with Cloudflare R2  
✅ **Offline-First**: Works without internet connection  
✅ **Easy Setup**: 5-minute configuration  
✅ **Flexible**: Manual and automatic backup options  

For questions or issues, check `casman sync status` first.
