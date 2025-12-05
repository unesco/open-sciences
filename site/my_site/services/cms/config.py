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

from ...models.cms import CMSCategory, CMSPage
from .permissions import CMSPermissionPolicy
from .schemas import CMSCategorySchema, CMSPageSchema


class CMSPageLink(Link):
    """Link variables setter for CMS Page links."""

    @staticmethod
    def vars(page, vars):
        """Set variables for the URI template."""
        vars.update({"id": page.id})


class CMSCategoryLink(Link):
    """Link variables setter for CMS Category links."""

    @staticmethod
    def vars(category, vars):
        """Set variables for the URI template."""
        vars.update({"id": category.id})


class SearchOptions:
    """Base search options for CMS resources."""

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

    pagination_options = {
        "default_results_per_page": 25,
    }


class CMSPageSearchOptions(SearchOptions):
    """Search options for CMS pages."""

    sort_default = "created"
    sort_options = {
        "id": dict(
            title=_("Id"),
            fields=["id"],
        ),
        "title": dict(
            title=_("Title"),
            fields=["title"],
        ),
        "slug": dict(
            title=_("Slug"),
            fields=["slug"],
        ),
        "created": dict(
            title=_("Created"),
            fields=["created"],
        ),
        "updated": dict(
            title=_("Updated"),
            fields=["updated"],
        ),
        "published_at": dict(
            title=_("Published"),
            fields=["published_at"],
        ),
        "sort_order": dict(
            title=_("Sort Order"),
            fields=["sort_order"],
        ),
    }


class CMSCategorySearchOptions(SearchOptions):
    """Search options for CMS categories."""

    sort_default = "sort_order"
    sort_direction_default = "asc"

    sort_options = {
        "id": dict(
            title=_("Id"),
            fields=["id"],
        ),
        "name": dict(
            title=_("Name"),
            fields=["name"],
        ),
        "slug": dict(
            title=_("Slug"),
            fields=["slug"],
        ),
        "sort_order": dict(
            title=_("Sort Order"),
            fields=["sort_order"],
        ),
        "created": dict(
            title=_("Created"),
            fields=["created"],
        ),
    }


class CMSPageServiceConfig(ServiceConfig):
    """Configuration for CMS Page Service."""

    # Permission policy
    permission_policy_cls = CMSPermissionPolicy

    # Schema for serialization/deserialization
    schema = CMSPageSchema

    # Search options
    search = CMSPageSearchOptions

    # Model class
    record_cls = CMSPage

    # Links
    links_item = {
        "self": CMSPageLink("{+api}/cms/pages/{id}"),
    }
    links_search = pagination_links("{+api}/cms/pages{?args*}")


class CMSCategoryServiceConfig(ServiceConfig):
    """Configuration for CMS Category Service."""

    # Permission policy
    permission_policy_cls = CMSPermissionPolicy

    # Schema for serialization/deserialization
    schema = CMSCategorySchema

    # Search options
    search = CMSCategorySearchOptions

    # Model class
    record_cls = CMSCategory

    # Links
    links_item = {
        "self": CMSCategoryLink("{+api}/cms/categories/{id}"),
    }
    links_search = pagination_links("{+api}/cms/categories{?args*}")
