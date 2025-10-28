#!/usr/bin/env python3
"""
Test script to validate Lens.org mapping without creating records.

This script tests the mapping of Lens.org data to InvenioRDM format
by loading a sample record and displaying the mapped metadata.
"""

import sys
import json
from pathlib import Path
from pprint import pprint

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sources.lens.reader import JSONFileReader
from src.sources.lens.mappers import (
    StandardFieldsMapper,
    CustomFieldsMapper,
    RelatedIdentifiersMapper,
)
from src.sources.lens.config import LensImportConfig


def test_mapping(json_file: str, record_index: int = 0):
    """
    Test mapping for a single record.

    Args:
        json_file: Path to Lens.org JSON file
        record_index: Index of record to test (default: 0 = first record)
    """
    print("=" * 70)
    print("LENS.ORG MAPPING TEST")
    print("=" * 70)
    print()

    # Load data
    print(f"📂 Loading data from: {json_file}")
    reader = JSONFileReader(json_file)
    records = reader.read_records()

    print(f"✓ Loaded {len(records)} records")
    print()

    # Get test record
    if record_index >= len(records):
        print(
            f"❌ Error: Record index {record_index} out of range (0-{len(records)-1})"
        )
        sys.exit(1)

    lens_record = records[record_index]
    lens_id = lens_record.get("lens_id", "unknown")

    print(f"🔬 Testing record {record_index}: {lens_id}")
    print(f"   Title: {lens_record.get('title', 'N/A')[:80]}...")
    print(f"   DEBUG: Record has 'authors' key: {'authors' in lens_record}")
    if "authors" in lens_record:
        print(f"   DEBUG: Number of authors: {len(lens_record['authors'])}")
    print()

    # Initialize mappers
    config = LensImportConfig()
    standard_mapper = StandardFieldsMapper(config)
    custom_mapper = CustomFieldsMapper(config)
    related_mapper = RelatedIdentifiersMapper(config)

    # Map standard fields
    print("=" * 70)
    print("STANDARD FIELDS MAPPING")
    print("=" * 70)
    try:
        standard_metadata = standard_mapper.map(lens_record)
        print("✓ Standard fields mapped successfully")
        print()
        pprint(standard_metadata, width=100, compact=False)
    except Exception as e:
        print(f"❌ Error mapping standard fields: {e}")
        import traceback

        traceback.print_exc()

    print()

    # Map custom fields
    print("=" * 70)
    print("CUSTOM FIELDS MAPPING")
    print("=" * 70)
    try:
        custom_metadata = custom_mapper.map(lens_record)
        if custom_metadata:
            print(f"✓ Mapped {len(custom_metadata)} custom field groups")
            print()
            pprint(custom_metadata, width=100, compact=False)
        else:
            print("⚠ No custom fields mapped")
    except Exception as e:
        print(f"❌ Error mapping custom fields: {e}")
        import traceback

        traceback.print_exc()

    print()

    # Map related identifiers
    print("=" * 70)
    print("RELATED IDENTIFIERS MAPPING")
    print("=" * 70)
    try:
        related_ids = related_mapper.map(lens_record)
        if related_ids:
            print(f"✓ Mapped {len(related_ids)} related identifiers")
            print()
            pprint(related_ids, width=100, compact=False)
        else:
            print("⚠ No related identifiers mapped")
    except Exception as e:
        print(f"❌ Error mapping related identifiers: {e}")
        import traceback

        traceback.print_exc()

    print()

    # Complete metadata structure
    print("=" * 70)
    print("COMPLETE INVENIO RDM METADATA STRUCTURE")
    print("=" * 70)

    metadata = {"metadata": standard_metadata}

    if custom_metadata:
        metadata["metadata"]["custom_fields"] = custom_metadata

    if related_ids:
        metadata["metadata"]["related_identifiers"] = related_ids

    print("✓ Complete metadata structure:")
    print()
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Lens.org to InvenioRDM mapping")
    parser.add_argument("json_file", help="Path to Lens.org JSON file")
    parser.add_argument(
        "--index", type=int, default=0, help="Index of record to test (default: 0)"
    )

    args = parser.parse_args()

    test_mapping(args.json_file, args.index)
