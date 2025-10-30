"""
Mapper for Lens.org-specific custom metadata fields.

Maps Lens.org-specific data that doesn't fit into standard InvenioRDM fields:
- MeSH terms
- ASJC subjects
- Chemical substances
- Citation metrics
- Funding details
- Open access information
- Lens-specific identifiers
"""

import logging
from typing import Dict, Any, List, Optional

from ..base import BaseMapper, MappingError
from ..config import LensImportConfig

logger = logging.getLogger(__name__)


class CustomFieldsMapper(BaseMapper):
    """
    Maps Lens.org-specific fields to InvenioRDM custom fields.

    All custom fields use the "lens:" namespace prefix.
    """

    def __init__(self, config: Optional[LensImportConfig] = None):
        """
        Initialize custom fields mapper.

        Args:
            config: Configuration instance (uses default if None)
        """
        self.config = config or LensImportConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

    def map(self, lens_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Lens.org record to custom metadata fields.

        Args:
            lens_record: Raw Lens.org publication record

        Returns:
            Dict with custom fields (keys prefixed with "lens:")
        """
        custom_fields = {}

        try:
            # Lens.org unique identifier
            lens_id = lens_record.get("lens_id")
            if lens_id:
                custom_fields["lens:id"] = lens_id

            # Open access information
            open_access_data = self._map_open_access(lens_record)
            if open_access_data:
                # TextCF requires a string, so we serialize to JSON
                import json

                custom_fields["lens:open_access"] = json.dumps(open_access_data)

            # External identifiers (DOI, PMID, PMCID, etc.)
            external_ids_data = self._map_external_ids(lens_record)
            if external_ids_data:
                import json

                custom_fields["lens:external_ids"] = json.dumps(external_ids_data)

            return custom_fields

        except Exception as e:
            self.logger.error(f"Error mapping custom fields: {e}")
            # Custom fields are optional, so we don't raise
            return {}

    def _map_lens_identifiers(
        self, lens_record: Dict[str, Any]
    ) -> Optional[List[Dict[str, str]]]:
        """
        Map Lens.org-specific identifiers.

        Includes: lens_id, magid, openalex, grid, ror, fundref, etc.
        """
        identifiers = []

        # Lens ID (primary identifier)
        lens_id = self.safe_get(lens_record, "lens_id")
        if lens_id:
            identifiers.append({"scheme": "lens_id", "identifier": lens_id})

        # Microsoft Academic Graph ID
        magid = self.safe_get(lens_record, "magid")
        if magid:
            identifiers.append({"scheme": "magid", "identifier": str(magid)})

        # OpenAlex ID
        openalex = self.safe_get(lens_record, "openalex_id")
        if openalex:
            identifiers.append({"scheme": "openalex", "identifier": openalex})

        # External IDs array
        external_ids = self.safe_get(lens_record, "external_ids", default=[])
        for ext_id in external_ids:
            if isinstance(ext_id, dict):
                scheme = self.safe_get(ext_id, "type")
                value = self.safe_get(ext_id, "value")
                if scheme and value:
                    identifiers.append(
                        {"scheme": scheme.lower(), "identifier": str(value)}
                    )

        return identifiers if identifiers else None

    def _map_mesh_terms(
        self, lens_record: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Map MeSH (Medical Subject Headings) terms.

        Format: [{"mesh_id": "D000001", "term": "Calcimycin", "is_major_topic": true, "qualifiers": [...]}]
        """
        mesh_headings = self.safe_get(lens_record, "mesh_terms", default=[])

        if not mesh_headings:
            return None

        mesh_terms = []
        for mesh in mesh_headings:
            if not isinstance(mesh, dict):
                continue

            mesh_id = self.safe_get(mesh, "mesh_id")
            term = self.safe_get(mesh, "mesh_heading")

            if not mesh_id or not term:
                continue

            mesh_term = {"mesh_id": mesh_id, "term": term}

            # Is major topic?
            is_major = self.safe_get(mesh, "is_major_topic")
            if is_major is not None:
                mesh_term["is_major_topic"] = bool(is_major)

            # Qualifiers
            qualifiers = self.safe_get(mesh, "qualifier", default=[])
            if qualifiers:
                mesh_term["qualifiers"] = [
                    {
                        "qualifier_id": q.get("qualifier_ui", ""),
                        "qualifier_name": q.get("qualifier_name", ""),
                    }
                    for q in qualifiers
                    if isinstance(q, dict) and q.get("qualifier_name")
                ]

            mesh_terms.append(mesh_term)

        return mesh_terms if mesh_terms else None

    def _map_asjc_subjects(
        self, lens_record: Dict[str, Any]
    ) -> Optional[List[Dict[str, str]]]:
        """
        Map ASJC (All Science Journal Classification) subjects.

        Format: [{"code": "2404", "subject": "Microbiology"}]
        """
        fields_of_study = self.safe_get(lens_record, "fields_of_study", default=[])

        if not fields_of_study:
            return None

        asjc_subjects = []
        for field in fields_of_study:
            if isinstance(field, dict):
                code = self.safe_get(field, "code")
                subject = self.safe_get(field, "name")

                if code and subject:
                    asjc_subjects.append({"code": str(code), "subject": subject})

        return asjc_subjects if asjc_subjects else None

    def _map_chemicals(
        self, lens_record: Dict[str, Any]
    ) -> Optional[List[Dict[str, str]]]:
        """
        Map chemical substances.

        Format: [{"registry_number": "526-95-4", "substance": "Glucose"}]
        """
        chemicals_list = self.safe_get(lens_record, "chemicals", default=[])

        if not chemicals_list:
            return None

        chemicals = []
        for chem in chemicals_list:
            if not isinstance(chem, dict):
                continue

            registry_number = self.safe_get(chem, "registry_number")
            substance = self.safe_get(chem, "substance_name")

            if registry_number or substance:
                chemical = {}
                if registry_number:
                    chemical["registry_number"] = registry_number
                if substance:
                    chemical["substance"] = substance
                chemicals.append(chemical)

        return chemicals if chemicals else None

    def _map_metrics(self, lens_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Map citation metrics and counts.

        Format: {
            "cited_by_count": 42,
            "reference_count": 51,
            "scholarly_citations_count": 38,
            "patent_citations_count": 4
        }
        """
        metrics = {}

        # Cited by count
        cited_by = self.safe_get(lens_record, "scholarly_citations_count")
        if cited_by is not None:
            metrics["cited_by_count"] = int(cited_by)

        # Reference count
        ref_count = self.safe_get(lens_record, "reference_count")
        if ref_count is not None:
            metrics["reference_count"] = int(ref_count)

        # Scholarly citations
        scholarly_cites = self.safe_get(lens_record, "scholarly_citations_count")
        if scholarly_cites is not None:
            metrics["scholarly_citations_count"] = int(scholarly_cites)

        # Patent citations
        patent_cites = self.safe_get(lens_record, "patent_citation_count")
        if patent_cites is not None:
            metrics["patent_citations_count"] = int(patent_cites)

        return metrics if metrics else None

    def _map_funding(
        self, lens_record: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Map funding information.

        Format: [{
            "organization": "National Science Foundation",
            "funding_id": "1234567",
            "country": "United States",
            "funder_id": "10.13039/00000001"
        }]
        """
        funding_list = self.safe_get(lens_record, "funding", default=[])

        if not funding_list:
            return None

        funding_details = []
        for funding in funding_list:
            if not isinstance(funding, dict):
                continue

            funding_detail = {}

            # Organization name
            org = self.safe_get(funding, "organisation")
            if org:
                funding_detail["organization"] = org

            # Funding ID (grant number)
            funding_id = self.safe_get(funding, "funding_id")
            if funding_id:
                funding_detail["funding_id"] = str(funding_id)

            # Country
            country = self.safe_get(funding, "country")
            if country:
                funding_detail["country"] = country

            # Crossref Funder ID (DOI)
            funder_id = self.safe_get(funding, "funder_id")
            if funder_id:
                funding_detail["funder_id"] = funder_id

            if funding_detail:
                funding_details.append(funding_detail)

        return funding_details if funding_details else None

    def _map_open_access(self, lens_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Map open access information.

        Format: {
            "license": "cc-by-nc-nd",
            "colour": "hybrid",
            "landing_page_urls": ["https://..."]
        }
        """
        oa_info = lens_record.get("open_access")
        if not oa_info:
            return None

        open_access = {}

        # License
        license_str = oa_info.get("license")
        if license_str:
            open_access["license"] = license_str

        # OA colour (note: Lens uses British spelling 'colour')
        oa_colour = oa_info.get("colour")
        if oa_colour:
            open_access["colour"] = oa_colour

        # Landing page URLs
        locations = oa_info.get("locations", {})
        landing_page_urls = locations.get("landing_page_urls", [])
        if landing_page_urls:
            open_access["landing_page_urls"] = landing_page_urls

        return open_access if open_access else None

    def _map_external_ids(
        self, lens_record: Dict[str, Any]
    ) -> Optional[List[Dict[str, str]]]:
        """
        Map external identifiers from Lens.org.

        Format: [
            {"type": "doi", "value": "10.1111/disa.12617"},
            {"type": "pmid", "value": "38098176"},
            {"type": "pmcid", "value": "PMC11640955"}
        ]

        Note: OpenAlex IDs are excluded as they're Lens-specific.
        """
        external_ids_raw = self.safe_get(lens_record, "external_ids", default=[])

        if not external_ids_raw:
            return None

        external_ids = []

        for ext_id in external_ids_raw:
            if not isinstance(ext_id, dict):
                continue

            id_type = self.safe_get(ext_id, "type", default="").lower()
            value = self.safe_get(ext_id, "value")

            if not id_type or not value:
                continue

            # Skip openalex as it's Lens-specific
            if id_type == "openalex":
                continue

            # Normalize PMCID to add PMC prefix if missing
            if id_type == "pmcid":
                value_str = str(value).strip()
                if not value_str.upper().startswith("PMC"):
                    value = f"PMC{value_str}"
                else:
                    # Normalize to uppercase PMC prefix
                    value = "PMC" + value_str[3:]

            external_ids.append({"type": id_type, "value": str(value)})

        return external_ids if external_ids else None
