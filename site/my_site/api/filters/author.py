"""Author filter backend."""

from typing import Dict, List, Optional
from invenio_search import current_search_client
from .base import BaseFilterBackend


class AuthorFilterBackend(BaseFilterBackend):
    """Filter backend for author names.

    Note: person_or_org.name is a text field, so we fetch records
    and aggregate authors in Python for proper substring matching.
    """

    def get_field_name(self) -> str:
        return "metadata.creators.person_or_org.name"

    def get_filter_key(self) -> str:
        return "author"

    def execute(self, search_term: Optional[str] = None) -> List[Dict]:
        """
        Override execute for authors - text field requires different approach.
        We fetch ALL records and filter/aggregate author names in Python.
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

            # Aggregate author names manually
            author_counts = {}
            for hit in result.get("hits", {}).get("hits", []):
                creators_list = (
                    hit.get("_source", {}).get("metadata", {}).get("creators", [])
                )
                for creator in creators_list:
                    author_name = creator.get("person_or_org", {}).get("name")
                    if author_name:
                        author_counts[author_name] = (
                            author_counts.get(author_name, 0) + 1
                        )

            # Filter by search term (case-insensitive substring match)
            if search_term:
                search_lower = search_term.lower()
                author_counts = {
                    name: count
                    for name, count in author_counts.items()
                    if search_lower in name.lower()
                }

            # Convert to results format and sort alphabetically
            results = []
            for author_name, count in author_counts.items():
                results.append(
                    {
                        "value": author_name,
                        "text": author_name,
                        "name": author_name,
                        "doc_count": count,
                    }
                )

            results.sort(key=lambda x: x["name"].lower())

            # Limit to max size
            return results[: self.get_aggregation_size()]

        except Exception as e:
            print(f"Error in AuthorFilterBackend: {str(e)}")
            return []
