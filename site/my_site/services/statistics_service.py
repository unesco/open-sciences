"""Statistics service for UNESCO Science Portal.

This service contains the business logic for generating and aggregating
statistics data. It's separated from views/API to be reusable across
different contexts (web views, API endpoints, CLI commands, etc.).
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any


class StatisticsService:
    """Service for generating and managing statistics data."""

    @staticmethod
    def generate_mock_statistics() -> Dict[str, Any]:
        """
        Generate mock statistics data for demonstration purposes.

        In production, this would query the database for real metrics.

        Returns:
            Dictionary containing statistics summary, daily activity,
            top subjects, and recent activities.
        """
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

    @staticmethod
    def get_summary_stats() -> Dict[str, Any]:
        """
        Get summary statistics only.

        Returns:
            Dictionary with summary statistics (total_records, downloads, users, growth).
        """
        full_stats = StatisticsService.generate_mock_statistics()
        return full_stats["summary"]

    @staticmethod
    def get_daily_activity(days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily activity data for specified number of days.

        Args:
            days: Number of days to retrieve (default: 30)

        Returns:
            List of daily activity records.
        """
        full_stats = StatisticsService.generate_mock_statistics()
        return full_stats["daily_activity"][-days:]

    @staticmethod
    def get_top_subjects(limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top subjects by record count.

        Args:
            limit: Maximum number of subjects to return (default: 5)

        Returns:
            List of top subjects with counts.
        """
        full_stats = StatisticsService.generate_mock_statistics()
        return full_stats["top_subjects"][:limit]
