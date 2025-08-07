"""
Configuration schema definitions for CAsMan.

Provides JSON schema validation for configuration files.
"""

from typing import Any, Dict, Optional

# JSON schema for CAsMan configuration
CASMAN_CONFIG_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "PART_TYPES": {
            "type": "object",
            "patternProperties": {
                r"^\d+$": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 2
                }
            },
            "additionalProperties": False
        },
        "CASMAN_PARTS_DB": {
            "type": "string",
            "description": "Path to the parts database file"
        },
        "CASMAN_ASSEMBLED_DB": {
            "type": "string",
            "description": "Path to the assembled components database file"
        },
        "database": {
            "type": "object",
            "properties": {
                "backup_enabled": {"type": "boolean"},
                "backup_interval_hours": {"type": "number", "minimum": 1},
                "max_backups": {"type": "integer", "minimum": 1},
                "integrity_check_enabled": {"type": "boolean"},
                "connection_timeout": {"type": "number", "minimum": 0}
            },
            "additionalProperties": True
        },
        "barcode": {
            "type": "object",
            "properties": {
                "default_format": {"type": "string"},
                "output_directory": {"type": "string"},
                "image_format": {"type": "string"},
                "pdf_page_size": {"type": "string"},
                "images_per_row": {"type": "integer", "minimum": 1},
                "margin_pixels": {"type": "integer", "minimum": 0},
                "max_barcode_width": {"type": "integer", "minimum": 1},
                "max_barcode_height": {"type": "integer", "minimum": 1}
            },
            "additionalProperties": True
        },
        "visualization": {
            "type": "object",
            "properties": {
                "web_port": {"type": "integer", "minimum": 1024, "maximum": 65535},
                "auto_refresh": {"type": "boolean"},
                "theme": {"type": "string"},
                "export_formats": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "additionalProperties": True
        },
        "logging": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                },
                "format": {"type": "string"},
                "file_path": {"type": "string"},
                "max_file_size_mb": {"type": "number", "minimum": 1},
                "backup_count": {"type": "integer", "minimum": 0}
            },
            "additionalProperties": True
        }
    },
    "required": ["PART_TYPES"],
    "additionalProperties": True
}


class ConfigSchema:
    """Configuration schema management class."""

    @staticmethod
    def get_default_schema() -> Dict[str, Any]:
        """Get the default CAsMan configuration schema."""
        return CASMAN_CONFIG_SCHEMA.copy()

    @staticmethod
    def validate_config(
            config: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> tuple[bool, str]:
        """
        Validate configuration against schema.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration to validate.
        schema : Dict[str, Any], optional
            Schema to validate against. Uses default if None.

        Returns
        -------
        tuple[bool, str]
            (is_valid, error_message)
        """
        if schema is None:
            schema = CASMAN_CONFIG_SCHEMA

        try:
            # Try importing jsonschema for validation
            import jsonschema  # type: ignore
            jsonschema.validate(config, schema)
            return True, ""
        except ImportError:
            return True, "jsonschema not available - skipping validation"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_config_template() -> Dict[str, Any]:
        """Get a configuration template with default values."""
        return {
            "PART_TYPES": {
                "1": ["ANTENNA", "ANT"],
                "2": ["LNA", "LNA"],
                "3": ["COAX1", "CX1"],
                "4": ["COAX2", "CX2"],
                "5": ["BACBOARD", "BAC"],
                "6": ["SNAP", "SNAP"]
            },
            "CASMAN_PARTS_DB": "database/parts.db",
            "CASMAN_ASSEMBLED_DB": "database/assembled_casm.db",
            "database": {
                "backup_enabled": True,
                "backup_interval_hours": 24,
                "max_backups": 7,
                "integrity_check_enabled": True,
                "connection_timeout": 30.0
            },
            "barcode": {
                "default_format": "code128",
                "output_directory": "barcodes",
                "image_format": "png",
                "pdf_page_size": "letter",
                "images_per_row": 3,
                "margin_pixels": 100,
                "max_barcode_width": 600,
                "max_barcode_height": 200
            },
            "visualization": {
                "web_port": 8080,
                "auto_refresh": True,
                "theme": "default",
                "export_formats": ["png", "svg", "pdf"]
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_path": "logs/casman.log",
                "max_file_size_mb": 10,
                "backup_count": 5
            }
        }
