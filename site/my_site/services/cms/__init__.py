# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS Service module."""

from .config import CMSPageServiceConfig, CMSCategoryServiceConfig
from .permissions import CMSPermissionPolicy
from .schemas import CMSPageSchema, CMSCategorySchema
from .service import CMSPageService, CMSCategoryService

__all__ = (
    "CMSPageService",
    "CMSCategoryService",
    "CMSPageServiceConfig",
    "CMSCategoryServiceConfig",
    "CMSPermissionPolicy",
    "CMSPageSchema",
    "CMSCategorySchema",
)
