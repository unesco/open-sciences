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
from .reindex import ReindexAPIView
from .search import SearchAPIView
from .statistics import StatisticsAPIView
from .update_fields import UpdateFieldsAPIView

__all__ = [
    "ExportAPIView",
    "LensExportProxyAPIView",
    "PatchRegionsAPIView",
    "ReindexAPIView",
    "SearchAPIView",
    "StatisticsAPIView",
    "UpdateFieldsAPIView",
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
