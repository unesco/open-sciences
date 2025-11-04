"""
Configuration for CSV import operations.

This module defines configuration constants, field mappings, and validation rules
for importing CSV data into InvenioRDM.
"""

from typing import Dict, Set, List


class CSVImportConfig:
    """Configuration constants for CSV import."""

    # Batch processing
    BATCH_SIZE = 10

    # Required CSV columns
    REQUIRED_COLUMNS: Set[str] = {"title", "creators"}

    # Optional CSV columns with their defaults
    OPTIONAL_COLUMNS: Dict[str, str] = {
        "record_id": "",
        "description": "",
        "resource_type": "dataset",
        "publication_date": "",  # Will use today if empty
        "access_record": "public",
        "access_files": "public",
        "publisher": "",
        "version": "",
        "languages": "",
        "subjects": "",
        "license": "",
        "additional_descriptions": "",
        "references": "",
        "contributors": "",
        "related_identifiers": "",
        "file_paths": "",
        "publish": "no",
    }

    # All recognized columns
    ALL_COLUMNS: Set[str] = REQUIRED_COLUMNS | set(OPTIONAL_COLUMNS.keys())

    # Default delimiter
    DEFAULT_DELIMITER = ","

    # Boolean value mappings
    BOOLEAN_TRUE_VALUES: Set[str] = {"yes", "true", "1", "y"}
    BOOLEAN_FALSE_VALUES: Set[str] = {"no", "false", "0", "n", ""}

    # Default resource types mapping
    RESOURCE_TYPES: Dict[str, str] = {
        "publication": "publication-article",
        "article": "publication-article",
        "dataset": "dataset",
        "image": "image-photo",
        "photo": "image-photo",
        "video": "video",
        "software": "software",
        "presentation": "presentation",
        "poster": "poster",
        "lesson": "lesson",
        "other": "other",
    }

    # Contributor role mappings
    CONTRIBUTOR_ROLES: Dict[str, str] = {
        "contactperson": "contactperson",
        "datacollector": "datacollector",
        "datacurator": "datacurator",
        "datamanager": "datamanager",
        "distributor": "distributor",
        "editor": "editor",
        "hostinginstitution": "hostinginstitution",
        "producer": "producer",
        "projectleader": "projectleader",
        "projectmanager": "projectmanager",
        "projectmember": "projectmember",
        "registrationagency": "registrationagency",
        "registrationauthority": "registrationauthority",
        "relatedperson": "relatedperson",
        "researcher": "researcher",
        "researchgroup": "researchgroup",
        "rightsholder": "rightsholder",
        "sponsor": "sponsor",
        "supervisor": "supervisor",
        "workpackageleader": "workpackageleader",
        "other": "other",
    }

    # Related identifier relation types
    RELATION_TYPES: Dict[str, str] = {
        "cites": "cites",
        "iscitedby": "iscitedby",
        "issupplementto": "issupplementto",
        "issupplementedby": "issupplementedby",
        "iscontinuedby": "iscontinuedby",
        "continues": "continues",
        "isdescribedby": "isdescribedby",
        "describes": "describes",
        "hasmetadata": "hasmetadata",
        "ismetadatafor": "ismetadatafor",
        "hasversion": "hasversion",
        "isversionof": "isversionof",
        "isnewversionof": "isnewversionof",
        "ispreviousversionof": "ispreviousversionof",
        "ispartof": "ispartof",
        "haspart": "haspart",
        "isreferencedby": "isreferencedby",
        "references": "references",
        "isdocumentedby": "isdocumentedby",
        "documents": "documents",
        "iscompiledby": "iscompiledby",
        "compiles": "compiles",
        "isvariantformof": "isvariantformof",
        "isoriginalformof": "isoriginalformof",
        "isidenticalto": "isidenticalto",
        "isalternateidentifier": "isalternateidentifier",
        "isreviewedby": "isreviewedby",
        "reviews": "reviews",
        "isderivedfrom": "isderivedfrom",
        "issourceof": "issourceof",
        "requires": "requires",
        "isrequiredby": "isrequiredby",
        "isobsoletedby": "isobsoletedby",
        "obsoletes": "obsoletes",
    }

    # Identifier schemes
    IDENTIFIER_SCHEMES: Dict[str, str] = {
        "doi": "doi",
        "arxiv": "arxiv",
        "pmid": "pmid",
        "pmcid": "pmcid",
        "url": "url",
        "urn": "urn",
        "isbn": "isbn",
        "issn": "issn",
        "orcid": "orcid",
        "ror": "ror",
        "gnd": "gnd",
        "handle": "handle",
    }

    # Description types
    DESCRIPTION_TYPES: Dict[str, str] = {
        "abstract": "abstract",
        "methods": "methods",
        "seriesinformation": "seriesinformation",
        "tableofcontents": "tableofcontents",
        "technicalinfo": "technicalinfo",
        "other": "other",
    }

    @staticmethod
    def get_resource_type(resource_type_str: str) -> str:
        """
        Get normalized resource type ID.

        Args:
            resource_type_str: Resource type string from CSV

        Returns:
            Normalized resource type ID
        """
        resource_type_lower = resource_type_str.lower().strip()
        return CSVImportConfig.RESOURCE_TYPES.get(
            resource_type_lower, resource_type_str
        )

    @staticmethod
    def get_contributor_role(role_str: str) -> str:
        """
        Get normalized contributor role ID.

        Args:
            role_str: Role string from CSV

        Returns:
            Normalized role ID
        """
        role_lower = role_str.lower().strip().replace(" ", "").replace("_", "")
        return CSVImportConfig.CONTRIBUTOR_ROLES.get(role_lower, "other")

    @staticmethod
    def get_relation_type(relation_str: str) -> str:
        """
        Get normalized relation type ID.

        Args:
            relation_str: Relation string from CSV

        Returns:
            Normalized relation type ID
        """
        relation_lower = relation_str.lower().strip().replace(" ", "").replace("_", "")
        return CSVImportConfig.RELATION_TYPES.get(relation_lower, "references")

    @staticmethod
    def get_description_type(desc_type_str: str) -> str:
        """
        Get normalized description type ID.

        Args:
            desc_type_str: Description type string from CSV

        Returns:
            Normalized description type ID
        """
        desc_type_lower = desc_type_str.lower().strip().replace(" ", "")
        return CSVImportConfig.DESCRIPTION_TYPES.get(desc_type_lower, "other")
