"""Funding organization filter backend."""

from typing import Dict, List, Optional
from invenio_search import current_search_client
from .base import BaseFilterBackend


class FundingOrgFilterBackend(BaseFilterBackend):
    """Filter backend for funding organizations.

    Note: funder.name is a text field (not keyword), so we cannot use
    standard aggregations. We fetch documents and aggregate in Python.
    """

    def get_field_name(self) -> str:
        return "metadata.funding.funder.name"

    def get_filter_key(self) -> str:
        return "funding"

    def execute(
        self,
        search_term: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        sort_by: str = "count",
    ) -> Dict:
        """
        Override execute for funding - text field requires different approach.
        We fetch ALL records and filter/aggregate funding organizations in Python.
        This allows for proper substring matching that works correctly.
        """
        try:
            # Build query - fetch all records with funding
            query_body = {
                "size": 1000,  # Fetch more records to get comprehensive funding data
                "_source": ["metadata.funding"],
                "query": {"exists": {"field": "metadata.funding"}},
            }

            # Execute search
            result = current_search_client.search(
                index=self.get_index_name(), body=query_body
            )

            # Aggregate funding organizations manually
            org_counts = {}
            for hit in result.get("hits", {}).get("hits", []):
                funding_list = (
                    hit.get("_source", {}).get("metadata", {}).get("funding", [])
                )
                for funding_item in funding_list:
                    funder_name = funding_item.get("funder", {}).get("name")
                    if funder_name:
                        org_counts[funder_name] = org_counts.get(funder_name, 0) + 1

            # Filter by search term (case-insensitive substring match)
            if search_term:
                search_lower = search_term.lower()
                org_counts = {
                    name: count
                    for name, count in org_counts.items()
                    if search_lower in name.lower()
                }

            # Convert to results format
            results = []
            for org_name, count in org_counts.items():
                results.append(
                    {
                        "value": org_name,
                        "text": org_name,
                        "name": org_name,
                        "count": count,
                    }
                )

            # Sort by count (descending) or name (alphabetical)
            if sort_by == "count":
                results.sort(key=lambda x: (-x["count"], x["name"].lower()))
            else:
                results.sort(key=lambda x: x["name"].lower())

            # Paginate
            total = len(results)
            start = (page - 1) * size
            end = start + size

            return {
                "results": results[start:end],
                "total": total,
                "page": page,
                "size": size,
                "has_more": end < total,
            }

        except Exception as e:
            print(f"Error in FundingOrgFilterBackend: {str(e)}")
            return []
