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
                return {
                    "status": "dry_run",
                    "lens_id": lens_id,
                    "metadata": full_metadata,
                }

            # Extract custom_fields from metadata for separate parameter
            # InvenioRDM API expects custom_fields as a separate parameter, not inside metadata
            metadata_dict = full_metadata.get("metadata", {})
            custom_fields = metadata_dict.pop("custom_fields", None)

            # DEBUG: Log custom fields
            if custom_fields:
                self.logger.info(f"Custom fields found: {list(custom_fields.keys())}")
            else:
                self.logger.warning("No custom fields found in mapped metadata")

            # TODO: Related identifiers seem to cause 500 errors - temporarily disable
            related_ids = metadata_dict.pop("related_identifiers", None)
            if related_ids:
                self.logger.debug(
                    f"Temporarily skipping {len(related_ids)} related identifiers (debugging)"
                )

            # TODO: Subjects might cause 500 errors - temporarily disable for testing
            subjects = metadata_dict.pop("subjects", None)
            if subjects:
                self.logger.debug(
                    f"Temporarily skipping {len(subjects)} subjects (debugging)"
                )

            # TODO: Remove affiliations from creators for testing
            if "creators" in metadata_dict:
                for creator in metadata_dict["creators"]:
                    if "affiliations" in creator:
                        del creator["affiliations"]
                self.logger.debug("Removed affiliations from creators (debugging)")

            # DEBUG: Log the metadata being sent
            import json

            self.logger.debug(
                f"Metadata being sent to InvenioRDM:\n{json.dumps(metadata_dict, indent=2)}"
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
