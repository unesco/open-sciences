"""
Mapper for standard InvenioRDM metadata fields from Lens.org data.

Maps core bibliographic fields like title, creators, publication date, etc.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base import BaseMapper, MappingError
from ..config import LensImportConfig

logger = logging.getLogger(__name__)


class StandardFieldsMapper(BaseMapper):
    """
    Maps Lens.org fields to InvenioRDM standard metadata fields.

    Handles:
    - Title and abstract
    - Creators and contributors (authors)
    - Publication date
    - Publisher
    - Resource type
    - Language
    - Description
    - Subjects/keywords
    """

    def __init__(self, config: Optional[LensImportConfig] = None):
        """
        Initialize standard fields mapper.

        Args:
            config: Configuration instance (uses default if None)
        """
        self.config = config or LensImportConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

    def map(self, lens_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Lens.org record to InvenioRDM standard metadata.

        Args:
            lens_record: Raw Lens.org publication record

        Returns:
            Dict with InvenioRDM metadata structure

        Raises:
            MappingError: If required fields are missing
        """
        metadata = {}

        try:
            # Resource type (required)
            metadata["resource_type"] = self._map_resource_type(lens_record)

            # Title (required)
            metadata["title"] = self._map_title(lens_record)

            # Creators (required - at least one author)
            metadata["creators"] = self._map_creators(lens_record)

            # Publication date (required)
            metadata["publication_date"] = self._map_publication_date(lens_record)

            # Publisher (optional but recommended)
            if publisher := self._map_publisher(lens_record):
                metadata["publisher"] = publisher

            # Description/Abstract (optional)
            if description := self._map_description(lens_record):
                metadata["description"] = description

            # Subjects/Keywords (optional)
            if subjects := self._map_subjects(lens_record):
                metadata["subjects"] = subjects

            # Language (optional)
            if language := self._map_language(lens_record):
                metadata["languages"] = [{"id": language}]

            # Rights/License (optional)
            if rights := self._map_rights(lens_record):
                metadata["rights"] = rights

            # Version (optional)
            if version := self.safe_get(lens_record, "version"):
                metadata["version"] = str(version)

            # Funding (optional)
            if funding := self._map_funding(lens_record):
                metadata["funding"] = funding

            return metadata

        except Exception as e:
            self.logger.error(f"Error mapping standard fields: {e}")
            raise MappingError(f"Standard fields mapping failed: {e}")

    def _map_resource_type(self, lens_record: Dict[str, Any]) -> Dict[str, str]:
        """Map resource type."""
        pub_type = self.safe_get(lens_record, "publication_type")

        if not pub_type:
            self.logger.warning(
                "No publication_type found, using default 'publication-article'"
            )
            return {"id": "publication-article"}

        resource_type_id = self.config.get_resource_type(pub_type)
        return {"id": resource_type_id}

    def _map_title(self, lens_record: Dict[str, Any]) -> str:
        """Map title (required field)."""
        title = self.safe_get(lens_record, "title")

        if not title:
            raise MappingError("Title is required but not found in record")

        # Clean HTML if present
        title = self.clean_html(title)

        # Trim whitespace
        title = title.strip()

        if not title:
            raise MappingError("Title is empty after cleaning")

        return title

    def _map_creators(self, lens_record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Map authors to creators.

        InvenioRDM requires at least one creator.
        """
        authors = self.safe_get(lens_record, "authors", default=[])

        if not authors:
            raise MappingError("At least one author is required")

        creators = []
        for i, author in enumerate(authors):
            self.logger.debug(f"Mapping author {i}: {author}")
            creator = self._map_person(author)
            if creator:
                creators.append(creator)
            else:
                self.logger.warning(f"Failed to map author {i}: {author}")

        if not creators:
            raise MappingError(
                f"No valid creators could be mapped from {len(authors)} authors"
            )

        return creators

    def _map_person(self, person_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Map a Lens.org author/contributor to InvenioRDM person format.

        Args:
            person_data: Lens.org author/contributor data

        Returns:
            InvenioRDM person dict or None if invalid
        """
        # Get or construct display name
        display_name = self.safe_get(person_data, "display_name")

        if not display_name:
            # Construct from first_name and last_name
            first_name = self.safe_get(person_data, "first_name")
            last_name = self.safe_get(person_data, "last_name")
            initials = self.safe_get(person_data, "initials")

            if last_name:
                if first_name:
                    display_name = f"{last_name}, {first_name}"
                elif initials:
                    display_name = f"{last_name}, {initials}"
                else:
                    display_name = last_name
            elif first_name:
                display_name = first_name
            else:
                self.logger.warning("Skipping person without name information")
                return None

        person = {"person_or_org": {"type": "personal", "name": display_name}}

        # Add family/given names if available
        family_name = self.safe_get(person_data, "last_name")
        given_name = self.safe_get(person_data, "first_name")
        initials = self.safe_get(person_data, "initials")

        if family_name:
            person["person_or_org"]["family_name"] = family_name

        if given_name:
            person["person_or_org"]["given_name"] = given_name
        elif initials:
            # Use initials as given name if full name not available
            person["person_or_org"]["given_name"] = initials

        # Add ORCID if available and valid
        # In Lens.org, ORCID is in the ids array
        orcid = None
        ids_list = self.safe_get(person_data, "ids", default=[])
        if ids_list:
            for id_obj in ids_list:
                if isinstance(id_obj, dict) and id_obj.get("type") == "orcid":
                    orcid = id_obj.get("value")
                    break

        # Fallback to direct orcid field
        if not orcid:
            orcid = self.safe_get(person_data, "orcid")

        if orcid and self.config.is_valid_orcid(orcid):
            # Ensure ORCID has correct format
            if not orcid.startswith("https://orcid.org/"):
                orcid = f"https://orcid.org/{orcid}"
            person["person_or_org"]["identifiers"] = [
                {"scheme": "orcid", "identifier": orcid}
            ]

        # Add affiliations if available
        affiliations_data = self.safe_get(person_data, "affiliations", default=[])
        if affiliations_data:
            affiliations = []
            for aff in affiliations_data:
                aff_name = self.safe_get(aff, "name")
                if aff_name:
                    affiliation = {"name": aff_name}

                    # Add ROR ID if available
                    # In Lens.org, ROR is in the ids array
                    ror_id = None
                    aff_ids = self.safe_get(aff, "ids", default=[])
                    if aff_ids:
                        for id_obj in aff_ids:
                            if isinstance(id_obj, dict) and id_obj.get("type") == "ror":
                                ror_id = id_obj.get("value")
                                break

                    # Fallback to direct ror_id field
                    if not ror_id:
                        ror_id = self.safe_get(aff, "ror_id")

                    # Skip ROR IDs - InvenioRDM validates against official registry
                    # and many Lens.org ROR IDs are invalid/non-existent
                    # Only import affiliation name

                    affiliations.append(affiliation)

            if affiliations:
                person["affiliations"] = affiliations

        return person

    def _map_publication_date(self, lens_record: Dict[str, Any]) -> str:
        """
        Map publication date (required field).

        Returns ISO 8601 date string (YYYY-MM-DD or YYYY).
        """
        # Try date_published first
        date_str = self.safe_get(lens_record, "date_published")

        # Fallback to year_published
        if not date_str:
            year = self.safe_get(lens_record, "year_published")
            if year:
                date_str = str(year)

        if not date_str:
            raise MappingError("Publication date is required but not found")

        # Parse and validate date
        try:
            # Try full date first
            if re.match(r"^\d{4}-\d{2}-\d{2}", date_str):
                # Validate it's a real date
                datetime.strptime(date_str[:10], "%Y-%m-%d")
                return date_str[:10]

            # Try year only
            elif re.match(r"^\d{4}$", date_str):
                year = int(date_str)
                if 1000 <= year <= 9999:
                    return date_str

            # Try to extract year from various formats
            year_match = re.search(r"(\d{4})", date_str)
            if year_match:
                year = int(year_match.group(1))
                if 1000 <= year <= 9999:
                    self.logger.warning(
                        f"Extracted year {year} from date string: {date_str}"
                    )
                    return str(year)

            raise ValueError(f"Could not parse date: {date_str}")

        except Exception as e:
            raise MappingError(f"Invalid publication date '{date_str}': {e}")

    def _map_publisher(self, lens_record: Dict[str, Any]) -> Optional[str]:
        """Map publisher name."""
        # Try source.publisher first
        publisher = self.safe_get(lens_record, "source", "publisher")

        if publisher:
            return publisher.strip()

        return None

    def _map_description(self, lens_record: Dict[str, Any]) -> Optional[str]:
        """Map abstract to description."""
        abstract = self.safe_get(lens_record, "abstract")

        if not abstract:
            return None

        # Clean HTML
        abstract = self.clean_html(abstract)

        # Trim whitespace
        abstract = abstract.strip()

        return abstract if abstract else None

    def _map_subjects(
        self, lens_record: Dict[str, Any]
    ) -> Optional[List[Dict[str, str]]]:
        """
        Map keywords and fields of study to subjects.

        InvenioRDM subjects format: [{"subject": "keyword"}]
        """
        subjects = []

        # Add keywords
        keywords = self.safe_get(lens_record, "keywords", default=[])
        for keyword in keywords:
            if isinstance(keyword, str) and keyword.strip():
                subjects.append({"subject": keyword.strip()})

        # Add fields of study
        fields_of_study = self.safe_get(lens_record, "fields_of_study", default=[])
        for field in fields_of_study:
            if isinstance(field, str) and field.strip():
                subject = field.strip()
                # Avoid duplicates
                if not any(s.get("subject") == subject for s in subjects):
                    subjects.append({"subject": subject})

        return subjects if subjects else None

    def _map_language(self, lens_record: Dict[str, Any]) -> Optional[str]:
        """
        Map language code.

        Returns ISO 639-3 language code (e.g., 'eng', 'deu').
        """
        # Lens.org uses full language names, not codes
        language = self.safe_get(lens_record, "language")

        if not language:
            return None

        # Simple mapping for common languages
        # TODO: Use a proper language code library (iso-639)
        language_map = {
            "english": "eng",
            "german": "deu",
            "french": "fra",
            "spanish": "spa",
            "italian": "ita",
            "portuguese": "por",
            "chinese": "zho",
            "japanese": "jpn",
            "russian": "rus",
            "arabic": "ara",
        }

        lang_lower = language.lower().strip()
        lang_code = language_map.get(lang_lower)

        if not lang_code:
            self.logger.warning(f"Unknown language '{language}', using default 'eng'")
            lang_code = "eng"

        return lang_code

    def _map_rights(
        self, lens_record: Dict[str, Any]
    ) -> Optional[List[Dict[str, str]]]:
        """
        Map license information to rights.

        InvenioRDM rights format: [{"id": "cc-by-4.0"}]
        """
        # Get license from source.license or license field
        license_str = self.safe_get(lens_record, "source", "license") or self.safe_get(
            lens_record, "license"
        )

        if not license_str:
            return None

        # Map to InvenioRDM license ID
        license_id = self.config.get_license_id(license_str)

        if license_id:
            return [{"id": license_id}]

        # If no mapping found, create custom rights entry
        self.logger.warning(f"Unknown license '{license_str}', adding as custom rights")
        return [
            {
                "title": {"en": license_str},
                "description": {"en": f"License: {license_str}"},
            }
        ]

    def _map_funding(
        self, lens_record: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Map funding information to InvenioRDM funding field.

        Lens.org format:
        {
            "funding": [
                {
                    "org": "European Commission",
                    "org_id": "10.13039/501100000780",  # CrossRef Funder ID
                    "funding_name": "H2020-12345"  # Optional grant number
                }
            ]
        }

        InvenioRDM format:
        {
            "funding": [
                {
                    "funder": {
                        "name": "European Commission"
                        # NOTE: "id" is omitted because InvenioRDM validates
                        # CrossRef Funder IDs against its vocabulary, and many
                        # Lens.org IDs are not in the InvenioRDM vocabulary.
                        # To use IDs, funders must be loaded into the vocabulary first.
                    },
                    "award": {
                        "number": "H2020-12345"
                    }
                }
            ]
        }
        """
        funding_data = self.safe_get(lens_record, "funding", default=[])

        if not funding_data:
            return None

        funding_list = []

        for fund in funding_data:
            if not isinstance(fund, dict):
                continue

            org_name = self.safe_get(fund, "org")
            if not org_name:
                continue

            # Use only the funder name, without ID
            # InvenioRDM validates IDs against its funder vocabulary
            funding_entry = {"funder": {"name": org_name}}

            # Add award/grant number if available
            funding_name = self.safe_get(fund, "funding_name")
            if funding_name:
                funding_entry["award"] = {"number": funding_name}

            funding_list.append(funding_entry)

        return funding_list if funding_list else None
