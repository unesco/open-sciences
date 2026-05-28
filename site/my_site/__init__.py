"""My Site module for InvenioRDM customizations.

This module provides custom views, API endpoints, filters, and services
for the UNESCO Science Portal built on InvenioRDM.

Structure:
    - views/: HTML page rendering (Flask MethodViews)
    - api/: JSON API endpoints (REST endpoints)
    - filters/: Search filter backends (modular filtering system)
    - services/: Business logic layer (reusable across views/APIs)
    - models/: SQLAlchemy database models
    - templates/: Jinja2 templates
    - assets/: Frontend JavaScript and CSS
    - alembic/: Database migrations
"""

__version__ = "1.0.0"

# Import models to ensure they are registered with SQLAlchemy
from .models import CMSContent

# Import error handlers and custom exceptions
from .error_handlers import (
    register_error_handlers, 
    configure_timeout_settings,
    TimeoutError,
    PublicationTimeoutError,
    PayloadTooLargeError,
    JSONParseError
)

__all__ = (
    "CMSContent", 
    "register_error_handlers", 
    "configure_timeout_settings",
    "TimeoutError",
    "PublicationTimeoutError",
    "PayloadTooLargeError",
    "JSONParseError"
)
