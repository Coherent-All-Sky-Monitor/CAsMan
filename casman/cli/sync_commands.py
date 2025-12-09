"""
Database synchronization commands for CAsMan CLI.

This module provides CLI commands for database backup and sync operations:
- backup: Manually backup databases to cloud storage
- restore: Restore databases from backups
- list: List available backups
- sync: Sync databases with remote storage
- status: Show sync status and configuration
"""

import argparse
import sys
from datetime import datetime, timezone
from typing import Optional

import argcomplete


def cmd_sync() -> None:
    """
    Database sync command handler.

    Provides sub-commands for database backup and synchronization:
    - backup: Manually backup databases
    - restore: Restore from a backup
    - list: List available backups
    - sync: Sync with remote storage
    - status: Show sync configuration and status
    """
    args_to_parse = sys.argv[1:]
    if args_to_parse and args_to_parse[0] == "sync":
        args_to_parse = args_to_parse[1:]

    parser = argparse.ArgumentParser(
        description="CAsMan Database Backup & Sync\n\n"
        "Cloud-based database backup and synchronization for parts.db and assembled_casm.db.\n"
        "Supports Cloudflare R2 and AWS S3 backends with versioned backups.\n\n"
        "Subcommands:\n"
        "  backup  - Manually backup databases to cloud storage\n"
        "  restore - Restore databases from a backup\n"
        "  list    - List available backups\n"
        "  sync    - Sync databases with remote storage\n"
        "  status  - Show sync configuration and status\n\n"
        "Examples:\n"
        "  casman sync backup                    # Backup both databases\n"
        "  casman sync backup --parts            # Backup only parts.db\n"
        "  casman sync list                      # List all backups\n"
        "  casman sync restore <backup-key>      # Restore from specific backup\n"
        "  casman sync sync                      # Download latest versions\n"
        "  casman sync status                    # Show configuration\n\n"
        "Configuration:\n"
        "- Set R2 credentials via environment variables or config.yaml\n"
        "- R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY\n"
        "- Automatic backups trigger on part generation and scans",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog="casman sync",
    )

    subparsers = parser.add_subparsers(
        dest="subcommand", help="Sync operation to perform", metavar="SUBCOMMAND"
    )

    # Backup subcommand
    backup_parser = subparsers.add_parser(
        "backup",
        help="Manually backup databases to cloud storage",
        description="Upload databases to cloud storage with versioning.\n"
        "By default backs up both databases unless specific options are used.\n\n"
        "Features:\n"
        "- Versioned backups with timestamps\n"
        "- Automatic cleanup of old versions\n"
        "- Checksum validation\n"
        "- Metadata tracking (record counts, operations)\n\n"
        "Examples:\n"
        "  casman sync backup                    # Backup both databases\n"
        "  casman sync backup --parts            # Only parts.db\n"
        "  casman sync backup --assembled        # Only assembled_casm.db",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    backup_parser.add_argument(
        "--parts", action="store_true", help="Backup only parts.db"
    )
    backup_parser.add_argument(
        "--assembled", action="store_true", help="Backup only assembled_casm.db"
    )

    # Restore subcommand
    restore_parser = subparsers.add_parser(
        "restore",
        help="Restore database from a backup",
        description="Download and restore a database from a specific backup.\n"
        "Creates a safety backup of the current database before restoring.\n\n"
        "Features:\n"
        "- Safety backup before restore\n"
        "- Integrity validation\n"
        "- Atomic operations (no partial restores)\n\n"
        "Examples:\n"
        "  casman sync list                                     # Find backup key\n"
        "  casman sync restore backups/parts.db/20241208_143022_parts.db",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    restore_parser.add_argument(
        "backup_key", type=str, help="S3 key of the backup to restore"
    )
    restore_parser.add_argument(
        "--dest",
        type=str,
        help="Destination path (default: detected from backup key)",
    )
    restore_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip safety backup of current database",
    )

    # List subcommand
    list_parser = subparsers.add_parser(
        "list",
        help="List available backups",
        description="Display all available backups with metadata.\n\n"
        "Shows:\n"
        "- Backup timestamps\n"
        "- Database sizes\n"
        "- Record counts\n"
        "- Operations that triggered the backup\n\n"
        "Examples:\n"
        "  casman sync list                      # All backups\n"
        "  casman sync list --db parts.db        # Only parts.db backups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    list_parser.add_argument(
        "--db",
        type=str,
        choices=["parts.db", "assembled_casm.db"],
        help="Filter by database name",
    )

    # Sync subcommand
    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync databases with remote storage",
        description="Download latest versions of databases from remote storage.\n"
        "Only downloads if remote version is newer than local.\n\n"
        "Features:\n"
        "- Checksum-based change detection\n"
        "- No unnecessary downloads\n"
        "- Offline-safe (fails gracefully)\n\n"
        "Examples:\n"
        "  casman sync sync                      # Sync both databases\n"
        "  casman sync sync --parts              # Only parts.db\n"
        "  casman sync sync --force              # Force download",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sync_parser.add_argument(
        "--parts", action="store_true", help="Sync only parts.db"
    )
    sync_parser.add_argument(
        "--assembled", action="store_true", help="Sync only assembled_casm.db"
    )
    sync_parser.add_argument(
        "--force", action="store_true", help="Force sync even if up to date"
    )

    # Status subcommand
    status_parser = subparsers.add_parser(
        "status",
        help="Show sync configuration and status",
        description="Display current sync configuration and database status.\n\n"
        "Shows:\n"
        "- Backend configuration (R2/S3)\n"
        "- Local database status\n"
        "- Remote sync status\n"
        "- Scan tracker status\n"
        "- Configuration settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Maintain subcommand
    maintain_parser = subparsers.add_parser(
        "maintain",
        help="Maintain R2 Standard storage class",
        description="Touch all backup objects to keep them in Standard storage class.\n\n"
        "R2 may automatically transition objects that aren't accessed to\n"
        "Infrequent Access storage, which:\n"
        "- Costs money (not free tier eligible)\n"
        "- Has retrieval fees\n"
        "- Has 30-day minimum storage duration\n\n"
        "This command performs HEAD requests on all backup objects to\n"
        "maintain their access pattern and keep them in Standard storage.\n\n"
        "Run this at least once per month (recommended: weekly).\n\n"
        "Examples:\n"
        "  casman sync maintain                  # Touch all backups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    argcomplete.autocomplete(parser)

    args, _ = parser.parse_known_args(args_to_parse)

    if args.subcommand is None:
        parser.print_help()
        return

    # Route to appropriate subcommand
    if args.subcommand == "backup":
        backup_args = []
        if "backup" in args_to_parse:
            backup_index = args_to_parse.index("backup")
            backup_args = args_to_parse[backup_index + 1 :]
        cmd_sync_backup(backup_parser, backup_args)
    elif args.subcommand == "restore":
        restore_args = []
        if "restore" in args_to_parse:
            restore_index = args_to_parse.index("restore")
            restore_args = args_to_parse[restore_index + 1 :]
        cmd_sync_restore(restore_parser, restore_args)
    elif args.subcommand == "list":
        list_args = []
        if "list" in args_to_parse:
            list_index = args_to_parse.index("list")
            list_args = args_to_parse[list_index + 1 :]
        cmd_sync_list(list_parser, list_args)
    elif args.subcommand == "sync":
        sync_args = []
        if "sync" in args_to_parse:
            # Find the second occurrence of "sync"
            indices = [i for i, x in enumerate(args_to_parse) if x == "sync"]
            if len(indices) > 1:
                sync_args = args_to_parse[indices[1] + 1 :]
        cmd_sync_sync(sync_parser, sync_args)
    elif args.subcommand == "status":
        cmd_sync_status()
    elif args.subcommand == "maintain":
        cmd_sync_maintain()
    else:
        parser.print_help()


def cmd_sync_backup(parser: argparse.ArgumentParser, remaining_args: list) -> None:
    """Handle sync backup subcommand."""
    args = parser.parse_args(remaining_args)

    from ..database.connection import get_database_path
    from ..database.sync import DatabaseSyncManager

    try:
        sync_manager = DatabaseSyncManager()

        if not sync_manager.config.enabled:
            print("✗ Sync is disabled in configuration")
            print("  Enable in config.yaml or set CASMAN_SYNC_ENABLED=true")
            sys.exit(1)

        if sync_manager.backend is None:
            print("✗ Storage backend not available")
            print("  Please configure R2/S3 credentials")
            sys.exit(1)

        # Determine which databases to backup
        backup_parts = args.parts or not args.assembled
        backup_assembled = args.assembled or not args.parts

        results = []

        if backup_parts:
            print("Backing up parts.db...")
            db_path = get_database_path("parts.db")
            metadata = sync_manager.backup_database(
                db_path, "parts.db", operation="Manual CLI backup"
            )
            if metadata:
                results.append(("parts.db", metadata))
            else:
                print("✗ Failed to backup parts.db")

        if backup_assembled:
            print("Backing up assembled_casm.db...")
            db_path = get_database_path("assembled_casm.db")
            metadata = sync_manager.backup_database(
                db_path, "assembled_casm.db", operation="Manual CLI backup"
            )
            if metadata:
                results.append(("assembled_casm.db", metadata))
            else:
                print("✗ Failed to backup assembled_casm.db")

        if results:
            print(f"\n✓ Successfully backed up {len(results)} database(s)")
        else:
            print("\n✗ No databases were backed up")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Backup failed: {e}")
        sys.exit(1)


def cmd_sync_restore(parser: argparse.ArgumentParser, remaining_args: list) -> None:
    """Handle sync restore subcommand."""
    args = parser.parse_args(remaining_args)

    from ..database.connection import get_database_path
    from ..database.sync import DatabaseSyncManager

    try:
        sync_manager = DatabaseSyncManager()

        if not sync_manager.config.enabled or sync_manager.backend is None:
            print("✗ Storage backend not available")
            sys.exit(1)

        # Determine destination path
        if args.dest:
            dest_path = args.dest
        else:
            # Infer from backup key
            if "parts.db" in args.backup_key:
                dest_path = get_database_path("parts.db")
            elif "assembled" in args.backup_key:
                dest_path = get_database_path("assembled_casm.db")
            else:
                print("✗ Could not determine destination. Use --dest")
                sys.exit(1)

        print(f"Restoring {args.backup_key} to {dest_path}...")

        success = sync_manager.restore_database(
            args.backup_key, dest_path, create_backup=not args.no_backup
        )

        if success:
            print(f"✓ Database restored successfully")
        else:
            print(f"✗ Restore failed")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Restore failed: {e}")
        sys.exit(1)


def cmd_sync_list(parser: argparse.ArgumentParser, remaining_args: list) -> None:
    """Handle sync list subcommand."""
    args = parser.parse_args(remaining_args)

    from ..database.sync import DatabaseSyncManager

    try:
        sync_manager = DatabaseSyncManager()

        if not sync_manager.config.enabled or sync_manager.backend is None:
            print("✗ Storage backend not available")
            sys.exit(1)

        backups = sync_manager.list_backups(args.db)

        if not backups:
            print("No backups found")
            return

        print(f"Available Backups ({len(backups)}):")
        print("=" * 80)

        for key, metadata in backups:
            print(f"\n{key}")
            print(f"  Database:    {metadata.db_name}")
            print(f"  Timestamp:   {metadata.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  Size:        {metadata.size_bytes / 1024:.1f} KB")
            if metadata.record_count is not None:
                print(f"  Records:     {metadata.record_count}")
            if metadata.operation:
                print(f"  Operation:   {metadata.operation}")
            print(f"  Checksum:    {metadata.checksum[:16]}...")

        print("\nUse 'casman sync restore <key>' to restore a backup")

    except Exception as e:
        print(f"✗ Failed to list backups: {e}")
        sys.exit(1)


def cmd_sync_sync(parser: argparse.ArgumentParser, remaining_args: list) -> None:
    """Handle sync sync subcommand."""
    args = parser.parse_args(remaining_args)

    from ..database.connection import get_database_path
    from ..database.sync import DatabaseSyncManager

    try:
        sync_manager = DatabaseSyncManager()

        if not sync_manager.config.enabled or sync_manager.backend is None:
            print("✗ Storage backend not available")
            sys.exit(1)

        # Determine which databases to sync
        sync_parts = args.parts or not args.assembled
        sync_assembled = args.assembled or not args.parts

        synced_count = 0

        if sync_parts:
            print("Checking parts.db...")
            db_path = get_database_path("parts.db")
            if sync_manager.sync_from_remote(db_path, "parts.db", force=args.force):
                synced_count += 1
            else:
                print("  (already up to date)")

        if sync_assembled:
            print("Checking assembled_casm.db...")
            db_path = get_database_path("assembled_casm.db")
            if sync_manager.sync_from_remote(
                db_path, "assembled_casm.db", force=args.force
            ):
                synced_count += 1
            else:
                print("  (already up to date)")

        if synced_count > 0:
            print(f"\n✓ Synced {synced_count} database(s)")
        else:
            print("\n✓ All databases are up to date")

    except Exception as e:
        print(f"✗ Sync failed: {e}")
        print("  (Continuing with local databases)")


def cmd_sync_status() -> None:
    """Handle sync status subcommand."""
    import os

    from ..database.connection import get_database_path
    from ..database.sync import DatabaseSyncManager, ScanTracker

    try:
        sync_manager = DatabaseSyncManager()
        config = sync_manager.config

        print("Database Sync Status")
        print("=" * 80)
        print()

        # Configuration
        print("Configuration:")
        print(f"  Enabled:              {config.enabled}")
        print(f"  Backend:              {config.backend}")
        print(f"  Bucket:               {config.bucket_name}")
        print(f"  Keep Versions:        {config.keep_versions}")
        print(f"  Backup on Scans:      Every {config.backup_on_scan_count} scans")
        print(f"  Backup on Time:       Every {config.backup_on_hours} hours")
        print()

        # Backend status
        print("Backend Status:")
        if sync_manager.backend is not None:
            print(f"  ✓ {config.backend.upper()} backend initialized")
            print(f"  Endpoint:             {config.endpoint or 'default'}")
        else:
            print(f"  ✗ Backend not available")
            if not config.access_key_id:
                print("  Missing: R2_ACCESS_KEY_ID")
            if not config.secret_access_key:
                print("  Missing: R2_SECRET_ACCESS_KEY")
        print()

        # Local database status
        print("Local Databases:")
        for db_name in ["parts.db", "assembled_casm.db"]:
            db_path = get_database_path(db_name)
            if os.path.exists(db_path):
                size = os.path.getsize(db_path) / 1024
                print(f"  {db_name:20s} {size:>8.1f} KB  ✓")
                
                # Check if needs sync
                if sync_manager.backend:
                    needs_sync = sync_manager.check_needs_sync(db_path, db_name)
                    if needs_sync:
                        print(f"                            ⚠ Newer version available remotely")
            else:
                print(f"  {db_name:20s}           ✗ Not found")
        print()

        # Scan tracker status
        print("Scan Tracker:")
        try:
            tracker = ScanTracker()
            print(f"  Scans since backup:   {tracker.data['scans_since_backup']}")
            if tracker.data['last_backup_time']:
                last_backup = datetime.fromisoformat(tracker.data['last_backup_time'])
                hours_since = (datetime.now(timezone.utc) - last_backup).total_seconds() / 3600
                print(f"  Last backup:          {hours_since:.1f} hours ago")
            else:
                print(f"  Last backup:          Never")
                
            will_trigger = tracker.should_backup(config)
            if will_trigger:
                print(f"  Status:               ⚠ Backup will trigger on next scan")
            else:
                scans_remaining = config.backup_on_scan_count - tracker.data['scans_since_backup']
                print(f"  Status:               OK ({scans_remaining} scans until backup)")
        except Exception as e:
            print(f"  Error:                {e}")
        print()
        
        # R2 Quota Usage (R2 backend only)
        if config.backend == "r2" and sync_manager.quota_tracker:
            print("R2 Free Tier Quota Usage:")
            try:
                usage = sync_manager.quota_tracker.get_usage_summary(config.quota_limits)
                
                # Storage
                storage_status = "✓" if usage["storage_percent"] < 80 else ("⚠" if usage["storage_percent"] < 95 else "✗")
                print(f"  Storage:              {storage_status} {usage['storage_gb']:.2f} / {usage['storage_limit_gb']:.0f} GB ({usage['storage_percent']:.1f}%)")
                
                # Class A operations
                class_a_status = "✓" if usage["class_a_percent"] < 80 else ("⚠" if usage["class_a_percent"] < 95 else "✗")
                print(f"  Class A Ops (writes): {class_a_status} {usage['class_a_ops']:,} / {usage['class_a_limit']:,} ({usage['class_a_percent']:.1f}%)")
                
                # Class B operations
                class_b_status = "✓" if usage["class_b_percent"] < 80 else ("⚠" if usage["class_b_percent"] < 95 else "✗")
                print(f"  Class B Ops (reads):  {class_b_status} {usage['class_b_ops']:,} / {usage['class_b_limit']:,} ({usage['class_b_percent']:.1f}%)")
                
                print(f"  Backups this month:   {usage['backups_this_month']}")
                print(f"  Restores this month:  {usage['restores_this_month']}")
                
                # Warnings
                if usage["storage_percent"] >= 95 or usage["class_a_percent"] >= 95 or usage["class_b_percent"] >= 95:
                    print()
                    print("  ✗ CRITICAL: Quota limit reached! Operations blocked at 95%.")
                    print("    Consider upgrading to paid tier or reducing backup frequency.")
                elif usage["storage_percent"] >= 80 or usage["class_a_percent"] >= 80 or usage["class_b_percent"] >= 80:
                    print()
                    print("  ⚠ WARNING: Approaching quota limits (80%). Monitor usage closely.")
                
            except Exception as e:
                print(f"  Error:                {e}")

    except Exception as e:
        print(f"✗ Error getting status: {e}")
        sys.exit(1)


def cmd_sync_maintain() -> None:
    """Handle sync maintain subcommand."""
    from casman.database.sync import DatabaseSyncManager

    print("R2 Storage Class Maintenance")
    print("=" * 80)
    print()
    
    try:
        sync_manager = DatabaseSyncManager()
        
        if not sync_manager.config.enabled:
            print("✗ Database sync is not enabled in configuration")
            print()
            print("To enable sync, set in config.yaml:")
            print("  database:")
            print("    sync:")
            print("      enabled: true")
            print("      backend: r2")
            sys.exit(1)
        
        if sync_manager.config.backend != "r2":
            print(f"✗ Maintenance only required for R2 backend (current: {sync_manager.config.backend})")
            print()
            print("S3 buckets don't have automatic storage class transitions.")
            sys.exit(0)
        
        print("Starting maintenance to keep objects in Standard storage class...")
        print("This prevents automatic transition to Infrequent Access storage.")
        print()
        
        result = sync_manager.maintain_storage_class()
        
        if result["success"]:
            print(f"✓ Maintenance complete: {result['objects_touched']} objects touched")
            print()
            print(f"  {result['message']}")
            
            # Show quota impact
            if sync_manager.quota_tracker:
                print()
                print("Quota Usage After Maintenance:")
                usage = sync_manager.quota_tracker.get_usage_summary(sync_manager.config.quota_limits)
                print(f"  Class A Ops: {usage['class_a_ops']:,} / {usage['class_a_limit']:,} ({usage['class_a_percent']:.1f}%)")
                print(f"  Class B Ops: {usage['class_b_ops']:,} / {usage['class_b_limit']:,} ({usage['class_b_percent']:.1f}%)")
            
            print()
            print("Recommendation: Run this command at least once per month.")
            print("                Consider adding to cron/systemd timer for automation.")
            
        else:
            print(f"✗ Maintenance failed: {result['error']}")
            if "Quota exceeded" in result["error"]:
                print()
                print("You're close to your R2 free tier limits.")
                print("Maintenance is still important - wait until next month or reduce backup frequency.")
            sys.exit(1)
    
    except Exception as e:
        print(f"✗ Error during maintenance: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

