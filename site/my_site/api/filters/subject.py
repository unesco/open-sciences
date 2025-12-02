"""Subject/Keyword filter backend."""

from typing import Dict, List, Optional
from invenio_search import current_search_client
from .base import BaseFilterBackend


class SubjectFilterBackend(BaseFilterBackend):
    """Filter backend for subjects/keywords.

    Note: subjects.subject is a text field, so we fetch records
    and aggregate subjects in Python for proper substring matching.
    """

    def get_field_name(self) -> str:
        return "metadata.subjects.subject"

    def get_filter_key(self) -> str:
        return "subject"

    def execute(self, search_term: Optional[str] = None) -> List[Dict]:
        """
        Override execute for subjects - text field requires different approach.
        We fetch ALL records and filter/aggregate subjects in Python.
        """
        try:
            # Build query - fetch all records with subjects
            query_body = {
                "size": 1000,
                "_source": ["metadata.subjects"],
                "query": {"exists": {"field": "metadata.subjects"}},
            }

            # Execute search
            result = current_search_client.search(
                index=self.get_index_name(), body=query_body
            )

            # Aggregate subjects manually
            subject_counts = {}
            for hit in result.get("hits", {}).get("hits", []):
                subjects_list = (
                    hit.get("_source", {}).get("metadata", {}).get("subjects", [])
                )
                for subject_obj in subjects_list:
                    subject = subject_obj.get("subject")
                    if subject:
                        subject_counts[subject] = subject_counts.get(subject, 0) + 1

            # Filter by search term (case-insensitive substring match)
            if search_term:
                search_lower = search_term.lower()
                subject_counts = {
                    name: count
                    for name, count in subject_counts.items()
                    if search_lower in name.lower()
                }

            # Convert to results format and sort alphabetically
            results = []
            for subject, count in subject_counts.items():
                results.append(
                    {
                        "value": subject,
                        "text": subject,
                        "name": subject,
                        "doc_count": count,
                    }
                )

            results.sort(key=lambda x: x["name"].lower())

            # Limit to max size
            return results[: self.get_aggregation_size()]

        except Exception as e:
            print(f"Error in SubjectFilterBackend: {str(e)}")
            return []
