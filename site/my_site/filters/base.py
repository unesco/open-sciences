"""Base filter backend class.

Inspired by Django REST Framework and django-filter patterns.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from invenio_search import current_search_client


class BaseFilterBackend(ABC):
    """Base class for filter backends."""

    @abstractmethod
    def get_field_name(self) -> str:
        """Return the OpenSearch field name to aggregate on."""
        pass

    @abstractmethod
    def get_filter_key(self) -> str:
        """Return the filter key used in URL (e.g., 'country', 'funding')."""
        pass

    def get_index_name(self) -> str:
        """Return the OpenSearch index name. Override if needed."""
        return "my-site-rdmrecords-records"

    def get_aggregation_size(self) -> int:
        """Return the maximum number of aggregation buckets. Override if needed."""
        return 100

    def get_aggregation_order(self) -> Dict[str, str]:
        """Return the aggregation order. Override if needed."""
        return {"_key": "asc"}

    def build_query(self, search_term: Optional[str] = None) -> Dict[str, Any]:
        """Build the OpenSearch query with aggregations."""
        return {
            "size": 0,  # We don't need the actual documents
            "aggs": {
                f"unique_{self.get_filter_key()}": {
                    "terms": {
                        "field": self.get_field_name(),
                        "size": self.get_aggregation_size(),
                        "order": self.get_aggregation_order(),
                    }
                }
            },
        }

    def execute(
        self,
        search_term: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        sort_by: str = "count",
    ) -> Dict:
        """Execute the search and return filtered results with pagination.

        Args:
            search_term: Optional search term for filtering
            page: Page number (1-indexed)
            size: Number of results per page
            sort_by: Sort order ('count' for doc_count desc, 'name' for alphabetical)

        Returns:
            Dict with 'results', 'total', 'page', 'size', 'has_more'
        """
        try:
            query = self.build_query(search_term)
            result = current_search_client.search(
                index=self.get_index_name(), body=query
            )

            # Extract buckets from aggregations
            agg_key = f"unique_{self.get_filter_key()}"
            buckets = []
            if "aggregations" in result and agg_key in result["aggregations"]:
                buckets = result["aggregations"][agg_key]["buckets"]

            # Convert to results format with 'count' field
            results = []
            for bucket in buckets:
                key = bucket["key"]
                # Filter by search term if provided
                if not search_term or search_term.lower() in key.lower():
                    results.append(
                        {
                            "name": key,
                            "value": key,
                            "text": key,
                            "count": bucket["doc_count"],  # Use 'count' not 'doc_count'
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
            # Log error and return empty results
            print(f"Error in {self.__class__.__name__}: {str(e)}")
            return {
                "results": [],
                "total": 0,
                "page": page,
                "size": size,
                "has_more": False,
            }
