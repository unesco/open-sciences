#!/usr/bin/env python3
"""
Test script to debug publishing issues
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invenio_client import create_client_from_env
from datetime import datetime

# Create client
client = create_client_from_env()

# Create a minimal record
metadata = {
    "title": "Test Publication",
    "creators": [
        {
            "person_or_org": {
                "given_name": "John",
                "family_name": "Doe",
                "type": "personal",
                "name": "Doe, John",
            }
        }
    ],
    "resource_type": {"id": "dataset"},
    "publication_date": datetime.now().strftime("%Y-%m-%d"),
}

access = {"record": "public", "files": "public"}

files_config = {"enabled": False}

print("Creating draft...")
try:
    draft = client.create_draft(metadata=metadata, access=access, files=files_config)
    record_id = draft["id"]
    print(f"✅ Draft created: {record_id}")

    print(f"\nPublishing draft {record_id}...")
    published = client.publish_draft(record_id)
    print(f"✅ Record published successfully!")
    print(f"Published record: {published.get('links', {}).get('self_html', 'N/A')}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
