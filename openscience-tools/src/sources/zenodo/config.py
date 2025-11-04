"""
Configuration and mapping settings for Zenodo import.

This module contains:
- Zenodo API configuration
- Resource type mappings from Zenodo to InvenioRDM
- License mappings
- Contributor role mappings
"""

from typing import Dict

# Zenodo API Configuration
ZENODO_API_BASE = "https://zenodo.org/api"

# Resource type mappings: Zenodo type -> InvenioRDM type
RESOURCE_TYPE_MAP: Dict[str, str] = {
    "publication": "publication",
    "publication-article": "publication-article",
    "publication-book": "publication-book",
    "publication-section": "publication-section",
    "publication-conferencepaper": "publication-conferencepaper",
    "publication-datamanagementplan": "publication-datamanagementplan",
    "publication-patent": "publication-patent",
    "publication-preprint": "publication-preprint",
    "publication-report": "publication-report",
    "publication-thesis": "publication-thesis",
    "publication-technicalnote": "publication-technicalnote",
    "publication-workingpaper": "publication-workingpaper",
    "poster": "poster",
    "presentation": "presentation",
    "dataset": "dataset",
    "image": "image",
    "image-figure": "image-figure",
    "image-plot": "image-plot",
    "image-drawing": "image-drawing",
    "image-diagram": "image-diagram",
    "image-photo": "image-photo",
    "image-other": "image-other",
    "video": "video",
    "software": "software",
    "lesson": "lesson",
    "physicalobject": "other",
    "other": "other",
}

# License mappings: Zenodo license -> InvenioRDM license
LICENSE_MAP: Dict[str, str] = {
    "cc-by-4.0": "cc-by-4.0",
    "cc-by-sa-4.0": "cc-by-sa-4.0",
    "cc-by-nc-4.0": "cc-by-nc-4.0",
    "cc-by-nc-sa-4.0": "cc-by-nc-sa-4.0",
    "cc-by-nd-4.0": "cc-by-nd-4.0",
    "cc-by-nc-nd-4.0": "cc-by-nc-nd-4.0",
    "cc0-1.0": "cc0-1.0",
    "mit": "mit",
    "mit-license": "mit",
    "apache-2.0": "apache-2.0",
    "bsd-3-clause": "bsd-3-clause",
    "gpl-3.0": "gpl-3.0-only",
    "lgpl-3.0": "lgpl-3.0-only",
}

# Default license for unmapped cases
DEFAULT_LICENSE = "cc-by-4.0"

# Contributor role mappings: Zenodo type -> InvenioRDM role
CONTRIBUTOR_ROLE_MAP: Dict[str, str] = {
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
    "relatedperson": "other",
    "researcher": "researcher",
    "researchgroup": "researchgroup",
    "rightsholder": "rightsholder",
    "sponsor": "sponsor",
    "supervisor": "supervisor",
    "workpackageleader": "workpackageleader",
    "other": "other",
}

# Related identifier relation types
RELATION_TYPE_MAP: Dict[str, str] = {
    "iscitedby": "iscitedby",
    "cites": "cites",
    "issupplementto": "issupplementto",
    "issupplementedby": "issupplementedby",
    "iscontinuedby": "iscontinuedby",
    "continues": "continues",
    "isdescribedby": "isdescribedby",
    "describes": "describes",
    "hasmetadata": "hasmetadata",
    "ismetadatafor": "ismetadatafor",
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
    "isrequiredby": "isrequiredby",
    "requires": "requires",
    "isobsoletedby": "isobsoletedby",
    "obsoletes": "obsoletes",
}


def get_resource_type(zenodo_type: str) -> str:
    """
    Map Zenodo resource type to InvenioRDM resource type.

    Args:
        zenodo_type: Resource type from Zenodo

    Returns:
        InvenioRDM resource type identifier
    """
    # Handle dict format from Zenodo
    if isinstance(zenodo_type, dict):
        zenodo_type = zenodo_type.get("type", "other")

    return RESOURCE_TYPE_MAP.get(zenodo_type.lower(), "other")


def get_license(zenodo_license: str) -> str:
    """
    Map Zenodo license to InvenioRDM license.

    Args:
        zenodo_license: License identifier from Zenodo

    Returns:
        InvenioRDM license identifier
    """
    # Handle dict format from Zenodo
    if isinstance(zenodo_license, dict):
        zenodo_license = zenodo_license.get("id", "")

    license_lower = zenodo_license.lower()
    return LICENSE_MAP.get(license_lower, DEFAULT_LICENSE)


def get_contributor_role(zenodo_role: str) -> str:
    """
    Map Zenodo contributor type to InvenioRDM role.

    Args:
        zenodo_role: Contributor type from Zenodo

    Returns:
        InvenioRDM contributor role identifier
    """
    return CONTRIBUTOR_ROLE_MAP.get(zenodo_role.lower(), "other")


def get_relation_type(zenodo_relation: str) -> str:
    """
    Map Zenodo relation type to InvenioRDM relation type.

    Args:
        zenodo_relation: Relation type from Zenodo

    Returns:
        InvenioRDM relation type identifier
    """
    return RELATION_TYPE_MAP.get(zenodo_relation.lower(), "isrelatedto")
