# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""CMS Resource Registry.

This module defines the available CMS resource types with their:
- JSON Schema for validation
- Output format (html/json)
- Template for rendering
- React component for editing
- Singleton vs collection behavior
"""

# Available languages for CMS content
CMS_LANGUAGES = [
    {"code": "en", "name": "English"},
]

# Resource Registry
CMS_RESOURCES = {
    # ===========================================
    # SINGLETON RESOURCES (one per language)
    # ===========================================
    "header": {
        "label": "Header",
        "description": "Site header configuration",
        "is_singleton": True,
        "output_format": "json",
        "template": None,
        "component": "HeaderEditor",
        "schema": {
            "type": "object",
            "properties": {
                "unesco_logo_url": {
                    "type": "string",
                    "format": "uri",
                    "title": "UNESCO Logo URL",
                    "description": "URL to the UNESCO logotype image",
                },
                "site_title": {
                    "type": "string",
                    "title": "Site Title",
                    "maxLength": 200,
                },
            },
            "required": [],
        },
    },
    "footer": {
        "label": "Footer",
        "description": "Site footer configuration",
        "is_singleton": True,
        "output_format": "json",
        "template": None,
        "component": "FooterEditor",
        "schema": {
            "type": "object",
            "properties": {
                # Left column - Logo
                "unesco_logo": {
                    "type": "string",
                    "title": "UNESCO Logo",
                    "description": "Upload a custom logo image. Leave empty to use the default UNESCO logo.",
                    "format": "image",
                },
                # Left column - Website link
                "unesco_website_url": {
                    "type": "string",
                    "format": "uri",
                    "title": "UNESCO Website URL",
                    "description": "Link to official UNESCO website",
                    "default": "https://www.unesco.org",
                },
                "unesco_website_label": {
                    "type": "string",
                    "title": "UNESCO Website Label",
                    "description": "Text for UNESCO website link",
                    "default": "Official UNESCO Website",
                },
                # Right column
                "contact_email": {
                    "type": "string",
                    "format": "email",
                    "title": "Contact Email",
                    "description": "Contact email displayed in footer",
                },
                "navigation_links": {
                    "type": "array",
                    "title": "Navigation Links",
                    "description": "Footer navigation links (max 4)",
                    "maxItems": 4,
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {
                                "type": "string",
                                "title": "Link Label",
                                "maxLength": 100,
                            },
                            "url": {
                                "type": "string",
                                "title": "Link URL",
                            },
                            "external": {
                                "type": "boolean",
                                "title": "External Link",
                                "description": "Opens in new tab if true",
                                "default": False,
                            },
                        },
                        "required": ["label", "url"],
                    },
                },
                # Bottom section
                "copyright_text": {
                    "type": "string",
                    "title": "Copyright Text",
                    "description": "Main copyright line",
                },
                "tagline": {
                    "type": "string",
                    "title": "Tagline",
                    "description": "Secondary tagline text",
                },
            },
            "required": ["contact_email"],
        },
    },
    "homepage_hero": {
        "label": "Homepage Hero",
        "description": "Homepage hero section with search",
        "is_singleton": True,
        "output_format": "json",
        "template": None,
        "component": "HomepageHeroEditor",
        "schema": {
            "type": "object",
            "properties": {
                "search_placeholder": {
                    "type": "string",
                    "title": "Search Placeholder",
                    "description": "Watermark text for search input box",
                    "maxLength": 200,
                },
                "recommendation_title": {
                    "type": "string",
                    "title": "Recommendation Title",
                    "description": "2021 UNESCO Recommendation title",
                },
                "recommendation_text": {
                    "type": "string",
                    "title": "Recommendation Text",
                    "description": "2021 UNESCO Recommendation on Open Science text",
                    "format": "html",
                },
                "recommendation_link": {
                    "type": "string",
                    "format": "uri",
                    "title": "Recommendation Link",
                },
            },
            "required": ["search_placeholder"],
        },
    },
    "homepage_highlights": {
        "label": "Homepage Highlights",
        "description": "Evidence-based highlights section",
        "is_singleton": True,
        "output_format": "json",
        "template": None,
        "component": "HomepageHighlightsEditor",
        "schema": {
            "type": "object",
            "properties": {
                "section_title": {
                    "type": "string",
                    "title": "Section Title",
                    "description": "Header for the highlights section",
                },
                "tiles": {
                    "type": "array",
                    "title": "Highlight Tiles",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "title": "Tile Title"},
                            "description": {"type": "string", "title": "Description"},
                            "icon": {"type": "string", "title": "Icon name or URL"},
                            "link": {
                                "type": "string",
                                "format": "uri",
                                "title": "Link URL",
                            },
                            "image_url": {
                                "type": "string",
                                "format": "uri",
                                "title": "Image URL",
                            },
                        },
                        "required": ["title"],
                    },
                },
            },
            "required": ["section_title"],
        },
    },
    "homepage_partners": {
        "label": "Homepage Partners",
        "description": "Partners section with logos",
        "is_singleton": True,
        "output_format": "json",
        "template": None,
        "component": "HomepagePartnersEditor",
        "schema": {
            "type": "object",
            "properties": {
                "section_title": {
                    "type": "string",
                    "title": "Section Title",
                },
                "section_text": {
                    "type": "string",
                    "title": "Partners Text",
                    "format": "html",
                },
                "partners": {
                    "type": "array",
                    "title": "Partners",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "title": "Partner Name"},
                            "logo_url": {
                                "type": "string",
                                "format": "uri",
                                "title": "Logo URL",
                            },
                            "website_url": {
                                "type": "string",
                                "format": "uri",
                                "title": "Website URL",
                            },
                        },
                        "required": ["name", "logo_url"],
                    },
                },
            },
            "required": ["section_title"],
        },
    },
    "homepage_infographics": {
        "label": "Homepage Infographics",
        "description": "Infographics section on homepage",
        "is_singleton": True,
        "output_format": "json",
        "template": None,
        "component": "HomepageInfographicsEditor",
        "schema": {
            "type": "object",
            "properties": {
                "section_title": {
                    "type": "string",
                    "title": "Section Title",
                },
                "infographics": {
                    "type": "array",
                    "title": "Infographics",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "title": "Title"},
                            "image_url": {
                                "type": "string",
                                "format": "uri",
                                "title": "Image URL",
                            },
                            "description": {"type": "string", "title": "Description"},
                            "link": {
                                "type": "string",
                                "format": "uri",
                                "title": "Link",
                            },
                        },
                        "required": ["title", "image_url"],
                    },
                },
            },
            "required": [],
        },
    },
    "privacy_policy": {
        "label": "Privacy Policy",
        "description": "Privacy statement page",
        "is_singleton": True,
        "output_format": "html",
        "template": "my_site/cms/privacy_policy.html",
        "component": "RichTextPageEditor",
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "title": "Page Title",
                    "maxLength": 200,
                },
                "content": {
                    "type": "string",
                    "title": "Content",
                    "format": "html",
                    "description": "Privacy statement HTML content",
                },
                "meta_description": {
                    "type": "string",
                    "title": "Meta Description",
                    "maxLength": 300,
                },
            },
            "required": ["title", "content"],
        },
    },
    # ===========================================
    # COLLECTION RESOURCES (multiple per language)
    # ===========================================
    "plain_language_summary": {
        "label": "Plain Language Summary",
        "description": "Accessible summaries of scientific content",
        "is_singleton": False,
        "output_format": "html",
        "template": "my_site/cms/plain_language_summary.html",
        "component": "PlainLanguageSummaryEditor",
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "title": "Title",
                    "maxLength": 200,
                },
                "slug": {
                    "type": "string",
                    "title": "URL Slug",
                    "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
                    "maxLength": 200,
                },
                "description": {
                    "type": "string",
                    "title": "Description",
                    "format": "html",
                    "description": "Main content (WYSIWYG)",
                },
                "image_url": {
                    "type": "string",
                    "format": "uri",
                    "title": "Featured Image URL",
                },
                "excerpt": {
                    "type": "string",
                    "title": "Excerpt",
                    "maxLength": 500,
                    "description": "Short summary for listings",
                },
            },
            "required": ["title", "slug", "description"],
        },
    },
    "static_page": {
        "label": "Static Page",
        "description": "Generic static content pages",
        "is_singleton": False,
        "output_format": "html",
        "template": "my_site/cms/static_page.html",
        "component": "RichTextPageEditor",
        "schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "title": "Page Title",
                    "maxLength": 200,
                },
                "slug": {
                    "type": "string",
                    "title": "URL Slug",
                    "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
                    "maxLength": 200,
                },
                "content": {
                    "type": "string",
                    "title": "Content",
                    "format": "html",
                },
                "meta_title": {
                    "type": "string",
                    "title": "Meta Title",
                    "maxLength": 100,
                },
                "meta_description": {
                    "type": "string",
                    "title": "Meta Description",
                    "maxLength": 300,
                },
            },
            "required": ["title", "slug", "content"],
        },
    },
}


def get_resource(resource_type: str) -> dict:
    """Get resource definition by type.

    Args:
        resource_type: Resource type identifier

    Returns:
        Resource definition dict

    Raises:
        ValueError: If resource type not found
    """
    if resource_type not in CMS_RESOURCES:
        raise ValueError(f"Unknown resource type: {resource_type}")
    return CMS_RESOURCES[resource_type]


def get_all_resources() -> dict:
    """Get all resource definitions.

    Returns:
        Dictionary of all resources with their definitions
    """
    return CMS_RESOURCES


def get_resource_list() -> list:
    """Get list of resources with basic info for UI.

    Returns:
        List of resource info dicts
    """
    return [
        {
            "type": key,
            "label": value["label"],
            "description": value["description"],
            "is_singleton": value["is_singleton"],
            "output_format": value["output_format"],
            "component": value["component"],
            "schema": value["schema"],
        }
        for key, value in CMS_RESOURCES.items()
    ]


def validate_resource_data(resource_type: str, data: dict) -> tuple:
    """Validate data against resource schema.

    Args:
        resource_type: Resource type identifier
        data: Data to validate

    Returns:
        Tuple of (is_valid, errors)
    """
    import jsonschema
    from jsonschema import Draft7Validator

    resource = get_resource(resource_type)
    schema = resource["schema"]

    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    if errors:
        error_messages = [{"path": list(e.path), "message": e.message} for e in errors]
        return False, error_messages

    return True, []
