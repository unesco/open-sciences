"""Additional views."""

from flask import Blueprint, jsonify, request
from flask.views import MethodView
from invenio_search import current_search_client
from .statistics.statistics import StatisticsView, StatisticsAPIView


class CountriesAPIView(MethodView):
    """API endpoint to get all unique countries with optional search filter."""

    def get(self):
        """Return list of unique countries, optionally filtered by search term."""
        search_term = request.args.get("q", "").lower()

        # Query OpenSearch to get all unique countries using aggregations with size 100
        search_query = {
            "size": 0,  # We don't need the actual documents
            "aggs": {
                "unique_countries": {
                    "terms": {
                        "field": "custom_fields.publication:country",
                        "size": 100,  # Get up to 100 unique countries
                        "order": {"_key": "asc"}  # Sort alphabetically
                    }
                }
            }
        }

        try:
            # Execute search against rdmrecords index
            result = current_search_client.search(
                index="my-site-rdmrecords-records",
                body=search_query
            )

            # Extract unique countries from aggregations
            countries = []
            if "aggregations" in result and "unique_countries" in result["aggregations"]:
                for bucket in result["aggregations"]["unique_countries"]["buckets"]:
                    country_name = bucket["key"]
                    # Filter by search term if provided
                    if not search_term or search_term in country_name.lower():
                        countries.append({
                            "name": country_name,
                            "value": country_name,
                            "text": country_name,
                            "doc_count": bucket["doc_count"]
                        })

            return jsonify({"results": countries})

        except Exception as e:
            return jsonify({"error": str(e), "results": []}), 500


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

    # Countries API endpoint - returns all unique countries with optional search filter
    blueprint.add_url_rule(
        "/data/countries",
        view_func=CountriesAPIView.as_view("countries_api"),
        methods=["GET"],
    )

    return blueprint
