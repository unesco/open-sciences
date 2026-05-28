"""Statistics API endpoint for JSON responses."""

from flask import jsonify
from flask.views import MethodView
from ..services import StatisticsService


class StatisticsAPIView(MethodView):
    """Statistics API endpoint - returns JSON data."""

    def get(self):
        """
        Return statistics data as JSON.

        Response includes:
        - summary: Overall statistics (total records, downloads, users, growth)
        - daily_activity: Last 30 days of upload/download activity
        - top_subjects: Top 5 subjects by record count
        - recent_activities: Latest 5 activities
        - last_updated: Timestamp of data generation
        """
        stats_data = StatisticsService.generate_mock_statistics()
        return jsonify(stats_data)
