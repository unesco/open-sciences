#!/usr/bin/env python3
"""
Update Example: Update a specific record by Lens ID

This script demonstrates how to update an existing record in InvenioRDM
using the SDK. It shows partial updates using smart merge.
"""

import os
import json
import time
from pathlib import Path
from openscience_tools.sources.lens import LensOrgImporter


def load_publication_by_lens_id(lens_id: str):
    """Load a specific publication from publications.json by lens_id."""
    data_file = Path(__file__).parent.parent / "data" / "publications.json"

    with open(data_file, "r") as f:
        publications = json.load(f)

    for pub in publications:
        if pub.get("lens_id") == lens_id:
            return pub

    return None


def deep_merge(original: dict, updates: dict) -> dict:
    """
    Deep merge: recursively merge updates into original, preserving nested structures.
    """
    merged = original.copy()

    for key, value in updates.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            merged[key] = deep_merge(merged[key], value)
        elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
            # For lists, extend instead of replace (for keywords)
            if key == "keywords":
                # Avoid duplicates in keywords
                merged[key] = list(set(merged[key] + value))
            else:
                merged[key] = value
        else:
            # Replace value
            merged[key] = value

    return merged


def main():
    print("\n" + "=" * 70)
    print("UPDATE EXAMPLE: Modify Existing Record")
    print("=" * 70)
    print("\nThis script updates record 000-035-558-593-934")
    print("by modifying its title and adding keywords.\n")

    # Target Lens ID
    LENS_ID = "000-035-558-593-934"

    # Initialize importer (uses env vars)
    base_url = os.getenv("OPENSCIENCE_TOOLS_BASE_URL")
    token = os.getenv("OPENSCIENCE_TOOLS_TOKEN")

    if not base_url or not token:
        print("❌ Error: Missing environment variables")
        print("   Set OPENSCIENCE_TOOLS_BASE_URL and OPENSCIENCE_TOOLS_TOKEN")
        return

    print(f"📡 Connecting to: {base_url}")
    importer = LensOrgImporter(base_url=base_url, token=token)

    # Load original publication data from JSON file
    print(f"\n📂 Loading publication {LENS_ID} from publications.json...")
    original_data = load_publication_by_lens_id(LENS_ID)

    if not original_data:
        print(f"❌ Error: Publication {LENS_ID} not found in publications.json")
        return

    print(f"✓ Loaded: {original_data.get('title', 'Unknown')[:60]}...")

    # Define partial updates (only what you want to change)
    print("\n📝 Preparing updates...")
    updates = {
        "title": original_data["title"] + " [UPDATED EDITION]",
        "keywords": ["organizational behavior", "disaster management"],  # These will be added
    }

    print(f"   - New title: {updates['title'][:60]}...")
    print(f"   - Adding keywords: organizational behavior, disaster management")

    # Deep merge updates with original data (preserves all fields including custom_fields)
    updated_data = deep_merge(original_data, updates)

    # Perform UPDATE
    print(f"\n🔄 Updating record {LENS_ID}...")
    status_code, record_id, message = importer.update(LENS_ID, updated_data, publish=True)

    if status_code == 200:
        print(f"✅ UPDATE successful!")
        print(f"   Record ID: {record_id}")
        print(f"   Status: {status_code}")

        # Wait for OpenSearch indexing
        print("\n⏳ Waiting 2 seconds for indexing...")
        time.sleep(2)

        print(f"\n🔗 View updated record:")
        print(f"   {base_url}/records/{record_id}")
    else:
        print(f"❌ UPDATE failed!")
        print(f"   Status: {status_code}")
        print(f"   Message: {message}")

    print("\n" + "=" * 70)
    print("✓ Update example completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
