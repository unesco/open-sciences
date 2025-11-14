"""
Main importer orchestrator for Lens.org publications to InvenioRDM.

Coordinates readers, mappers, and InvenioRDM client to perform complete imports.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from ...invenio_client import InvenioRDMClient
from .base import ImportResult, MappingError, ValidationError
from .config import LensImportConfig
from .reader import LensDataReader, create_reader
from .mappers import StandardFieldsMapper, CustomFieldsMapper, RelatedIdentifiersMapper

logger = logging.getLogger(__name__)


class LensOrgImporter:
    """
    Main orchestrator for importing Lens.org publications to InvenioRDM.

    Coordinates:
    - Data reading from various sources
    - Metadata mapping (standard + custom fields)
    - Record creation in InvenioRDM
    - Error handling and reporting
    """

    def __init__(
        self,
        client: Optional[InvenioRDMClient] = None,
        config: Optional[LensImportConfig] = None,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize Lens.org importer.

        Args:
            client: InvenioRDM API client (created if None)
            config: Import configuration (uses default if None)
            base_url: InvenioRDM base URL (used if client is None)
            token: API token (used if client is None)
        """
        # Create client if not provided
        if client is None:
            import os

            if base_url is None:
                base_url = os.getenv("OPENSCIENCE_TOOLS_BASE_URL") or os.getenv("INVENIO_BASE_URL")
            if token is None:
                token = os.getenv("OPENSCIENCE_TOOLS_TOKEN") or os.getenv("INVENIO_TOKEN")

            if not base_url or not token:
                raise ValueError("Either provide client or both base_url and token parameters")

            client = InvenioRDMClient(base_url=base_url, token=token)

        self.client = client
        self.config = config or LensImportConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize mappers
        self.standard_mapper = StandardFieldsMapper(config)
        self.custom_mapper = CustomFieldsMapper(config)
        self.related_mapper = RelatedIdentifiersMapper(config)

    def import_from_source(
        self,
        source: str,
        source_type: str = "auto",
        dry_run: bool = False,
        skip_existing: bool = True,
        batch_size: Optional[int] = None,
    ) -> ImportResult:
        """
        Import publications from a data source.

        Args:
            source: Path to data file or API endpoint
            source_type: Type of source ('json', 'api', 'auto')
            dry_run: If True, validate but don't create records
            skip_existing: If True, skip records with existing DOI
            batch_size: Records per batch (uses config default if None)

        Returns:
            ImportResult with statistics and errors
        """
        self.logger.info(f"Starting import from: {source}")

        # Create reader
        reader = create_reader(source, source_type)

        # Get records
        records = reader.read_records()
        self.logger.info(f"Loaded {len(records)} records")

        # Import records
        batch_size = batch_size or self.config.BATCH_SIZE
        result = self._import_records(
            records, dry_run=dry_run, skip_existing=skip_existing, batch_size=batch_size
        )

        # Log summary
        self._log_import_summary(result)

        return result

    def import_single_record(
        self, lens_record: Dict[str, Any], dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Import a single Lens.org publication record.

        Args:
            lens_record: Raw Lens.org publication record
            dry_run: If True, validate but don't create record

        Returns:
            Dict with import result

        Raises:
            MappingError: If mapping fails
            ValidationError: If validation fails
        """
        lens_id = lens_record.get("lens_id", "unknown")

        try:
            # Map metadata
            full_metadata = self._map_metadata(lens_record)

            if dry_run:
                self.logger.info(f"[DRY RUN] Would create record for Lens ID: {lens_id}")

                # Log mapped metadata for verification
                import json

                metadata_dict = full_metadata.get("metadata", {})
                self.logger.info("=== MAPPED METADATA ===")
                self.logger.info(f"Title: {metadata_dict.get('title')}")
                self.logger.info(f"Publication date: {metadata_dict.get('publication_date')}")
                self.logger.info(f"Volume: {metadata_dict.get('volume')}")
                self.logger.info(f"Issue: {metadata_dict.get('issue')}")
                self.logger.info(f"Pages: {metadata_dict.get('pages')}")
                self.logger.info(f"Publisher: {metadata_dict.get('publisher')}")
                self.logger.info(f"Creators: {len(metadata_dict.get('creators', []))}")
                self.logger.info(f"Subjects/Keywords: {len(metadata_dict.get('subjects', []))}")
                self.logger.info(
                    f"Related identifiers: {len(metadata_dict.get('related_identifiers', []))}"
                )

                # Show related identifiers detail
                related_ids = metadata_dict.get("related_identifiers", [])
                if related_ids:
                    self.logger.info("Related identifiers:")
                    for rid in related_ids:
                        self.logger.info(f"  - {rid.get('scheme')}: {rid.get('identifier')}")

                # Show subjects detail
                subjects = metadata_dict.get("subjects", [])
                if subjects:
                    self.logger.info(
                        f"Subjects (first 5): {[s.get('subject') for s in subjects[:5]]}"
                    )

                # Show custom fields
                custom_fields = metadata_dict.get("custom_fields", {})
                if custom_fields:
                    self.logger.info(f"Custom fields: {list(custom_fields.keys())}")

                return {
                    "status": "dry_run",
                    "lens_id": lens_id,
                    "metadata": full_metadata,
                }

            # Extract custom_fields from metadata for separate parameter
            # InvenioRDM API expects custom_fields as a separate parameter, not inside metadata
            metadata_dict = full_metadata.get("metadata", {})
            custom_fields = metadata_dict.pop("custom_fields", None)

            # Log custom fields if present
            if custom_fields:
                self.logger.info(f"Custom fields found: {list(custom_fields.keys())}")

            # Log related identifiers if present
            related_ids = metadata_dict.get("related_identifiers", [])
            if related_ids:
                self.logger.debug(
                    f"Including {len(related_ids)} related identifiers (DOI, PMID, ISSN, etc.)"
                )

            # Log subjects/keywords if present
            subjects = metadata_dict.get("subjects", [])
            if subjects:
                self.logger.debug(f"Including {len(subjects)} subjects/keywords")

            # Log publication details (journal custom field)
            if custom_fields:
                journal = custom_fields.get("journal:journal")
                if journal:
                    volume = journal.get("volume")
                    issue = journal.get("issue")
                    pages = journal.get("pages")
                    journal_title = journal.get("title")
                    self.logger.info(
                        f"Journal info - Title: {journal_title}, Volume: {volume}, Issue: {issue}, Pages: {pages}"
                    )

            # Log creators with affiliations
            creators = metadata_dict.get("creators", [])
            creators_with_aff = sum(
                1 for c in creators if "affiliations" in c and c["affiliations"]
            )
            if creators_with_aff:
                self.logger.debug(f"{creators_with_aff}/{len(creators)} creators have affiliations")

            # DEBUG: Log the metadata being sent
            import json

            self.logger.debug(
                f"Metadata being sent to InvenioRDM:\n{json.dumps(metadata_dict, indent=2)}"
            )

            # Log related_identifiers specifically for debugging
            if "related_identifiers" in metadata_dict:
                self.logger.info(
                    f"Related identifiers ({len(metadata_dict['related_identifiers'])}):"
                )
                for idx, rel_id in enumerate(metadata_dict["related_identifiers"]):
                    self.logger.info(
                        f"  [{idx}] scheme={rel_id.get('scheme')}, "
                        f"identifier={rel_id.get('identifier')[:50]}"
                    )

            # Set access configuration for metadata-only records (no files)
            access = {"record": "public", "files": "public", "status": "metadata-only"}

            # Disable files for metadata-only records
            files = {"enabled": False}

            # Create draft with separated metadata and custom_fields
            draft = self.client.create_draft(
                metadata=metadata_dict,
                access=access,
                files=files,
                custom_fields=custom_fields,
            )
            draft_id = draft.get("id")

            self.logger.info(f"Created draft {draft_id} for Lens ID: {lens_id}")

            # Publish draft
            record = self.client.publish_draft(draft_id)
            record_id = record.get("id")

            self.logger.info(f"Published record {record_id} for Lens ID: {lens_id}")

            return {
                "status": "success",
                "lens_id": lens_id,
                "record_id": record_id,
                "draft_id": draft_id,
                "metadata": full_metadata,
            }

        except Exception as e:
            self.logger.error(f"Failed to import Lens ID {lens_id}: {e}")
            raise

    def _import_records(
        self,
        records: List[Dict[str, Any]],
        dry_run: bool = False,
        skip_existing: bool = True,
        batch_size: int = 10,
    ) -> ImportResult:
        """
        Import multiple records with batching and error handling.

        Args:
            records: List of Lens.org publication records
            dry_run: If True, validate but don't create records
            skip_existing: If True, skip records with existing DOI
            batch_size: Number of records per batch

        Returns:
            ImportResult with statistics
        """
        result = ImportResult()
        result.total = len(records)

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(records) + batch_size - 1) // batch_size

            self.logger.info(f"Processing batch {batch_num}/{total_batches}")

            for record in batch:
                lens_id = record.get("lens_id", f"unknown_{result.total}")

                try:
                    # Check if should skip
                    if skip_existing and self._should_skip_record(record):
                        self.logger.info(f"Skipping existing record: {lens_id}")
                        result.skipped += 1
                        continue

                    # Import record
                    import_result = self.import_single_record(record, dry_run)

                    result.successful += 1
                    if not dry_run:
                        result.imported_ids.append(import_result["record_id"])

                except MappingError as e:
                    self.logger.warning(f"Mapping error for {lens_id}: {e}")
                    result.failed += 1
                    result.errors.append(
                        {"lens_id": lens_id, "error_type": "mapping", "message": str(e)}
                    )

                except ValidationError as e:
                    self.logger.warning(f"Validation error for {lens_id}: {e}")
                    result.failed += 1
                    result.errors.append(
                        {
                            "lens_id": lens_id,
                            "error_type": "validation",
                            "message": str(e),
                        }
                    )

                except Exception as e:
                    self.logger.error(f"Unexpected error for {lens_id}: {e}")
                    result.failed += 1
                    result.errors.append(
                        {
                            "lens_id": lens_id,
                            "error_type": "unexpected",
                            "message": str(e),
                        }
                    )

        return result

    def _map_metadata(self, lens_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Lens.org record to complete InvenioRDM metadata.

        Combines standard fields, custom fields, and related identifiers.

        Note: DOI is mapped as a related_identifier (not PID) because InvenioRDM
        only accepts PIDs with configured providers (DataCite, Crossref, etc.).
        External DOIs should remain in related_identifiers.

        Args:
            lens_record: Raw Lens.org publication record

        Returns:
            Complete InvenioRDM metadata dict
        """
        # Map standard fields (required)
        metadata = self.standard_mapper.map(lens_record)

        # Map custom fields (optional)
        custom_fields = self.custom_mapper.map(lens_record)
        if custom_fields:
            metadata["custom_fields"] = custom_fields

        # Map related identifiers (optional)
        # This includes DOI, PMID, ISSN, etc.
        related_identifiers = self.related_mapper.map(lens_record)
        if related_identifiers:
            metadata["related_identifiers"] = related_identifiers

        return {"metadata": metadata}

    def _should_skip_record(self, lens_record: Dict[str, Any]) -> bool:
        """
        Check if record should be skipped (e.g., already exists).

        Args:
            lens_record: Lens.org publication record

        Returns:
            True if record should be skipped
        """
        # Check if DOI already exists in InvenioRDM
        doi = lens_record.get("doi")

        if doi:
            # Search for existing record with this DOI
            try:
                query = f'metadata.identifiers.identifier:"{doi}"'
                results = self.client.search_records(query, size=1)

                if results.get("hits", {}).get("total", 0) > 0:
                    self.logger.debug(f"Record with DOI {doi} already exists")
                    return True

            except Exception as e:
                self.logger.warning(f"Error checking for existing DOI {doi}: {e}")

        return False

    def _log_import_summary(self, result: ImportResult):
        """
        Log summary of import operation.

        Args:
            result: ImportResult to summarize
        """
        self.logger.info("=" * 60)
        self.logger.info("IMPORT SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total records:     {result.total}")
        self.logger.info(f"Successful:        {result.successful}")
        self.logger.info(f"Failed:            {result.failed}")
        self.logger.info(f"Skipped:           {result.skipped}")
        self.logger.info("=" * 60)

        if result.errors:
            self.logger.warning(f"Errors encountered: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5 errors
                self.logger.warning(
                    f"  - {error['lens_id']}: " f"[{error['error_type']}] {error['message']}"
                )
            if len(result.errors) > 5:
                self.logger.warning(f"  ... and {len(result.errors) - 5} more errors")

        if result.warnings:
            self.logger.info(f"Warnings: {len(result.warnings)}")

    # =====================================
    # SDK METHODS (insert, update, delete)
    # =====================================

    def insert(
        self, data: Dict[str, Any], publish: bool = True
    ) -> tuple[int, Optional[str], Optional[str]]:
        """
        Insert a single Lens.org record into InvenioRDM.

        Args:
            data: Lens.org publication record (similar to publications.json entries)
            publish: If True, publish the draft immediately; if False, leave as draft

        Returns:
            Tuple of (status_code, record_id, message)
            - status_code: HTTP status code (201 for success, 4xx/5xx for errors)
            - record_id: InvenioRDM record ID if successful, None otherwise
            - message: Error message if failed, None otherwise

        Example:
            >>> importer = LensOrgImporter(base_url="...", token="...")
            >>> status, record_id, msg = importer.insert({
            ...     "lens_id": "000-035-558-593-934",
            ...     "title": "Test publication",
            ...     "authors": [...],
            ...     ...
            ... })
            >>> if status == 201:
            ...     print(f"Created record: {record_id}")
            ... else:
            ...     print(f"Error {status}: {msg}")
        """
        lens_id = data.get("lens_id", "unknown")

        try:
            # Map Lens metadata to InvenioRDM format
            full_metadata = self._map_metadata(data)

            # Extract components
            metadata_dict = full_metadata.get("metadata", {})
            custom_fields = metadata_dict.pop("custom_fields", None)

            # Set access configuration for metadata-only records
            access = {"record": "public", "files": "public", "status": "metadata-only"}
            files = {"enabled": False}

            # Create draft
            draft = self.client.create_draft(
                metadata=metadata_dict,
                access=access,
                files=files,
                custom_fields=custom_fields,
            )
            draft_id = draft.get("id")

            self.logger.info(f"Created draft {draft_id} for Lens ID: {lens_id}")

            if publish:
                # Publish the draft
                record = self.client.publish_draft(draft_id)
                record_id = record.get("id")
                self.logger.info(f"Published record {record_id} for Lens ID: {lens_id}")
                return (201, record_id, None)
            else:
                # Return draft ID without publishing
                self.logger.info(f"Draft {draft_id} created (not published)")
                return (201, draft_id, None)

        except Exception as e:
            error_msg = f"Failed to insert Lens ID {lens_id}: {str(e)}"
            self.logger.error(error_msg)

            # Try to extract status code from exception
            status_code = 500
            if hasattr(e, "response") and hasattr(e.response, "status_code"):
                status_code = e.response.status_code

            return (status_code, None, error_msg)

    def update(
        self, lens_id: str, data: Dict[str, Any], publish: bool = True
    ) -> tuple[int, Optional[str], Optional[str]]:
        """
        Update an existing Lens.org record in InvenioRDM by its lens_id.

        Searches for the record with the given lens_id and updates its metadata.
        If multiple records exist with the same lens_id, deletes the older ones
        and updates only the most recent one.

        Args:
            lens_id: Lens.org identifier to find the record
            data: Updated Lens.org publication data (partial or complete)
            publish: If True, publish changes immediately; if False, leave as draft

        Returns:
            Tuple of (status_code, record_id, message)
            - status_code: HTTP status code (200 for success, 404 if not found, 4xx/5xx for errors)
            - record_id: InvenioRDM record ID if successful, None otherwise
            - message: Error message if failed, None otherwise

        Example:
            >>> importer = LensOrgImporter(base_url="...", token="...")
            >>> status, record_id, msg = importer.update(
            ...     lens_id="000-035-558-593-934",
            ...     data={"title": "Updated title", ...}
            ... )
            >>> if status == 200:
            ...     print(f"Updated record: {record_id}")
            ... else:
            ...     print(f"Error {status}: {msg}")
        """
        try:
            # Search for all records with this lens_id in custom fields
            query = f'custom_fields.lens\\:id:"{lens_id}"'
            results = self.client.search_records(query, size=100)

            total = results.get("hits", {}).get("total", 0)
            if total == 0:
                error_msg = f"No record found with lens_id: {lens_id}"
                self.logger.warning(error_msg)
                return (404, None, error_msg)

            hits = results["hits"]["hits"]

            # If multiple records, delete all but the most recent
            if total > 1:
                self.logger.warning(f"Found {total} duplicate records with lens_id: {lens_id}")

                # Sort by creation date (most recent first)
                sorted_hits = sorted(hits, key=lambda x: x.get("created", ""), reverse=True)

                # Keep the most recent, delete the rest
                record_to_keep = sorted_hits[0]
                records_to_delete = sorted_hits[1:]

                for old_record in records_to_delete:
                    old_record_id = old_record.get("id")
                    try:
                        self.client.delete_record(old_record_id)
                        self.logger.info(f"Deleted duplicate record {old_record_id}")
                    except Exception as e:
                        self.logger.warning(f"Failed to delete duplicate {old_record_id}: {e}")

                record = record_to_keep
            else:
                # Single record found
                record = hits[0]

            # Get the record ID
            record_id = record.get("id")

            self.logger.info(f"Found record {record_id} for Lens ID: {lens_id}")

            # Create a draft from the published record (required for editing)
            try:
                draft = self.client.create_draft_from_record(record_id)
                self.logger.info(f"Created draft from published record {record_id}")
            except Exception as e:
                # If draft already exists, that's OK - we'll update it
                self.logger.debug(f"Draft may already exist or record is already a draft: {e}")

            # Merge data with lens_id to ensure it's preserved
            update_data = {**data, "lens_id": lens_id}

            # Map updated metadata
            full_metadata = self._map_metadata(update_data)
            metadata_dict = full_metadata.get("metadata", {})
            custom_fields = metadata_dict.pop("custom_fields", {})

            # Set access configuration
            access = {"record": "public", "files": "public", "status": "metadata-only"}
            files = {"enabled": False}

            # Update draft with metadata AND custom_fields
            updated_draft = self.client.update_draft(
                record_id=record_id,
                metadata=metadata_dict,
                custom_fields=custom_fields,
                access=access,
                files=files,
            )

            self.logger.info(f"Updated draft {record_id} for Lens ID: {lens_id}")

            if publish:
                # Publish the updated draft
                published_record = self.client.publish_draft(record_id)
                self.logger.info(f"Published updated record {record_id}")
                return (200, record_id, None)
            else:
                self.logger.info(f"Draft {record_id} updated (not published)")
                return (200, record_id, None)

        except Exception as e:
            error_msg = f"Failed to update Lens ID {lens_id}: {str(e)}"
            self.logger.error(error_msg)

            # Extract status code
            status_code = 500
            if hasattr(e, "response") and hasattr(e.response, "status_code"):
                status_code = e.response.status_code

            return (status_code, None, error_msg)

    def delete(self, lens_id: str) -> tuple[int, Optional[str], Optional[str]]:
        """
        Delete all existing Lens.org records from InvenioRDM with the given lens_id.

        Searches for all records with the given lens_id and permanently deletes them.
        If multiple records exist with the same lens_id, all of them will be deleted.

        Args:
            lens_id: Lens.org identifier to find and delete the record(s)

        Returns:
            Tuple of (status_code, record_id, message)
            - status_code: HTTP status code (204 for success, 404 if not found, 4xx/5xx for errors)
            - record_id: Last deleted InvenioRDM record ID (if successful), None otherwise
            - message: Error message if failed, info message if multiple deleted, None for single deletion

        Example:
            >>> importer = LensOrgImporter(base_url="...", token="...")
            >>> status, record_id, msg = importer.delete(lens_id="000-035-558-593-934")
            >>> if status == 204:
            ...     print(f"Deleted record(s): {record_id}")
            ... else:
            ...     print(f"Error {status}: {msg}")
        """
        try:
            # Search for all records with this lens_id
            query = f'custom_fields.lens\\:id:"{lens_id}"'
            results = self.client.search_records(query, size=100)

            total = results.get("hits", {}).get("total", 0)
            if total == 0:
                error_msg = f"No record found with lens_id: {lens_id}"
                self.logger.warning(error_msg)
                return (404, None, error_msg)

            hits = results["hits"]["hits"]

            if total > 1:
                self.logger.warning(f"Found {total} records with lens_id: {lens_id}, deleting all")

            # Delete all records with this lens_id
            deleted_count = 0
            last_deleted_id = None
            errors = []

            for record in hits:
                record_id = record.get("id")
                try:
                    success = self.client.delete_record(record_id)
                    if success:
                        self.logger.info(f"Deleted record {record_id} (Lens ID: {lens_id})")
                        deleted_count += 1
                        last_deleted_id = record_id
                    else:
                        error_msg = f"Failed to delete record {record_id}"
                        self.logger.error(error_msg)
                        errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Error deleting record {record_id}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)

            # Return result based on what happened
            if deleted_count == 0:
                # All deletions failed
                error_msg = "; ".join(errors) if errors else "Failed to delete any records"
                return (500, None, error_msg)
            elif deleted_count < total:
                # Partial success
                info_msg = f"Deleted {deleted_count}/{total} records. Errors: {'; '.join(errors)}"
                self.logger.warning(info_msg)
                return (204, last_deleted_id, info_msg)
            else:
                # All deleted successfully
                if total > 1:
                    info_msg = f"Deleted all {total} duplicate records"
                    return (204, last_deleted_id, info_msg)
                else:
                    return (204, last_deleted_id, None)

        except Exception as e:
            error_msg = f"Failed to delete Lens ID {lens_id}: {str(e)}"
            self.logger.error(error_msg)

            # Extract status code
            status_code = 500
            if hasattr(e, "response") and hasattr(e.response, "status_code"):
                status_code = e.response.status_code

            return (status_code, None, error_msg)

    def search(
        self,
        lens_id: Optional[str] = None,
        title: Optional[str] = None,
        size: int = 10,
        page: int = 1,
        sort: str = "bestmatch",
    ) -> Dict[str, Any]:
        """
        Search for records in InvenioRDM using various filters.

        Builds a query from provided filters and executes search.
        Easily extensible by adding more filter parameters.

        Args:
            lens_id: Filter by Lens.org ID (exact match in custom_fields)
            title: Filter by title (case-insensitive partial match)
            size: Number of results per page (default: 10)
            page: Page number (default: 1)
            sort: Sort order - 'bestmatch', 'newest', 'oldest' (default: 'bestmatch')

        Returns:
            Dict with search results:
            {
                'hits': {
                    'total': int,
                    'hits': [list of records]
                },
                'query': str,
                'filters': dict
            }

        Example:
            >>> importer = LensOrgImporter(base_url="...", token="...")

            # Search by lens_id
            >>> results = importer.search(lens_id="000-035-558-593-934")

            # Search by title (case-insensitive)
            >>> results = importer.search(title="climate change")

            # Combine filters
            >>> results = importer.search(title="disaster", size=20, sort="newest")

            # Access results
            >>> total = results['hits']['total']
            >>> records = results['hits']['hits']
            >>> for record in records:
            ...     print(record['id'], record['metadata']['title'])
        """
        # Build query parts
        query_parts = []
        filters_used = {}

        # Filter by lens_id (exact match in custom_fields)
        if lens_id:
            query_parts.append(f'custom_fields.lens\\:id:"{lens_id}"')
            filters_used["lens_id"] = lens_id

        # Filter by title (case-insensitive partial match)
        if title:
            # Escape special characters and use case-insensitive search
            escaped_title = title.replace('"', '\\"')
            query_parts.append(f'metadata.title:"{escaped_title}"')
            filters_used["title"] = title

        # Combine query parts with AND
        if query_parts:
            query = " AND ".join(query_parts)
        else:
            # No filters - search all records
            query = "*"

        self.logger.info(f"Searching with query: {query}")

        try:
            # Execute search
            results = self.client.search_records(query=query, size=size, page=page, sort=sort)

            # Add metadata about the search
            search_result = {
                "hits": results.get("hits", {"total": 0, "hits": []}),
                "query": query,
                "filters": filters_used,
                "pagination": {"size": size, "page": page, "sort": sort},
            }

            total = results.get("hits", {}).get("total", 0)
            self.logger.info(f"Found {total} records matching filters")

            return search_result

        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "hits": {"total": 0, "hits": []},
                "query": query,
                "filters": filters_used,
                "error": error_msg,
            }


def create_importer(
    base_url: Optional[str] = None,
    token: Optional[str] = None,
    config: Optional[LensImportConfig] = None,
) -> LensOrgImporter:
    """
    Factory function to create LensOrgImporter with InvenioRDM client.

    Args:
        base_url: InvenioRDM base URL (uses env var if None)
        token: InvenioRDM API token (uses env var if None)
        config: Import configuration (uses default if None)

    Returns:
        Configured LensOrgImporter instance
    """
    return LensOrgImporter(base_url=base_url, token=token, config=config)
