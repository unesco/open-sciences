"""Subject/Keyword filter backend."""

from typing import Dict, List, Optional
from invenio_search import current_search_client
from .base import BaseFilterBackend


class SubjectFilterBackend(BaseFilterBackend):
    """Filter backend for subjects/keywords.

    Note: subjects.subject is a text field, so we use aggregation or scroll
    to count distinct documents per subject.
    """

    def get_field_name(self) -> str:
        return "metadata.subjects.subject"

    def get_filter_key(self) -> str:
        return "subject"

    def _normalize_subject_name(self, name: str) -> str:
        """Normalize subject name by removing extra spaces."""
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
        Override execute for subjects - use aggregation for better performance.

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
                        "unique_subjects": {
                            "terms": {
                                "field": "metadata.subjects.subject.keyword",
                                "size": 10000,  # Get all unique subjects
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
                    .get("unique_subjects", {})
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

            # Normalize subject names
            normalized_counts = {}
            original_names = {}

            for bucket in buckets:
                subject_name = bucket["key"]
                doc_count = bucket["doc_count"]

                # Normalize the name
                normalized = self._normalize_subject_name(subject_name)

                # Accumulate counts for normalized name
                if normalized in normalized_counts:
                    normalized_counts[normalized] += doc_count
                else:
                    normalized_counts[normalized] = doc_count
                    original_names[normalized] = subject_name

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
            print(f"Error in SubjectFilterBackend: {str(e)}")
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
        Fallback method using scroll API - counts distinct documents per subject.
        """
        try:
            # Build base query with filters from search context
            base_query = self.build_query(search_term, search_query, facet_filters)
            
            # Build scroll query - use scroll API to fetch ALL records
            query_body = {
                "size": 1000,
                "_source": ["metadata.subjects"],
            }
            
            # If there's a query filter, use it; otherwise just check field exists
            if "query" in base_query:
                query_body["query"] = base_query["query"]
            else:
                query_body["query"] = {"exists": {"field": "metadata.subjects"}}

            # Initialize scroll
            result = current_search_client.search(
                index=self.get_index_name(), body=query_body, scroll="2m"
            )

            scroll_id = result.get("_scroll_id")
            hits = result.get("hits", {}).get("hits", [])

            # Aggregate subjects by DOCUMENT (not by occurrence)
            # Use normalized names to avoid duplicates
            normalized_document_sets = {}
            original_names = {}

            # Process first batch
            for hit in hits:
                doc_id = hit.get("_id")
                subjects_list = (
                    hit.get("_source", {}).get("metadata", {}).get("subjects", [])
                )
                # Get unique normalized subjects in this document
                subjects_in_doc = set()
                for subject_obj in subjects_list:
                    subject_name = subject_obj.get("subject")
                    if subject_name:
                        normalized = self._normalize_subject_name(subject_name)
                        subjects_in_doc.add(normalized)
                        # Track original name
                        if normalized not in original_names:
                            original_names[normalized] = subject_name

                # Add document ID to each normalized subject's set
                for normalized in subjects_in_doc:
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
                    subjects_list = (
                        hit.get("_source", {}).get("metadata", {}).get("subjects", [])
                    )
                    subjects_in_doc = set()
                    for subject_obj in subjects_list:
                        subject_name = subject_obj.get("subject")
                        if subject_name:
                            normalized = self._normalize_subject_name(subject_name)
                            subjects_in_doc.add(normalized)
                            if normalized not in original_names:
                                original_names[normalized] = subject_name

                    for normalized in subjects_in_doc:
                        if normalized not in normalized_document_sets:
                            normalized_document_sets[normalized] = set()
                        normalized_document_sets[normalized].add(doc_id)

            # Clear scroll
            try:
                current_search_client.clear_scroll(scroll_id=scroll_id)
            except:
                pass

            # Count distinct documents per normalized subject
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
