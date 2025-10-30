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
        self, client: InvenioRDMClient, config: Optional[LensImportConfig] = None
    ):
        """
        Initialize Lens.org importer.

        Args:
            client: InvenioRDM API client
            config: Import configuration (uses default if None)
        """
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
                self.logger.info(
                    f"[DRY RUN] Would create record for Lens ID: {lens_id}"
                )

                # Log mapped metadata for verification
                import json

                metadata_dict = full_metadata.get("metadata", {})
                self.logger.info("=== MAPPED METADATA ===")
                self.logger.info(f"Title: {metadata_dict.get('title')}")
                self.logger.info(
                    f"Publication date: {metadata_dict.get('publication_date')}"
                )
                self.logger.info(f"Volume: {metadata_dict.get('volume')}")
                self.logger.info(f"Issue: {metadata_dict.get('issue')}")
                self.logger.info(f"Pages: {metadata_dict.get('pages')}")
                self.logger.info(f"Publisher: {metadata_dict.get('publisher')}")
                self.logger.info(f"Creators: {len(metadata_dict.get('creators', []))}")
                self.logger.info(
                    f"Subjects/Keywords: {len(metadata_dict.get('subjects', []))}"
                )
                self.logger.info(
                    f"Related identifiers: {len(metadata_dict.get('related_identifiers', []))}"
                )

                # Show related identifiers detail
                related_ids = metadata_dict.get("related_identifiers", [])
                if related_ids:
                    self.logger.info("Related identifiers:")
                    for rid in related_ids:
                        self.logger.info(
                            f"  - {rid.get('scheme')}: {rid.get('identifier')}"
                        )

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

            # Log creators with affiliations
            creators = metadata_dict.get("creators", [])
            creators_with_aff = sum(
                1 for c in creators if "affiliations" in c and c["affiliations"]
            )
            if creators_with_aff:
                self.logger.debug(
                    f"{creators_with_aff}/{len(creators)} creators have affiliations"
                )

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
                    f"  - {error['lens_id']}: "
                    f"[{error['error_type']}] {error['message']}"
                )
            if len(result.errors) > 5:
                self.logger.warning(f"  ... and {len(result.errors) - 5} more errors")

        if result.warnings:
            self.logger.info(f"Warnings: {len(result.warnings)}")


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
    import os

    # Read from environment variables if not provided
    if base_url is None:
        base_url = os.getenv("INVENIO_BASE_URL")

    if token is None:
        token = os.getenv("INVENIO_TOKEN") or os.getenv("INVENIO_API_TOKEN")

    client = InvenioRDMClient(base_url=base_url, token=token)
    return LensOrgImporter(client, config)
