"""Test configuration and fixtures for CAsMan tests."""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator, Optional
from unittest.mock import patch

import pytest

from casman.database import init_assembled_db, init_parts_db


@pytest.fixture(autouse=True)
def set_casman_db_env_vars(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Robustly isolate both parts and assembled DBs for every test."""
    temp_dir = str(tmp_path)
    parts_db = os.path.join(temp_dir, "parts.db")
    assembled_db = os.path.join(temp_dir, "assembled_casm.db")
    os.makedirs(temp_dir, exist_ok=True)
    if os.path.exists(parts_db):
        os.remove(parts_db)
    if os.path.exists(assembled_db):
        os.remove(assembled_db)
    monkeypatch.setenv("CASMAN_PARTS_DB", parts_db)
    monkeypatch.setenv("CASMAN_ASSEMBLED_DB", assembled_db)


@pytest.fixture
def temporary_directory() -> Generator[str, None, None]:
    """Create a temporary directory for tests."""
    temp_directory = tempfile.mkdtemp()
    yield temp_directory
    shutil.rmtree(temp_directory)


@pytest.fixture
def mock_database_path(temporary_directory_fixture: str) -> Generator:
    """Mock the database path to use temporary directory."""
    test_dir = temporary_directory_fixture

    def get_test_path(db_name: str, _db_dir: Optional[str] = None) -> str:
        # _db_dir is unused, but kept for signature compatibility
        return os.path.join(test_dir, db_name)

    # Patch all modules that import get_database_path
    with patch('casman.database.get_database_path', side_effect=get_test_path) as mock_path:
        with patch('casman.assembly.get_database_path', side_effect=get_test_path):
            with patch('casman.parts.get_database_path', side_effect=get_test_path):
                yield mock_path


@pytest.fixture
def mock_barcode_dir(barcode_temp_dir: str) -> Generator:
    """Mock the barcode directory to use temporary directory."""
    test_dir = barcode_temp_dir
    with patch('casman.barcode_utils.BARCODE_BASE_DIR', test_dir):
        yield test_dir


@pytest.fixture
def init_test_databases(
        _mock_database_path: Generator) -> Generator[None, None, None]:
    """Initialize test databases."""
    # _mock_database_path is required as a fixture to ensure DBs are created
    # in temp dir
    init_parts_db()
    init_assembled_db()
    yield


@pytest.fixture
def sample_parts_data() -> list:
    """Sample parts data for testing."""
    return [
        {
            'part_number': 'ANTP1-00001',
            'part_type': 'ANTENNA',
            'polarization': 'X',
        },
        {
            'part_number': 'LNAP1-00001',
            'part_type': 'LNA',
            'polarization': 'Y',
        },
        {
            'part_number': 'BACP1-00001',
            'part_type': 'BACBOARD',
            'polarization': 'H',
        },
    ]


@pytest.fixture
def sample_assembly_data() -> list:
    """Sample assembly data for testing."""
    return [
        {
            'part_number': 'ANTP1-00001',
            'connected_to': None,
        },
        {
            'part_number': 'LNAP1-00001',
            'connected_to': 'ANTP1-00001',
        },
        {
            'part_number': 'BACP1-00001',
            'connected_to': 'LNAP1-00001',
        },
    ]
