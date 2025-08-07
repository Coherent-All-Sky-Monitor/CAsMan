#!/usr/bin/env python3

import os
import tempfile
from casman.database import get_database_path
from casman.config import get_config, get_config_enhanced

# Test environment variable behavior
with tempfile.TemporaryDirectory() as temp_dir:
    temp_db_path = os.path.join(temp_dir, "parts.db")
    print(f"Temp path: {temp_db_path}")

    # Set environment variable
    os.environ["CASMAN_PARTS_DB"] = temp_db_path
    print(f"Environment variable set: {os.environ.get('CASMAN_PARTS_DB')}")

    # Test enhanced config directly
    enhanced_result = get_config_enhanced("CASMAN_PARTS_DB", None)
    print(f"get_config_enhanced result: {enhanced_result}")

    # Test environment directly
    env_result = os.environ.get("CASMAN_PARTS_DB")
    print(f"Direct env check: {env_result}")

    # Test get_config directly
    config_result = get_config("CASMAN_PARTS_DB")
    print(f"get_config result: {config_result}")
    print(f"get_config type: {type(config_result)}")

    # Test get_database_path with None
    result = get_database_path("parts.db", None)
    print(f"get_database_path result: {result}")
    print(f"Should match temp path: {result == temp_db_path}")
