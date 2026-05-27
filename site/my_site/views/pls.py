"""PLS detail HTML view (React mount point)."""

from flask import render_template
from flask.views import MethodView


class PLSDetailView(MethodView):
    """Plain Language Summary detail page - renders a React mount template.

    The React app fetches PLS data from Drupal via /cms/api/pls/<nid>.
    """

    def __init__(self):
        self.template = "my_site/pls/index.html"

    def get(self, nid=None, subpath=None):
        return render_template(self.template)
