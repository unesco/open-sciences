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
    from .views import StatisticsView
    from .api import SearchAPIView, StatisticsAPIView

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

    return blueprint
