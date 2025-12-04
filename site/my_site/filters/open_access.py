"""Open Access filter backend."""

from .base import BaseFilterBackend


class OpenAccessFilterBackend(BaseFilterBackend):
    """Filter backend for open access status."""

    def get_field_name(self) -> str:
        return "custom_fields.publication:is_open_access"

    def get_filter_key(self) -> str:
        return "open_access"

    def get_aggregation_size(self) -> int:
        """Only 2 possible values: 'true' or 'false'."""
        return 2
