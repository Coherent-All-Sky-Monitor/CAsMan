# R2 Storage Class Maintenance Guide

## The Problem

Cloudflare R2 has two storage classes:

### Standard Storage (FREE TIER ✓)
- **Free**: First 10 GB included
- **Paid**: $0.015/GB/month beyond 10 GB
- **Class A ops**: 1M/month free, then $4.50/million
- **Class B ops**: 10M/month free, then $0.36/million
- **Retrieval**: FREE
- **Minimum duration**: None

### Infrequent Access Storage (PAID ✗)
- **Free**: None (always paid)
- **Paid**: $0.01/GB/month
- **Class A ops**: $9.00/million (no free tier)
- **Class B ops**: $0.90/million (no free tier)
- **Retrieval**: $0.01/GB (always charged)
- **Minimum duration**: 30 days

## The Risk

**R2 may automatically transition objects that aren't accessed frequently to Infrequent Access storage.**

While Cloudflare's documentation doesn't explicitly state the exact inactivity threshold, industry standard for S3-compatible storage is typically:
- 30-90 days of no access → automatic transition
- Or based on lifecycle policies you may have set

**If this happens:**
- ❌ You lose free tier benefits
- ❌ Every backup costs $0.01/GB/month minimum
- ❌ Every restore costs $0.01/GB retrieval fee
- ❌ Operations cost 2-2.5x more
- ❌ 30-day minimum charge even if you delete immediately

## The Solution

**Access your backups at least once per month** to maintain Standard storage classification.

CAsMan provides the `maintain` command that performs HEAD requests on all backup objects:

```bash
casman sync maintain
```

### What This Does

1. Lists all objects in your R2 bucket (1 Class A operation)
2. Performs HEAD request on each object (1 Class B operation per object)
3. Updates the "last accessed" timestamp
4. Keeps objects in Standard storage class
5. Tracks quota usage

### Cost of Maintenance

With typical usage (20 backups):
- **Class A ops**: 1 (LIST operation)
- **Class B ops**: 20 (HEAD per backup)
- **Total monthly cost**: $0.00 (well within free tier)

Even with 100 backups:
- **Class A ops**: 1
- **Class B ops**: 100
- **Total monthly cost**: $0.00 (still free tier)

### Cost WITHOUT Maintenance

If 20 backups (200 MB total) transition to Infrequent Access:
- **Storage**: 0.2 GB × $0.01 = $0.002/month
- **Class B ops** (monthly checks): 20 × $0.90/million = negligible
- **Retrieval** (if you restore): 0.2 GB × $0.01 = $0.002 per restore

**This may seem small, but:**
1. You're no longer on the free tier
2. Costs scale with more backups
3. You pay for operations outside free tier limits
4. Defeats the purpose of using R2's free tier

## Automation

### Using Cron (Recommended)

Add to your crontab:

```bash
# Edit crontab
crontab -e

# Add this line (weekly on Sunday at 2am)
0 2 * * 0 /path/to/casman sync maintain >> /var/log/casman-maintain.log 2>&1
```

### Using Systemd Timer

Create `/etc/systemd/system/casman-maintain.service`:

```ini
[Unit]
Description=CAsMan R2 Storage Maintenance
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=casman
WorkingDirectory=/home/casman
ExecStart=/usr/local/bin/casman sync maintain
StandardOutput=append:/var/log/casman-maintain.log
StandardError=append:/var/log/casman-maintain.log
```

Create `/etc/systemd/system/casman-maintain.timer`:

```ini
[Unit]
Description=CAsMan R2 Storage Maintenance Timer
Requires=casman-maintain.service

[Timer]
OnCalendar=weekly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable casman-maintain.timer
sudo systemctl start casman-maintain.timer

# Check status
sudo systemctl status casman-maintain.timer
```

## Verification

### Check Last Maintenance

```bash
casman sync status
```

Look for:
```
R2 Free Tier Quota Usage:
  Class B Ops (reads):  ✓ 120 / 10,000,000 (0.0%)
```

If Class B ops are increasing weekly, maintenance is running.

### Check Storage Class in R2 Dashboard

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to **R2 Object Storage** → Your bucket
3. Click on any backup file
4. Look for **Storage Class**: Should show "Standard"

If it shows "Infrequent Access", run:
```bash
casman sync maintain
```

Note: Once transitioned to Infrequent Access, HEAD requests alone may not transition it back to Standard. You may need to copy the object:

```bash
# Use AWS CLI with R2 endpoint
aws s3api copy-object \
  --endpoint-url https://<ACCOUNT_ID>.r2.cloudflarestorage.com \
  --bucket casman-databases \
  --key backups/parts.db/20241208_143022_parts.db \
  --copy-source /casman-databases/backups/parts.db/20241208_143022_parts.db \
  --storage-class STANDARD
```

## Frequency Recommendations

### Minimum (Required)
- **Once per month**: Prevents automatic transition

### Recommended
- **Once per week**: Safe margin, accounts for transition policies

### Optimal
- **Twice per week**: Maximum safety with minimal quota impact

### Overkill
- **Daily**: Uses more Class B operations than necessary
- **Multiple times per day**: Wastes quota

## Quota Impact

### Weekly Maintenance (20 backups)

**Per run:**
- Class A: 1 operation
- Class B: 20 operations

**Monthly total:**
- Class A: 4 operations (0.0004% of 1M limit)
- Class B: 80 operations (0.0008% of 10M limit)

**Result:** Completely negligible quota usage.

### Weekly Maintenance (100 backups)

**Per run:**
- Class A: 1 operation
- Class B: 100 operations

**Monthly total:**
- Class A: 4 operations (0.0004% of 1M limit)
- Class B: 400 operations (0.004% of 10M limit)

**Result:** Still completely negligible.

## Troubleshooting

### "Quota exceeded" Error

If maintenance is blocked by quota limits:

```bash
# Check current usage
casman sync status
```

**Solutions:**
1. Wait until next month for quota reset
2. Reduce backup frequency to use fewer operations
3. Run maintenance less frequently (but at least monthly)

### Objects Still in Infrequent Access

If objects show Infrequent Access after maintenance:

1. **Check transition date**: Objects may have been recently transitioned
2. **Force copy to Standard**: Use the `copy-object` command above
3. **Wait 24-48 hours**: Storage class updates may be delayed

### Maintenance Command Fails

```bash
# Check backend status
casman sync status

# Verify credentials
echo $R2_ACCOUNT_ID
echo $R2_ACCESS_KEY_ID
# (Don't echo R2_SECRET_ACCESS_KEY)

# Test connection
aws s3 ls --endpoint-url https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com
```

## Summary

**DO THIS** (Required):
✓ Run `casman sync maintain` at least once per month
✓ Automate with cron or systemd timer
✓ Monitor Class B operations in `casman sync status`
✓ Verify objects stay in Standard storage class

**DON'T DO THIS**:
✗ Forget maintenance for 60+ days
✗ Assume objects will stay in Standard automatically
✗ Run maintenance more than daily (wastes quota)

**Result:**
- Stay on R2 free tier ($0/month)
- No surprise charges
- Predictable quota usage
- Peace of mind

## Additional Resources

- [Cloudflare R2 Storage Classes](https://developers.cloudflare.com/r2/buckets/storage-classes/)
- [R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [CAsMan R2 Quota Enforcement](./r2_quota_enforcement.md)
- [Database Backup Quick Start](./database_backup_quickstart.md)
