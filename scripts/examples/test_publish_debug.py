#!/usr/bin/env python3
"""
Test script to see the exact API error response
"""

import sys
from pathlib import Path
import requests
import json

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invenio_client import create_client_from_env

# Create client
client = create_client_from_env()

# Test with metadata similar to CSV record
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

print("Creating draft...")
draft = client.create_draft(metadata=metadata, access=access, files=files_config)
record_id = draft["id"]
print(f"✅ Draft created: {record_id}")

print(f"\nAttempting to publish {record_id}...")

# Make manual request to see full error
url = f"{client.api_url}/records/{record_id}/draft/actions/publish"
try:
    response = client.session.post(url)
    response.raise_for_status()
    print("✅ Published successfully!")
except requests.exceptions.HTTPError as e:
    print(f"❌ Publish failed with status {e.response.status_code}")
    print(f"\nFull error response:")
    try:
        error_data = e.response.json()
        print(json.dumps(error_data, indent=2))
    except:
        print(e.response.text)
