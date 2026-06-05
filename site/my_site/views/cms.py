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


class CmsReactPageView(MethodView):
    """Render the React mount point for CMS pages.

    The page to show is selected client-side from the URL hash slug
    (e.g. /page#about), which the React app fetches from
    /cms/api/pages/<slug> as { title, body }.
    """

    def __init__(self):
        """Store the template name."""
        self.template = "my_site/page/index.html"

    def get(self):
        """Render the React mount template."""
        return render_template(self.template)


class CMSPageView(MethodView):
    """View to render CMS content pages."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def get(self, slug):
        """Render a CMS page by slug.

        For static_page resources, the URL format is:
        - /pages/about -> renders static_page with slug "about"

        Args:
            slug: Page URL slug
        """
        identity = g.identity
        lang = request.args.get("lang", "en")

        try:
            # For now, we only support static_page resource type
            resource_type = "static_page"
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
                resource_def.get("template", "my_site/cms/static_page.html")
                if resource_def
                else "my_site/cms/static_page.html"
            )

            # Get data from content
            data = content.data or {}
            page_title = data.get("title", content_slug.replace("-", " ").title())
            page_content = data.get("content", "")
            meta_title = data.get("meta_title") or page_title
            meta_description = data.get("meta_description", "")

            return render_template(
                template,
                content=content,
                resource_type=resource_type,
                page_title=page_title,
                page_content=page_content,
                meta_title=meta_title,
                meta_description=meta_description,
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            abort(404)
