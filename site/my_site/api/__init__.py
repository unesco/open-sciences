"""API package for custom JSON endpoints."""

from .cms import (
    CMSCategoriesAPIView,
    CMSCategoryAPIView,
    CMSPageAPIView,
    CMSPageBySlugAPIView,
    CMSPagePublishAPIView,
    CMSPageUnpublishAPIView,
    CMSPagesAPIView,
)
from .search import SearchAPIView
from .statistics import StatisticsAPIView

__all__ = [
    "SearchAPIView",
    "StatisticsAPIView",
    "CMSPagesAPIView",
    "CMSPageAPIView",
    "CMSPageBySlugAPIView",
    "CMSPagePublishAPIView",
    "CMSPageUnpublishAPIView",
    "CMSCategoriesAPIView",
    "CMSCategoryAPIView",
]
