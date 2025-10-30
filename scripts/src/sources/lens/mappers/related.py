"""
Mapper for related identifiers (DOI, PMID, arXiv, etc.) from Lens.org data.

Maps external identifiers and references to InvenioRDM's related_identifiers field.
"""

import logging
import re
from typing import Dict, Any, List, Optional

from ..base import BaseMapper
from ..config import LensImportConfig

logger = logging.getLogger(__name__)


class RelatedIdentifiersMapper(BaseMapper):
    """
    Maps Lens.org external identifiers to InvenioRDM related_identifiers.

    Handles:
    - DOI
    - PubMed ID (PMID)
    - PubMed Central ID (PMCID)
    - arXiv
    - ISBN/ISSN
    - Other external identifiers
    """

    def __init__(self, config: Optional[LensImportConfig] = None):
        """
        Initialize related identifiers mapper.

        Args:
            config: Configuration instance (uses default if None)
        """
        self.config = config or LensImportConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

    def map(self, lens_record: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Map Lens.org record to related identifiers.

        Args:
            lens_record: Raw Lens.org publication record

        Returns:
            List of related identifiers in InvenioRDM format
        """
        identifiers = []

        # DOI
        if doi := self._extract_doi(lens_record):
            identifiers.append(
                {
                    "identifier": doi,
                    "scheme": "doi",
                    "relation_type": {"id": "isidenticalto"},
                }
            )

        # PubMed ID
        if pmid := self._extract_pmid(lens_record):
            identifiers.append(
                {
                    "identifier": pmid,
                    "scheme": "pmid",
                    "relation_type": {"id": "isidenticalto"},
                }
            )

        # arXiv
        if arxiv := self._extract_arxiv(lens_record):
            identifiers.append(
                {
                    "identifier": arxiv,
                    "scheme": "arxiv",
                    "relation_type": {"id": "isidenticalto"},
                }
            )

        # ISBN (for books/book chapters)
        if isbn_list := self._extract_isbn(lens_record):
            for isbn in isbn_list:
                identifiers.append(
                    {
                        "identifier": isbn,
                        "scheme": "isbn",
                        "relation_type": {"id": "isidenticalto"},
                    }
                )

        # ISSN (for journal articles)
        if issn_list := self._extract_issn(lens_record):
            for issn in issn_list:
                identifiers.append(
                    {
                        "identifier": issn,
                        "scheme": "issn",
                        "relation_type": {"id": "ispartof"},
                    }
                )

        # Other external IDs
        external_ids = self._extract_external_ids(lens_record)
        identifiers.extend(external_ids)

        return identifiers

    def _extract_doi(self, lens_record: Dict[str, Any]) -> Optional[str]:
        """Extract and validate DOI."""
        doi = self.safe_get(lens_record, "doi")

        if not doi:
            # Check in external_ids array
            external_ids = self.safe_get(lens_record, "external_ids", default=[])
            if external_ids:
                for ext_id in external_ids:
                    if isinstance(ext_id, dict):
                        if ext_id.get("type") == "doi":
                            doi = ext_id.get("value")
                            break

        if not doi:
            return None

        # Clean DOI: remove URL prefix if present
        doi = str(doi).strip()
        doi = re.sub(r"^https?://doi\.org/", "", doi)
        doi = re.sub(r"^doi:", "", doi, flags=re.IGNORECASE)

        # Validate DOI format (basic check)
        if re.match(r"^10\.\d{4,}/\S+", doi):
            return doi

        self.logger.warning(f"Invalid DOI format: {doi}")
        return None

    def _extract_pmid(self, lens_record: Dict[str, Any]) -> Optional[str]:
        """Extract PubMed ID."""
        pmid = self.safe_get(lens_record, "pubmed_id") or self.safe_get(
            lens_record, "pmid"
        )

        if not pmid:
            # Check in external_ids
            external_ids = self.safe_get(lens_record, "external_ids", default=[])
            if external_ids:  # Add null check
                for ext_id in external_ids:
                    if isinstance(ext_id, dict):
                        if ext_id.get("type") == "pmid":
                            pmid = ext_id.get("value")
                            break

        if pmid:
            # Ensure it's a string of digits
            pmid_str = str(pmid).strip()
            if pmid_str.isdigit():
                return pmid_str

        return None

    def _extract_pmcid(self, lens_record: Dict[str, Any]) -> Optional[str]:
        """Extract PubMed Central ID."""
        pmcid = self.safe_get(lens_record, "pmcid")

        if not pmcid:
            # Check in external_ids
            external_ids = self.safe_get(lens_record, "external_ids", default=[])
            if external_ids:  # Add null check
                for ext_id in external_ids:
                    if isinstance(ext_id, dict):
                        if ext_id.get("type") == "pmcid":
                            pmcid = ext_id.get("value")
                            break

        if pmcid:
            pmcid_str = str(pmcid).strip()
            # Ensure it starts with PMC (case-insensitive check)
            if not pmcid_str.upper().startswith("PMC"):
                pmcid_str = f"PMC{pmcid_str}"
            else:
                # Normalize to uppercase PMC prefix
                pmcid_str = "PMC" + pmcid_str[3:]
            return pmcid_str

        return None

    def _extract_arxiv(self, lens_record: Dict[str, Any]) -> Optional[str]:
        """Extract arXiv ID."""
        arxiv = self.safe_get(lens_record, "arxiv_id")

        if not arxiv:
            # Check in external_ids
            external_ids = self.safe_get(lens_record, "external_ids", default=[])
            if external_ids:  # Add null check
                for ext_id in external_ids:
                    if isinstance(ext_id, dict):
                        if ext_id.get("type") == "arxiv":
                            arxiv = ext_id.get("value")
                            break

        if arxiv:
            arxiv_str = str(arxiv).strip()
            # Validate arXiv format (YYMM.NNNNN or archive/YYMMNNN)
            if re.match(r"^\d{4}\.\d{4,5}$", arxiv_str) or re.match(
                r"^[a-z-]+/\d{7}$", arxiv_str
            ):
                return arxiv_str

        return None

    def _extract_isbn(self, lens_record: Dict[str, Any]) -> List[str]:
        """
        Extract ISBN (International Standard Book Number).

        Returns list since a book may have multiple ISBNs.
        """
        isbn_list = []

        # Check source.isbn
        source_isbn = self.safe_get(lens_record, "source", "isbn")
        if source_isbn:
            isbn_list.extend(self._normalize_isbn_list(source_isbn))

        # Check external_ids
        external_ids = self.safe_get(lens_record, "external_ids", default=[])
        if external_ids:  # Add null check
            for ext_id in external_ids:
                if isinstance(ext_id, dict):
                    if ext_id.get("type") == "isbn":
                        value = ext_id.get("value")
                        if value:
                            isbn_list.extend(self._normalize_isbn_list(value))

        # Remove duplicates
        return list(set(isbn_list))

    def _extract_issn(self, lens_record: Dict[str, Any]) -> List[str]:
        """
        Extract ISSN (International Standard Serial Number).

        Returns list since a journal may have print and electronic ISSNs.
        """
        issn_list = []

        # Check source.issn (can be array of objects with type/value)
        source_issn = self.safe_get(lens_record, "source", "issn")
        if source_issn:
            if isinstance(source_issn, list):
                for item in source_issn:
                    if isinstance(item, dict) and "value" in item:
                        # Extract value from {type: "electronic", value: "1234567"}
                        issn_list.extend(self._normalize_issn_list(item["value"]))
                    elif isinstance(item, str):
                        issn_list.extend(self._normalize_issn_list(item))
            else:
                issn_list.extend(self._normalize_issn_list(source_issn))

        # Check source.eissn
        source_eissn = self.safe_get(lens_record, "source", "eissn")
        if source_eissn:
            issn_list.extend(self._normalize_issn_list(source_eissn))

        # Check external_ids
        external_ids = self.safe_get(lens_record, "external_ids", default=[])
        if external_ids:  # Add null check
            for ext_id in external_ids:
                if isinstance(ext_id, dict):
                    ext_type = ext_id.get("type", "").lower()
                    if ext_type in ["issn", "eissn"]:
                        value = ext_id.get("value")
                        if value:
                            issn_list.extend(self._normalize_issn_list(value))

        # Remove duplicates
        return list(set(issn_list))

    def _extract_external_ids(
        self, lens_record: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Extract other external identifiers not covered by standard schemes.
        """
        identifiers = []

        external_ids = self.safe_get(lens_record, "external_ids", default=[])

        # Already handled schemes (standard + Lens-specific that we skip)
        handled_schemes = {
            "doi",
            "pmid",
            "pmcid",
            "arxiv",
            "isbn",
            "issn",
            "eissn",
            "openalex",  # Not supported by InvenioRDM, stored in custom fields
            "magid",  # Microsoft Academic Graph ID - not supported
        }

        if external_ids:  # Add null check
            for ext_id in external_ids:
                if not isinstance(ext_id, dict):
                    continue

                scheme = self.safe_get(ext_id, "type", default="").lower()
                value = self.safe_get(ext_id, "value")

                if not scheme or not value:
                    continue

                # Skip already handled or unsupported schemes
                if scheme in handled_schemes:
                    continue

                # Only include if it's a known InvenioRDM scheme
                if scheme in self.config.IDENTIFIER_SCHEMES:
                    identifiers.append(
                        {
                            "identifier": str(value),
                            "scheme": scheme,
                            "relation_type": {"id": "isidenticalto"},
                        }
                    )
                else:
                    # Log unknown scheme
                    self.logger.debug(f"Unknown external ID scheme: {scheme}")

        return identifiers

    def _normalize_isbn_list(self, isbn_value: Any) -> List[str]:
        """
        Normalize ISBN value(s) to list of valid ISBNs.

        Args:
            isbn_value: Can be string or list of strings

        Returns:
            List of normalized ISBN strings
        """
        if isinstance(isbn_value, list):
            isbn_list = isbn_value
        else:
            # Split by common separators
            isbn_str = str(isbn_value)
            isbn_list = re.split(r"[,;\s]+", isbn_str)

        normalized = []
        for isbn in isbn_list:
            isbn = str(isbn).strip()
            # Remove hyphens and spaces
            isbn = re.sub(r"[-\s]", "", isbn)
            # Validate ISBN-10 or ISBN-13
            if re.match(r"^\d{10}$", isbn) or re.match(r"^\d{13}$", isbn):
                normalized.append(isbn)

        return normalized

    def _normalize_issn_list(self, issn_value: Any) -> List[str]:
        """
        Normalize ISSN value(s) to list of valid ISSNs.

        Args:
            issn_value: Can be string or list of strings

        Returns:
            List of normalized ISSN strings
        """
        if isinstance(issn_value, list):
            issn_list = issn_value
        else:
            # Split by common separators
            issn_str = str(issn_value)
            issn_list = re.split(r"[,;\s]+", issn_str)

        normalized = []
        for issn in issn_list:
            issn = str(issn).strip()
            # Remove spaces but keep hyphen
            issn = issn.replace(" ", "")
            # Validate ISSN format (NNNN-NNNN)
            if re.match(r"^\d{4}-?\d{3}[\dX]$", issn, re.IGNORECASE):
                # Ensure hyphen is present
                if "-" not in issn:
                    issn = f"{issn[:4]}-{issn[4:]}"
                normalized.append(issn.upper())

        return normalized
