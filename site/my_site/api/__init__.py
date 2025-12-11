"""API package for custom JSON endpoints."""

# Resource-Driven CMS API
from .cms import (
    CMSContentByIdAPIView,
    CMSContentBySlugAPIView,
    CMSContentByTypeAPIView,
    CMSContentPublishAPIView,
    CMSContentSearchAPIView,
    CMSContentUnpublishAPIView,
    CMSPublicRenderAPIView,
    CMSRenderAPIView,
    CMSResourceDefinitionAPIView,
    CMSResourcesAPIView,
    CMSSingletonUpsertAPIView,
    CMSUploadAPIView,
)

# Other APIs
from .export import ExportAPIView
from .search import SearchAPIView
from .statistics import StatisticsAPIView

__all__ = [
    "ExportAPIView",
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
    "CMSPublicRenderAPIView",
    "CMSSingletonUpsertAPIView",
    "CMSUploadAPIView",
]
