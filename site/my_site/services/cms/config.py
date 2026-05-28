# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Service configuration for CMS.

This module defines the configuration classes for CMS services,
following the InvenioRDM service configuration pattern.
"""

from invenio_i18n import gettext as _
from invenio_records_resources.services import Link, ServiceConfig
from invenio_records_resources.services.records.links import pagination_links
from sqlalchemy import asc, desc

from ...models.cms import CMSContent
from .permissions import CMSPermissionPolicy


class CMSContentLink(Link):
    """Link variables setter for CMS Content links."""

    @staticmethod
    def vars(content, vars):
        """Set variables for the URI template."""
        vars.update({"id": content.id})


class CMSContentSearchOptions:
    """Search options for CMS content."""

    sort_default = "created"
    sort_direction_default = "desc"
    sort_direction_options = {
        "asc": dict(
            title=_("Ascending"),
            fn=asc,
        ),
        "desc": dict(
            title=_("Descending"),
            fn=desc,
        ),
    }

    sort_options = {
        "id": dict(
            title=_("Id"),
            fields=["id"],
        ),
        "created": dict(
            title=_("Created"),
            fields=["created"],
        ),
        "updated": dict(
            title=_("Updated"),
            fields=["updated"],
        ),
        "sort_order": dict(
            title=_("Sort Order"),
            fields=["sort_order"],
        ),
    }

    pagination_options = {
        "default_results_per_page": 25,
    }


class CMSContentServiceConfig(ServiceConfig):
    """Configuration for CMS Content Service."""

    # Permission policy
    permission_policy_cls = CMSPermissionPolicy

    # Service components (not used in this service)
    components = []

    # Search options
    search = CMSContentSearchOptions

    # Model class
    record_cls = CMSContent

    # Links
    links_item = {
        "self": CMSContentLink("{+api}/cms/content/{id}"),
    }
    links_search = pagination_links("{+api}/cms/content{?args*}")
