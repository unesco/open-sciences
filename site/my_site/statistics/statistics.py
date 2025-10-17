"""Statistics views for UNESCO Science Portal."""

import json
from datetime import datetime, timedelta
from flask import render_template, jsonify, request
from flask.views import MethodView
import random


class StatisticsView(MethodView):
    """Statistics dashboard view."""

    def __init__(self):
        self.template = "my_site/statistics.html"

    def get(self):
        """Render statistics dashboard."""
        return render_template(self.template)


class StatisticsAPIView(MethodView):
    """Statistics API endpoint."""

    def get(self):
        """Return statistics data as JSON."""
        # Simulated data - in a real application this would come from the database
        stats_data = self._generate_mock_statistics()
        return jsonify(stats_data)

    def _generate_mock_statistics(self):
        """Generate mock statistics data."""
        # Generate data for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Mock daily records uploaded
        daily_uploads = []
        current_date = start_date
        while current_date <= end_date:
            daily_uploads.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "uploads": random.randint(5, 50),
                    "downloads": random.randint(20, 200),
                }
            )
            current_date += timedelta(days=1)

        # Mock statistics summary
        total_records = random.randint(1500, 3000)
        total_downloads = random.randint(10000, 50000)
        active_users = random.randint(100, 500)

        # Mock top subjects
        subjects = [
            "Environmental Science",
            "Physics",
            "Biology",
            "Chemistry",
            "Computer Science",
            "Mathematics",
            "Engineering",
            "Medicine",
        ]
        top_subjects = [
            {"name": subject, "count": random.randint(50, 300)}
            for subject in random.sample(subjects, 5)
        ]

        # Mock recent activities
        activities = [
            {
                "action": "Record uploaded",
                "title": "Climate Change Impact Study",
                "time": "2 hours ago",
            },
            {
                "action": "Record downloaded",
                "title": "Quantum Computing Research",
                "time": "4 hours ago",
            },
            {
                "action": "Community created",
                "title": "Ocean Research Network",
                "time": "1 day ago",
            },
            {
                "action": "Record published",
                "title": "Renewable Energy Solutions",
                "time": "2 days ago",
            },
            {
                "action": "Record updated",
                "title": "Biodiversity Analysis 2024",
                "time": "3 days ago",
            },
        ]

        return {
            "summary": {
                "total_records": total_records,
                "total_downloads": total_downloads,
                "active_users": active_users,
                "growth_rate": round(random.uniform(5.0, 25.0), 1),
            },
            "daily_activity": daily_uploads,
            "top_subjects": sorted(
                top_subjects, key=lambda x: x["count"], reverse=True
            ),
            "recent_activities": activities,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
