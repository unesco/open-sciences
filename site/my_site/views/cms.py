# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS page view for rendering published content."""

from flask import abort, render_template, request
from flask.views import MethodView
from flask_login import current_user

from ..services.cms import CMSPageService, CMSPageServiceConfig


class CMSPageView(MethodView):
    """View to render CMS pages."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSPageService(CMSPageServiceConfig())

    def _get_identity(self):
        """Get current user identity."""
        if current_user.is_authenticated:
            return current_user
        from flask_principal import AnonymousIdentity

        return AnonymousIdentity()

    def get(self, slug):
        """Render a CMS page by slug.

        Args:
            slug: Page URL slug
        """
        identity = self._get_identity()
        lang = request.args.get("lang", "en")

        try:
            page = self.service.read_by_slug(identity, slug, lang)

            # Check if page is published (non-admin users)
            if not page.is_published:
                # TODO: Check if user is admin
                abort(404)

            # Render using the page's template
            template = page.template_name or "my_site/cms/page.html"

            return render_template(
                template,
                page=page,
                meta_title=page.meta_title or page.title,
                meta_description=page.meta_description or page.excerpt,
            )
        except Exception as e:
            abort(404)
