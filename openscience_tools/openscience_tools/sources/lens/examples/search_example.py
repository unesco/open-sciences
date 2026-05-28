#!/usr/bin/env python3
"""
Search Example: Search records using various filters

This script demonstrates how to search for records in InvenioRDM
using the SDK search() method with different filter combinations.
"""

import os
from openscience_tools.sources.lens import LensOrgImporter


def print_results(results, description):
    """Print search results in a readable format."""
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}")

    total = results["hits"]["total"]
    hits = results["hits"]["hits"]
    query = results.get("query", "N/A")
    filters = results.get("filters", {})

    print(f"Query: {query}")
    print(f"Filters: {filters}")
    print(f"Total matches: {total}")

    if total > 0:
        print(f"\nShowing {len(hits)} of {total} results:\n")
        for idx, record in enumerate(hits, 1):
            record_id = record.get("id")
            metadata = record.get("metadata", {})
            title = metadata.get("title", "No title")
            custom_fields = record.get("custom_fields", {})
            lens_id = custom_fields.get("lens:id", "N/A")

            print(f"  [{idx}] {record_id}")
            print(f"      Lens ID: {lens_id}")
            print(f"      Title: {title[:80]}{'...' if len(title) > 80 else ''}")
            print()
    else:
        print("\n⚠️  No records found\n")


def main():
    print("\n" + "=" * 70)
    print("SEARCH EXAMPLE: Search Records with Filters")
    print("=" * 70)
    print("\nThis script demonstrates various search capabilities:\n")
    print("  1. Search by lens_id (exact match)")
    print("  2. Search by title (case-insensitive partial match)")
    print("  3. Combined filters")
    print("  4. Pagination and sorting\n")

    # Initialize importer (uses env vars)
    base_url = os.getenv("OPENSCIENCE_TOOLS_BASE_URL")
    token = os.getenv("OPENSCIENCE_TOOLS_TOKEN")

    if not base_url or not token:
        print("❌ Error: Missing environment variables")
        print("   Set OPENSCIENCE_TOOLS_BASE_URL and OPENSCIENCE_TOOLS_TOKEN")
        return

    print(f"📡 Connecting to: {base_url}\n")
    importer = LensOrgImporter(base_url=base_url, token=token)

    # Example 1: Search by lens_id (exact match)
    print("\n🔍 Example 1: Search by Lens ID")
    results = importer.search(lens_id="000-035-558-593-934")
    print_results(results, "Search by lens_id='000-035-558-593-934'")

    # Example 2: Search by title (case-insensitive)
    print("\n🔍 Example 2: Search by Title (case-insensitive)")
    results = importer.search(title="disaster")
    print_results(results, "Search by title containing 'disaster'")

    # Example 3: Search all records (no filters)
    print("\n🔍 Example 3: List All Records (first 5)")
    results = importer.search(size=5)
    print_results(results, "All records (no filters, size=5)")

    # Example 4: Search with pagination and sorting
    print("\n🔍 Example 4: Search with Pagination and Sorting")
    results = importer.search(size=3, page=1, sort="newest")
    print_results(results, "All records sorted by newest (page 1, size=3)")

    # Example 5: Title search with more results
    print("\n🔍 Example 5: Title Search with Larger Page Size")
    results = importer.search(title="the", size=10)
    print_results(results, "Search by title containing 'the' (size=10)")

    print("\n" + "=" * 70)
    print("✓ Search examples completed!")
    print("=" * 70)
    print("\n💡 Tips:")
    print("   - lens_id: exact match in custom_fields.lens:id")
    print("   - title: case-insensitive partial match in metadata.title")
    print("   - Easily extensible: add more filters like author, date, etc.")
    print("   - Sort options: 'bestmatch', 'newest', 'oldest'")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
