"""
Integration tests for LensOrgImporter SDK methods: insert, update, delete, search.

These tests require a running InvenioRDM instance and valid credentials.
Each test starts with a clean database using the clean_database fixture.

Run with: pytest tests/test_sdk_integration.py -v
"""

import pytest
import time


@pytest.mark.integration
class TestInsert:
    """Test suite for insert() method."""

    def test_insert_minimal_record(self, lens_importer, clean_database, minimal_lens_record):
        """Test inserting a minimal valid record."""
        status, record_id, msg = lens_importer.insert(minimal_lens_record, publish=True)

        assert status == 201, f"Expected 201, got {status}: {msg}"
        assert record_id is not None, "Record ID should not be None"
        assert msg is None, f"Expected no error message, got: {msg}"

        # Wait for OpenSearch indexing
        time.sleep(3)

        # Verify record exists
        results = lens_importer.search(lens_id=minimal_lens_record["lens_id"])
        assert results["hits"]["total"] == 1

    def test_insert_full_record(self, lens_importer, clean_database, sample_lens_record):
        """Test inserting a complete record with all fields."""
        status, record_id, msg = lens_importer.insert(sample_lens_record, publish=True)

        assert status == 201
        assert record_id is not None
        assert msg is None

        # Wait for OpenSearch indexing
        time.sleep(3)

        # Verify custom fields preserved
        results = lens_importer.search(lens_id=sample_lens_record["lens_id"])
        assert results["hits"]["total"] == 1

        record = results["hits"]["hits"][0]
        custom_fields = record.get("custom_fields", {})
        assert custom_fields.get("lens:id") == sample_lens_record["lens_id"]

    def test_insert_unpublished_draft(self, lens_importer, clean_database, minimal_lens_record):
        """Test inserting a record without publishing (draft mode)."""
        status, draft_id, msg = lens_importer.insert(minimal_lens_record, publish=False)

        assert status == 201
        assert draft_id is not None
        assert msg is None

        # Note: Draft records may not appear in standard search
        # This is expected behavior

    def test_insert_duplicate_lens_id(self, lens_importer, clean_database, minimal_lens_record):
        """Test inserting two records with same lens_id creates both (duplicates allowed)."""
        # Insert first
        status1, record_id1, _ = lens_importer.insert(minimal_lens_record, publish=True)
        assert status1 == 201

        # Wait for indexing
        time.sleep(1)

        # Insert second with same lens_id
        status2, record_id2, _ = lens_importer.insert(minimal_lens_record, publish=True)
        assert status2 == 201

        # Wait for indexing
        time.sleep(1)

        # Both should exist (different record IDs)
        results = lens_importer.search(lens_id=minimal_lens_record["lens_id"])
        assert results["hits"]["total"] >= 2  # May be more if cleanup didn't run


@pytest.mark.integration
class TestUpdate:
    """Test suite for update() method."""

    def test_update_existing_record(self, lens_importer, clean_database, sample_lens_record):
        """Test updating an existing record's title and keywords."""
        # Insert initial record
        lens_id = sample_lens_record["lens_id"]
        status, record_id, _ = lens_importer.insert(sample_lens_record, publish=True)
        assert status == 201

        # Wait for indexing
        time.sleep(1)

        # Update record
        updated_data = sample_lens_record.copy()
        updated_data["title"] = sample_lens_record["title"] + " [UPDATED]"
        updated_data["keywords"] = sample_lens_record.get("keywords", []) + ["test-keyword"]

        status, updated_id, msg = lens_importer.update(lens_id, updated_data, publish=True)

        assert status == 200, f"Expected 200, got {status}: {msg}"
        assert updated_id == record_id or updated_id is not None
        assert msg is None

        # Wait for indexing
        time.sleep(1)

        # Verify custom fields preserved (lens_id should still exist)
        results = lens_importer.search(lens_id=lens_id)
        assert results["hits"]["total"] >= 1

        record = results["hits"]["hits"][0]
        custom_fields = record.get("custom_fields", {})
        assert custom_fields.get("lens:id") == lens_id, "lens_id custom field should be preserved"

    def test_update_nonexistent_record(self, lens_importer, clean_database):
        """Test updating a record that doesn't exist returns 404."""
        nonexistent_lens_id = "nonexistent-lens-id-99999"
        update_data = {"title": "This should fail"}

        status, record_id, msg = lens_importer.update(nonexistent_lens_id, update_data)

        assert status == 404
        assert record_id is None
        assert msg is not None
        assert "no record found" in msg.lower()

    def test_update_removes_duplicates(self, lens_importer, clean_database, sample_lens_record):
        """Test that update() removes duplicate records and keeps only the newest."""
        lens_id = sample_lens_record["lens_id"]

        # Insert same record twice (creates duplicates)
        lens_importer.insert(sample_lens_record, publish=True)
        time.sleep(0.5)
        lens_importer.insert(sample_lens_record, publish=True)
        time.sleep(1)

        # Should have 2 duplicates
        results_before = lens_importer.search(lens_id=lens_id)
        assert results_before["hits"]["total"] >= 2

        # Update should clean duplicates
        updated_data = sample_lens_record.copy()
        updated_data["title"] = sample_lens_record["title"] + " [DEDUPLICATED]"

        status, record_id, _ = lens_importer.update(lens_id, updated_data, publish=True)
        assert status == 200

        time.sleep(1)

        # Should now have only 1 record
        results_after = lens_importer.search(lens_id=lens_id)
        assert results_after["hits"]["total"] == 1


@pytest.mark.integration
class TestDelete:
    """Test suite for delete() method."""

    def test_delete_existing_record(self, lens_importer, clean_database, minimal_lens_record):
        """Test deleting an existing record."""
        lens_id = minimal_lens_record["lens_id"]

        # Insert record
        status, record_id, _ = lens_importer.insert(minimal_lens_record, publish=True)
        assert status == 201
        time.sleep(1)

        # Verify exists
        results_before = lens_importer.search(lens_id=lens_id)
        assert results_before["hits"]["total"] == 1

        # Delete record
        status, deleted_id, msg = lens_importer.delete(lens_id)

        assert status == 204
        assert deleted_id is not None

        time.sleep(1)

        # Verify deleted
        results_after = lens_importer.search(lens_id=lens_id)
        assert results_after["hits"]["total"] == 0

    def test_delete_nonexistent_record(self, lens_importer, clean_database):
        """Test deleting a record that doesn't exist returns 404."""
        nonexistent_lens_id = "nonexistent-lens-id-99999"

        status, record_id, msg = lens_importer.delete(nonexistent_lens_id)

        assert status == 404
        assert record_id is None
        assert msg is not None
        assert "no record found" in msg.lower()

    def test_delete_all_duplicates(self, lens_importer, clean_database, sample_lens_record):
        """Test that delete() removes ALL duplicate records with same lens_id."""
        lens_id = sample_lens_record["lens_id"]

        # Insert same record 3 times
        for _ in range(3):
            lens_importer.insert(sample_lens_record, publish=True)
            time.sleep(0.5)

        time.sleep(1)

        # Should have 3 duplicates
        results_before = lens_importer.search(lens_id=lens_id)
        assert results_before["hits"]["total"] >= 3

        # Delete should remove all
        status, _, msg = lens_importer.delete(lens_id)

        assert status == 204
        if msg:
            assert "duplicate" in msg.lower() or "3" in msg

        time.sleep(1)

        # All should be deleted
        results_after = lens_importer.search(lens_id=lens_id)
        assert results_after["hits"]["total"] == 0


@pytest.mark.integration
class TestSearch:
    """Test suite for search() method."""

    def test_search_by_lens_id(self, lens_importer, clean_database, sample_lens_record):
        """Test searching by lens_id (exact match)."""
        lens_id = sample_lens_record["lens_id"]

        # Insert record
        lens_importer.insert(sample_lens_record, publish=True)
        time.sleep(1)

        # Search by lens_id
        results = lens_importer.search(lens_id=lens_id)

        assert results["hits"]["total"] >= 1
        assert results["filters"]["lens_id"] == lens_id
        assert results["query"] == f'custom_fields.lens\\:id:"{lens_id}"'

        # Verify result
        record = results["hits"]["hits"][0]
        assert record.get("custom_fields", {}).get("lens:id") == lens_id

    def test_search_by_title(self, lens_importer, clean_database, sample_lens_record):
        """Test searching by title (case-insensitive partial match)."""
        # Insert record
        lens_importer.insert(sample_lens_record, publish=True)
        time.sleep(1)

        # Extract a word from title
        title = sample_lens_record["title"]
        search_word = title.split()[0] if title else "test"

        # Search by title
        results = lens_importer.search(title=search_word)

        assert results["hits"]["total"] >= 1
        assert results["filters"]["title"] == search_word

    def test_search_all_records(self, lens_importer, clean_database, sample_lens_records):
        """Test searching all records (no filters)."""
        # Insert multiple records
        for record in sample_lens_records:
            lens_importer.insert(record, publish=True)
            time.sleep(0.5)

        time.sleep(1)

        # Search all
        results = lens_importer.search()

        assert results["hits"]["total"] >= len(sample_lens_records)
        assert results["query"] == "*"
        assert results["filters"] == {}

    def test_search_pagination(self, lens_importer, clean_database, sample_lens_records):
        """Test search pagination."""
        # Insert multiple records
        for record in sample_lens_records:
            lens_importer.insert(record, publish=True)
            time.sleep(0.5)

        time.sleep(1)

        # Page 1
        results_p1 = lens_importer.search(size=2, page=1)
        assert len(results_p1["hits"]["hits"]) <= 2

        # Page 2
        results_p2 = lens_importer.search(size=2, page=2)
        # May have results or be empty depending on total count
        assert "hits" in results_p2

    def test_search_sorting(self, lens_importer, clean_database, sample_lens_records):
        """Test search sorting options."""
        # Insert multiple records
        for record in sample_lens_records:
            lens_importer.insert(record, publish=True)
            time.sleep(0.5)

        time.sleep(1)

        # Test different sort options
        for sort in ["bestmatch", "newest", "oldest"]:
            results = lens_importer.search(sort=sort)
            assert "hits" in results
            assert results["pagination"]["sort"] == sort

    def test_search_no_results(self, lens_importer, clean_database):
        """Test search with filters that match nothing."""
        results = lens_importer.search(lens_id="nonexistent-id-99999")

        assert results["hits"]["total"] == 0
        assert len(results["hits"]["hits"]) == 0


@pytest.mark.integration
@pytest.mark.slow
class TestIntegrationWorkflow:
    """End-to-end integration tests simulating real workflows."""

    def test_complete_crud_workflow(self, lens_importer, clean_database, sample_lens_record):
        """Test complete CRUD workflow: Create -> Read -> Update -> Delete."""
        lens_id = sample_lens_record["lens_id"]

        # CREATE
        status, record_id, _ = lens_importer.insert(sample_lens_record, publish=True)
        assert status == 201
        time.sleep(1)

        # READ
        search_results = lens_importer.search(lens_id=lens_id)
        assert search_results["hits"]["total"] == 1
        created_record = search_results["hits"]["hits"][0]
        assert created_record.get("custom_fields", {}).get("lens:id") == lens_id

        # UPDATE
        updated_data = sample_lens_record.copy()
        updated_data["title"] = sample_lens_record["title"] + " [MODIFIED]"

        status, updated_id, _ = lens_importer.update(lens_id, updated_data, publish=True)
        assert status == 200
        time.sleep(1)

        # Verify update
        search_results = lens_importer.search(lens_id=lens_id)
        assert search_results["hits"]["total"] == 1
        updated_record = search_results["hits"]["hits"][0]
        assert "[MODIFIED]" in updated_record["metadata"]["title"]

        # DELETE
        status, _, _ = lens_importer.delete(lens_id)
        assert status == 204
        time.sleep(1)

        # Verify deletion
        search_results = lens_importer.search(lens_id=lens_id)
        assert search_results["hits"]["total"] == 0

    def test_batch_import_workflow(self, lens_importer, clean_database, sample_lens_records):
        """Test batch import of multiple records."""
        imported_ids = []

        # Import batch
        for record in sample_lens_records:
            status, record_id, msg = lens_importer.insert(record, publish=True)
            assert status == 201, f"Failed to import {record.get('lens_id')}: {msg}"
            imported_ids.append(record_id)
            time.sleep(0.5)

        time.sleep(1)

        # Verify all imported
        for record in sample_lens_records:
            results = lens_importer.search(lens_id=record["lens_id"])
            assert results["hits"]["total"] >= 1

        # Verify total count
        all_results = lens_importer.search()
        assert all_results["hits"]["total"] >= len(sample_lens_records)
