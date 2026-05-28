"""Views package for HTML page rendering."""

from .cms import CMSPageView
from .statistics import StatisticsView

__all__ = ["StatisticsView", "CMSPageView"]
