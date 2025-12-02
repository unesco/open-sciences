"""Publication year filter backend."""

from typing import Dict, List, Optional
from .base import BaseFilterBackend


class PublicationYearFilterBackend(BaseFilterBackend):
    """Filter backend for publication years."""

    def get_field_name(self) -> str:
        return "metadata.publication_date"

    def get_filter_key(self) -> str:
        return "year"

    def get_aggregation_order(self) -> Dict[str, str]:
        """Order years in descending order."""
        return {"_key": "desc"}

    def filter_results(
        self, buckets: List[Dict], search_term: Optional[str]
    ) -> List[Dict]:
        """Extract year from date and filter."""
        results = []
        for bucket in buckets:
            # Extract year from date string (format: YYYY-MM-DD)
            date_str = (
                bucket["key_as_string"]
                if "key_as_string" in bucket
                else str(bucket["key"])
            )
            year = date_str.split("-")[0]

            # Filter by search term if provided
            if not search_term or search_term in year:
                results.append(
                    {
                        "name": year,
                        "value": year,
                        "text": year,
                        "doc_count": bucket["doc_count"],
                    }
                )
        return results
