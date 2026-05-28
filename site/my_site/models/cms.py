# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS Content SQLAlchemy model.

This module defines the unified CMS content model that stores
all CMS resources (singletons and collections) in a single table
with JSON data validated against resource-specific schemas.
"""

from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy_utils.models import Timestamp


class CMSContent(db.Model, Timestamp):
    """Unified CMS Content model.

    Stores all CMS content with resource-type-specific JSON data.
    Singleton resources have unique (resource_type, lang) constraint.
    Collection resources can have multiple entries per language.

    Attributes:
        id: Primary key
        resource_type: Type identifier (e.g., "footer", "plain_language_summary")
        slug: URL-friendly identifier (for collections, unique per type+lang)
        data: JSON content validated against resource schema
        lang: Language code (ISO 639-1)
        is_published: Publication status
        published_at: Publication timestamp
        author_id: Creator/editor user ID
        sort_order: Display ordering
        created: Auto-set creation timestamp
        updated: Auto-set update timestamp
    """

    __tablename__ = "cms_content"
    __table_args__ = (
        # For collections: unique slug per resource_type and language
        db.UniqueConstraint(
            "resource_type", "slug", "lang", name="uq_cms_content_type_slug_lang"
        ),
        # Index for common queries
        db.Index("ix_cms_content_type_lang", "resource_type", "lang"),
        db.Index("ix_cms_content_published", "is_published", "resource_type"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Resource identification
    resource_type = db.Column(db.String(100), nullable=False, index=True)
    slug = db.Column(db.String(255), nullable=True, index=True)

    # Content stored as JSON (validated against resource schema)
    data = db.Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="JSON content validated against resource schema",
    )

    # Language
    lang = db.Column(db.String(10), default="en", nullable=False, index=True)

    # Publication status
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)

    # Author tracking
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("accounts_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Display ordering (for collections)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    # Relationships
    author = relationship("User", backref="cms_contents")

    def __repr__(self):
        """String representation."""
        return f"<CMSContent(id={self.id}, type='{self.resource_type}', slug='{self.slug}', lang='{self.lang}')>"

    @classmethod
    def create(cls, data: dict) -> "CMSContent":
        """Create new CMS content.

        Args:
            data: Dictionary with content fields

        Returns:
            Created CMSContent instance
        """
        content = cls(
            resource_type=data.get("resource_type"),
            slug=data.get("slug"),
            data=data.get("data", {}),
            lang=data.get("lang", "en"),
            is_published=data.get("is_published", False),
            published_at=data.get("published_at"),
            author_id=data.get("author_id"),
            sort_order=data.get("sort_order", 0),
        )
        db.session.add(content)
        return content

    @classmethod
    def get(cls, id: int) -> Optional["CMSContent"]:
        """Get content by ID.

        Args:
            id: Content ID

        Returns:
            CMSContent instance or None
        """
        return cls.query.get(id)

    @classmethod
    def get_singleton(
        cls, resource_type: str, lang: str = "en"
    ) -> Optional["CMSContent"]:
        """Get singleton content by type and language.

        For singleton resources, there's only one entry per language.

        Args:
            resource_type: Resource type identifier
            lang: Language code

        Returns:
            CMSContent instance or None
        """
        return cls.query.filter_by(resource_type=resource_type, lang=lang).first()

    @classmethod
    def get_by_slug(
        cls, resource_type: str, slug: str, lang: str = "en"
    ) -> Optional["CMSContent"]:
        """Get content by resource type, slug, and language.

        Args:
            resource_type: Resource type identifier
            slug: Content slug
            lang: Language code

        Returns:
            CMSContent instance or None
        """
        return cls.query.filter_by(
            resource_type=resource_type, slug=slug, lang=lang
        ).first()

    @classmethod
    def get_by_type(
        cls, resource_type: str, lang: str = None, published_only: bool = False
    ) -> List["CMSContent"]:
        """Get all content of a specific type.

        Args:
            resource_type: Resource type identifier
            lang: Optional language filter
            published_only: Filter to published content only

        Returns:
            List of CMSContent instances
        """
        query = cls.query.filter_by(resource_type=resource_type)

        if lang:
            query = query.filter_by(lang=lang)

        if published_only:
            query = query.filter_by(is_published=True)

        return query.order_by(cls.sort_order, cls.created.desc()).all()

    @classmethod
    def search(cls, params: dict, filters: list = None) -> "sa.orm.Query":
        """Search content with filters and pagination.

        Args:
            params: Search parameters (resource_type, lang, q, page, size, sort)
            filters: Additional SQLAlchemy filter conditions

        Returns:
            SQLAlchemy pagination object
        """
        query = cls.query

        # Resource type filter
        if params.get("resource_type"):
            query = query.filter_by(resource_type=params["resource_type"])

        # Language filter
        if params.get("lang"):
            query = query.filter_by(lang=params["lang"])

        # Published filter
        if params.get("published_only"):
            query = query.filter_by(is_published=True)

        # Additional filters
        if filters:
            for f in filters:
                query = query.filter(f)

        # Text search in JSON data (PostgreSQL specific)
        if params.get("q"):
            search_term = f"%{params['q']}%"
            # Search in slug and cast JSON data to text
            query = query.filter(
                sa.or_(
                    cls.slug.ilike(search_term),
                    sa.cast(cls.data, sa.Text).ilike(search_term),
                )
            )

        # Sorting
        sort_field = params.get("sort", "created")
        sort_direction = params.get("sort_direction", "desc")

        if hasattr(cls, sort_field):
            order_col = getattr(cls, sort_field)
            if sort_direction == "desc":
                order_col = order_col.desc()
            query = query.order_by(order_col)

        # Pagination
        page = params.get("page", 1)
        size = params.get("size", 25)

        return query.paginate(page=page, per_page=size, error_out=False)

    def update(self, data: dict) -> "CMSContent":
        """Update content fields.

        Args:
            data: Dictionary with fields to update

        Returns:
            Updated CMSContent instance
        """
        updatable_fields = [
            "slug",
            "data",
            "lang",
            "is_published",
            "published_at",
            "sort_order",
        ]

        for key, value in data.items():
            if key in updatable_fields:
                setattr(self, key, value)

        self.updated = datetime.utcnow()
        return self

    def publish(self) -> None:
        """Publish the content."""
        self.is_published = True
        self.published_at = datetime.utcnow()

    def unpublish(self) -> None:
        """Unpublish the content."""
        self.is_published = False

    def get_data_field(self, field: str, default=None):
        """Get a specific field from JSON data.

        Args:
            field: Field name in data JSON
            default: Default value if field not found

        Returns:
            Field value or default
        """
        return self.data.get(field, default) if self.data else default
