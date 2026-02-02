"""Affiliation filter backend."""

from typing import Dict, List, Optional
from invenio_search import current_search_client
from .base import BaseFilterBackend


class AffiliationFilterBackend(BaseFilterBackend):
    """Filter backend for affiliations.

    Note: affiliations.name is a text field, so we use aggregation or scroll
    to count distinct documents per affiliation.
    """

    def get_field_name(self) -> str:
        return "metadata.creators.affiliations.name"

    def get_filter_key(self) -> str:
        return "affiliation"

    def _normalize_affiliation_name(self, name: str) -> str:
        """Normalize affiliation name by removing extra spaces."""
        return name.strip()

    def execute(
        self,
        search_term: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        sort_by: str = "count",
        search_query: Optional[str] = None,
        facet_filters: Optional[List[str]] = None,
    ) -> Dict:
        """
        Override execute for affiliations - use aggregation for better performance.

        Args:
            search_term: Optional search term for filtering
            page: Page number (1-indexed)
            size: Number of results per page
            sort_by: Sort order ('count' for doc_count desc, 'name' for alphabetical)
            search_query: Optional user's main search query for dynamic aggregations
            facet_filters: Optional list of active facet filters

        Returns:
            Dict with 'results' and pagination info
        """
        try:
            # First try with .keyword subfield (faster)
            try:
                query_body = {
                    "size": 0,
                    "aggs": {
                        "unique_affiliations": {
                            "terms": {
                                "field": "metadata.creators.affiliations.name.keyword",
                                "size": 10000,  # Get all unique affiliations
                                "order": {"_count": "desc"},
                            }
                        }
                    },
                }
                
                # Add query filter from parent class if search_query or facet_filters present
                base_query = self.build_query(search_term, search_query, facet_filters)
                if "query" in base_query:
                    query_body["query"] = base_query["query"]

                result = current_search_client.search(
                    index=self.get_index_name(), body=query_body
                )

                buckets = (
                    result.get("aggregations", {})
                    .get("unique_affiliations", {})
                    .get("buckets", [])
                )

                # If no buckets returned, try the scroll approach
                if not buckets:
                    raise Exception("No keyword field, fall back to scroll")

            except Exception as keyword_error:
                # Fallback: use scroll API if .keyword doesn't exist
                print(
                    f"Keyword aggregation failed, using scroll fallback: {keyword_error}"
                )
                return self._execute_with_scroll(search_term, page, size, sort_by, search_query, facet_filters)

            # Normalize affiliation names (though less likely to have duplicates than authors)
            normalized_counts = {}
            original_names = {}

            for bucket in buckets:
                affiliation_name = bucket["key"]
                doc_count = bucket["doc_count"]

                # Normalize the name
                normalized = self._normalize_affiliation_name(affiliation_name)

                # Accumulate counts for normalized name
                if normalized in normalized_counts:
                    normalized_counts[normalized] += doc_count
                else:
                    normalized_counts[normalized] = doc_count
                    original_names[normalized] = affiliation_name

            # Filter by search term (case-insensitive substring match)
            if search_term:
                search_lower = search_term.lower()
                normalized_counts = {
                    name: count
                    for name, count in normalized_counts.items()
                    if search_lower in name.lower()
                }

            # Convert to results format
            results = []
            for normalized_name, count in normalized_counts.items():
                display_name = original_names.get(normalized_name, normalized_name)
                results.append(
                    {
                        "value": display_name,
                        "text": display_name,
                        "name": display_name,
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
            print(f"Error in AffiliationFilterBackend: {str(e)}")
            import traceback

            traceback.print_exc()
            return {
                "results": [],
                "total": 0,
                "page": page,
                "size": size,
                "has_more": False,
            }

    def _execute_with_scroll(
        self,
        search_term: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        sort_by: str = "count",
        search_query: Optional[str] = None,
        facet_filters: Optional[List[str]] = None,
    ) -> Dict:
        """
        Fallback method using scroll API - counts distinct documents per affiliation.
        """
        try:
            # Build base query with filters from search context
            base_query = self.build_query(search_term, search_query, facet_filters)
            
            # Build scroll query - use scroll API to fetch ALL records
            query_body = {
                "size": 1000,
                "_source": ["metadata.creators"],
            }
            
            # If there's a query filter, use it; otherwise just check field exists
            if "query" in base_query:
                query_body["query"] = base_query["query"]
            else:
                query_body["query"] = {"exists": {"field": "metadata.creators"}}

            # Initialize scroll
            result = current_search_client.search(
                index=self.get_index_name(), body=query_body, scroll="2m"
            )

            scroll_id = result.get("_scroll_id")
            hits = result.get("hits", {}).get("hits", [])

            # Aggregate affiliations by DOCUMENT (not by occurrence)
            # Use normalized names to avoid duplicates
            normalized_document_sets = {}
            original_names = {}

            # Process first batch
            for hit in hits:
                doc_id = hit.get("_id")
                creators_list = (
                    hit.get("_source", {}).get("metadata", {}).get("creators", [])
                )
                # Get unique normalized affiliations in this document
                affiliations_in_doc = set()
                for creator in creators_list:
                    affiliations = creator.get("affiliations", [])
                    for affiliation in affiliations:
                        affiliation_name = affiliation.get("name")
                        if affiliation_name:
                            normalized = self._normalize_affiliation_name(
                                affiliation_name
                            )
                            affiliations_in_doc.add(normalized)
                            # Track original name
                            if normalized not in original_names:
                                original_names[normalized] = affiliation_name

                # Add document ID to each normalized affiliation's set
                for normalized in affiliations_in_doc:
                    if normalized not in normalized_document_sets:
                        normalized_document_sets[normalized] = set()
                    normalized_document_sets[normalized].add(doc_id)

            # Continue scrolling to get all documents
            while len(hits) > 0:
                result = current_search_client.scroll(scroll_id=scroll_id, scroll="2m")
                scroll_id = result.get("_scroll_id")
                hits = result.get("hits", {}).get("hits", [])

                for hit in hits:
                    doc_id = hit.get("_id")
                    creators_list = (
                        hit.get("_source", {}).get("metadata", {}).get("creators", [])
                    )
                    affiliations_in_doc = set()
                    for creator in creators_list:
                        affiliations = creator.get("affiliations", [])
                        for affiliation in affiliations:
                            affiliation_name = affiliation.get("name")
                            if affiliation_name:
                                normalized = self._normalize_affiliation_name(
                                    affiliation_name
                                )
                                affiliations_in_doc.add(normalized)
                                if normalized not in original_names:
                                    original_names[normalized] = affiliation_name

                    for normalized in affiliations_in_doc:
                        if normalized not in normalized_document_sets:
                            normalized_document_sets[normalized] = set()
                        normalized_document_sets[normalized].add(doc_id)

            # Clear scroll
            try:
                current_search_client.clear_scroll(scroll_id=scroll_id)
            except:
                pass

            # Count distinct documents per normalized affiliation
            normalized_counts = {}
            for normalized, doc_ids in normalized_document_sets.items():
                # Filter by search term
                if search_term:
                    search_lower = search_term.lower()
                    if search_lower not in normalized.lower():
                        continue
                normalized_counts[normalized] = len(doc_ids)

            # Convert to results format
            results = []
            for normalized, count in normalized_counts.items():
                display_name = original_names.get(normalized, normalized)
                results.append(
                    {
                        "value": display_name,
                        "text": display_name,
                        "name": display_name,
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
            print(f"Error in scroll fallback: {str(e)}")
            import traceback

            traceback.print_exc()
            return {
                "results": [],
                "total": 0,
                "page": page,
                "size": size,
                "has_more": False,
            }
