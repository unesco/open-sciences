# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS Service module."""

from .config import CMSContentServiceConfig
from .content_service import CMSContentService
from .permissions import CMSPermissionPolicy
from .resources import (
    CMS_LANGUAGES,
    CMS_RESOURCES,
    get_resource,
    get_resource_list,
    validate_resource_data,
)

__all__ = (
    # Service
    "CMSContentService",
    "CMSContentServiceConfig",
    "CMSPermissionPolicy",
    # Resources
    "CMS_LANGUAGES",
    "CMS_RESOURCES",
    "get_resource",
    "get_resource_list",
    "validate_resource_data",
)
