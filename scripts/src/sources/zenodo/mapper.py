"""
Metadata mapper from Zenodo format to InvenioRDM format.

This module handles the conversion of Zenodo record metadata
to InvenioRDM-compatible metadata structure.
"""

import logging
from typing import Dict, List, Any, Optional
from .config import (
    get_resource_type,
    get_license,
    get_contributor_role,
    get_relation_type,
)

logger = logging.getLogger(__name__)


class ZenodoMapper:
    """Maps Zenodo metadata to InvenioRDM format."""

    def __init__(self):
        """Initialize Zenodo mapper."""
        logger.debug("Initialized Zenodo mapper")

    def map_record(self, zenodo_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map complete Zenodo record to InvenioRDM format.

        Args:
            zenodo_record: Zenodo record dictionary

        Returns:
            InvenioRDM-compatible metadata dictionary
        """
        zenodo_meta = zenodo_record.get("metadata", {})

        # Build InvenioRDM metadata
        metadata = {
            "title": zenodo_meta.get("title", "Untitled"),
            "publication_date": zenodo_meta.get("publication_date", ""),
            "resource_type": self._map_resource_type(zenodo_meta),
            "creators": self._map_creators(zenodo_meta),
            "description": self._clean_html_description(
                zenodo_meta.get("description", "")
            ),
            "publisher": "Zenodo",
        }

        # Add optional fields
        contributors = self._map_contributors(zenodo_meta)
        if contributors:
            metadata["contributors"] = contributors

        related_identifiers = self._map_related_identifiers(zenodo_meta)
        if related_identifiers:
            metadata["related_identifiers"] = related_identifiers

        keywords = zenodo_meta.get("keywords")
        if keywords:
            metadata["subjects"] = [{"subject": kw} for kw in keywords]

        version = zenodo_meta.get("version")
        if version:
            metadata["version"] = version

        license_rights = self._map_license(zenodo_meta)
        if license_rights:
            metadata["rights"] = license_rights

        # Build complete record
        return {
            "access": {"record": "public", "files": "public"},
            "files": {"enabled": True},
            "metadata": metadata,
        }

    def _map_resource_type(self, zenodo_meta: Dict[str, Any]) -> Dict[str, str]:
        """Map resource type."""
        resource_type_data = zenodo_meta.get("resource_type", {})
        resource_type_id = get_resource_type(resource_type_data)
        return {"id": resource_type_id}

    def _map_creators(self, zenodo_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Map creators from Zenodo to InvenioRDM format.

        Args:
            zenodo_meta: Zenodo metadata dictionary

        Returns:
            List of creator dictionaries
        """
        creators = []

        for creator in zenodo_meta.get("creators", []):
            person = self._map_person(creator, is_creator=True)
            if person:
                creators.append(person)

        return creators

    def _map_contributors(self, zenodo_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Map contributors from Zenodo to InvenioRDM format.

        Args:
            zenodo_meta: Zenodo metadata dictionary

        Returns:
            List of contributor dictionaries
        """
        contributors = []

        for contrib in zenodo_meta.get("contributors", []):
            person = self._map_person(contrib, is_creator=False)
            if person:
                # Add role for contributors
                person["role"] = {
                    "id": get_contributor_role(contrib.get("type", "other"))
                }
                contributors.append(person)

        return contributors

    def _map_person(
        self, person_data: Dict[str, Any], is_creator: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Map a person (creator or contributor) from Zenodo format.

        Args:
            person_data: Person data from Zenodo
            is_creator: True if creator, False if contributor

        Returns:
            InvenioRDM person dictionary or None if invalid
        """
        name = person_data.get("name", "")
        if not name:
            logger.warning("Skipping person with no name")
            return None

        # Parse name into family and given name
        family_name, given_name = self._parse_name(name)

        person = {
            "person_or_org": {
                "type": "personal",
                "name": name,
                "family_name": family_name,
                "given_name": given_name,
            }
        }

        # Add ORCID if available
        orcid = person_data.get("orcid")
        if orcid:
            person["person_or_org"]["identifiers"] = [
                {"scheme": "orcid", "identifier": orcid}
            ]

        # Add affiliation if available
        affiliation = person_data.get("affiliation")
        if affiliation:
            person["affiliations"] = [{"name": affiliation}]

        return person

    def _parse_name(self, name: str) -> tuple[str, str]:
        """
        Parse a name into family and given name.

        Args:
            name: Full name (may be in "Last, First" or "First Last" format)

        Returns:
            Tuple of (family_name, given_name)
        """
        if "," in name:
            # Format: "Last, First"
            parts = name.split(",", 1)
            family_name = parts[0].strip()
            given_name = parts[1].strip() if len(parts) > 1 else ""
        else:
            # Format: "First Last" - assume last word is family name
            parts = name.split()
            if len(parts) > 1:
                family_name = parts[-1]
                given_name = " ".join(parts[:-1])
            else:
                family_name = name
                given_name = ""

        return family_name, given_name

    def _map_related_identifiers(
        self, zenodo_meta: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Map related identifiers from Zenodo to InvenioRDM format.

        Args:
            zenodo_meta: Zenodo metadata dictionary

        Returns:
            List of related identifier dictionaries
        """
        related_identifiers = []

        for rel_id in zenodo_meta.get("related_identifiers", []):
            identifier = rel_id.get("identifier", "")
            if not identifier:
                continue

            mapped = {
                "identifier": identifier,
                "scheme": rel_id.get("scheme", "url").lower(),
                "relation_type": {
                    "id": get_relation_type(rel_id.get("relation", "isrelatedto"))
                },
            }

            # Add resource type if available
            resource_type = rel_id.get("resource_type")
            if resource_type:
                mapped["resource_type"] = {"id": get_resource_type(resource_type)}

            related_identifiers.append(mapped)

        return related_identifiers

    def _map_license(
        self, zenodo_meta: Dict[str, Any]
    ) -> Optional[List[Dict[str, str]]]:
        """
        Map license from Zenodo to InvenioRDM format.

        Args:
            zenodo_meta: Zenodo metadata dictionary

        Returns:
            List containing license dictionary or None
        """
        license_data = zenodo_meta.get("license")
        if not license_data:
            return None

        license_id = get_license(license_data)
        return [{"id": license_id}]

    def _clean_html_description(self, description: str) -> str:
        """
        Clean HTML tags from description.

        Args:
            description: Description text with HTML

        Returns:
            Clean text description
        """
        if not description:
            return ""

        # Simple HTML tag removal and conversion
        clean = (
            description.replace("<p>", "")
            .replace("</p>", "\n")
            .replace("<ul>", "")
            .replace("</ul>", "")
            .replace("<li>", "- ")
            .replace("</li>", "\n")
            .replace("<strong>", "**")
            .replace("</strong>", "**")
            .replace("<em>", "*")
            .replace("</em>", "*")
            .replace("<code>", "`")
            .replace("</code>", "`")
            .replace("<br>", "\n")
            .replace("<br/>", "\n")
            .replace("<br />", "\n")
        )

        return clean.strip()


def create_mapper() -> ZenodoMapper:
    """
    Create a Zenodo mapper instance.

    Returns:
        Configured ZenodoMapper instance
    """
    return ZenodoMapper()
