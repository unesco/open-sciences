"""Administration views for CMS."""

from invenio_administration.views.base import AdminView
from invenio_i18n import lazy_gettext as _


class CMSAdminView(AdminView):
    """Custom CMS administration view."""

    name = "cms"
    category = _("Site management")
    title = _("CMS Administration")
    template = "my_site/administration/cms/index.html"
    url = "/cms"
    menu_label = _("CMS")
    icon = "edit outline"

    def get(self):
        """GET view method."""
        return self.render(title=self.title, name=self.name)
