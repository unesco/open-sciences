"""Filter backends package.

This package contains modular filter backends for the search API,
inspired by Django REST Framework and django-filter patterns.

Each filter backend implements the BaseFilterBackend interface and
provides filtering capabilities for specific fields (country, author, etc.).
"""

from typing import Optional
from .base import BaseFilterBackend
from .affiliation import AffiliationFilterBackend
from .affiliation_region import AffiliationRegionFilterBackend
from .author import AuthorFilterBackend
from .country import CountryFilterBackend
from .funding import FundingOrgFilterBackend
from .open_access import OpenAccessFilterBackend
from .resource_type import ResourceTypeFilterBackend
from .subject import SubjectFilterBackend
from .year import PublicationYearFilterBackend
from .keyword import KeywordFilterBackend
from .field_of_study import FieldOfStudyFilterBackend

# Registry of available filter backends
FILTER_BACKENDS_REGISTRY = {
    "affiliation": AffiliationFilterBackend,
    "affiliation_region": AffiliationRegionFilterBackend,
    "author": AuthorFilterBackend,
    "country": CountryFilterBackend,
    "field_of_study": FieldOfStudyFilterBackend,
    "funding": FundingOrgFilterBackend,
    "keyword": KeywordFilterBackend,
    "open_access": OpenAccessFilterBackend,
    "resource_type": ResourceTypeFilterBackend,
    "subject": SubjectFilterBackend,
    "year": PublicationYearFilterBackend,
}


def get_filter_backend(filter_key: str) -> Optional[BaseFilterBackend]:
    """
    Get a filter backend instance by key.

    Args:
        filter_key: The filter key (e.g., 'country', 'funding')

    Returns:
        Filter backend instance or None if not found
    """
    backend_class = FILTER_BACKENDS_REGISTRY.get(filter_key)
    if backend_class:
        return backend_class()
    return None


__all__ = [
    "BaseFilterBackend",
    "AffiliationFilterBackend",
    "AffiliationRegionFilterBackend",
    "AuthorFilterBackend",
    "CountryFilterBackend",
    "FundingOrgFilterBackend",
    "OpenAccessFilterBackend",
    "ResourceTypeFilterBackend",
    "SubjectFilterBackend",
    "PublicationYearFilterBackend",
    "FILTER_BACKENDS_REGISTRY",
    "get_filter_backend",
]
