"""
Import orchestrator for Zenodo records.

This module handles the complete import workflow:
- Fetching records from Zenodo
- Mapping metadata to InvenioRDM format
- Creating drafts in InvenioRDM
- Downloading and uploading files
- Publishing records
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.invenio_client import InvenioRDMClient
from .fetcher import ZenodoFetcher
from .mapper import ZenodoMapper

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Result of importing a single record."""

    success: bool
    zenodo_id: str
    invenio_id: Optional[str] = None
    title: Optional[str] = None
    doi: Optional[str] = None
    files_count: int = 0
    error: Optional[str] = None


class ZenodoImporter:
    """Orchestrates the import of Zenodo records to InvenioRDM."""

    def __init__(
        self,
        invenio_client: InvenioRDMClient,
        zenodo_fetcher: ZenodoFetcher,
        mapper: ZenodoMapper,
    ):
        """
        Initialize Zenodo importer.

        Args:
            invenio_client: InvenioRDM API client
            zenodo_fetcher: Zenodo API fetcher
            mapper: Metadata mapper
        """
        self.client = invenio_client
        self.fetcher = zenodo_fetcher
        self.mapper = mapper
        logger.info("Zenodo importer initialized")

    def import_record(
        self,
        record_id: str,
        skip_files: bool = False,
        dry_run: bool = False,
    ) -> ImportResult:
        """
        Import a single record from Zenodo to InvenioRDM.

        Args:
            record_id: Zenodo record ID
            skip_files: If True, don't download and upload files
            dry_run: If True, only validate without creating records

        Returns:
            ImportResult with details of the import
        """
        try:
            # Fetch Zenodo record
            logger.info(f"Importing Zenodo record: {record_id}")
            zenodo_record = self.fetcher.fetch_record(record_id)

            # Extract record info
            zenodo_meta = zenodo_record.get("metadata", {})
            title = zenodo_meta.get("title", "Untitled")
            doi = zenodo_record.get("doi", "N/A")
            files = zenodo_record.get("files", [])
            files_count = len(files)

            logger.info(f"Record: {title}")
            logger.info(f"DOI: {doi}")
            logger.info(f"Files: {files_count}")

            # Map metadata
            invenio_data = self.mapper.map_record(zenodo_record)

            # If skipping files or no files, disable files in metadata
            if skip_files or files_count == 0:
                invenio_data["files"]["enabled"] = False

            if dry_run:
                logger.info("DRY RUN - Validation successful")
                return ImportResult(
                    success=True,
                    zenodo_id=record_id,
                    title=title,
                    doi=doi,
                    files_count=files_count if not skip_files else 0,
                )

            # Create draft
            logger.info("Creating draft record in InvenioRDM...")
            draft = self.client.create_draft(
                metadata=invenio_data["metadata"],
                access=invenio_data.get("access"),
                files=invenio_data.get("files"),
            )
            draft_id = draft["id"]
            logger.info(f"Draft created: {draft_id}")

            # Download and upload files if requested
            if not skip_files and files_count > 0:
                logger.info(f"Processing {files_count} file(s)...")
                self._process_files(draft_id, files)

            # Publish record
            logger.info("Publishing record...")
            published = self.client.publish_draft(draft_id)
            invenio_id = published["id"]

            logger.info(f"Successfully imported record: {invenio_id}")

            return ImportResult(
                success=True,
                zenodo_id=record_id,
                invenio_id=invenio_id,
                title=title,
                doi=doi,
                files_count=files_count if not skip_files else 0,
            )

        except Exception as e:
            logger.error(f"Error importing record {record_id}: {e}")
            return ImportResult(
                success=False,
                zenodo_id=record_id,
                error=str(e),
            )

    def import_multiple(
        self,
        record_ids: List[str],
        skip_files: bool = False,
        dry_run: bool = False,
        skip_errors: bool = True,
    ) -> List[ImportResult]:
        """
        Import multiple records from Zenodo.

        Args:
            record_ids: List of Zenodo record IDs
            skip_files: If True, don't download and upload files
            dry_run: If True, only validate without creating records
            skip_errors: If True, continue on errors; if False, stop on first error

        Returns:
            List of ImportResult objects
        """
        results = []

        logger.info(f"Starting import of {len(record_ids)} records")

        for i, record_id in enumerate(record_ids, 1):
            logger.info(f"Processing record {i}/{len(record_ids)}")

            result = self.import_record(record_id, skip_files, dry_run)
            results.append(result)

            if not result.success and not skip_errors:
                logger.error(f"Stopping import due to error in record {record_id}")
                break

        # Summary
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)

        logger.info(f"Import completed: {successful} successful, {failed} failed")

        return results

    def search_and_import(
        self,
        query: str,
        max_results: int = 10,
        skip_files: bool = False,
        dry_run: bool = False,
        skip_errors: bool = True,
    ) -> List[ImportResult]:
        """
        Search Zenodo and import matching records.

        Args:
            query: Search query string
            max_results: Maximum number of results to import
            skip_files: If True, don't download and upload files
            dry_run: If True, only validate without creating records
            skip_errors: If True, continue on errors; if False, stop on first error

        Returns:
            List of ImportResult objects
        """
        # Search Zenodo
        logger.info(f"Searching Zenodo: '{query}'")
        records = self.fetcher.search_records(query, max_results)

        if not records:
            logger.warning("No records found")
            return []

        # Extract record IDs
        record_ids = []
        for record in records:
            zenodo_id = record.get("id") or record.get("recid")
            if zenodo_id:
                record_ids.append(str(zenodo_id))

        # Import records
        return self.import_multiple(record_ids, skip_files, dry_run, skip_errors)

    def _process_files(self, draft_id: str, files: List[Dict[str, Any]]) -> None:
        """
        Download files from Zenodo and upload to InvenioRDM draft.

        Args:
            draft_id: InvenioRDM draft ID
            files: List of file metadata from Zenodo
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for file_info in files:
                filename = file_info.get("key", "")
                file_url = file_info["links"]["self"]

                try:
                    # Download file
                    logger.info(f"Downloading: {filename}")
                    local_file = self.fetcher.download_file(
                        file_url, filename, temp_path
                    )

                    # Upload to InvenioRDM
                    logger.info(f"Uploading to InvenioRDM: {filename}")
                    self.client.upload_file_to_draft(draft_id, str(local_file))

                    logger.info(f"Successfully processed file: {filename}")

                except Exception as e:
                    logger.error(f"Error processing file {filename}: {e}")
                    # Continue with other files


def create_importer(
    invenio_client: InvenioRDMClient,
    zenodo_fetcher: ZenodoFetcher,
    mapper: ZenodoMapper,
) -> ZenodoImporter:
    """
    Create a Zenodo importer instance.

    Args:
        invenio_client: InvenioRDM API client
        zenodo_fetcher: Zenodo API fetcher
        mapper: Metadata mapper

    Returns:
        Configured ZenodoImporter instance
    """
    return ZenodoImporter(
        invenio_client=invenio_client,
        zenodo_fetcher=zenodo_fetcher,
        mapper=mapper,
    )
