"""
Pytest configuration and shared fixtures for openscience_tools tests.
"""

import os
import pytest
import json
from pathlib import Path
from typing import Dict, Any

from openscience_tools.invenio_client import InvenioRDMClient
from openscience_tools.sources.lens import LensOrgImporter
from openscience_tools.tools.cleanup import cleanup_all_records


# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def test_env():
    """
    Load test environment variables.

    Returns dict with base_url and token for testing.
    Falls back to localhost if not set.
    """
    base_url = os.getenv("OPENSCIENCE_TOOLS_BASE_URL", "https://127.0.0.1:5000")
    token = os.getenv("OPENSCIENCE_TOOLS_TOKEN")

    if not token:
        pytest.skip("OPENSCIENCE_TOOLS_TOKEN not set - skipping integration tests")

    return {"base_url": base_url, "token": token}


@pytest.fixture(scope="session")
def invenio_client(test_env):
    """Create InvenioRDM client for tests."""
    return InvenioRDMClient(base_url=test_env["base_url"], token=test_env["token"])


@pytest.fixture(scope="session")
def lens_importer(test_env):
    """Create LensOrgImporter for tests."""
    return LensOrgImporter(base_url=test_env["base_url"], token=test_env["token"])


@pytest.fixture(scope="function")
def clean_database(test_env):
    """
    Clean database before each test.

    This fixture runs cleanup_all_records before the test
    to ensure a clean state.
    """
    cleanup_all_records(
        base_url=test_env["base_url"],
        token=test_env["token"],
        confirm=True,
        dry_run=False,
        verbose=False,
    )
    yield
    # Optional: cleanup after test as well
    # Commented out to allow inspection after test failures


@pytest.fixture
def sample_lens_record() -> Dict[str, Any]:
    """
    Load a sample Lens.org record for testing.

    Returns the first record from publications.json.
    """
    data_file = TEST_DATA_DIR / "publications.json"

    if not data_file.exists():
        # Fallback to the actual data file
        data_file = (
            Path(__file__).parent.parent
            / "openscience_tools"
            / "sources"
            / "lens"
            / "data"
            / "publications.json"
        )

    with open(data_file, "r") as f:
        publications = json.load(f)

    return publications[0] if publications else None


@pytest.fixture
def sample_lens_records() -> list[Dict[str, Any]]:
    """
    Load multiple sample Lens.org records for testing.

    Returns first 5 records from publications.json.
    """
    data_file = TEST_DATA_DIR / "publications.json"

    if not data_file.exists():
        # Fallback to the actual data file
        data_file = (
            Path(__file__).parent.parent
            / "openscience_tools"
            / "sources"
            / "lens"
            / "data"
            / "publications.json"
        )

    with open(data_file, "r") as f:
        publications = json.load(f)

    return publications[:5] if len(publications) >= 5 else publications


@pytest.fixture
def minimal_lens_record() -> Dict[str, Any]:
    """
    Create a minimal valid Lens.org record for testing.
    """
    return {
        "lens_id": "test-lens-id-12345",
        "title": "Test Publication Title",
        "publication_type": "journal article",
        "year_published": 2024,
        "authors": [{"first_name": "John", "last_name": "Doe", "initials": "J"}],
        "external_ids": [{"type": "doi", "value": "10.1234/test.doi"}],
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires live InvenioRDM instance)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "unit: mark test as unit test (no external dependencies)")
