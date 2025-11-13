#!/usr/bin/env python3
"""
Batch import example: Insert all publications from publications.json.

This demonstrates how to import all records from the Lens.org data file
into InvenioRDM using the SDK.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from openscience_tools.sources.lens.importer import LensOrgImporter


def load_all_publications() -> List[Dict[str, Any]]:
    """Load all publications from publications.json"""
    data_file = Path(__file__).parent.parent / "data" / "publications.json"
    with open(data_file, "r", encoding="utf-8") as f:
        publications = json.load(f)
    return publications


def batch_import_all(publications: List[Dict[str, Any]], batch_size: int = 10, delay: float = 0.5):
    """
    Import all publications in batches.

    Args:
        publications: List of publication records to import
        batch_size: Number of records to process before showing progress
        delay: Seconds to wait between batches (to avoid overwhelming the server)
    """
    print("=" * 70)
    print("BATCH IMPORT: All Publications from publications.json")
    print("=" * 70)
    print(f"📊 Total records to import: {len(publications)}")
    print(f"📦 Batch size: {batch_size}")
    print(f"⏱️  Delay between batches: {delay}s")
    print()

    importer = LensOrgImporter()

    results = {"success": [], "failed": [], "skipped": []}

    total = len(publications)

    for idx, publication in enumerate(publications, 1):
        lens_id = publication.get("lens_id", "unknown")
        title = publication.get("title", "No title")[:60]

        # Progress indicator
        if idx % batch_size == 1 or batch_size == 1:
            print(f"\n📍 Processing records {idx}-{min(idx + batch_size - 1, total)} of {total}")

        print(f"  [{idx}/{total}] {lens_id}: {title}...", end=" ")

        try:
            status_code, record_id, message = importer.insert(data=publication, publish=True)

            if status_code == 201:
                print(f"✅ {record_id}")
                results["success"].append(
                    {"lens_id": lens_id, "record_id": record_id, "title": title}
                )
            else:
                print(f"❌ Error {status_code}")
                results["failed"].append(
                    {"lens_id": lens_id, "status": status_code, "message": message, "title": title}
                )
        except Exception as e:
            print(f"💥 Exception: {str(e)[:50]}")
            results["failed"].append({"lens_id": lens_id, "error": str(e), "title": title})

        # Delay between batches to avoid overwhelming the server
        if idx % batch_size == 0 and idx < total:
            time.sleep(delay)

    # Print summary
    print("\n" + "=" * 70)
    print("IMPORT SUMMARY")
    print("=" * 70)
    print(f"✅ Successful: {len(results['success'])}/{total}")
    print(f"❌ Failed: {len(results['failed'])}/{total}")
    print(f"⏭️  Skipped: {len(results['skipped'])}/{total}")

    if results["failed"]:
        print("\n❌ Failed records:")
        for fail in results["failed"][:10]:  # Show first 10 failures
            lens_id = fail.get("lens_id", "unknown")
            msg = fail.get("message", fail.get("error", "Unknown error"))[:60]
            print(f"  - {lens_id}: {msg}")
        if len(results["failed"]) > 10:
            print(f"  ... and {len(results['failed']) - 10} more")

    print("\n" + "=" * 70)

    return results


def main():
    """Main execution flow"""
    print(
        """
    ╔══════════════════════════════════════════════════════════════════╗
    ║  Batch Import: All Publications from publications.json          ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    This script imports ALL publications from the Lens.org data file
    into your InvenioRDM instance.
    
    Make sure to set the environment variables:
    - OPENSCIENCE_TOOLS_BASE_URL
    - OPENSCIENCE_TOOLS_TOKEN
    
    Data source: openscience_tools/sources/lens/data/publications.json
    
    ⚠️  WARNING: This will create multiple records in your database.
                 Use a development/test instance!
    """
    )

    print("📂 Loading publications from publications.json...")
    publications = load_all_publications()
    print(f"✓ Loaded {len(publications)} publications\n")

    # Start import
    start_time = time.time()
    results = batch_import_all(publications, batch_size=10, delay=0.5)
    elapsed_time = time.time() - start_time

    print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
    print(f"⚡ Average: {elapsed_time/len(publications):.2f} seconds per record")
    print("\n✓ Batch import completed!")


if __name__ == "__main__":
    main()
