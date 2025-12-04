"""Statistics HTML view for rendering dashboard page."""

from flask import render_template
from flask.views import MethodView


class StatisticsView(MethodView):
    """Statistics dashboard view - renders HTML page."""

    def __init__(self):
        self.template = "my_site/statistics.html"

    def get(self):
        """Render statistics dashboard page."""
        return render_template(self.template)
