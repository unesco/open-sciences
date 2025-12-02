"""Resource type filter backend."""

from .base import BaseFilterBackend


class ResourceTypeFilterBackend(BaseFilterBackend):
    """Filter backend for resource types."""

    def get_field_name(self) -> str:
        return "metadata.resource_type.id"

    def get_filter_key(self) -> str:
        return "resource_type"
