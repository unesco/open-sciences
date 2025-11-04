"""
Parsers for CSV field values.

This module contains functions to parse various CSV field formats
into InvenioRDM metadata structures.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .config import CSVImportConfig

logger = logging.getLogger(__name__)


def parse_creators(creators_str: str) -> List[Dict[str, Any]]:
    """
    Parse creators string into InvenioRDM creator format.

    Format: "Given Family; ORCID; Affiliation | Given2 Family2; ORCID2; Affiliation2"
    ORCID and Affiliation are optional.

    Args:
        creators_str: Pipe-separated creator information

    Returns:
        List of creator dictionaries
    """
    creators = []

    if not creators_str or not creators_str.strip():
        return creators

    # Split by pipe for multiple creators
    creator_groups = creators_str.split("|")

    for group in creator_groups:
        parts = [p.strip() for p in group.split(";")]
        if not parts or not parts[0]:
            continue

        # Parse name (required)
        name_parts = parts[0].strip().split()
        if len(name_parts) < 2:
            logger.warning(f"Skipping invalid creator name: {parts[0]}")
            continue

        given_name = " ".join(name_parts[:-1])
        family_name = name_parts[-1]

        creator = {
            "person_or_org": {
                "given_name": given_name,
                "family_name": family_name,
                "type": "personal",
                "name": f"{family_name}, {given_name}",
            }
        }

        # Parse ORCID (optional, second element)
        if len(parts) > 1 and parts[1].strip():
            orcid = parts[1].strip()
            # Remove common ORCID URL prefixes if present
            orcid = orcid.replace("https://orcid.org/", "").replace(
                "http://orcid.org/", ""
            )
            creator["person_or_org"]["identifiers"] = [
                {"identifier": orcid, "scheme": "orcid"}
            ]

        # Parse affiliation (optional, third element)
        if len(parts) > 2 and parts[2].strip():
            creator["affiliations"] = [{"name": parts[2].strip()}]

        creators.append(creator)

    return creators


def parse_contributors(contributors_str: str) -> List[Dict[str, Any]]:
    """
    Parse contributors string into InvenioRDM contributor format.

    Format: "Given Family; Affiliation; Role; ORCID | Given2 Family2; Affiliation2; Role2; ORCID2"
    All fields except name are optional.

    Args:
        contributors_str: Pipe-separated contributor information

    Returns:
        List of contributor dictionaries
    """
    contributors = []

    if not contributors_str or not contributors_str.strip():
        return contributors

    # Split by pipe for multiple contributors
    contributor_groups = contributors_str.split("|")

    for group in contributor_groups:
        parts = [p.strip() for p in group.split(";")]
        if not parts or not parts[0]:
            continue

        # Parse name (required)
        name_parts = parts[0].strip().split()
        if len(name_parts) < 2:
            logger.warning(f"Skipping invalid contributor name: {parts[0]}")
            continue

        given_name = " ".join(name_parts[:-1])
        family_name = name_parts[-1]

        contributor = {
            "person_or_org": {
                "given_name": given_name,
                "family_name": family_name,
                "type": "personal",
                "name": f"{family_name}, {given_name}",
            }
        }

        # Parse affiliation (optional, second element)
        if len(parts) > 1 and parts[1].strip():
            contributor["affiliations"] = [{"name": parts[1].strip()}]

        # Parse role (optional, third element, default: "other")
        role = "other"
        if len(parts) > 2 and parts[2].strip():
            role = CSVImportConfig.get_contributor_role(parts[2].strip())
        contributor["role"] = {"id": role}

        # Parse ORCID (optional, fourth element)
        if len(parts) > 3 and parts[3].strip():
            orcid = parts[3].strip()
            orcid = orcid.replace("https://orcid.org/", "").replace(
                "http://orcid.org/", ""
            )
            contributor["person_or_org"]["identifiers"] = [
                {"identifier": orcid, "scheme": "orcid"}
            ]

        contributors.append(contributor)

    return contributors


def parse_related_identifiers(related_ids_str: str) -> List[Dict[str, Any]]:
    """
    Parse related identifiers string.

    Format: "identifier; scheme; relation_type | identifier2; scheme2; relation_type2"

    Args:
        related_ids_str: Pipe-separated related identifiers

    Returns:
        List of related identifier dictionaries
    """
    related_ids = []

    if not related_ids_str or not related_ids_str.strip():
        return related_ids

    # Split by pipe for multiple identifiers
    id_groups = related_ids_str.split("|")

    for group in id_groups:
        parts = [p.strip() for p in group.split(";")]
        if len(parts) < 2:  # Need at least identifier and scheme
            logger.warning(f"Skipping invalid related identifier: {group}")
            continue

        related_id = {
            "identifier": parts[0],
            "scheme": parts[1].lower(),
        }

        # Parse relation type (optional, third element, default: "references")
        if len(parts) > 2 and parts[2].strip():
            relation_type = CSVImportConfig.get_relation_type(parts[2].strip())
            related_id["relation_type"] = {"id": relation_type}
        else:
            related_id["relation_type"] = {"id": "references"}

        related_ids.append(related_id)

    return related_ids


def parse_file_paths(file_paths_str: str) -> List[str]:
    """
    Parse file paths string into a list of paths.

    Format: "path/to/file1.csv; path/to/file2.txt"

    Args:
        file_paths_str: Semicolon-separated file paths

    Returns:
        List of file paths
    """
    if not file_paths_str or not file_paths_str.strip():
        return []

    return [p.strip() for p in file_paths_str.split(";") if p.strip()]


def parse_boolean(value: str, default: bool = False) -> bool:
    """
    Parse a boolean value from string.

    Args:
        value: String value (yes/no, true/false, 1/0)
        default: Default value if empty

    Returns:
        Boolean value
    """
    if not value or not value.strip():
        return default

    value_lower = value.strip().lower()
    return value_lower in CSVImportConfig.BOOLEAN_TRUE_VALUES


def parse_list_field(field_str: str, separator: str = ";") -> List[str]:
    """
    Parse a semicolon-separated string into a list.

    Args:
        field_str: String with separator-separated values
        separator: Separator character (default: semicolon)

    Returns:
        List of values
    """
    if not field_str or not field_str.strip():
        return []

    return [item.strip() for item in field_str.split(separator) if item.strip()]


def parse_publication_date(date_str: str) -> str:
    """
    Parse and validate publication date.

    Args:
        date_str: Date string (YYYY-MM-DD format expected)

    Returns:
        Validated date string or today's date if empty
    """
    if not date_str or not date_str.strip():
        return datetime.now().strftime("%Y-%m-%d")

    date_str = date_str.strip()

    # Basic validation - should be YYYY-MM-DD
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        logger.warning(
            f"Invalid date format '{date_str}', using today's date. Expected: YYYY-MM-DD"
        )
        return datetime.now().strftime("%Y-%m-%d")


def parse_additional_descriptions(desc_str: str) -> List[Dict[str, Any]]:
    """
    Parse additional descriptions.

    Format: "description text; type | another description; type2"

    Args:
        desc_str: Pipe-separated descriptions with types

    Returns:
        List of description dictionaries
    """
    descriptions = []

    if not desc_str or not desc_str.strip():
        return descriptions

    desc_groups = desc_str.split("|")

    for group in desc_groups:
        parts = [p.strip() for p in group.split(";", 1)]
        if not parts or not parts[0]:
            continue

        desc_text = parts[0]
        desc_type = "other"

        if len(parts) > 1 and parts[1].strip():
            desc_type = CSVImportConfig.get_description_type(parts[1].strip())

        descriptions.append({"description": desc_text, "type": {"id": desc_type}})

    return descriptions
