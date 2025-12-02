"""Additional views."""

from flask import Blueprint
from .statistics.statistics import StatisticsView, StatisticsAPIView
from .api import SearchAPIView


#
# Registration
#
def create_blueprint(app):
    """Register blueprint routes on app."""
    blueprint = Blueprint(
        "my_site",
        __name__,
        template_folder="./templates",
    )

    # Statistics dashboard page
    blueprint.add_url_rule(
        "/statistics",
        view_func=StatisticsView.as_view("statistics_dashboard"),
        methods=["GET"],
    )

    # Statistics API endpoint - using /data/ prefix instead of /api/
    blueprint.add_url_rule(
        "/data/statistics",
        view_func=StatisticsAPIView.as_view("statistics_api"),
        methods=["GET"],
    )

    # Generic search API endpoint for advanced search filters
    # Example: /data/search?field=country&q=belgium
    blueprint.add_url_rule(
        "/data/search",
        view_func=SearchAPIView.as_view("search_api"),
        methods=["GET"],
    )

    return blueprint
