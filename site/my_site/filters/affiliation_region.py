"""Affiliation Region filter backend."""

import json
import os
from typing import Dict, Optional
from invenio_search import current_search_client
from .base import BaseFilterBackend
from ..constants import REGION_DISPLAY_NAMES


def _load_country_region_mapping() -> Dict[str, str]:
    """Load country to region mapping from JSON file.
    
    JSON format: {"country_name": "REGION_KEY", ...}
    Returns: {"country_name": "Display Name", ...}
    """
    json_path = os.path.join(os.path.dirname(__file__), "data", "country_region_mapping.json")
    
    with open(json_path, "r", encoding="utf-8") as f:
        country_to_region_key = json.load(f)
    
    # Convert region keys to display names
    return {
        country: REGION_DISPLAY_NAMES[region_key]
        for country, region_key in country_to_region_key.items()
    }


# Load mapping at module level (once on import)
COUNTRY_TO_REGION = _load_country_region_mapping()


class AffiliationRegionFilterBackend(BaseFilterBackend):
    """Filter backend for author affiliation regions.
    
    Groups countries into UNESCO regional groups:
    - Europe & North America
    - Arab States  
    - Africa
    - Latin America & the Caribbean
    - Asia & the Pacific
    """

    def get_field_name(self) -> str:
        """Return the OpenSearch field name - we'll aggregate on country names."""
        return "custom_fields.publication:country"

    def get_filter_key(self) -> str:
        return "affiliation_region"

    def _get_region_for_country(self, country_name: str) -> Optional[str]:
        """Get the UNESCO region for a given country name.
        
        Args:
            country_name: Full country name (e.g., "United States", "Brazil")
            
        Returns:
            UNESCO region name or None if not found
        """
        return COUNTRY_TO_REGION.get(country_name)

    def execute(
        self,
        search_term: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        sort_by: str = "count",
    ) -> Dict:
        """
        Execute search and aggregate countries into UNESCO regions.

        Args:
            search_term: Optional search term for filtering regions
            page: Page number (1-indexed)
            size: Number of results per page
            sort_by: Sort order ('count' for doc_count desc, 'name' for alphabetical)

        Returns:
            Dict with 'results' and pagination info
        """
        try:
            # Get all unique countries from custom_fields.publication:country
            query_body = {
                "size": 0,
                "aggs": {
                    "by_country": {
                        "terms": {
                            "field": "custom_fields.publication:country",
                            "size": 10000,
                            "order": {"_count": "desc"},
                        }
                    }
                },
            }

            result = current_search_client.search(
                index=self.get_index_name(), body=query_body
            )

            # Extract country buckets
            country_buckets = (
                result.get("aggregations", {})
                .get("by_country", {})
                .get("buckets", [])
            )

            # Aggregate countries into regions
            region_counts = {}
            for bucket in country_buckets:
                country_name = bucket["key"]
                doc_count = bucket["doc_count"]
                
                # Map country name to UNESCO region
                region = self._get_region_for_country(country_name)
                if region:
                    if region in region_counts:
                        region_counts[region] += doc_count
                    else:
                        region_counts[region] = doc_count

            # Filter by search term if provided (case-insensitive substring match)
            if search_term:
                search_lower = search_term.lower()
                region_counts = {
                    region: count
                    for region, count in region_counts.items()
                    if search_lower in region.lower()
                }

            # Convert to results format
            results = []
            for region, count in region_counts.items():
                results.append(
                    {
                        "value": region,
                        "text": region,
                        "name": region,
                        "count": count,
                    }
                )

            # Sort results
            if sort_by == "count":
                results.sort(key=lambda x: (-x["count"], x["name"].lower()))
            else:
                results.sort(key=lambda x: x["name"].lower())

            # Pagination
            total = len(results)
            start = (page - 1) * size
            end = start + size
            paginated_results = results[start:end]

            return {
                "results": paginated_results,
                "total": total,
                "page": page,
                "size": size,
                "has_more": end < total,
            }

        except Exception as e:
            print(f"Error in AffiliationRegionFilterBackend: {str(e)}")
            import traceback

            traceback.print_exc()
            return {
                "results": [],
                "total": 0,
                "page": page,
                "size": size,
                "has_more": False,
            }
