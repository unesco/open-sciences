# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS Fixtures.

This module contains default content for CMS resources.
These fixtures are used to populate initial values when the CMS is set up.

Static page content is loaded from HTML templates in the templates/ directory
for better maintainability and editing.
"""

from datetime import datetime
from pathlib import Path

# =============================================================================
# TEMPLATE LOADING UTILITIES
# =============================================================================

# Base path for fixture templates
TEMPLATES_DIR = Path(__file__).parent / "templates"


def load_template(resource_type: str, filename: str) -> str:
    """Load an HTML template from the templates directory.

    Args:
        resource_type: The resource type subdirectory (e.g., "static_pages")
        filename: The HTML file name (e.g., "about.html")

    Returns:
        The template content as a string, or empty string if not found
    """
    template_path = TEMPLATES_DIR / resource_type / filename
    try:
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Warning: Template not found: {template_path}")
        return ""


# =============================================================================
# HEADER FRONTPAGE FIXTURE
# =============================================================================
HEADER_FRONTPAGE_DEFAULT = {
    "logo": "",  # Empty = use default /static/images/unesco-logo.svg
    "background_image": "",  # Empty = use default /static/images/science-background1.jpg
    "navigation_links": [
        {
            "label": "About",
            "url": "/pages/about",
            "external": False,
        },
        {
            "label": "Natural Sciences",
            "url": "https://www.unesco.org/en/natural-sciences",
            "external": True,
        },
        {
            "label": "Open Science",
            "url": "https://www.unesco.org/en/open-science",
            "external": True,
        },
    ],
    "title": "UNESCO Open Science Platform",
    "subtitle": "Your Gateway to Knowledge from the UNESCO Natural Science Family",
    "search_placeholder": "Search UNESCO\'s research publications",
    "advanced_search_label": "Advanced search",
}


# =============================================================================
# FOOTER FIXTURE
# =============================================================================
FOOTER_DEFAULT = {
    "unesco_logo": "",  # Path to uploaded logo (empty = use default)
    "unesco_website_url": "https://www.unesco.org",
    "unesco_website_label": "Official UNESCO Website",
    "contact_email": "open-science-platform@unesco.org",
    "navigation_links": [
        {
            "label": "About",
            "url": "/pages/about",
            "external": False,
        },
        {
            "label": "UNESCO Natural Sciences Family",
            "url": "/pages/natural-sciences-family",
        },
        {
            "label": "UNESCO Open Science Dashboards",
            "url": "https://www.unesco.org/en/open-science/",
            "external": True,
        },
        {
            "label": "Privacy",
            "url": "/pages/privacy",
            "external": False,
        },
    ],
    "copyright_text": "© 2025 UNESCO Open Science Portal - United Nations Educational, Scientific and Cultural Organization",
    "tagline": "Promoting international cooperation in education, science, and culture worldwide.",
}


# =============================================================================
# STATIC PAGES FIXTURES
# =============================================================================

# Define static pages metadata - content is loaded from HTML templates
# Templates are stored in: fixtures/templates/static_pages/<slug>.html
STATIC_PAGES_METADATA = {
    "about": {
        "title": "About the UNESCO Open Science Platform",
        "slug": "about",
        "template": "about.html",
        "meta_title": "About Open Science - UNESCO Open Science Platform",
        "meta_description": "Learn about the open science movement and its global impact on research, collaboration, and knowledge sharing.",
    },
    "privacy": {
        "title": "Privacy Notice",
        "slug": "privacy",
        "template": "privacy.html",
        "meta_title": "Privacy Notice - UNESCO Open Science Platform",
        "meta_description": "Privacy notice for the UNESCO Open Science Platform.",
    },
    "natural-sciences-family": {
        "title": "UNESCO Natural Sciences Family",
        "slug": "natural-sciences-family",
        "template": "natural-sciences-family.html",
        "meta_title": "UNESCO Natural Sciences Family - UNESCO Open Science Platform",
        "meta_description": "Learn about the UNESCO Natural Sciences Family and its role in open science.",
    },
    # Add more static pages here:
    # "terms": {
    #     "title": "Terms of Use",
    #     "slug": "terms",
    #     "template": "terms.html",
    #     "meta_title": "Terms of Use - UNESCO Open Science Platform",
    #     "meta_description": "Terms and conditions for using the UNESCO Open Science Platform.",
    # },
}


def get_static_page_fixture(slug: str) -> dict:
    """Get a static page fixture with loaded HTML content.

    Args:
        slug: The page slug (e.g., "about")

    Returns:
        Dictionary with page data including loaded content
    """
    if slug not in STATIC_PAGES_METADATA:
        return {}

    page_meta = STATIC_PAGES_METADATA[slug].copy()
    template_file = page_meta.pop("template", f"{slug}.html")

    # Load the HTML content from template
    content = load_template("static_pages", template_file)

    return {
        **page_meta,
        "content": content,
    }


def get_all_static_pages() -> dict:
    """Get all static page fixtures with loaded content.

    Returns:
        Dictionary mapping slug to page fixture data
    """
    return {slug: get_static_page_fixture(slug) for slug in STATIC_PAGES_METADATA}


# =============================================================================
# ALL FIXTURES REGISTRY (built lazily)
# =============================================================================
_cms_fixtures_cache = None


def _build_cms_fixtures() -> dict:
    """Build the complete CMS fixtures dictionary.

    This function loads static page templates at runtime.
    """
    return {
        "header_frontpage": {
            "en": HEADER_FRONTPAGE_DEFAULT,
        },
        "footer": {
            "en": FOOTER_DEFAULT,
        },
        "static_page": {
            "en": get_all_static_pages(),
        },
    }


def _get_cms_fixtures() -> dict:
    """Get CMS fixtures with lazy loading."""
    global _cms_fixtures_cache
    if _cms_fixtures_cache is None:
        _cms_fixtures_cache = _build_cms_fixtures()
    return _cms_fixtures_cache


def get_fixture(resource_type: str, lang: str = "en") -> dict:
    """Get fixture data for a resource type and language.

    Args:
        resource_type: The CMS resource type (e.g., "footer")
        lang: Language code (default: "en")

    Returns:
        Dictionary with fixture data, or empty dict if not found
    """
    fixtures = _get_cms_fixtures()

    if resource_type not in fixtures:
        return {}

    resource_fixtures = fixtures[resource_type]

    # Try requested language, fall back to English
    if lang in resource_fixtures:
        return resource_fixtures[lang]
    elif "en" in resource_fixtures:
        return resource_fixtures["en"]
    else:
        # Return first available language
        return next(iter(resource_fixtures.values()), {})


def get_all_fixtures() -> dict:
    """Get all CMS fixtures.

    Returns:
        Dictionary with all fixtures organized by resource_type and lang
    """
    return _get_cms_fixtures()
