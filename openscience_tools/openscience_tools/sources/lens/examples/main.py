#!/usr/bin/env python3
"""
Example usage of LensOrgImporter as an SDK.

This demonstrates how to use the insert, update, and delete methods
programmatically without using the CLI.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any
from openscience_tools.sources.lens.importer import LensOrgImporter


def load_sample_publication() -> Dict[str, Any]:
    """Load the first publication from publications.json"""
    data_file = Path(__file__).parent.parent / "data" / "publications.json"
    with open(data_file, "r", encoding="utf-8") as f:
        publications = json.load(f)
    return publications[0]


def merge_update_data(original: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Smart merge: start from original data and apply only the updates.

    Args:
        original: Original publication data
        updates: Dictionary with only the fields to update

    Returns:
        Merged dictionary with updates applied to original
    """
    merged = original.copy()
    merged.update(updates)
    return merged


def example_insert(sample_publication: Dict[str, Any]):
    """Example: Insert a new publication"""
    print("=" * 60)
    print("EXAMPLE: INSERT")
    print("=" * 60)
    print(f"📄 Publication: {sample_publication['title'][:60]}...")
    print(f"🔖 Lens ID: {sample_publication['lens_id']}")
    print(f"👥 Authors: {len(sample_publication.get('authors', []))} authors")

    # Initialize importer with credentials
    # Option 1: From environment variables
    importer = LensOrgImporter()

    # Option 2: Explicit credentials
    # importer = LensOrgImporter(
    #     base_url="https://your-invenio.org",
    #     token="your-api-token"
    # )

    # Insert the publication
    status_code, record_id, message = importer.insert(
        data=sample_publication, publish=True  # Set to False to keep as draft
    )

    if status_code == 201:
        print(f"✅ Success! Created record: {record_id}")
        return record_id
    else:
        print(f"❌ Error {status_code}: {message}")
        return None


def example_update(sample_publication: Dict[str, Any]):
    """Example: Update an existing publication"""
    print("\n" + "=" * 60)
    print("EXAMPLE: UPDATE")
    print("=" * 60)

    importer = LensOrgImporter()
    lens_id = sample_publication["lens_id"]

    # Smart update: only specify the fields you want to change
    # The merge will be done with the original publication data
    updates = {
        "title": sample_publication["title"] + " - UPDATED VIA SDK",
        "abstract": "This publication has been UPDATED using the SDK interface to demonstrate the smart update() method.",
    }

    print(f"📝 Updating fields: {', '.join(updates.keys())}")

    # Merge updates with original data
    update_data = merge_update_data(sample_publication, updates)

    # Update the publication
    status_code, record_id, message = importer.update(
        lens_id=lens_id, data=update_data, publish=True
    )

    if status_code == 200:
        print(f"✅ Success! Updated record: {record_id}")
        print(f"   New title: {updates['title'][:60]}...")
        return record_id
    else:
        print(f"❌ Error {status_code}: {message}")
        return None


def example_delete(lens_id: str):
    """Example: Delete a publication"""
    print("\n" + "=" * 60)
    print("EXAMPLE: DELETE")
    print("=" * 60)
    print(f"🗑️  Deleting all records with Lens ID: {lens_id}")

    importer = LensOrgImporter()

    # Delete the publication (deletes ALL records with this lens_id)
    status_code, record_id, message = importer.delete(lens_id=lens_id)

    if status_code == 204:
        if message:
            print(f"✅ Success! {message}")
        else:
            print(f"✅ Success! Deleted record: {record_id}")
        return record_id
    else:
        print(f"❌ Error {status_code}: {message}")
        return None


def example_batch_operations():
    """Example: Batch operations with multiple publications"""
    print("\n" + "=" * 60)
    print("EXAMPLE: BATCH OPERATIONS")
    print("=" * 60)

    importer = LensOrgImporter()

    publications = [
        {
            "lens_id": f"999-BATCH-{i:03d}",
            "title": f"Batch Publication #{i}",
            "publication_type": "journal article",
            "year_published": 2024,
            "authors": [{"first_name": "Jane", "last_name": f"Smith-{i}", "initials": "J"}],
        }
        for i in range(1, 4)
    ]

    results = []
    for pub in publications:
        status, record_id, msg = importer.insert(pub, publish=True)
        results.append(
            {"lens_id": pub["lens_id"], "status": status, "record_id": record_id, "message": msg}
        )

    # Print summary
    successful = sum(1 for r in results if r["status"] == 201)
    print(f"\n📊 Batch insert completed: {successful}/{len(publications)} successful")

    for result in results:
        if result["status"] == 201:
            print(f"  ✅ {result['lens_id']}: {result['record_id']}")
        else:
            print(f"  ❌ {result['lens_id']}: {result['message']}")


def main():
    """Main execution flow"""
    print(
        """
    ╔══════════════════════════════════════════════════════════╗
    ║  LensOrgImporter SDK Usage Examples                      ║
    ╚══════════════════════════════════════════════════════════╝
    
    This script demonstrates how to use the LensOrgImporter
    as an SDK for programmatic access to InvenioRDM.
    
    Make sure to set the environment variables:
    - OPENSCIENCE_TOOLS_BASE_URL
    - OPENSCIENCE_TOOLS_TOKEN
    
    Or pass credentials explicitly to the constructor.
    
    Data source: openscience_tools/sources/lens/data/publications.json
    """
    )

    # Load sample publication from JSON file
    print("📂 Loading sample publication from publications.json...")
    sample_publication = load_sample_publication()
    print(f"✓ Loaded: {sample_publication['title'][:60]}...\n")

    # Example 1: Insert a new publication
    record_id = example_insert(sample_publication)

    if record_id:
        # Wait for indexing (OpenSearch/Elasticsearch needs time to index)
        print("\n⏳ Waiting 2 seconds for record to be indexed...")
        time.sleep(2)

        # Example 2: Update the publication we just created
        example_update(sample_publication)

        # Example 3: Delete the publication
        example_delete(sample_publication["lens_id"])

    # Example 4: Batch operations
    # Uncomment to run batch example:
    # example_batch_operations()

    print("\n" + "=" * 60)
    print("✓ Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
