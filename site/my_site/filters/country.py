"""Country filter backend."""

from .base import BaseFilterBackend


class CountryFilterBackend(BaseFilterBackend):
    """Filter backend for publication countries."""

    def get_field_name(self) -> str:
        return "custom_fields.publication:country"

    def get_filter_key(self) -> str:
        return "country"
