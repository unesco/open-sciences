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
