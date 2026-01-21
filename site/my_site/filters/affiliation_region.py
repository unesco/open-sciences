"""Affiliation Region filter backend."""

from .base import BaseFilterBackend


class AffiliationRegionFilterBackend(BaseFilterBackend):
    """Filter backend for author affiliation regions."""

    def get_field_name(self) -> str:
        return "custom_fields.publication:affiliation_region"

    def get_filter_key(self) -> str:
        return "affiliation_region"
