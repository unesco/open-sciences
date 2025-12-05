# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Marshmallow schemas for CMS data validation and serialization.

These schemas are used by the CMS services to validate input data
and serialize output data for API responses.
"""

from datetime import datetime
from typing import Optional

from invenio_i18n import lazy_gettext as _
from marshmallow import Schema, fields, post_load, pre_load, validate, validates
from marshmallow.exceptions import ValidationError


class CMSCategorySchema(Schema):
    """Schema for CMS Category serialization/deserialization."""

    id = fields.Integer(dump_only=True)
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
        metadata={"description": "Category name"},
    )
    slug = fields.String(
        required=True,
        validate=[
            validate.Length(min=1, max=255),
            validate.Regexp(
                r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
                error=_(
                    "Slug must contain only lowercase letters, numbers, and hyphens"
                ),
            ),
        ],
        metadata={"description": "URL-friendly identifier"},
    )
    description = fields.String(
        allow_none=True, metadata={"description": "Category description"}
    )
    sort_order = fields.Integer(
        load_default=0, metadata={"description": "Display order (lower = first)"}
    )
    is_active = fields.Boolean(
        load_default=True, metadata={"description": "Whether category is active"}
    )
    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)

    # Links for HATEOAS
    links = fields.Method("get_links", dump_only=True)

    def get_links(self, obj):
        """Generate HATEOAS links for category."""
        if hasattr(obj, "id") and obj.id:
            return {"self": f"/api/cms/categories/{obj.id}"}
        return {}


class CMSPageSchema(Schema):
    """Schema for CMS Page serialization/deserialization."""

    id = fields.Integer(dump_only=True)
    slug = fields.String(
        required=True,
        validate=[
            validate.Length(min=1, max=500),
            validate.Regexp(
                r"^[a-z0-9]+(?:[-/][a-z0-9]+)*$",
                error=_(
                    "Slug must contain only lowercase letters, numbers, hyphens, and forward slashes"
                ),
            ),
        ],
        metadata={"description": "URL-friendly identifier"},
    )
    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=500),
        metadata={"description": "Page title"},
    )
    content = fields.String(allow_none=True, metadata={"description": "HTML content"})
    excerpt = fields.String(
        allow_none=True,
        validate=validate.Length(max=1000),
        metadata={"description": "Short description/preview"},
    )

    # SEO fields
    meta_title = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
        metadata={"description": "SEO title"},
    )
    meta_description = fields.String(
        allow_none=True,
        validate=validate.Length(max=500),
        metadata={"description": "SEO description"},
    )

    # Template
    template_name = fields.String(
        load_default="my_site/cms/page.html",
        validate=validate.Length(max=255),
        metadata={"description": "Jinja2 template path"},
    )

    # Status
    is_published = fields.Boolean(
        load_default=False, metadata={"description": "Publication status"}
    )
    published_at = fields.DateTime(
        allow_none=True, metadata={"description": "Publication date"}
    )

    # Author
    author_id = fields.Integer(
        allow_none=True, metadata={"description": "Author user ID"}
    )
    author = fields.Method("get_author_info", dump_only=True)

    # Language
    lang = fields.String(
        load_default="en",
        validate=validate.Length(min=2, max=10),
        metadata={"description": "Language code (ISO 639-1)"},
    )

    # Ordering
    sort_order = fields.Integer(
        load_default=0, metadata={"description": "Display order"}
    )

    # Timestamps
    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)

    # Categories
    category_ids = fields.List(
        fields.Integer(),
        load_only=True,
        metadata={"description": "List of category IDs to assign"},
    )
    categories = fields.Nested(
        CMSCategorySchema,
        many=True,
        dump_only=True,
        metadata={"description": "Associated categories"},
    )

    # Links for HATEOAS
    links = fields.Method("get_links", dump_only=True)

    def get_author_info(self, obj):
        """Get author information."""
        if hasattr(obj, "author") and obj.author:
            return {
                "id": obj.author.id,
                "email": obj.author.email,
            }
        return None

    def get_links(self, obj):
        """Generate HATEOAS links for page."""
        if hasattr(obj, "id") and obj.id:
            return {
                "self": f"/api/cms/pages/{obj.id}",
                "html": f"/pages/{obj.slug}" if hasattr(obj, "slug") else None,
            }
        return {}

    @pre_load
    def strip_strings(self, data, **kwargs):
        """Strip whitespace from string fields."""
        if isinstance(data, dict):
            for key in ("title", "slug", "meta_title", "meta_description"):
                if key in data and isinstance(data[key], str):
                    data[key] = data[key].strip()
        return data


class CMSPageListSchema(Schema):
    """Schema for paginated list of CMS pages."""

    hits = fields.Nested(CMSPageSchema, many=True)
    total = fields.Integer()
    page = fields.Integer()
    size = fields.Integer()
    links = fields.Dict()


class CMSCategoryListSchema(Schema):
    """Schema for paginated list of CMS categories."""

    hits = fields.Nested(CMSCategorySchema, many=True)
    total = fields.Integer()
    page = fields.Integer()
    size = fields.Integer()
    links = fields.Dict()
