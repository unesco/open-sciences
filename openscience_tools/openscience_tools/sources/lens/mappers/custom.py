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

import json
import logging
import os
import re
from typing import Dict, Any, List, Optional

from ..base import BaseMapper, MappingError
from ..config import LensImportConfig

logger = logging.getLogger(__name__)

# Import region display names from site constants
try:
    import sys
    from pathlib import Path
    # Add site directory to path to import constants
    site_path = Path(__file__).parent.parent.parent.parent.parent.parent / "site"
    if site_path.exists():
        sys.path.insert(0, str(site_path))
        from my_site.constants import REGION_DISPLAY_NAMES
        sys.path.pop(0)
    else:
        # Fallback if import fails
        REGION_DISPLAY_NAMES = {
            "EUROPE_NORTH_AMERICA": "Europe & North America",
            "ARAB_STATES": "Arab States",
            "AFRICA": "Africa",
            "LATIN_AMERICA_CARIBBEAN": "Latin America & the Caribbean",
            "ASIA_PACIFIC": "Asia & the Pacific",
        }
except ImportError:
    # Fallback if import fails
    REGION_DISPLAY_NAMES = {
        "EUROPE_NORTH_AMERICA": "Europe & North America",
        "ARAB_STATES": "Arab States",
        "AFRICA": "Africa",
        "LATIN_AMERICA_CARIBBEAN": "Latin America & the Caribbean",
        "ASIA_PACIFIC": "Asia & the Pacific",
    }


def _load_country_to_region_mapping() -> Dict[str, str]:
    """
    Load country code to region mapping from JSON file.
    
    Returns:
        Dict mapping country code (ISO alpha-2) to region display name
    """
    # First check for bundled copy next to this module
    module_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(module_dir, "data", "country_code_region_mapping.json")
    if os.path.exists(local_path):
        json_path = local_path
    else:
        # Fall back: walk up to find the project root containing 'site'
        json_path = None
        current_dir = module_dir
        while current_dir != os.path.dirname(current_dir):  # Not at root
            site_path = os.path.join(current_dir, "site", "my_site", "filters", "data", "country_code_region_mapping.json")
            if os.path.exists(site_path):
                json_path = site_path
                break
            current_dir = os.path.dirname(current_dir)
    
    if json_path is None:
        logger.warning("Could not find country_code_region_mapping.json in project structure")
        return {}
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            country_code_to_region_key = json.load(f)
        
        # Convert region keys to display names
        mapping = {
            code: REGION_DISPLAY_NAMES[region_key]
            for code, region_key in country_code_to_region_key.items()
        }
        logger.info(f"Loaded {len(mapping)} country code-to-region mappings from {json_path}")
        return mapping
    except FileNotFoundError:
        logger.warning(f"Country code-region mapping file not found at {json_path}")
        return {}
    except Exception as e:
        logger.warning(f"Error loading country code-region mapping: {e}")
        return {}


# Load mapping at module level (once on import)
COUNTRY_CODE_TO_REGION = _load_country_to_region_mapping()


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
            # Store raw Lens.org record for future field derivation
            import json
            custom_fields["lens:raw_lens_data"] = json.dumps(lens_record)

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

                # Extract colour separately for faceting/filtering
                colour = open_access_data.get("colour")
                if colour:
                    custom_fields["publication:open_access_colour"] = colour

            # Extract is_open_access flag from Lens.org data
            # Store as keyword 'true'/'false' for compatibility with CFTermsFacet
            is_oa = self.safe_get(lens_record, "is_open_access")
            if is_oa is not None:
                custom_fields["publication:is_open_access"] = "true" if is_oa else "false"

            # Affiliation countries for faceting (extract from authors' affiliations)
            country_names, country_codes = self._extract_affiliation_countries(lens_record)
            if country_names:
                custom_fields["publication:country"] = country_names
            
            # Map country codes to UNESCO regions
            if country_codes:
                regions = self._map_country_codes_to_regions(country_codes)
                if regions:
                    custom_fields["publication:affiliation_region"] = regions

            # Publication year for faceting (extract from year_published or date_published)
            year = self.safe_get(lens_record, "year_published")
            if not year:
                # Try extracting from date_published (format: YYYY-MM-DD or YYYY)
                date_str = self.safe_get(lens_record, "date_published")
                if date_str:

                    year_match = re.match(r"^(\d{4})", str(date_str))
                    if year_match:
                        year = int(year_match.group(1))

            if year:
                custom_fields["publication:year"] = str(year)

            # Funding organizations for faceting (extract from lens:funding)
            funding_orgs = self._extract_funding_orgs(lens_record)
            if funding_orgs:
                custom_fields["publication:funding_org"] = funding_orgs

            # External identifiers (DOI, PMID, PMCID, etc.)
            external_ids_data = self._map_external_ids(lens_record)
            if external_ids_data:
                import json

                custom_fields["lens:external_ids"] = json.dumps(external_ids_data)

            # Source information (journal, publisher, ISSN, etc.)
            source_data = self._map_source(lens_record)
            if source_data:
                import json

                custom_fields["lens:source"] = json.dumps(source_data)

            # References (cited works)
            references_data = self._map_references(lens_record)
            if references_data:
                import json

                custom_fields["lens:references"] = json.dumps(references_data)

            # MeSH terms (Medical Subject Headings)
            mesh_data = self._map_mesh_terms(lens_record)
            if mesh_data:
                import json

                custom_fields["lens:mesh_terms"] = json.dumps(mesh_data)

            # Scholarly citations (articles citing this work)
            citations_data = self._map_scholarly_citations(lens_record)
            if citations_data:
                import json

                custom_fields["lens:scholarly_citations"] = json.dumps(citations_data)

            # Chemical substances
            chemicals_data = self._map_chemicals(lens_record)
            if chemicals_data:
                import json

                custom_fields["lens:chemicals"] = json.dumps(chemicals_data)

            # Journal information (volume, issue, pages)
            journal_data = self._map_journal(lens_record)
            if journal_data:
                custom_fields["journal:journal"] = journal_data

            # Keywords (author-supplied, stored separately from fields of study)
            keywords = self.safe_get(lens_record, "keywords", default=[])
            kw_list = [kw.strip() for kw in keywords if isinstance(kw, str) and kw.strip()]
            if kw_list:
                custom_fields["publication:keyword"] = kw_list

            # Fields of study (stored separately from keywords)
            fields_of_study = self.safe_get(lens_record, "fields_of_study", default=[])
            fos_list = [f.strip() for f in fields_of_study if isinstance(f, str) and f.strip()]
            if fos_list:
                custom_fields["publication:field_of_study"] = fos_list
            # UNESCO relation types (funded by / published by / affiliated / collective author)
            unesco_relations = self._detect_unesco_relations(lens_record)
            if unesco_relations:
                custom_fields["publication:unesco_relation"] = unesco_relations

            # Patent citations count (direct field for API visibility)
            patent_cites = self.safe_get(lens_record, "patent_citations_count")
            if patent_cites is not None:
                custom_fields["publication:patent_citations_count"] = str(int(patent_cites))

            return custom_fields

        except Exception as e:
            self.logger.error(f"Error mapping custom fields: {e}")
            # Custom fields are optional, so we don't raise
            return {}

    # UNESCO pattern strings (lowercase) used for relation detection
    _UNESCO_PATTERNS = [
        "unesco",
        "united nations educational, scientific and cultural",
        "ictp",
        "international centre for theoretical physics",
    ]

    def _matches_unesco(self, text: str) -> bool:
        """Return True if text matches any UNESCO-related pattern (case-insensitive)."""
        if not text:
            return False
        text_lower = text.lower()
        return any(pat in text_lower for pat in self._UNESCO_PATTERNS)

    def _detect_unesco_relations(self, lens_record: Dict[str, Any]) -> Optional[List[str]]:
        """
        Detect UNESCO-related publication types.

        Returns a list of applicable relation labels from:
        - "Funded by UNESCO"        — funding[].org matches UNESCO patterns
        - "Published by UNESCO"     — source.publisher matches UNESCO patterns
        - "UNESCO Affiliated Author" — authors[].affiliations[].name matches UNESCO patterns
        - "UNESCO Collective Author" — author first/last name matches UNESCO patterns
        """
        relations = set()

        # 1. Funded by UNESCO
        for funding in self.safe_get(lens_record, "funding", default=[]):
            if isinstance(funding, dict):
                org = self.safe_get(funding, "org", default="")
                if self._matches_unesco(org):
                    relations.add("Funded by UNESCO")
                    break

        # 2. Published by UNESCO
        source = self.safe_get(lens_record, "source", default={})
        publisher = self.safe_get(source, "publisher", default="") if isinstance(source, dict) else ""
        if self._matches_unesco(publisher):
            relations.add("Published by UNESCO")

        # 3. UNESCO Affiliated Author / 4. UNESCO Collective Author
        for author in self.safe_get(lens_record, "authors", default=[]):
            if not isinstance(author, dict):
                continue

            # Collective author: UNESCO appears in the author's name itself
            first = self.safe_get(author, "first_name", default="")
            last = self.safe_get(author, "last_name", default="")
            if self._matches_unesco(first) or self._matches_unesco(last):
                relations.add("UNESCO Collective Author")

            # Affiliated author: UNESCO appears in any affiliation name
            for aff in self.safe_get(author, "affiliations", default=[]):
                if isinstance(aff, dict):
                    aff_name = self.safe_get(aff, "name", default="")
                    if self._matches_unesco(aff_name):
                        relations.add("UNESCO Affiliated Author")
                        break

        return sorted(relations) if relations else None

    def _map_lens_identifiers(self, lens_record: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
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
                    identifiers.append({"scheme": scheme.lower(), "identifier": str(value)})

        return identifiers if identifiers else None

    def _map_mesh_terms(self, lens_record: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
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

    def _map_asjc_subjects(self, lens_record: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
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

    def _map_chemicals(self, lens_record: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
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

    def _map_funding(self, lens_record: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
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

    def _map_external_ids(self, lens_record: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
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

    def _map_source(self, lens_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Map source information (journal, publisher, ISSN, etc.).

        Format: {
            "title": "Disasters",
            "type": "Journal",
            "publisher": "Wiley",
            "issn": [
                {"type": "electronic", "value": "14677717"},
                {"type": "print", "value": "03613666"}
            ],
            "country": "United Kingdom",
            "asjc_subjects": ["General Social Sciences", "General Earth and Planetary Sciences"]
        }
        """
        source = self.safe_get(lens_record, "source", default={})

        if not source:
            return None

        source_data = {}

        # Title (journal/book title)
        title = self.safe_get(source, "title")
        if title:
            source_data["title"] = title

        # Type (Journal, Book, etc.)
        source_type = self.safe_get(source, "type")
        if source_type:
            source_data["type"] = source_type

        # Publisher
        publisher = self.safe_get(source, "publisher")
        if publisher:
            source_data["publisher"] = publisher

        # ISSN (array of objects)
        issn_list = self.safe_get(source, "issn", default=[])
        if issn_list:
            issn_data = []
            for issn in issn_list:
                if isinstance(issn, dict):
                    issn_type = self.safe_get(issn, "type")
                    issn_value = self.safe_get(issn, "value")
                    if issn_value:
                        issn_data.append(
                            {
                                "type": issn_type if issn_type else "unknown",
                                "value": str(issn_value),
                            }
                        )
            if issn_data:
                source_data["issn"] = issn_data

        # Country
        country = self.safe_get(source, "country")
        if country:
            source_data["country"] = country

        # ASJC subjects (simplified)
        asjc_subjects = self.safe_get(source, "asjc_subjects", default=[])
        if asjc_subjects:
            source_data["asjc_subjects"] = asjc_subjects

        return source_data if source_data else None

    def _map_references(self, lens_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Map references (cited works).

        Format: {
            "count": 51,
            "resolved_count": 51,
            "items": [
                {"lens_id": "000-260-354-529-51X"},
                {"lens_id": "024-107-742-940-634", "text": "Zolin R. ..."}
            ]
        }
        """
        references = self.safe_get(lens_record, "references", default=[])

        if not references:
            return None

        references_data = {
            "count": self.safe_get(lens_record, "references_count", default=len(references)),
            "resolved_count": self.safe_get(lens_record, "references_resolved_count", default=0),
            "items": [],
        }

        # Limit to first 10 references for display (to avoid huge JSON)
        for ref in references[:10]:
            if isinstance(ref, dict):
                ref_item = {}

                lens_id = self.safe_get(ref, "lens_id")
                if lens_id:
                    ref_item["lens_id"] = lens_id

                text = self.safe_get(ref, "text")
                if text:
                    # Truncate very long text
                    ref_item["text"] = text[:500] if len(text) > 500 else text

                if ref_item:
                    references_data["items"].append(ref_item)

        return references_data if references_data["items"] else None

    def _map_mesh_terms(self, lens_record: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
        """
        Map MeSH (Medical Subject Headings) terms.

        Format: [
            {
                "mesh_heading": "Humans",
                "mesh_id": "D006801"
            },
            {
                "mesh_heading": "Commerce",
                "mesh_id": "D003132",
                "qualifier_name": "organization & administration",
                "qualifier_id": "Q000458"
            }
        ]
        """
        mesh_terms_raw = self.safe_get(lens_record, "mesh_terms", default=[])

        if not mesh_terms_raw:
            return None

        mesh_terms = []

        for term in mesh_terms_raw:
            if not isinstance(term, dict):
                continue

            mesh_item = {}

            # Main heading
            heading = self.safe_get(term, "mesh_heading")
            if heading:
                mesh_item["mesh_heading"] = heading

            # MeSH ID (Descriptor)
            mesh_id = self.safe_get(term, "mesh_id")
            if mesh_id:
                mesh_item["mesh_id"] = mesh_id

            # Optional qualifier
            qualifier_name = self.safe_get(term, "qualifier_name")
            if qualifier_name:
                mesh_item["qualifier_name"] = qualifier_name

            # Optional qualifier ID
            qualifier_id = self.safe_get(term, "qualifier_id")
            if qualifier_id:
                mesh_item["qualifier_id"] = qualifier_id

            if mesh_item and "mesh_heading" in mesh_item and "mesh_id" in mesh_item:
                mesh_terms.append(mesh_item)

        return mesh_terms if mesh_terms else None

    def _map_scholarly_citations(self, lens_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Map scholarly citations (articles citing this work).

        Format: {
            "count": 4,
            "items": [
                {"lens_id": "006-264-642-615-283"},
                {"lens_id": "084-815-691-268-940"}
            ]
        }
        """
        citations = self.safe_get(lens_record, "scholarly_citations", default=[])
        citations_count = self.safe_get(
            lens_record, "scholarly_citations_count", default=len(citations)
        )

        if not citations and citations_count == 0:
            return None

        citations_data = {"count": citations_count, "items": []}

        # Limit to first 10 citations for display
        for citation_id in citations[:10]:
            if citation_id:
                citations_data["items"].append({"lens_id": str(citation_id)})

        return citations_data if citations_data["count"] > 0 else None

    def _map_chemicals(self, lens_record: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
        """
        Map chemical substances from Lens.org to custom field.

        Lens.org format:
        {
            "chemicals": [
                {
                    "substance_name": "Polyethylene",
                    "registry_number": "9002-88-4",  # CAS Registry Number
                    "mesh_id": "D020959"             # MeSH ID
                }
            ]
        }

        Returns list of chemical dictionaries with substance_name, registry_number, and mesh_id.
        """
        chemicals_data = self.safe_get(lens_record, "chemicals", default=[])

        if not chemicals_data:
            return None

        chemicals_list = []

        for chemical in chemicals_data:
            if not isinstance(chemical, dict):
                continue

            chemical_item = {}

            # Substance name (required)
            substance_name = self.safe_get(chemical, "substance_name")
            if substance_name:
                chemical_item["substance_name"] = substance_name

            # CAS Registry Number (optional)
            registry_number = self.safe_get(chemical, "registry_number")
            if registry_number:
                chemical_item["registry_number"] = registry_number

            # MeSH ID (optional)
            mesh_id = self.safe_get(chemical, "mesh_id")
            if mesh_id:
                chemical_item["mesh_id"] = mesh_id

            # Only add if we have at least the substance name
            if chemical_item and "substance_name" in chemical_item:
                chemicals_list.append(chemical_item)

        return chemicals_list if chemicals_list else None

    def _extract_funding_orgs(self, lens_record: Dict[str, Any]) -> Optional[List[str]]:
        """
        Extract funding organization names from Lens.org funding data.

        Args:
            lens_record: Raw Lens.org publication record

        Returns:
            List of funding organization names or None if no funding data
        """
        funding_list = self.safe_get(lens_record, "funding", default=[])

        if not funding_list:
            return None

        funding_orgs = []

        for funding in funding_list:
            if not isinstance(funding, dict):
                continue

            # Extract organization name (field is called 'org' in Lens.org data)
            org = self.safe_get(funding, "org")
            if org and org not in funding_orgs:  # Avoid duplicates
                funding_orgs.append(org)

        return funding_orgs if funding_orgs else None

    def _extract_affiliation_countries(self, lens_record: Dict[str, Any]) -> tuple[Optional[List[str]], Optional[List[str]]]:
        """
        Extract country names and codes from authors' affiliations.

        Extracts country_code from each author's affiliations and converts
        them to full country names using pycountry.

        Args:
            lens_record: Raw Lens.org publication record

        Returns:
            Tuple of (country_names, country_codes) or (None, None) if no country data
        """
        try:
            import pycountry
        except ImportError:
            self.logger.warning("pycountry not installed, cannot extract affiliation countries")
            return None

        authors = self.safe_get(lens_record, "authors", default=[])

        if not authors:
            return None

        country_codes = set()  # Use set to avoid duplicates

        for author in authors:
            if not isinstance(author, dict):
                continue

            affiliations = self.safe_get(author, "affiliations", default=[])
            if not affiliations:
                continue

            for affiliation in affiliations:
                if not isinstance(affiliation, dict):
                    continue

                country_code = self.safe_get(affiliation, "country_code")
                if country_code:
                    country_codes.add(country_code.strip().upper())

        if not country_codes:
            return None, None

        # Convert country codes to full names
        country_names = []
        valid_codes = []
        for code in sorted(country_codes):  # Sort for consistency
            try:
                country = pycountry.countries.get(alpha_2=code)
                if country:
                    country_names.append(country.name)
                    valid_codes.append(code)
                else:
                    self.logger.warning(f"Unknown country code: {code}")
            except Exception as e:
                self.logger.warning(f"Error converting country code {code}: {e}")

        return (
            country_names if country_names else None,
            valid_codes if valid_codes else None
        )

    def _map_country_codes_to_regions(self, country_codes: List[str]) -> Optional[List[str]]:
        """Map country codes to UNESCO regions.
        
        Args:
            country_codes: List of ISO alpha-2 country codes (e.g., ['US', 'FR', 'JP'])
            
        Returns:
            List of unique UNESCO region names or None
        """
        if not country_codes:
            return None
        
        if not COUNTRY_CODE_TO_REGION:
            self.logger.warning("Country code-to-region mapping not loaded")
            return None
        
        regions = set()
        for country_code in country_codes:
            region = COUNTRY_CODE_TO_REGION.get(country_code)
            if region:
                regions.add(region)
            else:
                self.logger.warning(f"No region mapping found for country code: {country_code}")
        
        return sorted(list(regions)) if regions else None

    def _map_journal(self, lens_record: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Map journal information from Lens.org to InvenioRDM journal custom field.

        InvenioRDM journal custom field structure:
        {
            "title": "Journal title",
            "issn": "1234-5678",
            "volume": "15",
            "issue": "3",
            "pages": "123-456"
        }

        Args:
            lens_record: Raw Lens.org publication record

        Returns:
            Dictionary with journal information or None if no journal data
        """
        journal_data = {}

        # Volume
        if volume := self.safe_get(lens_record, "volume"):
            journal_data["volume"] = str(volume)

        # Issue
        if issue := self.safe_get(lens_record, "issue"):
            journal_data["issue"] = str(issue)

        # Pages (combine start_page and end_page)
        if start_page := self.safe_get(lens_record, "start_page"):
            pages = str(start_page)
            if end_page := self.safe_get(lens_record, "end_page"):
                pages += f"-{end_page}"
            journal_data["pages"] = pages

        # Journal title (from source.title if available)
        source_data = self.safe_get(lens_record, "source", default={})
        if isinstance(source_data, dict):
            if journal_title := self.safe_get(source_data, "title"):
                journal_data["title"] = journal_title

            # ISSN (from source if available)
            if issn := self.safe_get(source_data, "issn"):
                # Handle list of ISSNs
                if isinstance(issn, list) and issn:
                    journal_data["issn"] = issn[0]
                elif isinstance(issn, str):
                    journal_data["issn"] = issn

        return journal_data if journal_data else None
