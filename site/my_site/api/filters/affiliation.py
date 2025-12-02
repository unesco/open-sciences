"""Affiliation filter backend."""

from typing import Dict, List, Optional
from invenio_search import current_search_client
from .base import BaseFilterBackend


class AffiliationFilterBackend(BaseFilterBackend):
    """Filter backend for affiliations.

    Note: affiliations.name is a text field, so we fetch records
    and aggregate affiliations in Python for proper substring matching.
    """

    def get_field_name(self) -> str:
        return "metadata.creators.affiliations.name"

    def get_filter_key(self) -> str:
        return "affiliation"

    def execute(self, search_term: Optional[str] = None) -> List[Dict]:
        """
        Override execute for affiliations - text field requires different approach.
        We fetch ALL records and filter/aggregate affiliations in Python.
        """
        try:
            # Build query - fetch all records with creators
            query_body = {
                "size": 1000,
                "_source": ["metadata.creators"],
                "query": {"exists": {"field": "metadata.creators"}},
            }

            # Execute search
            result = current_search_client.search(
                index=self.get_index_name(), body=query_body
            )

            # Aggregate affiliations manually
            affiliation_counts = {}
            for hit in result.get("hits", {}).get("hits", []):
                creators_list = (
                    hit.get("_source", {}).get("metadata", {}).get("creators", [])
                )
                for creator in creators_list:
                    affiliations = creator.get("affiliations", [])
                    for affiliation in affiliations:
                        name = affiliation.get("name")
                        if name:
                            affiliation_counts[name] = (
                                affiliation_counts.get(name, 0) + 1
                            )

            # Filter by search term (case-insensitive substring match)
            if search_term:
                search_lower = search_term.lower()
                affiliation_counts = {
                    name: count
                    for name, count in affiliation_counts.items()
                    if search_lower in name.lower()
                }

            # Convert to results format and sort alphabetically
            results = []
            for name, count in affiliation_counts.items():
                results.append(
                    {
                        "value": name,
                        "text": name,
                        "name": name,
                        "doc_count": count,
                    }
                )

            results.sort(key=lambda x: x["name"].lower())

            # Limit to max size
            return results[: self.get_aggregation_size()]

        except Exception as e:
            print(f"Error in AffiliationFilterBackend: {str(e)}")
            return []
