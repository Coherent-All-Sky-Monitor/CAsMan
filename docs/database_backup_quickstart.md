# Database Backup Quick Start

Get your CAsMan database backup system up and running in 5 minutes.

## Step 1: Install Dependencies

```bash
pip install boto3
```

## Step 2: Create Cloudflare R2 Bucket

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com) → **R2 Object Storage**
2. Click **Create bucket** → Name it `casman-databases`
3. **Enable Public Access** (for read-only downloads):
   - Go to bucket **Settings**
   - Under **Public Access** → Click **Connect Domain** or **Allow Access**
   - Copy the public URL (e.g., `https://pub-xxxxx.r2.dev`)
   - This allows users to download databases without credentials
   - **Add to config.yaml**:
     ```yaml
     r2:
       public_urls:
         parts_db: "https://pub-xxxxx.r2.dev/backups/parts.db/latest_parts.db"
         assembled_db: "https://pub-xxxxx.r2.dev/backups/assembled_casm.db/latest_assembled_casm.db"
     ```
4. Go to **Manage R2 API Tokens** → **Create API Token**
5. Set permissions: **Object Read & Write** for `casman-databases`
6. Save the credentials shown (needed for uploads/backups only)

## Step 3: Configure Credentials

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# CAsMan R2 Backup
export R2_ACCOUNT_ID="your-account-id-here"
export R2_ACCESS_KEY_ID="your-access-key-here"
export R2_SECRET_ACCESS_KEY="your-secret-key-here"
```

Reload your shell:

```bash
source ~/.zshrc
```

## Step 4: Verify Setup

```bash
casman sync status
```

Should show:

```
Backend Status:
  ✓ R2 backend initialized
```

## Step 5: Create First Backup

```bash
casman sync backup
```

## Done!

Your databases will now automatically backup:
- After generating parts
- Every 10 scans OR every 24 hours

### Common Commands

```bash
# Manual backup
casman sync backup

# List backups
casman sync list

# Sync from remote
casman sync sync

# Check status
casman sync status

# Restore from backup
casman sync restore <backup-key>

# Keep in Standard storage (run monthly)
casman sync maintain
```

### Monthly Maintenance (IMPORTANT)

To keep backups in the free tier, run this **at least once per month**:

```bash
casman sync maintain
```

This prevents automatic transition to paid Infrequent Access storage.

**Automate it** (recommended - add to crontab):
```bash
# Weekly on Sunday at 2am
0 2 * * 0 /path/to/casman sync maintain >> /var/log/casman-maintain.log 2>&1
```

### For Field Sites

Sync latest databases:

```bash
casman sync sync
```

Work offline - sync when back online.

---

**Full documentation**: See `docs/database_backup_sync.md`
