"""
Pytest fixtures specific to Lens.org source tests.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any

from openscience_tools.sources.lens import LensOrgImporter


@pytest.fixture
def lens_importer(test_env):
    """Create LensOrgImporter for Lens-specific tests."""
    return LensOrgImporter(
        base_url=test_env["base_url"],
        token=test_env["token"]
    )


@pytest.fixture
def sample_lens_record() -> Dict[str, Any]:
    """
    Load a sample Lens.org record for testing.
    
    Returns the first record from publications.json.
    """
    data_file = Path(__file__).parent.parent.parent.parent / "openscience_tools" / "sources" / "lens" / "data" / "publications.json"
    
    with open(data_file, 'r') as f:
        publications = json.load(f)
    
    return publications[0] if publications else None


@pytest.fixture
def sample_lens_records() -> list[Dict[str, Any]]:
    """
    Load multiple sample Lens.org records for testing.
    
    Returns first 5 records from publications.json.
    """
    data_file = Path(__file__).parent.parent.parent.parent / "openscience_tools" / "sources" / "lens" / "data" / "publications.json"
    
    with open(data_file, 'r') as f:
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
        "authors": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "initials": "J"
            }
        ],
        "external_ids": [
            {
                "type": "doi",
                "value": "10.1234/test.doi"
            }
        ]
    }
