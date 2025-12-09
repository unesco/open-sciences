# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS API endpoints.

This module provides REST API endpoints for CMS pages and categories.
Endpoints follow RESTful conventions:
- GET /api/cms/pages - List/search pages
- GET /api/cms/pages/<id> - Get single page
- POST /api/cms/pages - Create page (admin only)
- PUT /api/cms/pages/<id> - Update page (admin only)
- DELETE /api/cms/pages/<id> - Delete page (admin only)
- POST /api/cms/pages/<id>/publish - Publish page (admin only)
- POST /api/cms/pages/<id>/unpublish - Unpublish page (admin only)

Same pattern for categories at /api/cms/categories
"""

from flask import g, jsonify, request
from flask.views import MethodView
from invenio_db import db

from ..services.cms import (
    CMSCategoryService,
    CMSCategoryServiceConfig,
    CMSPageService,
    CMSPageServiceConfig,
)


class CMSPagesAPIView(MethodView):
    """API endpoint for CMS pages collection."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSPageService(CMSPageServiceConfig())

    def get(self):
        """List/search CMS pages.

        Query params:
            - q: Search query
            - page: Page number (default: 1)
            - size: Page size (default: 25)
            - sort: Sort field (default: created)
            - sort_direction: asc/desc (default: desc)
            - published_only: Filter published only (default: false)
            - lang: Language filter
            - category_id: Category filter
        """
        identity = g.identity

        params = {
            "q": request.args.get("q"),
            "page": int(request.args.get("page", 1)),
            "size": int(request.args.get("size", 25)),
            "sort": request.args.get("sort", "created"),
            "sort_direction": request.args.get("sort_direction", "desc"),
            "published_only": request.args.get("published_only", "false").lower()
            == "true",
            "lang": request.args.get("lang"),
            "category_id": request.args.get("category_id"),
        }

        try:
            result = self.service.search(identity, params)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def post(self):
        """Create a new CMS page (admin only)."""
        identity = g.identity
        data = request.get_json() or {}

        try:
            page = self.service.create(identity, data)
            db.session.commit()
            return jsonify(self.service.schema.dump(page)), 201
        except PermissionError as e:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400


class CMSPageAPIView(MethodView):
    """API endpoint for single CMS page."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSPageService(CMSPageServiceConfig())

    def get(self, id):
        """Get a single CMS page by ID."""
        identity = g.identity

        try:
            page = self.service.read(identity, int(id))
            return jsonify(self.service.schema.dump(page)), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 404

    def put(self, id):
        """Update a CMS page (admin only)."""
        identity = g.identity
        data = request.get_json() or {}

        try:
            page = self.service.update(identity, int(id), data)
            db.session.commit()
            return jsonify(self.service.schema.dump(page)), 200
        except PermissionError as e:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    def delete(self, id):
        """Delete a CMS page (admin only)."""
        identity = g.identity

        try:
            self.service.delete(identity, int(id))
            db.session.commit()
            return jsonify({"message": "Page deleted"}), 200
        except PermissionError as e:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400


class CMSPageBySlugAPIView(MethodView):
    """API endpoint to get CMS page by slug."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSPageService(CMSPageServiceConfig())

    def get(self, slug):
        """Get a CMS page by slug.

        Query params:
            - lang: Language code (default: en)
        """
        identity = g.identity
        lang = request.args.get("lang", "en")

        try:
            page = self.service.read_by_slug(identity, slug, lang)
            return jsonify(self.service.schema.dump(page)), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 404


class CMSPagePublishAPIView(MethodView):
    """API endpoint to publish/unpublish a CMS page."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSPageService(CMSPageServiceConfig())

    def post(self, id):
        """Publish a CMS page (admin only)."""
        identity = g.identity

        try:
            page = self.service.publish(identity, int(id))
            db.session.commit()
            return jsonify(self.service.schema.dump(page)), 200
        except PermissionError as e:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400


class CMSPageUnpublishAPIView(MethodView):
    """API endpoint to unpublish a CMS page."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSPageService(CMSPageServiceConfig())

    def post(self, id):
        """Unpublish a CMS page (admin only)."""
        identity = g.identity

        try:
            page = self.service.unpublish(identity, int(id))
            db.session.commit()
            return jsonify(self.service.schema.dump(page)), 200
        except PermissionError as e:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400


class CMSCategoriesAPIView(MethodView):
    """API endpoint for CMS categories collection."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSCategoryService(CMSCategoryServiceConfig())

    def get(self):
        """List/search CMS categories.

        Query params:
            - q: Search query
            - page: Page number (default: 1)
            - size: Page size (default: 25)
            - sort: Sort field (default: sort_order)
            - sort_direction: asc/desc (default: asc)
            - active_only: Filter active only (default: false)
        """
        identity = g.identity

        params = {
            "q": request.args.get("q"),
            "page": int(request.args.get("page", 1)),
            "size": int(request.args.get("size", 25)),
            "sort": request.args.get("sort", "sort_order"),
            "sort_direction": request.args.get("sort_direction", "asc"),
            "active_only": request.args.get("active_only", "false").lower() == "true",
        }

        try:
            result = self.service.search(identity, params)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def post(self):
        """Create a new CMS category (admin only)."""
        identity = g.identity
        data = request.get_json() or {}

        try:
            category = self.service.create(identity, data)
            db.session.commit()
            return jsonify(self.service.schema.dump(category)), 201
        except PermissionError as e:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400


class CMSCategoryAPIView(MethodView):
    """API endpoint for single CMS category."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSCategoryService(CMSCategoryServiceConfig())

    def get(self, id):
        """Get a single CMS category by ID."""
        identity = g.identity

        try:
            category = self.service.read(identity, int(id))
            return jsonify(self.service.schema.dump(category)), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 404

    def put(self, id):
        """Update a CMS category (admin only)."""
        identity = g.identity
        data = request.get_json() or {}

        try:
            category = self.service.update(identity, int(id), data)
            db.session.commit()
            return jsonify(self.service.schema.dump(category)), 200
        except PermissionError as e:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    def delete(self, id):
        """Delete a CMS category (admin only)."""
        identity = g.identity

        try:
            self.service.delete(identity, int(id))
            db.session.commit()
            return jsonify({"message": "Category deleted"}), 200
        except PermissionError as e:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400
