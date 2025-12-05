# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Create CMS tables.

Revision ID: 20251205_154517
Revises: 00000000_create_my_site_branch
Create Date: 2024-12-05

This migration creates the following tables:
- cms_category: Categories for organizing CMS pages
- cms_page: Main CMS content pages
- cms_page_category: Many-to-many relationship table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "cms001_create_tables"
down_revision = "000000_my_site_branch"
branch_labels = None
depends_on = None


def upgrade():
    """Create CMS tables."""

    # Create cms_category table
    op.create_table(
        "cms_category",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, default=0),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_cms_category_name"),
        sa.UniqueConstraint("slug", name="uq_cms_category_slug"),
    )

    # Create index on cms_category.slug
    op.create_index("ix_cms_category_slug", "cms_category", ["slug"], unique=True)

    # Create cms_page table
    op.create_table(
        "cms_page",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("meta_title", sa.String(length=255), nullable=True),
        sa.Column("meta_description", sa.String(length=500), nullable=True),
        sa.Column(
            "template_name",
            sa.String(length=255),
            nullable=False,
            default="my_site/cms/page.html",
        ),
        sa.Column("is_published", sa.Boolean(), nullable=False, default=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("lang", sa.String(length=10), nullable=False, default="en"),
        sa.Column("sort_order", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["accounts_user.id"],
            name="fk_cms_page_author_id",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("slug", "lang", name="uq_cms_page_slug_lang"),
    )

    # Create indexes on cms_page
    op.create_index("ix_cms_page_slug", "cms_page", ["slug"])
    op.create_index("ix_cms_page_is_published", "cms_page", ["is_published"])
    op.create_index("ix_cms_page_lang", "cms_page", ["lang"])
    op.create_index("ix_cms_page_author_id", "cms_page", ["author_id"])

    # Create cms_page_category association table
    op.create_table(
        "cms_page_category",
        sa.Column("page_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint("page_id", "category_id"),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["cms_page.id"],
            name="fk_cms_page_category_page_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["cms_category.id"],
            name="fk_cms_page_category_category_id",
            ondelete="CASCADE",
        ),
    )

    # Create indexes on cms_page_category
    op.create_index("ix_cms_page_category_page_id", "cms_page_category", ["page_id"])
    op.create_index(
        "ix_cms_page_category_category_id", "cms_page_category", ["category_id"]
    )


def downgrade():
    """Drop CMS tables."""

    # Drop indexes first
    op.drop_index("ix_cms_page_category_category_id", table_name="cms_page_category")
    op.drop_index("ix_cms_page_category_page_id", table_name="cms_page_category")

    # Drop cms_page_category table
    op.drop_table("cms_page_category")

    # Drop cms_page indexes
    op.drop_index("ix_cms_page_author_id", table_name="cms_page")
    op.drop_index("ix_cms_page_lang", table_name="cms_page")
    op.drop_index("ix_cms_page_is_published", table_name="cms_page")
    op.drop_index("ix_cms_page_slug", table_name="cms_page")

    # Drop cms_page table
    op.drop_table("cms_page")

    # Drop cms_category index
    op.drop_index("ix_cms_category_slug", table_name="cms_category")

    # Drop cms_category table
    op.drop_table("cms_category")
