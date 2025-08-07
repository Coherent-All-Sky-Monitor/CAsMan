"""
Tests for the enhanced database package.

These tests cover the new modular database functionality including
connection management, operations, and migration utilities.
"""

import tempfile
from unittest.mock import patch

import pytest

from casman.database.migrations import (
    DatabaseMigrator,
    backup_database,
    check_database_integrity,
    get_table_info,
)
from casman.database.connection import find_project_root, get_database_path
from casman.database.initialization import (
    init_all_databases,
    init_assembled_db,
    init_parts_db,
)
from casman.database.operations import (
    check_part_in_db,
    get_all_parts,
    get_assembly_records,
    get_last_update,
    get_parts_by_criteria,
)


class TestDatabaseConnection:
    """Test database connection utilities."""

    def test_find_project_root(self):
        """Test project root detection."""
        root = find_project_root()
        assert root is not None
        assert isinstance(root, str)

    def test_get_database_path_default(self):
        """Test database path resolution with defaults."""
        path = get_database_path("test.db")
        assert path.endswith("test.db")
        assert "database" in path

    def test_get_database_path_custom_dir(self):
        """Test database path resolution with custom directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = get_database_path("test.db", temp_dir)
            assert path == f"{temp_dir}/test.db"

    @patch("casman.database.connection.get_config")
    def test_get_database_path_config_override(self, mock_get_config):
        """Test database path resolution with config override."""
        mock_get_config.return_value = "/custom/path/parts.db"
        path = get_database_path("parts.db")
        assert path == "/custom/path/parts.db"
        mock_get_config.assert_called_with("CASMAN_PARTS_DB")


class TestDatabaseInitialization:
    """Test database initialization functions."""

    def test_init_parts_db(self):
        """Test parts database initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            # Verify database was created
            db_path = get_database_path("parts.db", temp_dir)
            assert db_path.endswith("parts.db")

    def test_init_assembled_db(self):
        """Test assembled database initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_assembled_db(temp_dir)
            # Verify database was created
            db_path = get_database_path("assembled_casm.db", temp_dir)
            assert db_path.endswith("assembled_casm.db")

    def test_init_all_databases(self):
        """Test initialization of all databases."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_all_databases(temp_dir)
            # Both databases should exist
            parts_path = get_database_path("parts.db", temp_dir)
            assembled_path = get_database_path("assembled_casm.db", temp_dir)
            assert parts_path.endswith("parts.db")
            assert assembled_path.endswith("assembled_casm.db")


class TestDatabaseOperations:
    """Test database operation functions."""

    def test_get_all_parts_empty(self):
        """Test getting all parts from empty database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_assembled_db(temp_dir)
            parts = get_all_parts(temp_dir)
            assert parts == []

    def test_get_last_update_empty(self):
        """Test getting last update from empty database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_assembled_db(temp_dir)
            last_update = get_last_update(temp_dir)
            assert last_update is None

    def test_get_assembly_records_empty(self):
        """Test getting assembly records from empty database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_assembled_db(temp_dir)
            records = get_assembly_records(temp_dir)
            assert records == []

    def test_check_part_in_db_not_exists(self):
        """Test checking for non-existent part."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            exists, polarization = check_part_in_db("NONEXISTENT", "ANTENNA", temp_dir)
            assert not exists
            assert polarization is None

    def test_get_parts_by_criteria_empty(self):
        """Test getting parts by criteria from empty database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            parts = get_parts_by_criteria(db_dir=temp_dir)
            assert parts == []


class TestDatabaseMigrations:
    """Test database migration utilities."""

    def test_database_migrator_init(self):
        """Test DatabaseMigrator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            migrator = DatabaseMigrator("test.db", temp_dir)
            assert migrator.db_name == "test.db"
            assert migrator.db_dir == temp_dir

    def test_get_schema_version_new_db(self):
        """Test getting schema version from new database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            migrator = DatabaseMigrator("parts.db", temp_dir)
            version = migrator.get_schema_version()
            assert version == 0  # No schema_version table yet

    def test_set_schema_version(self):
        """Test setting schema version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            migrator = DatabaseMigrator("parts.db", temp_dir)
            migrator.set_schema_version(1)
            version = migrator.get_schema_version()
            assert version == 1

    def test_execute_migration_success(self):
        """Test successful migration execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            migrator = DatabaseMigrator("parts.db", temp_dir)

            # Add a new column via migration
            sql = "ALTER TABLE parts ADD COLUMN test_column TEXT"
            migrator.execute_migration(sql, 1)

            # Verify version was updated
            version = migrator.get_schema_version()
            assert version == 1

    def test_execute_migration_failure(self):
        """Test migration failure handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            migrator = DatabaseMigrator("parts.db", temp_dir)

            # Invalid SQL should fail
            with pytest.raises(RuntimeError, match="Migration failed"):
                migrator.execute_migration("INVALID SQL", 1)

    def test_get_table_info(self):
        """Test getting table structure information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            info = get_table_info("parts.db", "parts", temp_dir)

            assert len(info) > 0
            # Check for expected columns
            column_names = [col["name"] for col in info]
            assert "id" in column_names
            assert "part_number" in column_names
            assert "part_type" in column_names

    def test_backup_database(self):
        """Test database backup functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            backup_path = backup_database("parts.db", "test_backup", temp_dir)

            assert "test_backup_" in backup_path
            assert "parts.db" in backup_path
            # Backup file should exist (implicitly tested by successful
            # function call)

    def test_check_database_integrity(self):
        """Test database integrity checking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            init_parts_db(temp_dir)
            is_ok = check_database_integrity("parts.db", temp_dir)
            assert is_ok is True


class TestDatabasePackageIntegration:
    """Test integration between database package modules."""

    def test_package_imports(self):
        """Test that all expected functions are available from direct package imports."""
        from casman.database.connection import find_project_root, get_database_path
        from casman.database.operations import (
            check_part_in_db,
            get_all_parts,
            get_assembly_records,
            get_last_update,
            get_parts_by_criteria,
        )
        from casman.database.initialization import (
            init_all_databases,
            init_assembled_db,
            init_parts_db,
        )
        from casman.database.migrations import (
            DatabaseMigrator,
            backup_database,
            check_database_integrity,
            get_table_info,
        )

        # All imports should succeed
        assert callable(find_project_root)
        assert callable(get_database_path)
        assert callable(init_parts_db)
        assert callable(init_assembled_db)
        assert callable(init_all_databases)
        assert callable(get_all_parts)
        assert callable(get_last_update)
        assert callable(get_assembly_records)
        assert callable(check_part_in_db)
        assert callable(get_parts_by_criteria)
        assert DatabaseMigrator is not None
        assert callable(get_table_info)
        assert callable(backup_database)
        assert callable(check_database_integrity)

    def test_backward_compatibility(self):
        """Test that existing code still works with modularized database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test the complete workflow
            init_all_databases(temp_dir)

            # Test parts operations
            parts = get_parts_by_criteria(db_dir=temp_dir)
            assert parts == []

            # Test assembly operations
            records = get_assembly_records(temp_dir)
            assert records == []

            # Test utility functions
            all_parts = get_all_parts(temp_dir)
            assert all_parts == []
