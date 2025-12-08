# R2 Free Tier Quota Enforcement

## Overview

CAsMan enforces Cloudflare R2 free tier limits to ensure you **NEVER exceed** the free tier quotas. The system tracks usage and automatically blocks operations that would exceed limits.

## Free Tier Limits

| Resource | Limit | Monthly Reset |
|----------|-------|---------------|
| **Storage** | 10 GB | No (cumulative) |
| **Class A Operations** | 1,000,000 | Yes |
| **Class B Operations** | 10,000,000 | Yes |

### Operation Classification

**Class A (Write Operations - 1M/month):**
- Upload backups (PUT)
- List backups (LIST)
- Delete old backups (DELETE)

**Class B (Read Operations - 10M/month):**
- Download/restore backups (GET)
- Check backup existence (HEAD)
- Sync operations (HEAD per file)

## Enforcement Thresholds

The system uses two thresholds to protect against quota violations:

### Warning Threshold (80%)
- Logs warning messages
- Operations still allowed
- Displays ⚠ in status output

### Blocking Threshold (95%)
- **Blocks all operations** that would use that quota
- Raises `QuotaExceededError`
- Displays ✗ in status output
- Prevents accidental overages

## Storage Class Maintenance

**IMPORTANT**: R2 may automatically transition objects that aren't accessed to **Infrequent Access** storage, which:
- ❌ Costs money (NOT free tier eligible)
- ❌ Has data retrieval fees ($0.01/GB)
- ❌ Has 30-day minimum storage duration
- ❌ Higher operation costs

To prevent this, CAsMan provides a maintenance command that **touches all backup objects** to maintain their access pattern:

```bash
# Run at least once per month (recommended: weekly)
casman sync maintain
```

This performs HEAD requests (Class B operations) on all backups to keep them in Standard storage (free tier eligible).

**Automation Recommended**:
```bash
# Add to crontab (weekly on Sunday at 2am)
0 2 * * 0 /path/to/casman sync maintain >> /var/log/casman-maintain.log 2>&1
```

## How It Works

### 1. Quota Tracking

The `QuotaTracker` class maintains a persistent state file:
```
database/.r2_quota_tracker.json
```

This file tracks:
- `total_storage_bytes`: Cumulative storage used
- `class_a_ops_month`: Class A operations this month
- `class_b_ops_month`: Class B operations this month
- `backups_this_month`: Number of backups created
- `restores_this_month`: Number of restores performed
- `last_reset`: Timestamp of last monthly reset

### 2. Automatic Monthly Reset

Operation counters automatically reset on the first operation after a month boundary:
```python
# Example: January 15 → February 1
# First operation in February resets class_a_ops_month and class_b_ops_month to 0
```

Storage is **cumulative** and does not reset (deleted backups reduce storage count).

### 3. Pre-Operation Checks

Before any R2 operation:
```python
# Example: Before uploading backup
quota_tracker.check_quota(config["quota_limits"], operation="backup")
# Raises QuotaExceededError if at 95% or above
```

### 4. Post-Operation Recording

After successful operations:
```python
# Example: After uploading 1 MB backup
quota_tracker.record_backup(size_bytes=1048576)
# Updates total_storage_bytes and class_a_ops_month
```

## Usage Examples

### Check Current Quota Status

```bash
casman sync status
```

Output:
```
R2 Free Tier Quota Usage:
  Storage:              ✓ 2.34 / 10 GB (23.4%)
  Class A Ops (writes): ⚠ 850,000 / 1,000,000 (85.0%)
  Class B Ops (reads):  ✓ 1,234,567 / 10,000,000 (12.3%)
  Backups this month:   850
  Restores this month:  12
```

### What Happens at 95% Threshold

```bash
$ casman sync backup parts.db
Error: R2 quota limit reached: 95.3% of Class A operations used.
Operation 'backup' blocked to prevent exceeding free tier limits.
Storage: 3.45/10 GB, Class A: 953,000/1,000,000, Class B: 234,567/10,000,000
```

### Manual Backup with Quota Check

```python
from casman.database.sync import DatabaseSyncManager

sync = DatabaseSyncManager()
try:
    result = sync.backup_database("parts.db")
    print(f"Backup created: {result['backup_name']}")
except QuotaExceededError as e:
    print(f"Cannot backup: {e}")
```

## Configuration

In `config.yaml`:

```yaml
database:
  sync:
    r2:
      quota_limits:
        storage_gb: 10.0              # 10 GB storage limit
        class_a_operations: 1000000   # 1M Class A ops/month
        class_b_operations: 10000000  # 10M Class B ops/month
        warn_threshold: 0.8           # Warn at 80%
        block_threshold: 0.95         # Block at 95%
```

## Best Practices

### 1. Monitor Usage Regularly

```bash
# Check quota status daily
casman sync status
```

### 2. Optimize Backup Frequency

```yaml
# Instead of every scan, use time-based backups
backup_on_scans: 50      # Only backup every 50 scans
backup_on_hours: 24      # Or once per day
```

### 3. Limit Backup Retention

```yaml
# Keep fewer versions to reduce storage
keep_versions: 5         # Keep only 5 versions per database
```

### 4. Use Sync Wisely

```bash
# Sync only when needed, not continuously
casman sync sync        # Manual sync when required
```

### 5. Plan for Month-End

Class A and Class B operations reset monthly. If you're near limits:
- Wait until next month for non-critical operations
- Prioritize critical backups
- Reduce sync frequency

## Expected Usage Patterns

### Small Shop (1-2 users)
- **Storage**: ~500 MB (50 backups × 10 MB each)
- **Class A ops**: ~1,500/month (50 backups + lists)
- **Class B ops**: ~500/month (occasional restores)
- **Result**: ✓ Well within limits

### Medium Shop (5-10 users)
- **Storage**: ~2 GB (200 backups × 10 MB each)
- **Class A ops**: ~6,000/month (200 backups + lists)
- **Class B ops**: ~2,000/month (occasional restores/syncs)
- **Result**: ✓ Comfortably within limits

### Large Shop (20+ users)
- **Storage**: ~5 GB (500 backups × 10 MB each)
- **Class A ops**: ~15,000/month (500 backups + lists)
- **Class B ops**: ~5,000/month (frequent syncs)
- **Result**: ✓ Still well below limits

### When You Might Hit Limits

**Class A Operations** (most likely to hit):
- Backing up on **every scan** with high scan volume
- Running frequent list operations
- Solution: Increase `backup_on_scans` to 20-50

**Storage** (unlikely):
- Keeping too many versions (>50 per database)
- Solution: Reduce `keep_versions` to 5-10

**Class B Operations** (very unlikely):
- Constantly syncing across many machines
- Solution: Use time-based sync (every 6-12 hours)

## Troubleshooting

### Quota Exceeded Error

**Symptom:**
```
QuotaExceededError: R2 quota limit reached: 95.3% of Class A operations used
```

**Solutions:**
1. Wait until next month for operations to reset
2. Check current usage: `casman sync status`
3. Reduce backup frequency in `config.yaml`
4. Manually clean old backups if storage is full

### Quota Tracker Not Resetting

**Symptom:**
```
Class A Ops shows high percentage at start of month
```

**Solution:**
```bash
# Check last reset date
casman sync status

# Quota tracker auto-resets on first operation of new month
# Just perform any operation (backup/list/etc)
```

### False Quota Readings

**Symptom:**
```
Quota shows 0% but backups exist
```

**Solution:**
```bash
# Quota tracker initializes on first use
# Perform a list operation to sync state
casman sync list

# Or manually reset tracker (USE WITH CAUTION)
rm database/.r2_quota_tracker.json
casman sync status  # Recreates with current state
```

## Technical Details

### Quota Calculation

```python
# Storage usage
storage_gb = total_storage_bytes / (1024**3)
storage_usage = storage_gb / 10.0  # Percent of 10 GB

# Class A usage
class_a_usage = class_a_ops_month / 1_000_000  # Percent of 1M

# Class B usage
class_b_usage = class_b_ops_month / 10_000_000  # Percent of 10M
```

### Monthly Reset Logic

```python
def _check_monthly_reset(self):
    """Reset monthly counters if new month."""
    last_reset = datetime.fromisoformat(self.data["last_reset"])
    now = datetime.now()
    
    # Different month or year
    if now.month != last_reset.month or now.year != last_reset.year:
        self.data["class_a_ops_month"] = 0
        self.data["class_b_ops_month"] = 0
        self.data["backups_this_month"] = 0
        self.data["restores_this_month"] = 0
        self.data["last_reset"] = now.isoformat()
        self._save()
```

### Operation Type Detection

```python
# Backup: Uses storage + Class A
check_usage = max(storage_usage, class_a_usage)

# Restore/Sync: Uses Class B
check_usage = class_b_usage

# List: Uses Class A
check_usage = class_a_usage
```

## Summary

The quota enforcement system ensures CAsMan **never exceeds** R2 free tier limits by:

1. ✓ **Tracking** all storage and operations
2. ✓ **Warning** at 80% usage
3. ✓ **Blocking** at 95% usage
4. ✓ **Auto-resetting** monthly counters
5. ✓ **Displaying** real-time quota status

This protection is **always active** and requires no manual intervention. Just monitor with `casman sync status` periodically to ensure healthy usage patterns.
