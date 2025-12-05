"""Administration views for CMS."""

from flask import jsonify, request
from invenio_administration.views.base import AdminView
from invenio_i18n import lazy_gettext as _


class CMSAdminView(AdminView):
    """Custom CMS administration view.

    This view provides the admin interface for managing CMS pages and categories.
    It renders a React-based UI that communicates with the CMS API endpoints.
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
        # Pass API endpoints to the template for the React app
        return self.render(
            title=self.title,
            name=self.name,
            api_config={
                "pages_endpoint": "/api/cms/pages",
                "categories_endpoint": "/api/cms/categories",
            },
        )


class CMSPagesAdminView(AdminView):
    """Administration view for CMS Pages list.

    This is an alternative list-based admin view using InvenioRDM's
    built-in admin list functionality.
    """

    name = "cms-pages"
    category = _("Site management")
    title = _("CMS Pages")
    template = "my_site/administration/cms/pages.html"
    url = "/cms/pages"
    menu_label = _("Pages")
    icon = "file alternate outline"

    # Enable search
    search_enabled = True
    search_api = "/api/cms/pages"

    # Display columns
    display_columns = [
        {"field": "id", "title": "ID", "width": "5%"},
        {"field": "title", "title": "Title", "width": "25%"},
        {"field": "slug", "title": "Slug", "width": "20%"},
        {"field": "lang", "title": "Language", "width": "10%"},
        {"field": "is_published", "title": "Published", "width": "10%"},
        {"field": "updated", "title": "Last Updated", "width": "15%"},
    ]

    # Actions
    item_actions = ["edit", "delete", "publish"]

    def get(self):
        """GET view method."""
        return self.render(
            title=self.title,
            name=self.name,
            display_columns=self.display_columns,
            search_api=self.search_api,
        )


class CMSCategoriesAdminView(AdminView):
    """Administration view for CMS Categories list."""

    name = "cms-categories"
    category = _("Site management")
    title = _("CMS Categories")
    template = "my_site/administration/cms/categories.html"
    url = "/cms/categories"
    menu_label = _("Categories")
    icon = "tags"

    # Enable search
    search_enabled = True
    search_api = "/api/cms/categories"

    # Display columns
    display_columns = [
        {"field": "id", "title": "ID", "width": "10%"},
        {"field": "name", "title": "Name", "width": "25%"},
        {"field": "slug", "title": "Slug", "width": "25%"},
        {"field": "is_active", "title": "Active", "width": "15%"},
        {"field": "sort_order", "title": "Order", "width": "10%"},
    ]

    def get(self):
        """GET view method."""
        return self.render(
            title=self.title,
            name=self.name,
            display_columns=self.display_columns,
            search_api=self.search_api,
        )
