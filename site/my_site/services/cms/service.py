# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS Service API.

This module provides the service layer for CMS operations.
Services encapsulate business logic and handle:
- Permission checking
- Data validation
- Database operations
- Unit of work pattern
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from flask import current_app
from invenio_db import db
from invenio_records_resources.services.base import Service
from invenio_records_resources.services.base.utils import map_search_params
from invenio_records_resources.services.uow import unit_of_work

from ...models.cms import CMSCategory, CMSPage, CMSPageCategory


class CMSPageService(Service):
    """Service for CMS Page operations."""

    @property
    def schema(self):
        """Get the schema instance."""
        return self.config.schema()

    @property
    def record_cls(self):
        """Get the record class."""
        return self.config.record_cls

    def _get_permission(self, action_name):
        """Get permission for action."""
        return self.config.permission_policy_cls(action_name)

    @unit_of_work()
    def create(self, identity, data: Dict[str, Any], uow=None) -> CMSPage:
        """Create a new CMS page.

        Args:
            identity: User identity
            data: Page data
            uow: Unit of work

        Returns:
            Created CMSPage instance
        """
        self.require_permission(identity, "create")

        # Validate data (Marshmallow 3.x)
        validated_data = self.schema.load(data)

        # Extract category IDs before creating page
        category_ids = validated_data.pop("category_ids", [])

        # Set author if not provided
        if not validated_data.get("author_id") and hasattr(identity, "id"):
            validated_data["author_id"] = identity.id

        # Create page
        page = self.record_cls.create(validated_data)
        db.session.flush()  # Get the ID

        # Add categories
        if category_ids:
            self._set_page_categories(page.id, category_ids)

        return page

    def read(self, identity, id: int) -> CMSPage:
        """Read a CMS page by ID.

        Args:
            identity: User identity
            id: Page ID

        Returns:
            CMSPage instance

        Raises:
            Exception if page not found
        """
        self.require_permission(identity, "read")

        page = self.record_cls.get(id)
        if not page:
            raise Exception(f"Page with id {id} not found")

        return page

    def read_by_slug(self, identity, slug: str, lang: str = "en") -> CMSPage:
        """Read a CMS page by slug and language.

        Args:
            identity: User identity
            slug: Page slug
            lang: Language code

        Returns:
            CMSPage instance

        Raises:
            Exception if page not found
        """
        self.require_permission(identity, "read")

        page = self.record_cls.get_by_slug(slug, lang)
        if not page:
            raise Exception(f"Page with slug '{slug}' and lang '{lang}' not found")

        return page

    def search(self, identity, params: Dict = None) -> Dict:
        """Search CMS pages.

        Args:
            identity: User identity
            params: Search parameters

        Returns:
            Dictionary with hits, total, pagination info
        """
        self.require_permission(identity, "search")

        params = params or {}
        filters = []

        # Filter by published status for non-admin users
        # (In production, check identity permissions)
        if params.get("published_only", False):
            filters.append(CMSPage.is_published == True)

        # Filter by language
        if params.get("lang"):
            filters.append(CMSPage.lang == params["lang"])

        # Filter by category
        if params.get("category_id"):
            filters.append(
                CMSPage.categories.any(CMSCategory.id == params["category_id"])
            )

        # Text search
        if params.get("q"):
            search_term = f"%{params['q']}%"
            filters.append(
                sa.or_(
                    CMSPage.title.ilike(search_term),
                    CMSPage.content.ilike(search_term),
                    CMSPage.slug.ilike(search_term),
                )
            )

        # Execute search
        pagination = self.record_cls.search(params, filters)

        return {
            "hits": [self.schema.dump(page) for page in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "size": pagination.per_page,
            "pages": pagination.pages,
        }

    @unit_of_work()
    def update(self, identity, id: int, data: Dict[str, Any], uow=None) -> CMSPage:
        """Update a CMS page.

        Args:
            identity: User identity
            id: Page ID
            data: Updated data
            uow: Unit of work

        Returns:
            Updated CMSPage instance
        """
        self.require_permission(identity, "update")

        # Validate data (Marshmallow 3.x - partial for updates)
        validated_data = self.schema.load(data, partial=True)

        # Extract category IDs
        category_ids = validated_data.pop("category_ids", None)

        # Update page
        page = self.record_cls.update(validated_data, id)
        if not page:
            raise Exception(f"Page with id {id} not found")

        # Update categories if provided
        if category_ids is not None:
            self._set_page_categories(id, category_ids)

        return page

    @unit_of_work()
    def delete(self, identity, id: int, uow=None) -> bool:
        """Delete a CMS page.

        Args:
            identity: User identity
            id: Page ID
            uow: Unit of work

        Returns:
            True if deleted
        """
        self.require_permission(identity, "delete")

        page = self.record_cls.get(id)
        if not page:
            raise Exception(f"Page with id {id} not found")

        self.record_cls.delete(page)
        return True

    @unit_of_work()
    def publish(self, identity, id: int, uow=None) -> CMSPage:
        """Publish a CMS page.

        Args:
            identity: User identity
            id: Page ID
            uow: Unit of work

        Returns:
            Published CMSPage instance
        """
        self.require_permission(identity, "publish")

        page = self.record_cls.get(id)
        if not page:
            raise Exception(f"Page with id {id} not found")

        page.publish()
        return page

    @unit_of_work()
    def unpublish(self, identity, id: int, uow=None) -> CMSPage:
        """Unpublish a CMS page.

        Args:
            identity: User identity
            id: Page ID
            uow: Unit of work

        Returns:
            Unpublished CMSPage instance
        """
        self.require_permission(identity, "unpublish")

        page = self.record_cls.get(id)
        if not page:
            raise Exception(f"Page with id {id} not found")

        page.unpublish()
        return page

    def _set_page_categories(self, page_id: int, category_ids: List[int]) -> None:
        """Set categories for a page (replaces existing).

        Args:
            page_id: Page ID
            category_ids: List of category IDs
        """
        # Remove existing
        CMSPageCategory.query.filter_by(page_id=page_id).delete()

        # Add new
        for idx, cat_id in enumerate(category_ids):
            assoc = CMSPageCategory(page_id=page_id, category_id=cat_id, sort_order=idx)
            db.session.add(assoc)


class CMSCategoryService(Service):
    """Service for CMS Category operations."""

    @property
    def schema(self):
        """Get the schema instance."""
        return self.config.schema()

    @property
    def record_cls(self):
        """Get the record class."""
        return self.config.record_cls

    @unit_of_work()
    def create(self, identity, data: Dict[str, Any], uow=None) -> CMSCategory:
        """Create a new CMS category.

        Args:
            identity: User identity
            data: Category data
            uow: Unit of work

        Returns:
            Created CMSCategory instance
        """
        self.require_permission(identity, "create")

        # Validate data (Marshmallow 3.x)
        validated_data = self.schema.load(data)

        # Create category
        category = self.record_cls.create(validated_data)
        return category

    def read(self, identity, id: int) -> CMSCategory:
        """Read a CMS category by ID.

        Args:
            identity: User identity
            id: Category ID

        Returns:
            CMSCategory instance
        """
        self.require_permission(identity, "read")

        category = self.record_cls.get(id)
        if not category:
            raise Exception(f"Category with id {id} not found")

        return category

    def read_by_slug(self, identity, slug: str) -> CMSCategory:
        """Read a CMS category by slug.

        Args:
            identity: User identity
            slug: Category slug

        Returns:
            CMSCategory instance
        """
        self.require_permission(identity, "read")

        category = self.record_cls.get_by_slug(slug)
        if not category:
            raise Exception(f"Category with slug '{slug}' not found")

        return category

    def search(self, identity, params: Dict = None) -> Dict:
        """Search CMS categories.

        Args:
            identity: User identity
            params: Search parameters

        Returns:
            Dictionary with hits, total, pagination info
        """
        self.require_permission(identity, "search")

        params = params or {}
        filters = []

        # Filter by active status
        if params.get("active_only", False):
            filters.append(CMSCategory.is_active == True)

        # Text search
        if params.get("q"):
            search_term = f"%{params['q']}%"
            filters.append(
                sa.or_(
                    CMSCategory.name.ilike(search_term),
                    CMSCategory.slug.ilike(search_term),
                    CMSCategory.description.ilike(search_term),
                )
            )

        # Execute search
        pagination = self.record_cls.search(params, filters)

        return {
            "hits": [self.schema.dump(cat) for cat in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "size": pagination.per_page,
            "pages": pagination.pages,
        }

    @unit_of_work()
    def update(self, identity, id: int, data: Dict[str, Any], uow=None) -> CMSCategory:
        """Update a CMS category.

        Args:
            identity: User identity
            id: Category ID
            data: Updated data
            uow: Unit of work

        Returns:
            Updated CMSCategory instance
        """
        self.require_permission(identity, "update")

        # Validate data (Marshmallow 3.x - partial for updates)
        validated_data = self.schema.load(data, partial=True)

        category = self.record_cls.get(id)
        if not category:
            raise Exception(f"Category with id {id} not found")

        for key, value in validated_data.items():
            if hasattr(category, key):
                setattr(category, key, value)

        return category

    @unit_of_work()
    def delete(self, identity, id: int, uow=None) -> bool:
        """Delete a CMS category.

        Args:
            identity: User identity
            id: Category ID
            uow: Unit of work

        Returns:
            True if deleted
        """
        self.require_permission(identity, "delete")

        category = self.record_cls.get(id)
        if not category:
            raise Exception(f"Category with id {id} not found")

        db.session.delete(category)
        return True

    def get_active(self, identity) -> List[CMSCategory]:
        """Get all active categories.

        Args:
            identity: User identity

        Returns:
            List of active CMSCategory instances
        """
        self.require_permission(identity, "search")
        return self.record_cls.get_active()
