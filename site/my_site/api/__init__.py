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
    CMSServeUploadedFileView,
    CMSSingletonUpsertAPIView,
    CMSUploadAPIView,
)

# Lens.org Proxy API
from .lens_proxy import LensExportProxyAPIView

# Other APIs
from .export import ExportAPIView
from .patch_regions import PatchRegionsAPIView
from .patch_resource_types import PatchResourceTypesAPIView
from .reindex import ReindexAPIView
from .search import SearchAPIView
from .statistics import StatisticsAPIView

__all__ = [
    "ExportAPIView",
    "LensExportProxyAPIView",
    "PatchRegionsAPIView",
    "PatchResourceTypesAPIView",
    "ReindexAPIView",
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
    "CMSServeUploadedFileView",
]
