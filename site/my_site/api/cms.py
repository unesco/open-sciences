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
- GET /uploads/<path:filepath> - Serve uploaded files
"""

import os
from flask import g, jsonify, request, send_from_directory, current_app
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
        For collections: returns paginated list with filtering

        Query params:
            - lang: Language filter (default: en)
            - published_only: Filter published only
            - page: Page number (default: 1)
            - size: Items per page (default: 25)
            - q: Search query (searches in title, slug, content)
            - sort: Sort field (default: created)
            - sort_direction: Sort direction (default: desc)
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
                # Return paginated collection with filters
                page = int(request.args.get("page", 1))
                size = int(request.args.get("size", 25))
                q = request.args.get("q", "").strip() or None
                sort = request.args.get("sort", "created")
                sort_direction = request.args.get("sort_direction", "desc")

                result = self.service.list_by_type(
                    g.identity,
                    resource_type,
                    lang=lang,
                    published_only=published_only,
                    page=page,
                    size=size,
                    q=q,
                    sort=sort,
                    sort_direction=sort_direction,
                )
                return (
                    jsonify(
                        {
                            "resource_type": resource_type,
                            "is_singleton": False,
                            **result,
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
    PUBLIC_RESOURCES = {"footer", "header_frontpage"}

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
    """API endpoint for CMS file uploads (saves to MinIO S3)."""

    def post(self):
        """Upload a file to MinIO S3 bucket.

        Form data:
            - file: The file to upload
            - path: Target subdirectory within bucket (default: uploads/cms)

        Returns:
            JSON with the relative path to the uploaded file
        """
        import os
        import boto3
        from werkzeug.utils import secure_filename
        from flask import current_app
        from botocore.exceptions import ClientError

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

        # Get S3 configuration from Flask config
        s3_endpoint = current_app.config.get("S3_ENDPOINT_URL", "http://minio:9000")
        s3_access_key = current_app.config.get("S3_ACCESS_KEY_ID", "minioadmin")
        s3_secret_key = current_app.config.get("S3_SECRET_ACCESS_KEY", "minioadmin")
        s3_region = current_app.config.get("S3_REGION_NAME", "us-east-1")
        bucket_name = current_app.config.get("S3_BUCKET_NAME", "default")

        try:
            # Initialize S3 client
            s3_client = boto3.client(
                "s3",
                endpoint_url=s3_endpoint,
                aws_access_key_id=s3_access_key,
                aws_secret_access_key=s3_secret_key,
                region_name=s3_region,
            )

            # Build S3 object key with path prefix
            base, ext = os.path.splitext(filename)
            object_key = f"{target_path}/{filename}"

            # Check if file exists and add suffix if needed
            counter = 1
            while True:
                try:
                    s3_client.head_object(Bucket=bucket_name, Key=object_key)
                    # File exists, try next suffix
                    filename = f"{base}_{counter}{ext}"
                    object_key = f"{target_path}/{filename}"
                    counter += 1
                except ClientError as e:
                    if e.response["Error"]["Code"] == "404":
                        # File doesn't exist, we can use this key
                        break
                    else:
                        raise

            # Upload file to S3
            file.seek(0)  # Reset file pointer
            s3_client.upload_fileobj(
                file,
                bucket_name,
                object_key,
                ExtraArgs={
                    "ContentType": file.content_type or "application/octet-stream",
                    "ACL": "public-read",  # Make file publicly accessible
                },
            )

            # Return the relative path for storage in CMS
            relative_path = f"{target_path}/{filename}"

            return (
                jsonify(
                    {
                        "success": True,
                        "path": relative_path,
                        "filename": filename,
                        "storage": "s3",
                        "bucket": bucket_name,
                    }
                ),
                200,
            )

        except Exception as e:
            current_app.logger.error(f"S3 upload error: {str(e)}")
            return jsonify({"error": f"Upload failed: {str(e)}"}), 500


class CMSServeUploadedFileView(MethodView):
    """Serve uploaded files from MinIO S3 bucket."""

    def get(self, filepath):
        """Serve a file from MinIO S3 bucket.

        Args:
            filepath: Relative path to the file (e.g., 'cms/image.png')

        Returns:
            Redirect to S3 presigned URL or proxy the file content
        """
        import boto3
        from flask import redirect, Response
        from botocore.exceptions import ClientError

        # Get S3 configuration from Flask config
        s3_endpoint = current_app.config.get("S3_ENDPOINT_URL", "http://minio:9000")
        s3_access_key = current_app.config.get("S3_ACCESS_KEY_ID", "minioadmin")
        s3_secret_key = current_app.config.get("S3_SECRET_ACCESS_KEY", "minioadmin")
        s3_region = current_app.config.get("S3_REGION_NAME", "us-east-1")
        bucket_name = current_app.config.get("S3_BUCKET_NAME", "default")

        # Build S3 object key
        object_key = f"uploads/{filepath}"

        try:
            # Initialize S3 client
            s3_client = boto3.client(
                "s3",
                endpoint_url=s3_endpoint,
                aws_access_key_id=s3_access_key,
                aws_secret_access_key=s3_secret_key,
                region_name=s3_region,
            )

            # Get file from S3
            try:
                response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    return jsonify({"error": "File not found"}), 404
                raise

            # Stream the file content
            file_content = response["Body"].read()
            content_type = response.get("ContentType", "application/octet-stream")

            return Response(
                file_content,
                mimetype=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{os.path.basename(filepath)}"',
                    "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
                },
            )

        except Exception as e:
            current_app.logger.error(f"S3 file serve error: {str(e)}")
            return jsonify({"error": "Failed to retrieve file"}), 500
