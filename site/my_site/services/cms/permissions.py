# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Permission policies for CMS services.

This module defines the permission policies that control access to
CMS resources (pages and categories). It integrates with InvenioRDM's
permission system.
"""

from invenio_administration.generators import Administration
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    SystemProcess,
)


class CMSPermissionPolicy(RecordPermissionPolicy):
    """Permission policy for CMS resources.

    Permissions:
        - search/read: Any user (public pages) or authenticated (unpublished)
        - create/update/delete: Administration users only
    """

    # Anyone can search and read published pages
    can_search = [AnyUser(), SystemProcess()]
    can_read = [AnyUser(), SystemProcess()]

    # Only admins can create, update, delete
    can_create = [Administration(), SystemProcess()]
    can_update = [Administration(), SystemProcess()]
    can_delete = [Administration(), SystemProcess()]

    # Admin-only actions
    can_manage = [Administration(), SystemProcess()]
    can_publish = [Administration(), SystemProcess()]
    can_unpublish = [Administration(), SystemProcess()]
