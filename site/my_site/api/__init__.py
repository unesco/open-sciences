"""API package for custom JSON endpoints."""

# Resource-Driven CMS API
from .cms import (
    CMSContentByIdAPIView,
    CMSContentBySlugAPIView,
    CMSContentByTypeAPIView,
    CMSContentPublishAPIView,
    CMSContentSearchAPIView,
    CMSContentUnpublishAPIView,
    CMSRenderAPIView,
    CMSResourceDefinitionAPIView,
    CMSResourcesAPIView,
    CMSSingletonUpsertAPIView,
)

# Other APIs
from .search import SearchAPIView
from .statistics import StatisticsAPIView

__all__ = [
    "SearchAPIView",
    "StatisticsAPIView",
    # CMS Content API
    "CMSResourcesAPIView",
    "CMSResourceDefinitionAPIView",
    "CMSContentSearchAPIView",
    "CMSContentByTypeAPIView",
    "CMSContentBySlugAPIView",
    "CMSContentByIdAPIView",
    "CMSContentPublishAPIView",
    "CMSContentUnpublishAPIView",
    "CMSRenderAPIView",
    "CMSSingletonUpsertAPIView",
]
