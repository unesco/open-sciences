# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CLI commands for my_site module."""

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db


@click.group()
def cms():
    """CMS management commands."""
    pass


@cms.command("load-fixtures")
@click.option(
    "--resource",
    "-r",
    default=None,
    help="Load fixtures for a specific resource type only (e.g., footer)",
)
@click.option(
    "--slug",
    "-s",
    default=None,
    help="Load fixture for a specific slug only (e.g., about). Requires --resource.",
)
@click.option(
    "--lang",
    "-l",
    default=None,
    help="Load fixtures for a specific language only (e.g., en)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Overwrite existing content (default: skip existing)",
)
@with_appcontext
def load_fixtures(resource, slug, lang, force):
    """Load CMS fixtures into the database.

    Examples:
        invenio cms load-fixtures
        invenio cms load-fixtures --resource footer
        invenio cms load-fixtures --resource static_page --slug about --force
        invenio cms load-fixtures --resource footer --lang en
        invenio cms load-fixtures --force
    """
    from .fixtures import get_all_fixtures
    from .models import CMSContent
    from .services.cms import get_resource

    fixtures = get_all_fixtures()

    # Filter by resource if specified
    if resource:
        if resource not in fixtures:
            click.echo(f"❌ Unknown resource type: {resource}")
            click.echo(f"   Available: {', '.join(fixtures.keys())}")
            return
        fixtures = {resource: fixtures[resource]}

    created = 0
    skipped = 0
    updated = 0

    for resource_type, lang_data in fixtures.items():
        resource_def = get_resource(resource_type)
        if not resource_def:
            click.echo(f"⚠️  Skipping unknown resource: {resource_type}")
            continue

        is_singleton = resource_def.get("is_singleton", False)

        for fixture_lang, data in lang_data.items():
            # Filter by language if specified
            if lang and fixture_lang != lang:
                continue

            if is_singleton:
                # Singleton: data is the content directly
                # slug = resource_type
                items_to_create = [(resource_type, data)]
            else:
                # Collection: data is {slug: content_data}
                items_to_create = [
                    (item_slug, content_data)
                    for item_slug, content_data in data.items()
                    if slug is None or item_slug == slug
                ]

            for item_slug, content_data in items_to_create:
                # Check if content already exists
                existing = CMSContent.query.filter_by(
                    resource_type=resource_type, slug=item_slug, lang=fixture_lang
                ).first()

                if existing:
                    if force:
                        # Update existing and publish
                        from datetime import datetime

                        existing.data = content_data
                        existing.is_published = True
                        existing.published_at = datetime.utcnow()
                        updated += 1
                        click.echo(
                            f"✏️  Updated: {resource_type}/{item_slug} ({fixture_lang})"
                        )
                    else:
                        skipped += 1
                        click.echo(
                            f"⏭️  Skipped (exists): {resource_type}/{item_slug} ({fixture_lang})"
                        )
                else:
                    # Create new
                    content = CMSContent.create(
                        {
                            "resource_type": resource_type,
                            "slug": item_slug,
                            "data": content_data,
                            "lang": fixture_lang,
                            "is_published": True,  # Fixtures are published by default
                        }
                    )
                    created += 1
                    click.echo(f"✅ Created: {resource_type}/{item_slug} ({fixture_lang})")

    db.session.commit()

    click.echo("")
    click.echo(f"📊 Summary: {created} created, {updated} updated, {skipped} skipped")


@cms.command("list-fixtures")
@with_appcontext
def list_fixtures():
    """List available CMS fixtures."""
    from .fixtures import get_all_fixtures

    fixtures = get_all_fixtures()

    click.echo("📦 Available CMS Fixtures:")
    click.echo("")

    for resource_type, lang_data in fixtures.items():
        languages = list(lang_data.keys())
        click.echo(f"  • {resource_type}: {', '.join(languages)}")

    click.echo("")
    click.echo("Use 'invenio cms load-fixtures' to load them into the database.")
