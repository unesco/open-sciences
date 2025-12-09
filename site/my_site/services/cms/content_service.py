# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS Content Service.

This module provides the service layer for the resource-driven CMS.
It handles:
- Resource registry access
- Content CRUD operations
- JSON Schema validation
- Singleton vs collection logic
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import current_app
from invenio_db import db
from invenio_records_resources.services.base import Service
from invenio_records_resources.services.uow import unit_of_work

from ...models.cms import CMSContent
from .resources import (
    CMS_LANGUAGES,
    get_resource,
    get_resource_list,
    validate_resource_data,
)


class CMSContentService(Service):
    """Service for CMS Content operations."""

    # ==========================================
    # Resource Registry Access
    # ==========================================

    def get_resources(self, identity) -> Dict:
        """Get all available resource types.

        Args:
            identity: User identity

        Returns:
            Dictionary with resources list and languages
        """
        self.require_permission(identity, "search")

        return {
            "resources": get_resource_list(),
            "languages": CMS_LANGUAGES,
        }

    def get_resource_definition(self, identity, resource_type: str) -> Dict:
        """Get single resource definition with schema.

        Args:
            identity: User identity
            resource_type: Resource type identifier

        Returns:
            Resource definition
        """
        self.require_permission(identity, "search")

        resource = get_resource(resource_type)
        return {
            "type": resource_type,
            **resource,
        }

    # ==========================================
    # Content CRUD Operations
    # ==========================================

    def search(self, identity, params: Dict = None) -> Dict:
        """Search CMS content.

        Args:
            identity: User identity
            params: Search parameters

        Returns:
            Dictionary with hits, total, pagination info
        """
        self.require_permission(identity, "search")

        params = params or {}

        # Execute search
        pagination = CMSContent.search(params)

        return {
            "hits": [self._serialize_content(c) for c in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "size": pagination.per_page,
            "pages": pagination.pages,
        }

    def read(self, identity, id: int) -> Dict:
        """Read content by ID.

        Args:
            identity: User identity
            id: Content ID

        Returns:
            Serialized content
        """
        self.require_permission(identity, "read")

        content = CMSContent.get(id)
        if not content:
            raise ValueError(f"Content with id {id} not found")

        return self._serialize_content(content)

    def read_singleton(
        self, identity, resource_type: str, lang: str = "en"
    ) -> Optional[Dict]:
        """Read singleton content.

        Args:
            identity: User identity
            resource_type: Resource type
            lang: Language code

        Returns:
            Serialized content or None
        """
        self.require_permission(identity, "read")

        # Verify it's a singleton
        resource = get_resource(resource_type)
        if not resource["is_singleton"]:
            raise ValueError(f"Resource '{resource_type}' is not a singleton")

        content = CMSContent.get_singleton(resource_type, lang)
        if content:
            return self._serialize_content(content)
        return None

    def read_by_slug(
        self, identity, resource_type: str, slug: str, lang: str = "en"
    ) -> Optional[CMSContent]:
        """Read content by slug.

        Args:
            identity: User identity
            resource_type: Resource type
            slug: Content slug
            lang: Language code

        Returns:
            CMSContent object or None
        """
        self.require_permission(identity, "read")

        content = CMSContent.get_by_slug(resource_type, slug, lang)
        return content

    def list_by_type(
        self,
        identity,
        resource_type: str,
        lang: str = None,
        published_only: bool = False,
    ) -> List[Dict]:
        """List all content of a specific type.

        Args:
            identity: User identity
            resource_type: Resource type
            lang: Optional language filter
            published_only: Filter published only

        Returns:
            List of serialized content
        """
        self.require_permission(identity, "search")

        contents = CMSContent.get_by_type(resource_type, lang, published_only)
        return [self._serialize_content(c) for c in contents]

    @unit_of_work()
    def create(
        self, identity, resource_type: str, data: Dict[str, Any], uow=None
    ) -> Dict:
        """Create new CMS content.

        Args:
            identity: User identity
            resource_type: Resource type
            data: Content data
            uow: Unit of work

        Returns:
            Serialized created content
        """
        self.require_permission(identity, "create")

        # Get resource definition
        resource = get_resource(resource_type)

        # Validate data against schema
        content_data = data.get("data", {})
        is_valid, errors = validate_resource_data(resource_type, content_data)
        if not is_valid:
            raise ValueError(f"Validation errors: {errors}")

        lang = data.get("lang", "en")

        # For singletons, check if one already exists
        if resource["is_singleton"]:
            existing = CMSContent.get_singleton(resource_type, lang)
            if existing:
                raise ValueError(
                    f"Singleton '{resource_type}' already exists for language '{lang}'"
                )

        # For collections, ensure slug is provided and unique
        slug = data.get("slug") or content_data.get("slug")
        if not resource["is_singleton"]:
            if not slug:
                raise ValueError("Slug is required for collection resources")

            existing = CMSContent.get_by_slug(resource_type, slug, lang)
            if existing:
                raise ValueError(
                    f"Content with slug '{slug}' already exists for type '{resource_type}' and language '{lang}'"
                )

        # Create content
        content = CMSContent.create(
            {
                "resource_type": resource_type,
                "slug": slug,
                "data": content_data,
                "lang": lang,
                "is_published": data.get("is_published", False),
                "author_id": getattr(identity, "id", None),
                "sort_order": data.get("sort_order", 0),
            }
        )

        db.session.flush()
        return self._serialize_content(content)

    @unit_of_work()
    def update(self, identity, id: int, data: Dict[str, Any], uow=None) -> Dict:
        """Update existing CMS content.

        Args:
            identity: User identity
            id: Content ID
            data: Updated data
            uow: Unit of work

        Returns:
            Serialized updated content
        """
        self.require_permission(identity, "update")

        content = CMSContent.get(id)
        if not content:
            raise ValueError(f"Content with id {id} not found")

        # Validate data against schema if data field is being updated
        if "data" in data:
            is_valid, errors = validate_resource_data(
                content.resource_type, data["data"]
            )
            if not is_valid:
                raise ValueError(f"Validation errors: {errors}")

        # Update content
        content.update(data)

        return self._serialize_content(content)

    @unit_of_work()
    def upsert_singleton(
        self, identity, resource_type: str, data: Dict[str, Any], uow=None
    ) -> Dict:
        """Create or update singleton content.

        Convenience method for singletons - creates if not exists, updates if exists.

        Args:
            identity: User identity
            resource_type: Resource type
            data: Content data
            uow: Unit of work

        Returns:
            Serialized content
        """
        # Verify it's a singleton
        resource = get_resource(resource_type)
        if not resource["is_singleton"]:
            raise ValueError(f"Resource '{resource_type}' is not a singleton")

        lang = data.get("lang", "en")
        existing = CMSContent.get_singleton(resource_type, lang)

        if existing:
            return self.update(identity, existing.id, data, uow=uow)
        else:
            return self.create(identity, resource_type, data, uow=uow)

    @unit_of_work()
    def delete(self, identity, id: int, uow=None) -> bool:
        """Delete CMS content.

        Args:
            identity: User identity
            id: Content ID
            uow: Unit of work

        Returns:
            True if deleted
        """
        self.require_permission(identity, "delete")

        content = CMSContent.get(id)
        if not content:
            raise ValueError(f"Content with id {id} not found")

        db.session.delete(content)
        return True

    @unit_of_work()
    def publish(self, identity, id: int, uow=None) -> Dict:
        """Publish content.

        Args:
            identity: User identity
            id: Content ID
            uow: Unit of work

        Returns:
            Serialized content
        """
        self.require_permission(identity, "publish")

        content = CMSContent.get(id)
        if not content:
            raise ValueError(f"Content with id {id} not found")

        content.publish()
        return self._serialize_content(content)

    @unit_of_work()
    def unpublish(self, identity, id: int, uow=None) -> Dict:
        """Unpublish content.

        Args:
            identity: User identity
            id: Content ID
            uow: Unit of work

        Returns:
            Serialized content
        """
        self.require_permission(identity, "unpublish")

        content = CMSContent.get(id)
        if not content:
            raise ValueError(f"Content with id {id} not found")

        content.unpublish()
        return self._serialize_content(content)

    # ==========================================
    # Output Rendering
    # ==========================================

    def render(
        self, identity, resource_type: str, slug: str = None, lang: str = "en"
    ) -> Dict:
        """Get rendered output for content.

        For JSON output_format: returns data directly
        For HTML output_format: returns rendered HTML

        Args:
            identity: User identity
            resource_type: Resource type
            slug: Content slug (for collections)
            lang: Language code

        Returns:
            Dictionary with output_format and content
        """
        self.require_permission(identity, "read")

        resource = get_resource(resource_type)

        # Get content
        if resource["is_singleton"]:
            content = CMSContent.get_singleton(resource_type, lang)
        else:
            if not slug:
                raise ValueError("Slug required for collection resources")
            content = CMSContent.get_by_slug(resource_type, slug, lang)

        if not content:
            raise ValueError(f"Content not found")

        # Check published status for public access
        if not content.is_published:
            # Could add admin check here
            pass

        output_format = resource["output_format"]

        if output_format == "json":
            return {
                "format": "json",
                "data": content.data,
            }
        else:
            # HTML rendering using template
            from flask import render_template_string, render_template

            template = resource.get("template")
            if template:
                try:
                    html = render_template(
                        template,
                        content=content,
                        data=content.data,
                        lang=lang,
                    )
                    return {
                        "format": "html",
                        "html": html,
                        "data": content.data,
                    }
                except Exception as e:
                    current_app.logger.error(f"Template rendering error: {e}")
                    return {
                        "format": "html",
                        "html": None,
                        "data": content.data,
                        "error": str(e),
                    }
            else:
                return {
                    "format": "html",
                    "html": None,
                    "data": content.data,
                }

    # ==========================================
    # Serialization
    # ==========================================

    def _serialize_content(self, content: CMSContent) -> Dict:
        """Serialize CMSContent to dictionary.

        Args:
            content: CMSContent instance

        Returns:
            Serialized dictionary
        """
        resource = get_resource(content.resource_type)

        return {
            "id": content.id,
            "resource_type": content.resource_type,
            "slug": content.slug,
            "data": content.data,
            "lang": content.lang,
            "is_published": content.is_published,
            "published_at": (
                content.published_at.isoformat() if content.published_at else None
            ),
            "author_id": content.author_id,
            "sort_order": content.sort_order,
            "created": content.created.isoformat() if content.created else None,
            "updated": content.updated.isoformat() if content.updated else None,
            # Include resource info
            "resource": {
                "label": resource["label"],
                "is_singleton": resource["is_singleton"],
                "output_format": resource["output_format"],
                "component": resource["component"],
            },
            "links": {
                "self": f"/data/cms/content/{content.id}",
            },
        }
