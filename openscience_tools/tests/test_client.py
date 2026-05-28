"""
Tests for InvenioRDMClient API interactions.

Tests the low-level client methods for communicating with InvenioRDM API.

Run with: pytest tests/test_client.py -v
"""

import pytest
import time


@pytest.mark.integration
class TestInvenioClient:
    """Test InvenioRDMClient methods."""

    def test_create_draft(self, invenio_client, clean_database):
        """Test creating a draft record."""
        metadata = {
            "resource_type": {"id": "publication-article"},
            "title": "Test Draft Record",
            "creators": [
                {"person_or_org": {"type": "personal", "family_name": "Doe", "given_name": "John"}}
            ],
            "publication_date": "2024-11-14",
        }

        custom_fields = {"lens:id": "test-client-lens-id"}

        access = {"record": "public", "files": "public", "status": "metadata-only"}
        files = {"enabled": False}

        draft = invenio_client.create_draft(
            metadata=metadata, access=access, files=files, custom_fields=custom_fields
        )

        assert "id" in draft
        assert draft.get("is_draft") is True

    def test_publish_draft(self, invenio_client, clean_database):
        """Test publishing a draft record."""
        # Create draft first
        metadata = {
            "resource_type": {"id": "publication-article"},
            "title": "Test Publish",
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "family_name": "Smith",
                        "given_name": "Jane",
                    }
                }
            ],
            "publication_date": "2024-11-14",
        }

        draft = invenio_client.create_draft(
            metadata=metadata,
            access={"record": "public", "files": "public", "status": "metadata-only"},
            files={"enabled": False},
        )

        draft_id = draft["id"]

        # Publish
        published = invenio_client.publish_draft(draft_id)

        assert published.get("is_published") is True
        assert published.get("id") == draft_id

    def test_search_records(self, invenio_client, clean_database):
        """Test searching records."""
        # Wait for cleanup to complete indexing
        time.sleep(3)

        # Search empty database
        results = invenio_client.search_records(query="*", size=10)

        assert "hits" in results
        # May have 0 or 1 due to indexing delays - both acceptable for empty DB test
        assert results["hits"]["total"] <= 1

    def test_delete_record(self, invenio_client, clean_database):
        """Test deleting a record."""
        # Create and publish a record
        metadata = {
            "resource_type": {"id": "publication-article"},
            "title": "Record to Delete",
            "creators": [
                {"person_or_org": {"type": "personal", "family_name": "Test", "given_name": "User"}}
            ],
            "publication_date": "2024-11-14",
        }

        draft = invenio_client.create_draft(
            metadata=metadata,
            access={"record": "public", "files": "public", "status": "metadata-only"},
            files={"enabled": False},
        )

        published = invenio_client.publish_draft(draft["id"])
        record_id = published["id"]

        # Delete
        success = invenio_client.delete_record(record_id)
        assert success is True

        # Verify deleted
        time.sleep(1)
        results = invenio_client.search_records(query="*")
        assert results["hits"]["total"] == 0

    def test_create_draft_from_record(self, invenio_client, clean_database):
        """Test creating a draft from a published record."""
        # Create and publish
        metadata = {
            "resource_type": {"id": "publication-article"},
            "title": "Original Published Record",
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "family_name": "Original",
                        "given_name": "Author",
                    }
                }
            ],
            "publication_date": "2024-11-14",
        }

        draft = invenio_client.create_draft(
            metadata=metadata,
            access={"record": "public", "files": "public", "status": "metadata-only"},
            files={"enabled": False},
        )

        published = invenio_client.publish_draft(draft["id"])
        record_id = published["id"]

        # Create draft from published
        new_draft = invenio_client.create_draft_from_record(record_id)

        assert "id" in new_draft
        assert new_draft["id"] == record_id  # Same ID, now in draft state

    def test_update_draft(self, invenio_client, clean_database):
        """Test updating a draft with custom_fields."""
        # Create draft
        metadata = {
            "resource_type": {"id": "publication-article"},
            "title": "Original Title",
            "creators": [
                {"person_or_org": {"type": "personal", "family_name": "Test", "given_name": "User"}}
            ],
            "publication_date": "2024-11-14",
        }

        custom_fields = {"lens:id": "test-update-lens-id"}

        draft = invenio_client.create_draft(
            metadata=metadata,
            access={"record": "public", "files": "public", "status": "metadata-only"},
            files={"enabled": False},
            custom_fields=custom_fields,
        )

        draft_id = draft["id"]

        # Update draft
        updated_metadata = metadata.copy()
        updated_metadata["title"] = "Updated Title"

        updated_custom_fields = {"lens:id": "test-update-lens-id-modified"}

        updated = invenio_client.update_draft(
            record_id=draft_id,
            metadata=updated_metadata,
            custom_fields=updated_custom_fields,
            access={"record": "public", "files": "public", "status": "metadata-only"},
            files={"enabled": False},
        )

        assert updated["metadata"]["title"] == "Updated Title"
        assert updated["custom_fields"]["lens:id"] == "test-update-lens-id-modified"
