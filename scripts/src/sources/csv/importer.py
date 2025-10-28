"""
CSV importer for InvenioRDM.

This module handles the import process of CSV records into InvenioRDM,
including record creation, updates, file uploads, and publishing.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ...invenio_client import InvenioRDMClient, create_client_from_env
from .mapper import CSVMapper, create_mapper
from .config import CSVImportConfig

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Results from an import operation."""

    total: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    created: int = 0
    updated: int = 0
    published: int = 0
    errors: List[Dict[str, Any]] = None
    warnings: List[str] = None
    record_ids: List[str] = None

    def __post_init__(self):
        """Initialize mutable default values."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.record_ids is None:
            self.record_ids = []


class CSVImporter:
    """
    Importer for CSV records into InvenioRDM.

    This class orchestrates the import process, handling record creation,
    updates, file uploads, and publishing.
    """

    def __init__(
        self,
        client: Optional[InvenioRDMClient] = None,
        mapper: Optional[CSVMapper] = None,
    ):
        """
        Initialize the CSV importer.

        Args:
            client: InvenioRDM client (creates from env if not provided)
            mapper: CSV mapper (creates default if not provided)
        """
        self.client = client or create_client_from_env()
        self.mapper = mapper or create_mapper()
        self.config = CSVImportConfig

        logger.info("CSV importer initialized")

    def import_records(
        self,
        records: List[Dict[str, str]],
        dry_run: bool = False,
        skip_errors: bool = False,
        batch_size: int = None,
    ) -> ImportResult:
        """
        Import multiple CSV records.

        Args:
            records: List of CSV rows as dictionaries
            dry_run: If True, validate without creating records
            skip_errors: If True, continue on errors
            batch_size: Number of records to process per batch

        Returns:
            ImportResult with operation statistics
        """
        batch_size = batch_size or self.config.BATCH_SIZE
        result = ImportResult()
        result.total = len(records)

        logger.info(
            f"Starting import of {result.total} records "
            f"(dry_run={dry_run}, skip_errors={skip_errors}, batch_size={batch_size})"
        )

        # Process records
        for idx, row in enumerate(records):
            row_num = row.get("_row_number", idx + 2)  # +2 for header and 1-indexing

            try:
                record_result = self._import_single_record(row, dry_run=dry_run)

                if record_result["success"]:
                    result.successful += 1
                    if record_result.get("record_id"):
                        result.record_ids.append(record_result["record_id"])

                    # Track operation type
                    if record_result["operation"].startswith("create"):
                        result.created += 1
                    elif record_result["operation"].startswith("update"):
                        result.updated += 1

                    # Track publishing
                    if record_result.get("published"):
                        result.published += 1

                    # Track warnings
                    if record_result.get("warnings"):
                        result.warnings.extend(record_result["warnings"])

                else:
                    result.failed += 1
                    result.errors.append(
                        {
                            "row": row_num,
                            "title": record_result.get("title", ""),
                            "error": record_result.get("error", "Unknown error"),
                        }
                    )

                    if not skip_errors:
                        logger.error(f"Stopping import due to error at row {row_num}")
                        break

            except Exception as e:
                result.failed += 1
                result.errors.append(
                    {"row": row_num, "title": row.get("title", ""), "error": str(e)}
                )

                logger.exception(f"Unexpected error processing row {row_num}")

                if not skip_errors:
                    logger.error(f"Stopping import due to error at row {row_num}")
                    break

        logger.info(
            f"Import completed: {result.successful} successful, "
            f"{result.failed} failed, {result.skipped} skipped"
        )

        return result

    def _import_single_record(
        self, row: Dict[str, str], dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Import a single CSV record.

        Args:
            row: CSV row as dictionary
            dry_run: If True, only validate

        Returns:
            Dictionary with operation result
        """
        result = {
            "success": False,
            "operation": None,
            "record_id": None,
            "error": None,
            "title": row.get("title", ""),
            "warnings": [],
        }

        try:
            # Map CSV row to InvenioRDM format
            metadata, access, files_config, file_paths, should_publish = (
                self.mapper.map_record(row)
            )

            # Get existing record ID if present
            existing_record_id = self.mapper.get_existing_record_id(row)

            # Dry run mode - just validate
            if dry_run:
                if existing_record_id:
                    result["operation"] = "update (dry-run)"
                    result["record_id"] = existing_record_id
                else:
                    result["operation"] = "create (dry-run)"
                result["success"] = True
                return result

            # Check if updating existing record
            if existing_record_id and self._record_exists(existing_record_id):
                result["operation"] = "update"
                result["record_id"] = existing_record_id
                draft = self._update_record(
                    existing_record_id, metadata, access, files_config
                )
            else:
                result["operation"] = "create"
                draft = self._create_record(metadata, access, files_config)
                result["record_id"] = draft["id"]

            # Upload files if specified
            if file_paths:
                self._upload_files(result["record_id"], file_paths, result["warnings"])

            # Publish if requested
            if should_publish:
                try:
                    self.client.publish_draft(result["record_id"])
                    result["published"] = True
                    logger.info(f"Published record {result['record_id']}")
                except Exception as e:
                    result["published"] = False
                    result["warnings"].append(f"Failed to publish: {str(e)}")
                    logger.warning(
                        f"Failed to publish record {result['record_id']}: {e}"
                    )

            result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Failed to import record '{result['title']}': {e}")

        return result

    def _record_exists(self, record_id: str) -> bool:
        """
        Check if a record exists.

        Args:
            record_id: Record identifier

        Returns:
            True if record exists, False otherwise
        """
        try:
            self.client.get_record(record_id)
            return True
        except Exception:
            return False

    def _create_record(
        self, metadata: Dict[str, Any], access: Dict[str, str], files: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Create a new record draft.

        Args:
            metadata: Record metadata
            access: Access settings
            files: Files configuration

        Returns:
            Created draft
        """
        logger.info(f"Creating new record: {metadata.get('title', 'Untitled')}")
        return self.client.create_draft(metadata=metadata, access=access, files=files)

    def _update_record(
        self,
        record_id: str,
        metadata: Dict[str, Any],
        access: Dict[str, str],
        files: Dict[str, bool],
    ) -> Dict[str, Any]:
        """
        Update an existing record.

        Args:
            record_id: Record identifier
            metadata: Record metadata
            access: Access settings
            files: Files configuration

        Returns:
            Updated draft
        """
        logger.info(f"Updating record {record_id}")

        # Try to get existing draft
        try:
            draft = self.client.get_draft(record_id)
        except Exception:
            # No draft exists, create one (or use edit endpoint for new version)
            logger.info(f"No draft exists for {record_id}, creating new draft")
            draft = self.client.create_draft(
                metadata=metadata, access=access, files=files
            )
            return draft

        # Update the draft
        return self.client.update_draft(
            record_id, metadata=metadata, access=access, files=files
        )

    def _upload_files(self, record_id: str, file_paths: List[str], warnings: List[str]):
        """
        Upload files to a record draft.

        Args:
            record_id: Record identifier
            file_paths: List of file paths to upload
            warnings: List to append warnings to
        """
        for file_path in file_paths:
            if not os.path.exists(file_path):
                warning = f"File not found: {file_path}"
                warnings.append(warning)
                logger.warning(warning)
                continue

            try:
                self.client.upload_file_to_draft(record_id, file_path)
                logger.info(f"Uploaded file to {record_id}: {Path(file_path).name}")
            except Exception as e:
                warning = f"Failed to upload {file_path}: {str(e)}"
                warnings.append(warning)
                logger.warning(warning)


def create_importer(
    client: Optional[InvenioRDMClient] = None, mapper: Optional[CSVMapper] = None
) -> CSVImporter:
    """
    Factory function to create a CSV importer.

    Args:
        client: InvenioRDM client (creates from env if not provided)
        mapper: CSV mapper (creates default if not provided)

    Returns:
        CSVImporter instance
    """
    return CSVImporter(client=client, mapper=mapper)
