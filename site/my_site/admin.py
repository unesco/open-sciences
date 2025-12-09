"""Administration views for CMS."""

from invenio_administration.views.base import AdminView
from invenio_i18n import lazy_gettext as _


class CMSAdminView(AdminView):
    """Resource-Driven CMS administration view.

    This view provides the admin interface for managing all CMS resource types.
    It renders a React-based UI that communicates with the Resource-Driven CMS API.
    """

    name = "cms"
    category = _("Site management")
    title = _("CMS Administration")
    template = "my_site/administration/cms/index.html"
    url = "/cms"
    menu_label = _("CMS")
    icon = "edit outline"

    def get(self):
        """GET view method - renders the CMS admin interface."""
        return self.render(
            title=self.title,
            name=self.name,
            api_config={
                "endpoint": "/data/cms",
            },
        )
