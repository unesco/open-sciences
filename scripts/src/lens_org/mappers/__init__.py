"""
Field mappers for transforming Lens.org data to InvenioRDM format.

This package provides specialized mappers for different types of metadata:
- StandardFieldsMapper: Core bibliographic metadata
- CustomFieldsMapper: Lens.org-specific custom fields
- RelatedIdentifiersMapper: External identifiers and references
"""

from .standard import StandardFieldsMapper
from .custom import CustomFieldsMapper
from .related import RelatedIdentifiersMapper

__all__ = [
    "StandardFieldsMapper",
    "CustomFieldsMapper",
    "RelatedIdentifiersMapper",
]
