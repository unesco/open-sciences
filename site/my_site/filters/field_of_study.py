"""Field of Study filter backend."""

from .base import BaseFilterBackend


class FieldOfStudyFilterBackend(BaseFilterBackend):
    """Filter backend for fields of study."""

    def get_field_name(self) -> str:
        return "custom_fields.publication:field_of_study"

    def get_filter_key(self) -> str:
        return "field_of_study"
