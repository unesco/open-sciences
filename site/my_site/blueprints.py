"""Blueprint registration for custom routes."""

from flask import Blueprint

from .constants import API_PREFIX


def create_blueprint(app):
    """
    Register blueprint routes on app.

    This function creates and configures the my_site blueprint,
    registering all custom routes for views and API endpoints.

    Args:
        app: Flask application instance

    Returns:
        Configured Blueprint instance
    """
    from .views import StatisticsView, CMSPageView
    from .api import (
        SearchAPIView,
        StatisticsAPIView,
        CMSPagesAPIView,
        CMSPageAPIView,
        CMSPageBySlugAPIView,
        CMSPagePublishAPIView,
        CMSPageUnpublishAPIView,
        CMSCategoriesAPIView,
        CMSCategoryAPIView,
    )

    blueprint = Blueprint(
        "my_site",
        __name__,
        template_folder="./templates",
    )

    # ========================================
    # HTML Views (Page Rendering)
    # ========================================

    # Statistics dashboard page
    blueprint.add_url_rule(
        "/statistics",
        view_func=StatisticsView.as_view("statistics_dashboard"),
        methods=["GET"],
    )

    # CMS Page view - render published pages by slug
    blueprint.add_url_rule(
        "/pages/<path:slug>",
        view_func=CMSPageView.as_view("cms_page"),
        methods=["GET"],
    )

    # ========================================
    # API Endpoints (JSON Responses)
    # ========================================

    # Statistics API endpoint - using API_PREFIX instead of /api/
    blueprint.add_url_rule(
        f"{API_PREFIX}/statistics",
        view_func=StatisticsAPIView.as_view("statistics_api"),
        methods=["GET"],
    )

    # Generic search API endpoint for advanced search filters
    # Example: f"{API_PREFIX}/search?field=country&q=belgium"
    blueprint.add_url_rule(
        f"{API_PREFIX}/search",
        view_func=SearchAPIView.as_view("search_api"),
        methods=["GET"],
    )

    # ========================================
    # CMS API Endpoints
    # ========================================

    # CMS Pages collection
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/pages",
        view_func=CMSPagesAPIView.as_view("cms_pages_api"),
        methods=["GET", "POST"],
    )

    # CMS Single page by ID
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/pages/<int:id>",
        view_func=CMSPageAPIView.as_view("cms_page_api"),
        methods=["GET", "PUT", "DELETE"],
    )

    # CMS Page by slug
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/pages/by-slug/<path:slug>",
        view_func=CMSPageBySlugAPIView.as_view("cms_page_by_slug_api"),
        methods=["GET"],
    )

    # CMS Page publish/unpublish
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/pages/<int:id>/publish",
        view_func=CMSPagePublishAPIView.as_view("cms_page_publish_api"),
        methods=["POST"],
    )
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/pages/<int:id>/unpublish",
        view_func=CMSPageUnpublishAPIView.as_view("cms_page_unpublish_api"),
        methods=["POST"],
    )

    # CMS Categories collection
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/categories",
        view_func=CMSCategoriesAPIView.as_view("cms_categories_api"),
        methods=["GET", "POST"],
    )

    # CMS Single category by ID
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/categories/<int:id>",
        view_func=CMSCategoryAPIView.as_view("cms_category_api"),
        methods=["GET", "PUT", "DELETE"],
    )

    return blueprint
