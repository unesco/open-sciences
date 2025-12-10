# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS Content API endpoints.

Resource-driven CMS API:
- GET /data/cms/resources - List all resource types
- GET /data/cms/resources/<type> - Get resource definition with schema
- GET /data/cms/content - Search all content
- GET /data/cms/content/<type> - List content by type
- GET /data/cms/content/<type>/<slug> - Get content by slug (collections)
- GET /data/cms/content/id/<id> - Get content by ID
- POST /data/cms/content/<type> - Create new content
- PUT /data/cms/content/id/<id> - Update content
- DELETE /data/cms/content/id/<id> - Delete content
- POST /data/cms/content/id/<id>/publish - Publish content
- POST /data/cms/content/id/<id>/unpublish - Unpublish content
- GET /data/cms/render/<type>[/<slug>] - Get rendered output
"""

from flask import g, jsonify, request
from flask.views import MethodView
from invenio_db import db

from ..services.cms import CMSContentService, CMSContentServiceConfig


class CMSResourcesAPIView(MethodView):
    """API endpoint for CMS resource definitions."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def get(self):
        """List all available resource types with schemas.

        Returns:
            JSON with resources list and available languages
        """
        try:
            result = self.service.get_resources(g.identity)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


class CMSResourceDefinitionAPIView(MethodView):
    """API endpoint for single resource definition."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def get(self, resource_type):
        """Get resource definition with full schema.

        Args:
            resource_type: Resource type identifier

        Returns:
            JSON with resource definition
        """
        try:
            result = self.service.get_resource_definition(g.identity, resource_type)
            return jsonify(result), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500


class CMSContentSearchAPIView(MethodView):
    """API endpoint for searching all CMS content."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def get(self):
        """Search CMS content with filters.

        Query params:
            - resource_type: Filter by type
            - lang: Language filter
            - q: Search query
            - page: Page number (default: 1)
            - size: Page size (default: 25)
            - published_only: Filter published only
        """
        params = {
            "resource_type": request.args.get("resource_type"),
            "lang": request.args.get("lang"),
            "q": request.args.get("q"),
            "page": int(request.args.get("page", 1)),
            "size": int(request.args.get("size", 25)),
            "sort": request.args.get("sort", "created"),
            "sort_direction": request.args.get("sort_direction", "desc"),
            "published_only": request.args.get("published_only", "false").lower()
            == "true",
        }

        try:
            result = self.service.search(g.identity, params)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


class CMSContentByTypeAPIView(MethodView):
    """API endpoint for content by resource type."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def get(self, resource_type):
        """List content of a specific type.

        For singletons: returns the single item (or null)
        For collections: returns list of items

        Query params:
            - lang: Language filter (default: en)
            - published_only: Filter published only
        """
        from ..services.cms import get_resource

        lang = request.args.get("lang", "en")
        published_only = request.args.get("published_only", "false").lower() == "true"

        try:
            resource = get_resource(resource_type)

            if resource["is_singleton"]:
                # Return singleton
                result = self.service.read_singleton(g.identity, resource_type, lang)
                return (
                    jsonify(
                        {
                            "resource_type": resource_type,
                            "is_singleton": True,
                            "content": result,
                        }
                    ),
                    200,
                )
            else:
                # Return collection
                contents = self.service.list_by_type(
                    g.identity, resource_type, lang, published_only
                )
                return (
                    jsonify(
                        {
                            "resource_type": resource_type,
                            "is_singleton": False,
                            "hits": contents,
                            "total": len(contents),
                        }
                    ),
                    200,
                )

        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def post(self, resource_type):
        """Create new content of a specific type.

        Body:
            - data: Content data (validated against schema)
            - lang: Language (default: en)
            - slug: URL slug (required for collections)
            - is_published: Publish immediately (default: false)
        """
        data = request.get_json() or {}

        try:
            result = self.service.create(g.identity, resource_type, data)
            db.session.commit()
            return jsonify(result), 201
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500


class CMSContentBySlugAPIView(MethodView):
    """API endpoint for content by slug."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def get(self, resource_type, slug):
        """Get content by type and slug.

        Query params:
            - lang: Language (default: en)
        """
        lang = request.args.get("lang", "en")

        try:
            result = self.service.read_by_slug(g.identity, resource_type, slug, lang)
            return jsonify(result), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500


class CMSContentByIdAPIView(MethodView):
    """API endpoint for content by ID."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def get(self, resource_type, content_id):
        """Get content by ID."""
        try:
            result = self.service.read(g.identity, int(content_id))
            return jsonify(result), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def put(self, resource_type, content_id):
        """Update content by ID.

        Body:
            - data: Updated content data
            - lang: Language
            - slug: URL slug
            - is_published: Publication status
        """
        data = request.get_json() or {}

        try:
            result = self.service.update(g.identity, int(content_id), data)
            db.session.commit()
            return jsonify(result), 200
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    def delete(self, resource_type, content_id):
        """Delete content by ID."""
        try:
            self.service.delete(g.identity, int(content_id))
            db.session.commit()
            return jsonify({"message": "Content deleted"}), 200
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 404
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500


class CMSContentPublishAPIView(MethodView):
    """API endpoint to publish content."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def post(self, resource_type, content_id):
        """Publish content by ID."""
        try:
            result = self.service.publish(g.identity, int(content_id))
            db.session.commit()
            return jsonify(result), 200
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 404
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500


class CMSContentUnpublishAPIView(MethodView):
    """API endpoint to unpublish content."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def post(self, resource_type, content_id):
        """Unpublish content by ID."""
        try:
            result = self.service.unpublish(g.identity, int(content_id))
            db.session.commit()
            return jsonify(result), 200
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 404
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500


class CMSRenderAPIView(MethodView):
    """API endpoint for rendered content output."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def get(self, resource_type, slug=None):
        """Get rendered output for content.

        For JSON resources: returns data directly
        For HTML resources: returns rendered HTML

        Query params:
            - lang: Language (default: en)
        """
        lang = request.args.get("lang", "en")

        try:
            result = self.service.render(g.identity, resource_type, slug, lang)
            return jsonify(result), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500


class CMSPublicRenderAPIView(MethodView):
    """Public API endpoint for rendering public CMS content (no auth required).

    This endpoint is used by templates to fetch content like footer, header, etc.
    It returns data with fallback to fixtures if no content exists in DB.
    """

    # Resource types allowed for public access
    PUBLIC_RESOURCES = {"footer", "header", "homepage_hero"}

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def get(self, resource_type):
        """Get public content for a resource type.

        This endpoint:
        1. Checks if resource_type is allowed for public access
        2. Tries to fetch published content from DB
        3. Falls back to fixtures if no content exists
        4. Returns data ready for template rendering

        Query params:
            - lang: Language (default: en)

        Returns:
            JSON with content data
        """
        # Check if resource type is allowed for public access
        if resource_type not in self.PUBLIC_RESOURCES:
            return jsonify({"error": "Resource not available for public access"}), 403

        lang = request.args.get("lang", "en")

        try:
            # Try to get published content from DB
            from ..models import CMSContent
            from ..fixtures import get_fixture

            content = CMSContent.query.filter_by(
                resource_type=resource_type,
                slug=resource_type,  # Singletons have slug = resource_type
                lang=lang,
                is_published=True,
            ).first()

            if content:
                # Return DB content
                return (
                    jsonify(
                        {
                            "resource_type": resource_type,
                            "lang": lang,
                            "data": content.data,
                            "source": "database",
                        }
                    ),
                    200,
                )
            else:
                # Fall back to fixtures
                fixture_data = get_fixture(resource_type, lang)
                if fixture_data:
                    return (
                        jsonify(
                            {
                                "resource_type": resource_type,
                                "lang": lang,
                                "data": fixture_data,
                                "source": "fixture",
                            }
                        ),
                        200,
                    )
                else:
                    return (
                        jsonify(
                            {
                                "resource_type": resource_type,
                                "lang": lang,
                                "data": {},
                                "source": "empty",
                            }
                        ),
                        200,
                    )

        except Exception as e:
            return jsonify({"error": str(e)}), 500


class CMSSingletonUpsertAPIView(MethodView):
    """API endpoint for singleton upsert (create or update)."""

    def __init__(self):
        """Initialize the service."""
        self.service = CMSContentService(CMSContentServiceConfig())

    def put(self, resource_type):
        """Create or update singleton content.

        Convenience endpoint for singletons - creates if not exists, updates if exists.

        Body:
            - data: Content data
            - lang: Language (default: en)
        """
        data = request.get_json() or {}

        try:
            result = self.service.upsert_singleton(g.identity, resource_type, data)
            db.session.commit()
            return jsonify(result), 200
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400
        except PermissionError:
            return jsonify({"error": "Permission denied"}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500


class CMSUploadAPIView(MethodView):
    """API endpoint for CMS file uploads."""

    def post(self):
        """Upload a file to the CMS static directory.

        Form data:
            - file: The file to upload
            - path: Target subdirectory within static (default: uploads/cms)

        Returns:
            JSON with the relative path to the uploaded file
        """
        import os
        from werkzeug.utils import secure_filename
        from flask import current_app

        # Check for file in request
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Get target path (default: uploads/cms)
        target_path = request.form.get("path", "uploads/cms")

        # Secure the filename
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({"error": "Invalid filename"}), 400

        # Build the full path
        # Static folder is typically at instance/static or static/
        static_folder = current_app.static_folder
        if not static_folder:
            # Fallback to instance static folder
            static_folder = os.path.join(current_app.instance_path, "static")

        upload_dir = os.path.join(static_folder, target_path)

        # Create directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)

        # Save the file
        file_path = os.path.join(upload_dir, filename)

        # If file exists, add a suffix
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{base}_{counter}{ext}"
            file_path = os.path.join(upload_dir, filename)
            counter += 1

        file.save(file_path)

        # Return the relative path for storage in CMS
        relative_path = f"{target_path}/{filename}"

        return (
            jsonify(
                {
                    "success": True,
                    "path": relative_path,
                    "filename": filename,
                }
            ),
            200,
        )
