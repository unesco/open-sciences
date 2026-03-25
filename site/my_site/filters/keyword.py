"""Keyword filter backend."""

from .base import BaseFilterBackend


class KeywordFilterBackend(BaseFilterBackend):
    """Filter backend for publication keywords."""

    def get_field_name(self) -> str:
        return "custom_fields.publication:keyword"

    def get_filter_key(self) -> str:
        return "keyword"
