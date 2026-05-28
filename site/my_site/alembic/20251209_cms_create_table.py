# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Create CMS content table.

This migration creates the cms_content table for the Resource-Driven CMS.
All CMS resources (singletons and collections) are stored in this unified table
with JSON data validated against resource-specific schemas.

Revision ID: cms001
Revises:
Create Date: 2025-12-09
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "cms001"
down_revision = "000000_my_site_branch"
branch_labels = None
depends_on = None


def upgrade():
    """Create cms_content table."""
    # Check if table already exists (created by db.create_all())
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "cms_content" in inspector.get_table_names():
        # Table already exists, skip creation
        return

    op.create_table(
        "cms_content",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(255), nullable=True),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
            comment="JSON content validated against resource schema",
        ),
        sa.Column("lang", sa.String(10), nullable=False, server_default="en"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        # Primary key
        sa.PrimaryKeyConstraint("id"),
        # Foreign key to users table
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["accounts_user.id"],
            name="fk_cms_content_author",
            ondelete="SET NULL",
        ),
        # Unique constraint for resource_type + slug + lang
        sa.UniqueConstraint(
            "resource_type", "slug", "lang", name="uq_cms_content_type_slug_lang"
        ),
    )

    # Create indexes for common queries
    op.create_index(
        "ix_cms_content_resource_type", "cms_content", ["resource_type"], unique=False
    )
    op.create_index("ix_cms_content_slug", "cms_content", ["slug"], unique=False)
    op.create_index("ix_cms_content_lang", "cms_content", ["lang"], unique=False)
    op.create_index(
        "ix_cms_content_author_id", "cms_content", ["author_id"], unique=False
    )
    op.create_index(
        "ix_cms_content_type_lang",
        "cms_content",
        ["resource_type", "lang"],
        unique=False,
    )
    op.create_index(
        "ix_cms_content_published",
        "cms_content",
        ["is_published", "resource_type"],
        unique=False,
    )
    op.create_index(
        "ix_cms_content_sort_order", "cms_content", ["sort_order"], unique=False
    )


def downgrade():
    """Drop cms_content table."""
    op.drop_index("ix_cms_content_sort_order", table_name="cms_content")
    op.drop_index("ix_cms_content_published", table_name="cms_content")
    op.drop_index("ix_cms_content_type_lang", table_name="cms_content")
    op.drop_index("ix_cms_content_author_id", table_name="cms_content")
    op.drop_index("ix_cms_content_lang", table_name="cms_content")
    op.drop_index("ix_cms_content_slug", table_name="cms_content")
    op.drop_index("ix_cms_content_resource_type", table_name="cms_content")
    op.drop_table("cms_content")
