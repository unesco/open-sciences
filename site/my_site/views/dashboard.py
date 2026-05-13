"""Dashboard HTML view for rendering Open Science dashboards page."""

from flask import render_template
from flask.views import MethodView


class DashboardView(MethodView):
    """Open Science dashboards view - renders HTML page."""

    def __init__(self):
        self.template = "my_site/dashboard/index.html"

    def get(self, subpath=None):
        """Render dashboard page. Subpath is handled by client-side router."""
        return render_template(self.template)
