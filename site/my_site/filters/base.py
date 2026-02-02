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

    def build_query(
        self,
        search_term: Optional[str] = None,
        search_query: Optional[str] = None,
        facet_filters: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build the OpenSearch query with aggregations.

        Args:
            search_term: Optional search term for filtering aggregation results
            search_query: Optional user's main search query (e.g., author name)
            facet_filters: Optional list of facet filters (e.g., ['country:Belgium'])

        Returns:
            OpenSearch query dict with aggregations filtered by search context
        """
        query_dict = {
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

        # Build query filter to match current search context
        must_queries = []

        # Add user's search query if present
        if search_query:
            must_queries.append(
                {"query_string": {"query": search_query, "default_operator": "AND"}}
            )

        # Add facet filters if present (excluding the current facet being queried)
        if facet_filters:
            for facet_filter in facet_filters:
                if ":" in facet_filter:
                    facet_name, facet_value = facet_filter.split(":", 1)
                    # Skip if it's the same facet we're aggregating on
                    if facet_name != self.get_filter_key():
                        # Determine the field to filter on based on facet name
                        field_mapping = self._get_facet_field_mapping()
                        field_name = field_mapping.get(
                            facet_name, f"metadata.{facet_name}"
                        )
                        
                        # Handle hierarchical resource_type format
                        if facet_name == "resource_type":
                            if "+inner:" in facet_value:
                                # Format: "publication+inner:publication-article"
                                # Extract the actual child value after +inner:
                                facet_value = facet_value.split("+inner:", 1)[1]
                                must_queries.append({"term": {field_name: facet_value}})
                            else:
                                # Format: "publication" (parent only)
                                # Use prefix match to get all children (publication-article, publication-book, etc.)
                                must_queries.append({"prefix": {field_name: f"{facet_value}-"}})
                        else:
                            must_queries.append({"term": {field_name: facet_value}})

        # Apply query filter if there are any conditions
        if must_queries:
            query_dict["query"] = {"bool": {"must": must_queries}}

        return query_dict

    def _get_facet_field_mapping(self) -> Dict[str, str]:
        """Map facet names to their OpenSearch field paths.

        Override this in subclasses if needed for custom mappings.
        """
        return {
            "resource_type": "metadata.resource_type.id",
            "publication_country": "custom_fields.publication:country",
            "affiliation_region": "custom_fields.publication:affiliation_region",
            "subject": "metadata.subjects.subject",
            "funding_org": "metadata.funding.funder.name",
            "publication_year": "custom_fields.publication:year",
            "is_open_access": "custom_fields.publication:is_open_access",
            "author": "metadata.creators.person_or_org.name.keyword",
            "affiliation": "metadata.creators.affiliations.name.keyword",
            "country": "custom_fields.publication:country",
            "funding": "metadata.funding.funder.name.keyword",
        }

    def execute(
        self,
        search_term: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        sort_by: str = "count",
        search_query: Optional[str] = None,
        facet_filters: Optional[List[str]] = None,
    ) -> Dict:
        """Execute the search and return filtered results with pagination.

        Args:
            search_term: Optional search term for filtering
            page: Page number (1-indexed)
            size: Number of results per page
            sort_by: Sort order ('count' for doc_count desc, 'name' for alphabetical)
            search_query: Optional user's main search query for dynamic aggregations
            facet_filters: Optional list of active facet filters

        Returns:
            Dict with 'results', 'total', 'page', 'size', 'has_more'
        """
        try:
            query = self.build_query(search_term, search_query, facet_filters)
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
