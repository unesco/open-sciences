#!/usr/bin/env python3
"""
Delete Example: Delete a specific record by Lens ID

This script demonstrates how to delete a record from InvenioRDM using the SDK.
It will delete ALL records with the specified lens_id.
"""

import os
import time
from openscience_tools.sources.lens import LensOrgImporter


def main():
    print("\n" + "=" * 70)
    print("DELETE EXAMPLE: Remove Record by Lens ID")
    print("=" * 70)
    print("\n⚠️  WARNING: This will DELETE record 000-035-558-593-934")
    print("   and any duplicates from your InvenioRDM instance!\n")

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

    # Perform DELETE
    print(f"\n🗑️  Deleting all records with Lens ID: {LENS_ID}...")
    status_code, record_id, message = importer.delete(LENS_ID)

    if status_code == 204:
        print(f"✅ DELETE successful!")
        print(f"   {message}")
        print(f"   Status: {status_code}")

        # Wait for OpenSearch indexing
        print("\n⏳ Waiting 2 seconds for indexing...")
        time.sleep(2)

        print(f"\n✓ Record(s) with Lens ID {LENS_ID} have been removed")
    elif status_code == 404:
        print(f"ℹ️  No records found with Lens ID: {LENS_ID}")
        print(f"   Status: {status_code}")
        print(f"   Message: {message}")
    else:
        print(f"❌ DELETE failed!")
        print(f"   Status: {status_code}")
        print(f"   Message: {message}")

    print("\n" + "=" * 70)
    print("✓ Delete example completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
