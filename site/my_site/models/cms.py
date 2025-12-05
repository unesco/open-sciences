# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS SQLAlchemy models for custom content management.

This module defines the database models for the CMS system:
- CMSPage: Main content pages
- CMSCategory: Categories for organizing pages
- CMSPageCategory: Many-to-many relationship between pages and categories

These models integrate with InvenioRDM's database infrastructure using
invenio_db and follow the same patterns as core Invenio modules.
"""

from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy.orm import relationship
from sqlalchemy_utils.models import Timestamp


class CMSCategory(db.Model, Timestamp):
    """Category model for organizing CMS pages.

    Attributes:
        id: Primary key
        name: Category name (unique)
        slug: URL-friendly identifier (unique)
        description: Optional category description
        sort_order: Order for display (lower = first)
        is_active: Whether category is active/visible
        created: Auto-set creation timestamp
        updated: Auto-set update timestamp
    """

    __tablename__ = "cms_category"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    slug = db.Column(db.String(255), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    pages = relationship(
        "CMSPage",
        secondary="cms_page_category",
        back_populates="categories",
        lazy="dynamic",
    )

    def __repr__(self):
        """String representation."""
        return f"<CMSCategory(id={self.id}, name='{self.name}')>"

    @classmethod
    def create(cls, data: dict) -> "CMSCategory":
        """Create a new category.

        Args:
            data: Dictionary with category fields

        Returns:
            Created CMSCategory instance
        """
        category = cls(
            name=data.get("name"),
            slug=data.get("slug"),
            description=data.get("description"),
            sort_order=data.get("sort_order", 0),
            is_active=data.get("is_active", True),
        )
        db.session.add(category)
        return category

    @classmethod
    def get(cls, id: int) -> Optional["CMSCategory"]:
        """Get category by ID.

        Args:
            id: Category ID

        Returns:
            CMSCategory instance or None
        """
        return cls.query.get(id)

    @classmethod
    def get_by_slug(cls, slug: str) -> Optional["CMSCategory"]:
        """Get category by slug.

        Args:
            slug: Category slug

        Returns:
            CMSCategory instance or None
        """
        return cls.query.filter_by(slug=slug).first()

    @classmethod
    def get_active(cls) -> List["CMSCategory"]:
        """Get all active categories ordered by sort_order.

        Returns:
            List of active CMSCategory instances
        """
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order).all()

    @classmethod
    def search(cls, params: dict, filters: list = None) -> "sa.orm.Query":
        """Search categories with filters.

        Args:
            params: Search parameters (q, page, size, sort, sort_direction)
            filters: Additional SQLAlchemy filter conditions

        Returns:
            SQLAlchemy query object
        """
        query = cls.query

        if filters:
            for f in filters:
                query = query.filter(f)

        # Sorting
        sort_field = params.get("sort", "sort_order")
        sort_direction = params.get("sort_direction", "asc")

        if hasattr(cls, sort_field):
            order_col = getattr(cls, sort_field)
            if sort_direction == "desc":
                order_col = order_col.desc()
            query = query.order_by(order_col)

        # Pagination
        page = params.get("page", 1)
        size = params.get("size", 25)

        return query.paginate(page=page, per_page=size, error_out=False)


class CMSPage(db.Model, Timestamp):
    """CMS Page model for content management.

    Attributes:
        id: Primary key
        slug: URL-friendly identifier (unique)
        title: Page title
        content: HTML content
        excerpt: Short description/preview
        meta_title: SEO title
        meta_description: SEO description
        template_name: Jinja2 template path
        is_published: Publication status
        published_at: Publication date
        author_id: Foreign key to accounts_user
        lang: Language code (ISO 639-1)
        sort_order: Order for display
        created: Auto-set creation timestamp
        updated: Auto-set update timestamp
    """

    __tablename__ = "cms_page"
    __table_args__ = (
        db.UniqueConstraint("slug", "lang", name="uq_cms_page_slug_lang"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slug = db.Column(db.String(500), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=True)
    excerpt = db.Column(db.Text, nullable=True)

    # SEO fields
    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.String(500), nullable=True)

    # Template
    template_name = db.Column(
        db.String(255), default="my_site/cms/page.html", nullable=False
    )

    # Status
    is_published = db.Column(db.Boolean, default=False, nullable=False, index=True)
    published_at = db.Column(db.DateTime, nullable=True)

    # Author - Foreign Key to InvenioRDM's User table
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("accounts_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Language
    lang = db.Column(db.String(10), default="en", nullable=False, index=True)

    # Ordering
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    # Relationships
    author = relationship("User", backref="cms_pages")
    categories = relationship(
        "CMSCategory",
        secondary="cms_page_category",
        back_populates="pages",
        lazy="joined",
    )

    def __repr__(self):
        """String representation."""
        return f"<CMSPage(id={self.id}, slug='{self.slug}', lang='{self.lang}')>"

    @classmethod
    def create(cls, data: dict) -> "CMSPage":
        """Create a new page.

        Args:
            data: Dictionary with page fields

        Returns:
            Created CMSPage instance
        """
        page = cls(
            slug=data.get("slug"),
            title=data.get("title"),
            content=data.get("content"),
            excerpt=data.get("excerpt"),
            meta_title=data.get("meta_title"),
            meta_description=data.get("meta_description"),
            template_name=data.get("template_name", "my_site/cms/page.html"),
            is_published=data.get("is_published", False),
            published_at=data.get("published_at"),
            author_id=data.get("author_id"),
            lang=data.get("lang", "en"),
            sort_order=data.get("sort_order", 0),
        )
        db.session.add(page)
        return page

    @classmethod
    def get(cls, id: int) -> Optional["CMSPage"]:
        """Get page by ID.

        Args:
            id: Page ID

        Returns:
            CMSPage instance or None
        """
        return cls.query.get(id)

    @classmethod
    def get_by_slug(cls, slug: str, lang: str = "en") -> Optional["CMSPage"]:
        """Get page by slug and language.

        Args:
            slug: Page slug
            lang: Language code

        Returns:
            CMSPage instance or None
        """
        return cls.query.filter_by(slug=slug, lang=lang).first()

    @classmethod
    def get_published(cls, lang: str = None) -> List["CMSPage"]:
        """Get all published pages.

        Args:
            lang: Optional language filter

        Returns:
            List of published CMSPage instances
        """
        query = cls.query.filter_by(is_published=True)
        if lang:
            query = query.filter_by(lang=lang)
        return query.order_by(cls.sort_order).all()

    @classmethod
    def update(cls, data: dict, id: int) -> Optional["CMSPage"]:
        """Update an existing page.

        Args:
            data: Dictionary with updated fields
            id: Page ID to update

        Returns:
            Updated CMSPage instance or None
        """
        page = cls.get(id)
        if page:
            for key, value in data.items():
                if hasattr(page, key) and key not in ("id", "created"):
                    setattr(page, key, value)
            page.updated = datetime.utcnow()
        return page

    @classmethod
    def delete(cls, page: "CMSPage") -> None:
        """Delete a page.

        Args:
            page: CMSPage instance to delete
        """
        db.session.delete(page)

    @classmethod
    def search(cls, params: dict, filters: list = None) -> "sa.orm.Query":
        """Search pages with filters.

        Args:
            params: Search parameters (q, page, size, sort, sort_direction)
            filters: Additional SQLAlchemy filter conditions

        Returns:
            SQLAlchemy pagination object
        """
        query = cls.query

        if filters:
            for f in filters:
                query = query.filter(f)

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

    def publish(self) -> None:
        """Publish the page."""
        self.is_published = True
        self.published_at = datetime.utcnow()

    def unpublish(self) -> None:
        """Unpublish the page."""
        self.is_published = False


class CMSPageCategory(db.Model):
    """Association table for many-to-many relationship between pages and categories.

    This is an explicit association model rather than a simple association table
    to allow for additional metadata like ordering.
    """

    __tablename__ = "cms_page_category"
    __table_args__ = (db.PrimaryKeyConstraint("page_id", "category_id"),)

    page_id = db.Column(
        db.Integer, db.ForeignKey("cms_page.id", ondelete="CASCADE"), nullable=False
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey("cms_category.id", ondelete="CASCADE"), nullable=False
    )
    # Optional: ordering within category
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        """String representation."""
        return (
            f"<CMSPageCategory(page_id={self.page_id}, category_id={self.category_id})>"
        )
