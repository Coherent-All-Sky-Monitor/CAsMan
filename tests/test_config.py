"""Simplified tests for CAsMan configuration functionality."""

from casman.config.schema import ConfigSchema


class TestConfig:
    """Test configuration functionality."""

    def test_config_schema_validation(self):
        """Test configuration schema validation."""
        valid_config = {
            "CASMAN_PARTS_DB": "database/parts.db",
            "CASMAN_ASSEMBLED_DB": "database/assembled_casm.db"
        }
        is_valid, _ = ConfigSchema.validate_config(valid_config)
        assert is_valid

    def test_config_template(self):
        """Test configuration template generation."""
        template = ConfigSchema.get_config_template()
        assert "PART_TYPES" in template
        assert "CASMAN_PARTS_DB" in template
        assert isinstance(template, dict)
