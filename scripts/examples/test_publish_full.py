#!/usr/bin/env python3
"""
Test script to debug CSV publishing issues with real metadata
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invenio_client import create_client_from_env

# Create client
client = create_client_from_env()

# Test with metadata similar to CSV record #3 (AI Model Training Results)
metadata = {
    "title": "AI Model Training Results Test",
    "description": "Results from training a deep learning model for image classification",
    "creators": [
        {
            "person_or_org": {
                "given_name": "Alice",
                "family_name": "Smith",
                "type": "personal",
                "name": "Smith, Alice",
                "identifiers": [
                    {"identifier": "0000-0002-3456-7890", "scheme": "orcid"}
                ],
            },
            "affiliations": [{"name": "MIT"}],
        },
        {
            "person_or_org": {
                "given_name": "Bob",
                "family_name": "Johnson",
                "type": "personal",
                "name": "Johnson, Bob",
                "identifiers": [
                    {"identifier": "0000-0003-4567-8901", "scheme": "orcid"}
                ],
            },
            "affiliations": [{"name": "Stanford University"}],
        },
    ],
    "resource_type": {"id": "publication-article"},
    "publication_date": "2024-02-20",
}

access = {"record": "public", "files": "public"}

files_config = {"enabled": False}

print("Creating draft with multiple creators and description...")
try:
    draft = client.create_draft(metadata=metadata, access=access, files=files_config)
    record_id = draft["id"]
    print(f"✅ Draft created: {record_id}")

    print(f"\nPublishing draft {record_id}...")
    published = client.publish_draft(record_id)
    print(f"✅ Record published successfully!")
    print(f"Published record: {published.get('links', {}).get('self_html', 'N/A')}")

    # Get DOI if available
    pids = published.get("pids", {})
    if "doi" in pids:
        doi = pids["doi"]["identifier"]
        print(f"DOI: {doi}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
