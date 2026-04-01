"""Patch Affiliation Regions API endpoint.

Runs the affiliation region patch to populate publication:affiliation_region
on existing records by deriving regions from publication:country.

- POST /data/patch-regions - Trigger the patch (optional ?dry_run=true)
- GET  /data/patch-regions - Check patch status
"""

import threading
from datetime import datetime, timezone

from flask import current_app, jsonify, request
from flask.views import MethodView
from invenio_administration.permissions import administration_permission

_patch_status = {
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "message": "",
}
_status_lock = threading.Lock()


def _run_patch(app, dry_run=False):
    """Run the patch_affiliation_region script in a background thread."""
    with app.app_context():
        try:
            app.logger.info("PatchRegions: Starting patch_affiliation_region...")

            from invenio_oauth2server.models import Token

            # Get admin token for API calls
            token = Token.query.first()
            if not token:
                with _status_lock:
                    _patch_status["status"] = "failed"
                    _patch_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                    _patch_status["message"] = "No API token found. Create one via admin panel."
                return

            base_url = app.config.get("SITE_UI_URL", "https://127.0.0.1:5000")

            from my_site.tools.patch_affiliation_region import patch_records
            summary = patch_records(base_url, token.access_token, dry_run=dry_run)

            with _status_lock:
                _patch_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                _patch_status["status"] = "completed"
                _patch_status["message"] = summary
                app.logger.info("PatchRegions: completed. %s", summary)
        except Exception as exc:
            with _status_lock:
                _patch_status["status"] = "failed"
                _patch_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                _patch_status["message"] = f"Unexpected error: {exc}"
            app.logger.exception("PatchRegions: unexpected error: %s", exc)


class PatchRegionsAPIView(MethodView):
    """API endpoint to trigger and monitor affiliation region patching."""

    def get(self):
        """Check the current patch status."""
        if not administration_permission.can():
            return jsonify({"error": "Permission denied"}), 403

        with _status_lock:
            return jsonify(dict(_patch_status)), 200

    def post(self):
        """Trigger the affiliation region patch.

        Query params:
            dry_run: if 'true', show what would change without modifying.

        Returns:
            202 Accepted, or 409 if already running.
        """
        if not administration_permission.can():
            return jsonify({"error": "Permission denied"}), 403

        dry_run = request.args.get("dry_run", "false").lower() == "true"

        with _status_lock:
            if _patch_status["status"] == "running":
                return jsonify({
                    "status": "running",
                    "message": "A patch is already in progress.",
                    "started_at": _patch_status["started_at"],
                }), 409

            _patch_status["status"] = "running"
            _patch_status["started_at"] = datetime.now(timezone.utc).isoformat()
            _patch_status["finished_at"] = None
            mode = "dry-run" if dry_run else "live"
            _patch_status["message"] = f"Patch process is running ({mode} mode)..."

        app = current_app._get_current_object()

        thread = threading.Thread(
            target=_run_patch,
            args=(app, dry_run),
            daemon=True,
        )
        thread.start()

        return jsonify({
            "status": "accepted",
            "message": f"Patch process has been started ({mode} mode). This may take several minutes.",
        }), 202
