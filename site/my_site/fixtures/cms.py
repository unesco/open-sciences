# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS Fixtures.

This module contains default content for CMS resources.
These fixtures are used to populate initial values when the CMS is set up.
"""

from datetime import datetime

# =============================================================================
# HEADER FRONTPAGE FIXTURE
# =============================================================================
HEADER_FRONTPAGE_DEFAULT = {
    "logo": "",  # Empty = use default /static/images/unesco-logo.svg
    "background_image": "",  # Empty = use default /static/images/science-background1.jpg
    "navigation_links": [
        {
            "label": "About",
            "url": "/about",
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
    "search_placeholder": "Search UNESCO research publications",
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
            "url": "/about",
            "external": False,
        },
        {
            "label": "UNESCO Natural Sciences Family",
            "url": "https://www.unesco.org/en/natural-sciences",
            "external": True,
        },
        {
            "label": "UNESCO Open Science",
            "url": "https://www.unesco.org/en/open-science",
            "external": True,
        },
    ],
    "copyright_text": "© 2025 UNESCO Open Science Portal - United Nations Educational, Scientific and Cultural Organization",
    "tagline": "Promoting international cooperation in education, science, and culture worldwide.",
}


# =============================================================================
# ALL FIXTURES REGISTRY
# =============================================================================
CMS_FIXTURES = {
    "header_frontpage": {
        "en": HEADER_FRONTPAGE_DEFAULT,
    },
    "footer": {
        "en": FOOTER_DEFAULT,
    },
    # Add more resource fixtures here as needed
    # "header": {...},
    # "homepage_hero": {...},
}


def get_fixture(resource_type: str, lang: str = "en") -> dict:
    """Get fixture data for a resource type and language.

    Args:
        resource_type: The CMS resource type (e.g., "footer")
        lang: Language code (default: "en")

    Returns:
        Dictionary with fixture data, or empty dict if not found
    """
    if resource_type not in CMS_FIXTURES:
        return {}

    fixtures = CMS_FIXTURES[resource_type]

    # Try requested language, fall back to English
    if lang in fixtures:
        return fixtures[lang]
    elif "en" in fixtures:
        return fixtures["en"]
    else:
        # Return first available language
        return next(iter(fixtures.values()), {})


def get_all_fixtures() -> dict:
    """Get all CMS fixtures.

    Returns:
        Dictionary with all fixtures organized by resource_type and lang
    """
    return CMS_FIXTURES
