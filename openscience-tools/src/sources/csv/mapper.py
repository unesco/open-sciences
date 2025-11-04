"""
Mapper for CSV records to InvenioRDM metadata.

This module handles the mapping of CSV row data to InvenioRDM metadata format.
"""

import logging
from typing import Dict, Any, Tuple, List

from .config import CSVImportConfig
from .parsers import (
    parse_creators,
    parse_contributors,
    parse_related_identifiers,
    parse_file_paths,
    parse_boolean,
    parse_list_field,
    parse_publication_date,
    parse_additional_descriptions,
)

logger = logging.getLogger(__name__)


class CSVMapper:
    """
    Maps CSV row data to InvenioRDM metadata format.

    This class handles the transformation of CSV fields into the structure
    required by InvenioRDM's REST API.
    """

    def __init__(self):
        """Initialize the CSV mapper."""
        self.config = CSVImportConfig

    def map_record(
        self, row: Dict[str, str]
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], List[str], bool]:
        """
        Map a CSV row to InvenioRDM record format.

        Args:
            row: CSV row as dictionary

        Returns:
            Tuple of (metadata, access, files_config, file_paths, should_publish)

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate and extract required fields
        title = self._validate_required_field(row, "title", "Title")
        creators_str = self._validate_required_field(row, "creators", "Creators")

        # Parse creators
        creators = parse_creators(creators_str)
        if not creators:
            raise ValueError("At least one valid creator is required")

        # Build metadata
        metadata = self._build_metadata(row, title, creators)

        # Build access settings
        access = self._build_access(row)

        # Parse file paths
        file_paths = parse_file_paths(row.get("file_paths", ""))

        # Files configuration
        files_config = {"enabled": len(file_paths) > 0}

        # Parse publish flag
        should_publish = parse_boolean(row.get("publish", ""), default=False)

        return metadata, access, files_config, file_paths, should_publish

    def _validate_required_field(
        self, row: Dict[str, str], field: str, label: str
    ) -> str:
        """
        Validate that a required field is present and non-empty.

        Args:
            row: CSV row
            field: Field name
            label: Human-readable field label

        Returns:
            Field value

        Raises:
            ValueError: If field is missing or empty
        """
        value = row.get(field, "").strip()
        if not value:
            raise ValueError(f"{label} is required")
        return value

    def _build_metadata(
        self, row: Dict[str, str], title: str, creators: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build the metadata section of the record.

        Args:
            row: CSV row
            title: Record title
            creators: Parsed creators list

        Returns:
            Metadata dictionary
        """
        # Start with required fields
        resource_type = row.get("resource_type", "dataset").strip() or "dataset"
        resource_type_id = self.config.get_resource_type(resource_type)

        publication_date = parse_publication_date(row.get("publication_date", ""))

        metadata = {
            "title": title,
            "creators": creators,
            "resource_type": {"id": resource_type_id},
            "publication_date": publication_date,
        }

        # Add optional fields
        self._add_optional_fields(metadata, row)

        return metadata

    def _add_optional_fields(self, metadata: Dict[str, Any], row: Dict[str, str]):
        """
        Add optional metadata fields from CSV row.

        Args:
            metadata: Metadata dictionary to update
            row: CSV row
        """
        # Description
        description = row.get("description", "").strip()
        if description:
            metadata["description"] = description

        # Publisher
        publisher = row.get("publisher", "").strip()
        if publisher:
            metadata["publisher"] = publisher

        # Version
        version = row.get("version", "").strip()
        if version:
            metadata["version"] = version

        # Languages (semicolon-separated ISO 639-3 codes)
        languages_str = row.get("languages", "").strip()
        if languages_str:
            lang_codes = parse_list_field(languages_str)
            if lang_codes:
                metadata["languages"] = [{"id": code} for code in lang_codes]

        # Subjects/Keywords (semicolon-separated)
        subjects_str = row.get("subjects", "").strip()
        if subjects_str:
            subject_list = parse_list_field(subjects_str)
            if subject_list:
                metadata["subjects"] = [{"subject": subj} for subj in subject_list]

        # License/Rights
        license_id = row.get("license", "").strip()
        if license_id:
            metadata["rights"] = [{"id": license_id}]

        # Additional descriptions
        add_desc_str = row.get("additional_descriptions", "").strip()
        if add_desc_str:
            add_descs = parse_additional_descriptions(add_desc_str)
            if add_descs:
                metadata["additional_descriptions"] = add_descs

        # References (semicolon-separated)
        references_str = row.get("references", "").strip()
        if references_str:
            refs = parse_list_field(references_str)
            if refs:
                metadata["references"] = [{"reference": ref} for ref in refs]

        # Contributors
        contributors_str = row.get("contributors", "").strip()
        if contributors_str:
            contributors = parse_contributors(contributors_str)
            if contributors:
                metadata["contributors"] = contributors

        # Related identifiers
        related_ids_str = row.get("related_identifiers", "").strip()
        if related_ids_str:
            related_ids = parse_related_identifiers(related_ids_str)
            if related_ids:
                metadata["related_identifiers"] = related_ids

    def _build_access(self, row: Dict[str, str]) -> Dict[str, str]:
        """
        Build the access section of the record.

        Args:
            row: CSV row

        Returns:
            Access dictionary
        """
        access_record = row.get("access_record", "public").strip() or "public"
        access_files = row.get("access_files", "public").strip() or "public"

        return {"record": access_record, "files": access_files}

    def get_existing_record_id(self, row: Dict[str, str]) -> str:
        """
        Get existing record ID from CSV row if present.

        Args:
            row: CSV row

        Returns:
            Record ID or empty string
        """
        return row.get("record_id", "").strip()


def create_mapper() -> CSVMapper:
    """
    Factory function to create a CSV mapper.

    Returns:
        CSVMapper instance
    """
    return CSVMapper()
