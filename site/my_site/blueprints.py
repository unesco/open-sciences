"""Blueprint registration for custom routes."""

from flask import Blueprint, current_app, render_template, request
from flask_login import current_user

from .constants import API_PREFIX


def create_blueprint(app):
    """
    Register blueprint routes on app.

    This function creates and configures the my_site blueprint,
    registering all custom routes for views and API endpoints.

    Args:
        app: Flask application instance

    Returns:
        Configured Blueprint instance
    """
    from .views import StatisticsView, CMSPageView, CmsReactPageView
    from .views.dashboard import DashboardView
    from .views.pls import PLSDetailView
    from .api import (
        ExportAPIView,
        LensExportProxyAPIView,
        PatchRegionsAPIView,
        ReindexAPIView,
        SearchAPIView,
        StatisticsAPIView,
        UpdateFieldsAPIView,
        # Resource-Driven CMS API
        CMSResourcesAPIView,
        CMSResourceDefinitionAPIView,
        CMSContentSearchAPIView,
        CMSContentByTypeAPIView,
        CMSContentBySlugAPIView,
        CMSContentByIdAPIView,
        CMSContentPublishAPIView,
        CMSContentUnpublishAPIView,
        CMSRenderAPIView,
        CMSPublicRenderAPIView,
        CMSSingletonUpsertAPIView,
        CMSUploadAPIView,
        CMSServeUploadedFileView,
    )

    # Register custom error handlers
    from .error_handlers import register_error_handlers, configure_timeout_settings

    register_error_handlers(app)
    configure_timeout_settings(app)

    blueprint = Blueprint(
        "my_site",
        __name__,
        template_folder="./templates",
    )

    # WIP mode: show WIP page only on the frontpage for unauthenticated users
    @blueprint.before_app_request
    def check_wip_mode():
        wip_mode = current_app.config.get("WIP_MODE", False)
        if isinstance(wip_mode, str):
            wip_mode = wip_mode.lower() in ("true", "1", "yes")
        if not wip_mode:
            return None
        if not current_user.is_anonymous:
            return None
        # Only show WIP page on the root/frontpage
        if request.path == "/":
            return render_template("invenio_app_rdm/wip.html")

    # ========================================
    # HTML Views (Page Rendering)
    # ========================================

    # Statistics dashboard page
    blueprint.add_url_rule(
        "/statistics",
        view_func=StatisticsView.as_view("statistics_dashboard"),
        methods=["GET"],
    )

    # CMS Page view - render published content by slug
    blueprint.add_url_rule(
        "/pages/<path:slug>",
        view_func=CMSPageView.as_view("cms_page"),
        methods=["GET"],
    )

    # CMS React page - mount point; page selected client-side via hash (/page#about)
    blueprint.add_url_rule(
        "/page",
        view_func=CmsReactPageView.as_view("cms_react_page"),
        methods=["GET"],
    )


    # Plain Language Summary detail page (React + Drupal API)
    pls_view = PLSDetailView.as_view("pls_detail")
    blueprint.add_url_rule("/pls/<int:nid>", view_func=pls_view, methods=["GET"])
    blueprint.add_url_rule(
        "/pls/<int:nid>/<path:subpath>", view_func=pls_view, methods=["GET"]
    )

    # Open Science dashboards page (catch-all for client-side routing)
    dashboard_view = DashboardView.as_view("dashboard")
    blueprint.add_url_rule(
        "/dashboards",
        view_func=dashboard_view,
        methods=["GET"],
    )
    blueprint.add_url_rule(
        "/dashboards/<path:subpath>",
        view_func=dashboard_view,
        methods=["GET"],
    )

    # ========================================
    # API Endpoints (JSON Responses)
    # ========================================

    # Statistics API endpoint
    blueprint.add_url_rule(
        f"{API_PREFIX}/statistics",
        view_func=StatisticsAPIView.as_view("statistics_api"),
        methods=["GET"],
    )

    # Generic search API endpoint for advanced search filters
    blueprint.add_url_rule(
        f"{API_PREFIX}/search",
        view_func=SearchAPIView.as_view("search_api"),
        methods=["GET"],
    )

    # Export search results as XLSX
    blueprint.add_url_rule(
        f"{API_PREFIX}/export",
        view_func=ExportAPIView.as_view("export_api"),
        methods=["GET"],
    )

    # Lens.org export proxy (bypasses CORS)
    blueprint.add_url_rule(
        f"{API_PREFIX}/lens/export",
        view_func=LensExportProxyAPIView.as_view("lens_export_proxy_api"),
        methods=["GET"],
    )

    # Trigger OpenSearch reindex (admin only)
    blueprint.add_url_rule(
        f"{API_PREFIX}/reindex",
        view_func=ReindexAPIView.as_view("reindex_api"),
        methods=["GET", "POST"],
    )

    # Patch affiliation regions on existing records (admin only)
    blueprint.add_url_rule(
        f"{API_PREFIX}/patch-regions",
        view_func=PatchRegionsAPIView.as_view("patch_regions_api"),
        methods=["GET", "POST"],
    )

    # Update custom fields from Lens source data (admin only)
    blueprint.add_url_rule(
        f"{API_PREFIX}/update-fields",
        view_func=UpdateFieldsAPIView.as_view("update_fields_api"),
        methods=["GET", "POST"],
    )

    # ========================================
    # Resource-Driven CMS API Endpoints
    # ========================================

    # List all available CMS resource types
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/resources",
        view_func=CMSResourcesAPIView.as_view("cms_resources_api"),
        methods=["GET"],
    )

    # Get specific resource type definition
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/resources/<string:resource_type>",
        view_func=CMSResourceDefinitionAPIView.as_view("cms_resource_definition_api"),
        methods=["GET"],
    )

    # Search content across all resource types
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/content",
        view_func=CMSContentSearchAPIView.as_view("cms_content_search_api"),
        methods=["GET"],
    )

    # CMS Content collection for a resource type (list/create)
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/content/<string:resource_type>",
        view_func=CMSContentByTypeAPIView.as_view("cms_content_by_type_api"),
        methods=["GET", "POST"],
    )

    # CMS Content by slug
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/content/<string:resource_type>/slug/<string:slug>",
        view_func=CMSContentBySlugAPIView.as_view("cms_content_by_slug_api"),
        methods=["GET"],
    )

    # CMS Content item by ID
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/content/<string:resource_type>/<int:content_id>",
        view_func=CMSContentByIdAPIView.as_view("cms_content_by_id_api"),
        methods=["GET", "PUT", "DELETE"],
    )

    # CMS Content publish
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/content/<string:resource_type>/<int:content_id>/publish",
        view_func=CMSContentPublishAPIView.as_view("cms_content_publish_api"),
        methods=["POST"],
    )

    # CMS Content unpublish
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/content/<string:resource_type>/<int:content_id>/unpublish",
        view_func=CMSContentUnpublishAPIView.as_view("cms_content_unpublish_api"),
        methods=["POST"],
    )

    # CMS Content render by slug
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/content/<string:resource_type>/<string:slug>/render",
        view_func=CMSRenderAPIView.as_view("cms_render_api"),
        methods=["GET"],
    )

    # CMS Singleton upsert (create or update singleton content)
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/singleton/<string:resource_type>",
        view_func=CMSSingletonUpsertAPIView.as_view("cms_singleton_upsert_api"),
        methods=["PUT"],
    )

    # CMS File upload endpoint
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/upload",
        view_func=CMSUploadAPIView.as_view("cms_upload_api"),
        methods=["POST"],
    )

    # ========================================
    # PUBLIC CMS API (No Authentication Required)
    # ========================================

    # Public render endpoint for templates (footer, header, etc.)
    # This endpoint is used by Jinja templates to fetch CMS content
    # with fallback to fixtures if no DB content exists
    blueprint.add_url_rule(
        f"{API_PREFIX}/cms/public/<string:resource_type>",
        view_func=CMSPublicRenderAPIView.as_view("cms_public_render_api"),
        methods=["GET"],
    )

    # ========================================
    # Serve Uploaded Files
    # ========================================

    # Serve uploaded CMS files (images, etc.)
    blueprint.add_url_rule(
        "/uploads/<path:filepath>",
        view_func=CMSServeUploadedFileView.as_view("cms_serve_uploaded_file"),
        methods=["GET"],
    )

    return blueprint
