"""Publication year filter backend."""

from typing import Dict, List, Optional
from .base import BaseFilterBackend


class PublicationYearFilterBackend(BaseFilterBackend):
    """Filter backend for publication years.

    Uses the custom field 'publication:year' which contains extracted year values.
    This is a keyword field so standard aggregation works correctly.
    """

    def get_field_name(self) -> str:
        return "custom_fields.publication:year"

    def get_filter_key(self) -> str:
        return "year"

    def get_aggregation_order(self) -> Dict[str, str]:
        """Order years in descending order."""
        return {"_key": "desc"}
