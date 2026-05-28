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
    "header_frontpage": {
        "label": "Header Frontpage",
        "description": "Homepage header with hero section and search",
        "is_singleton": True,
        "output_format": "json",
        "template": None,
        "component": "HeaderFrontpageEditor",
        "schema": {
            "type": "object",
            "properties": {
                # Logo
                "logo": {
                    "type": "string",
                    "title": "Logo",
                    "description": "Upload a custom logo. Leave empty to use the default UNESCO logo.",
                    "format": "image",
                },
                # Background
                "background_image": {
                    "type": "string",
                    "title": "Background Image",
                    "description": "Upload a background image for the hero section.",
                    "format": "image",
                },
                # Navigation links
                "navigation_links": {
                    "type": "array",
                    "title": "Navigation Links",
                    "description": "Header navigation links (max 5)",
                    "maxItems": 5,
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
                # Hero section
                "title": {
                    "type": "string",
                    "title": "Title",
                    "description": "Main hero title",
                    "maxLength": 200,
                },
                "subtitle": {
                    "type": "string",
                    "title": "Subtitle",
                    "description": "Hero subtitle text",
                    "maxLength": 300,
                },
                # Search
                "search_placeholder": {
                    "type": "string",
                    "title": "Search Placeholder",
                    "description": "Placeholder text in search box",
                    "maxLength": 200,
                },
                "advanced_search_label": {
                    "type": "string",
                    "title": "Advanced Search Label",
                    "description": "Text for advanced search link",
                    "maxLength": 100,
                },
            },
            "required": ["title"],
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
    # ===========================================
    # COLLECTION RESOURCES (multiple per language)
    # ===========================================
    "static_page": {
        "label": "Static Page",
        "description": "Generic static content pages (About, Privacy Policy, etc.)",
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
