"""Resource type filter backend."""

from typing import Dict, Optional
from .base import BaseFilterBackend


class ResourceTypeFilterBackend(BaseFilterBackend):
    """Filter backend for resource types.

    Uses metadata.resource_type.id which is a keyword field.
    Standard aggregation works correctly.
    """

    def get_field_name(self) -> str:
        return "metadata.resource_type.id"

    def get_filter_key(self) -> str:
        return "resource_type"

    def get_aggregation_order(self) -> Dict[str, str]:
        """Order by count descending."""
        return {"_count": "desc"}

    def get_sort_priority(self, name: str) -> int:
        """Pin "other" resource types (e.g. 'publication-other') to the bottom."""
        normalized = name.lower()
        if normalized == "other" or normalized.endswith("-other"):
            return 1
        return 0
