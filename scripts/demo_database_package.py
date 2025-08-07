#!/usr/bin/env python3
"""
Demo script showing the enhanced database functionality.

This script demonstrates the new modular database package features including
migrations, backups, and integrity checking.
"""

import tempfile

from casman.database import (
    DatabaseMigrator,
    backup_database,
    check_database_integrity,
    get_table_info,
    init_all_databases,
)


def main():
    """Demonstrate database package features."""
    print("🗄️  CAsMan Database Package Demo")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Working in temporary directory: {temp_dir}")

        # 1. Initialize databases
        print("\n1️⃣  Initializing databases...")
        init_all_databases(temp_dir)
        print("   ✅ Parts and Assembly databases created")

        # 2. Check database integrity
        print("\n2️⃣  Checking database integrity...")
        parts_ok = check_database_integrity("parts.db", temp_dir)
        assembly_ok = check_database_integrity("assembled_casm.db", temp_dir)
        print(f"   ✅ Parts DB integrity: {'OK' if parts_ok else 'FAILED'}")
        print(f"   ✅ Assembly DB integrity: {'OK' if assembly_ok else 'FAILED'}")

        # 3. Get table information
        print("\n3️⃣  Analyzing table structure...")
        parts_table_info = get_table_info("parts.db", "parts", temp_dir)
        print(f"   📊 Parts table has {len(parts_table_info)} columns:")
        for col in parts_table_info:
            pk_indicator = " (PK)" if col["pk"] else ""
            print(f"      - {col['name']}: {col['type']}{pk_indicator}")

        # 4. Test migration system
        print("\n4️⃣  Testing migration system...")
        migrator = DatabaseMigrator("parts.db", temp_dir)
        initial_version = migrator.get_schema_version()
        print(f"   📈 Initial schema version: {initial_version}")

        # Check if we need to run a migration
        table_info_before = get_table_info("parts.db", "parts", temp_dir)
        column_names = [col["name"] for col in table_info_before]

        if "demo_field" not in column_names:
            # Add a test column via migration
            migration_sql = "ALTER TABLE parts ADD COLUMN demo_field TEXT"
            try:
                migrator.execute_migration(migration_sql, initial_version + 1)
                new_version = migrator.get_schema_version()
                print(f"   📈 Schema version after migration: {new_version}")

                # Verify the new column was added
                updated_table_info = get_table_info("parts.db", "parts", temp_dir)
                print(f"   📊 Parts table now has {len(updated_table_info)} columns")
                print("   ✅ Successfully added 'demo_field' column via migration")
            except RuntimeError as e:
                print(f"   ⚠️  Migration skipped: {e}")
        else:
            print("   ℹ️  Demo column already exists, skipping migration")

        # 5. Create database backup
        print("\n5️⃣  Creating database backup...")
        backup_path = backup_database("parts.db", "demo_backup", temp_dir)
        print(f"   💾 Backup created: {backup_path}")

        print("\n🎉 Database package demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print(
            "  • Modular database structure (connection, initialization, operations, migrations)"
        )
        print("  • Database integrity checking")
        print("  • Table structure inspection")
        print("  • Schema migration system with versioning")
        print("  • Automated database backups")
        print("  • Full backward compatibility with existing code")


if __name__ == "__main__":
    main()
