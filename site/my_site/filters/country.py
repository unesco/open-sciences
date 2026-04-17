"""Country filter backend with region-aware filtering."""

import json
import os
from typing import Dict, List, Optional

from .base import BaseFilterBackend
from my_site.constants import REGION_DISPLAY_NAMES as _REGION_DISPLAY_NAMES

# Reverse: display name → region key
_DISPLAY_NAME_TO_KEY = {v: k for k, v in _REGION_DISPLAY_NAMES.items()}


def _load_region_to_country_names() -> Dict[str, set]:
    """Build region display name → set of country names using the mapping file and pycountry."""
    json_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "data", "country_code_region_mapping.json")
    )
    if not os.path.exists(json_path):
        return {}

    with open(json_path, "r", encoding="utf-8") as f:
        code_to_region_key = json.load(f)

    try:
        import pycountry
    except ImportError:
        return {}

    # Build ISO code → country name(s) for reverse lookup
    code_to_names = {}
    for c in pycountry.countries:
        names = {c.name}
        if hasattr(c, "common_name"):
            names.add(c.common_name)
        if hasattr(c, "official_name"):
            names.add(c.official_name)
        code_to_names[c.alpha_2] = names

    # Build region display name → set of all possible country name variants
    region_countries: Dict[str, set] = {}
    for code, region_key in code_to_region_key.items():
        display = _REGION_DISPLAY_NAMES.get(region_key)
        if not display:
            continue
        if display not in region_countries:
            region_countries[display] = set()
        for name in code_to_names.get(code, set()):
            region_countries[display].add(name.lower())

    return region_countries


# Cache the mapping at module level (loaded once)
_REGION_COUNTRIES_CACHE: Optional[Dict[str, set]] = None


def _get_region_countries() -> Dict[str, set]:
    global _REGION_COUNTRIES_CACHE
    if _REGION_COUNTRIES_CACHE is None:
        _REGION_COUNTRIES_CACHE = _load_region_to_country_names()
    return _REGION_COUNTRIES_CACHE


class CountryFilterBackend(BaseFilterBackend):
    """Filter backend for publication countries, with region-aware filtering."""

    def get_field_name(self) -> str:
        return "custom_fields.publication:country"

    def get_filter_key(self) -> str:
        return "country"

    def execute(
        self,
        search_term: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        sort_by: str = "count",
        search_query: Optional[str] = None,
        facet_filters: Optional[List[str]] = None,
    ) -> Dict:
        """Execute search with additional region-based country filtering.

        When an affiliation_region facet filter is active, the result set is
        further narrowed to only those countries that belong to the selected
        region according to the authoritative mapping file.  This avoids
        leaking countries from multi-region documents.
        """
        # Detect active region filter
        active_region = None
        if facet_filters:
            for ff in facet_filters:
                if ":" in ff:
                    name, value = ff.split(":", 1)
                    if name == "affiliation_region":
                        active_region = value
                        break

        # Delegate to the base implementation for the OpenSearch query
        result = super().execute(
            search_term=search_term,
            page=page,
            size=size,
            sort_by=sort_by,
            search_query=search_query,
            facet_filters=facet_filters,
        )

        # If a region is selected, post-filter countries using the mapping
        if active_region:
            region_countries = _get_region_countries()
            allowed = region_countries.get(active_region)
            if allowed is not None:
                filtered = [
                    r for r in result.get("results", [])
                    if r["value"].lower() in allowed
                ]
                # Recalculate pagination on the filtered set
                total = len(filtered)
                start = (page - 1) * size
                end = start + size
                result["results"] = filtered[start:end] if start < total else []
                result["total"] = total
                result["has_more"] = end < total

        return result
