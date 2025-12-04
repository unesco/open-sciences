"""Search API endpoint for advanced filtering."""

from flask import jsonify, request
from flask.views import MethodView
from ..filters import get_filter_backend, FILTER_BACKENDS_REGISTRY


class SearchAPIView(MethodView):
    """
    Generic search API endpoint for advanced search filters.

    URL pattern: /data/search?field=<filter_key>&q=<search_term>

    Query parameters:
        - field (required): The filter field key (e.g., 'country', 'funding', 'year')
        - q (optional): Search term to filter results

    Example requests:
        /data/search?field=country&q=belgium
        /data/search?field=funding&q=national
        /data/search?field=year
    """

    def get(self):
        """Handle GET requests for search filtering."""
        # Get query parameters
        filter_key = request.args.get("field")
        search_term = request.args.get("q", "")
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", 20))
        sort_by = request.args.get("sort", "count")

        # Validate required parameters
        if not filter_key:
            return (
                jsonify(
                    {"error": "Missing required parameter: 'field'", "results": []}
                ),
                400,
            )

        # Get the appropriate filter backend
        filter_backend = get_filter_backend(filter_key)

        if not filter_backend:
            return (
                jsonify(
                    {
                        "error": f"Unknown filter field: '{filter_key}'",
                        "available_fields": list(FILTER_BACKENDS_REGISTRY.keys()),
                        "results": [],
                    }
                ),
                400,
            )

        # Execute the filter and return results
        try:
            result = filter_backend.execute(
                search_term=search_term if search_term else None,
                page=page,
                size=size,
                sort_by=sort_by,
            )

            # Handle both dict and list returns (for backward compatibility)
            if isinstance(result, dict):
                return jsonify(
                    {
                        "field": filter_key,
                        "query": search_term,
                        **result,
                    }
                )
            else:
                # Legacy format
                return jsonify(
                    {
                        "field": filter_key,
                        "query": search_term,
                        "count": len(result),
                        "results": result,
                    }
                )
        except Exception as e:
            return jsonify({"error": str(e), "results": []}), 500
