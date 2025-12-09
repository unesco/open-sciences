# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS page view for rendering published content."""

from flask import abort, g, render_template, request
from flask.views import MethodView

from ..services.cms import CMSContentService, CMSContentServiceConfig


class CMSPageView(MethodView):
    """View to render CMS content pages."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def get(self, slug):
        """Render a CMS page by slug.

        This view supports rendering content from any resource type
        that has output_format="html". The slug format is:
        - For collections: resource_type/content_slug (e.g., "privacy_policy/en")
        - For singletons: resource_type (e.g., "footer")

        Args:
            slug: Page URL slug (can include resource_type prefix)
        """
        identity = g.identity
        lang = request.args.get("lang", "en")

        try:
            # Try to parse slug as resource_type/content_slug
            parts = slug.split("/", 1)
            if len(parts) == 2:
                resource_type, content_slug = parts
            else:
                # Assume the whole slug is the resource_type (singleton)
                resource_type = slug
                content_slug = slug

            # Get content by slug
            content = self.service.read_by_slug(
                identity, resource_type, content_slug, lang
            )

            if not content:
                abort(404)

            # Check if content is published (non-admin users)
            if not content.is_published:
                # TODO: Check if user is admin
                abort(404)

            # Get resource definition for template
            from ..services.cms import get_resource

            resource_def = get_resource(resource_type)

            # Determine template
            template = (
                resource_def.get("template", "my_site/cms/page.html")
                if resource_def
                else "my_site/cms/page.html"
            )

            # Get title and description from content data
            data = content.data or {}
            title = data.get("title") or data.get("heading") or content.slug
            description = data.get("description") or data.get("excerpt") or ""

            return render_template(
                template,
                content=content,
                resource_type=resource_type,
                meta_title=title,
                meta_description=description,
            )
        except Exception as e:
            abort(404)
