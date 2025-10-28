"""
Configuration for Lens.org to InvenioRDM import.

This module contains all mapping tables, configuration settings,
and constants used during the import process.
"""

from typing import Dict, List, Set


class LensImportConfig:
    """
    Central configuration for Lens.org import process.

    This class contains all mapping tables and configuration settings
    needed to transform Lens.org metadata into InvenioRDM format.
    """

    # ========================================================================
    # RESOURCE TYPE MAPPING
    # ========================================================================

    RESOURCE_TYPE_MAPPING: Dict[str, str] = {
        "journal article": "publication-article",
        "letter": "publication-other",  # InvenioRDM doesn't have 'letter', use 'other'
        "review": "publication-review",
        "conference paper": "publication-conferencepaper",
        "conference proceeding": "publication-conferencepaper",
        "book chapter": "publication-section",
        "book": "publication-book",
        "preprint": "publication-preprint",
        "editorial": "publication-other",
        "comment": "publication-other",
        "correction": "publication-other",
        "retraction": "publication-other",
        "case report": "publication-article",
        "clinical trial": "publication-article",
        "dataset": "dataset",
        "software": "software",
        "other": "other",
    }

    DEFAULT_RESOURCE_TYPE = "publication-article"

    # ========================================================================
    # LICENSE MAPPING
    # ========================================================================

    LICENSE_MAPPING: Dict[str, str] = {
        "cc-by": "cc-by-4.0",
        "cc-by-4.0": "cc-by-4.0",
        "cc-by-nc": "cc-by-nc-4.0",
        "cc-by-nc-4.0": "cc-by-nc-4.0",
        "cc-by-nc-nd": "cc-by-nc-nd-4.0",
        "cc-by-nc-nd-4.0": "cc-by-nc-nd-4.0",
        "cc-by-nc-sa": "cc-by-nc-sa-4.0",
        "cc-by-nc-sa-4.0": "cc-by-nc-sa-4.0",
        "cc-by-nd": "cc-by-nd-4.0",
        "cc-by-nd-4.0": "cc-by-nd-4.0",
        "cc-by-sa": "cc-by-sa-4.0",
        "cc-by-sa-4.0": "cc-by-sa-4.0",
        "cc0": "cc0-1.0",
        "cc0-1.0": "cc0-1.0",
        "public-domain": "cc0-1.0",
    }

    # ========================================================================
    # IDENTIFIER SCHEMES
    # ========================================================================

    # External ID types and their InvenioRDM schemes
    IDENTIFIER_SCHEMES: Dict[str, str] = {
        "doi": "doi",
        "pmid": "pmid",
        "pmcid": "pmcid",
        "arxiv": "arxiv",
        "isbn": "isbn",
        "issn": "issn",
        "purl": "url",
    }

    # Lens.org specific identifier types (stored in custom fields)
    LENS_IDENTIFIER_TYPES: Set[str] = {
        "lens_id",
        "magid",
        "openalex",
        "grid",
        "ror",
        "fundref",
    }

    # Author identifier types
    AUTHOR_ID_TYPES: Set[str] = {
        "orcid",
        "magid",
        "openalex",
    }

    # ========================================================================
    # RELATED IDENTIFIER RELATIONS
    # ========================================================================

    # How to map external IDs to related identifiers
    EXTERNAL_ID_RELATIONS: Dict[str, str] = {
        "doi": "isidenticalto",
        "pmid": "isidenticalto",
        "pmcid": "isidenticalto",
        "openalex": "isidenticalto",
        "arxiv": "isidenticalto",
    }

    # ========================================================================
    # FIELD INCLUSION/EXCLUSION
    # ========================================================================

    # Fields to skip during import (if present in Lens.org data)
    SKIP_FIELDS: Set[str] = {
        "created",  # Lens.org creation date, not needed
        "updated",  # Lens.org update date, not needed
    }

    # Whether to include various optional data
    INCLUDE_REFERENCES: bool = True
    INCLUDE_CITATIONS: bool = False  # Can be huge, default to False
    INCLUDE_MESH_TERMS: bool = True
    INCLUDE_CHEMICALS: bool = True
    INCLUDE_FUNDING: bool = True

    # Maximum number of items to include
    MAX_REFERENCES: int = 100
    MAX_CITATIONS: int = 50
    MAX_KEYWORDS: int = 20

    # ========================================================================
    # VALIDATION RULES
    # ========================================================================

    # Required fields in Lens.org data
    REQUIRED_FIELDS: Set[str] = {
        "lens_id",
        "title",
    }

    # Minimum required metadata for InvenioRDM
    MIN_REQUIRED_FOR_INVENIO: Set[str] = {
        "title",
        "publication_date",
        "resource_type",
        "creators",
    }

    # ORCID validation regex
    ORCID_REGEX = r"^(\d{4}-){3}\d{3}[\dX]$"

    # ========================================================================
    # PERFORMANCE SETTINGS
    # ========================================================================

    # Batch processing
    BATCH_SIZE: int = 10

    # Concurrent processing
    MAX_WORKERS: int = 5
    ENABLE_PARALLEL: bool = False  # Parallel processing (experimental)

    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2  # seconds

    # ========================================================================
    # CUSTOM FIELDS CONFIGURATION
    # ========================================================================

    # Namespace for Lens.org custom fields
    CUSTOM_FIELD_NAMESPACE: str = "lens"

    # Custom field names
    CUSTOM_FIELDS: Dict[str, str] = {
        "identifiers": f"{CUSTOM_FIELD_NAMESPACE}:identifiers",
        "mesh_terms": f"{CUSTOM_FIELD_NAMESPACE}:mesh_terms",
        "asjc_subjects": f"{CUSTOM_FIELD_NAMESPACE}:asjc_subjects",
        "chemicals": f"{CUSTOM_FIELD_NAMESPACE}:chemicals",
        "metrics": f"{CUSTOM_FIELD_NAMESPACE}:metrics",
        "funding_details": f"{CUSTOM_FIELD_NAMESPACE}:funding_details",
        "open_access_details": f"{CUSTOM_FIELD_NAMESPACE}:open_access",
    }

    # ========================================================================
    # LOGGING & REPORTING
    # ========================================================================

    # Logging level
    LOG_LEVEL: str = "INFO"

    # Report generation
    GENERATE_REPORT: bool = True
    REPORT_FORMAT: str = "json"  # json, csv, or both

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    @classmethod
    def get_resource_type(cls, lens_type: str) -> str:
        """
        Get InvenioRDM resource type from Lens.org publication type.

        Args:
            lens_type: Lens.org publication_type value

        Returns:
            InvenioRDM resource_type.id
        """
        if not lens_type:
            return cls.DEFAULT_RESOURCE_TYPE

        lens_type_lower = lens_type.lower().strip()
        return cls.RESOURCE_TYPE_MAPPING.get(lens_type_lower, cls.DEFAULT_RESOURCE_TYPE)

    @classmethod
    def get_license_id(cls, lens_license: str) -> str:
        """
        Get InvenioRDM license ID from Lens.org license.

        Args:
            lens_license: Lens.org license string

        Returns:
            InvenioRDM license ID or None if not found
        """
        if not lens_license:
            return None

        lens_license_lower = lens_license.lower().strip()
        return cls.LICENSE_MAPPING.get(lens_license_lower)

    @classmethod
    def is_valid_orcid(cls, orcid: str) -> bool:
        """
        Validate ORCID format.

        Args:
            orcid: ORCID identifier

        Returns:
            True if valid format, False otherwise
        """
        if not orcid:
            return False

        import re

        return bool(re.match(cls.ORCID_REGEX, orcid))

    @classmethod
    def get_identifier_scheme(cls, id_type: str) -> str:
        """
        Get InvenioRDM identifier scheme from Lens.org ID type.

        Args:
            id_type: Lens.org external_id type

        Returns:
            InvenioRDM identifier scheme
        """
        return cls.IDENTIFIER_SCHEMES.get(id_type.lower(), "url")

    @classmethod
    def should_skip_field(cls, field_name: str) -> bool:
        """
        Check if a field should be skipped during import.

        Args:
            field_name: Name of the field

        Returns:
            True if field should be skipped
        """
        return field_name in cls.SKIP_FIELDS

    @classmethod
    def get_custom_field_name(cls, field_key: str) -> str:
        """
        Get the full custom field name with namespace.

        Args:
            field_key: Key from CUSTOM_FIELDS dict

        Returns:
            Full custom field name
        """
        return cls.CUSTOM_FIELDS.get(
            field_key, f"{cls.CUSTOM_FIELD_NAMESPACE}:{field_key}"
        )
