"""Update Custom Fields API endpoint.

Re-derives custom fields on existing records from their stored data
(metadata + custom_fields). No external source file needed.

- POST /data/update-fields - Trigger update (optional ?fields=field1,field2)
- GET  /data/update-fields - Check update status
"""

import threading
from datetime import datetime, timezone

from flask import current_app, jsonify, request
from flask.views import MethodView
from invenio_administration.permissions import administration_permission

_update_status = {
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "message": "",
}
_status_lock = threading.Lock()


def _run_update(app, only_fields=None):
    """Run the update_custom_fields in a background thread."""
    with app.app_context():
        try:
            app.logger.info("UpdateFields: Starting custom fields update...")

            from invenio_oauth2server.models import Token

            token = Token.query.first()
            if not token:
                with _status_lock:
                    _update_status["status"] = "failed"
                    _update_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                    _update_status["message"] = "No API token found. Create one via admin panel."
                return

            base_url = app.config.get("SITE_UI_URL", "https://127.0.0.1:5000")

            from my_site.tools.update_custom_fields import update_records
            summary = update_records(
                base_url,
                token.access_token,
                dry_run=False,
                only_fields=only_fields,
            )

            with _status_lock:
                _update_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                _update_status["status"] = "completed"
                _update_status["message"] = summary
                app.logger.info("UpdateFields: completed. %s", summary)

        except Exception as exc:
            with _status_lock:
                _update_status["status"] = "failed"
                _update_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                _update_status["message"] = f"Unexpected error: {exc}"
            app.logger.exception("UpdateFields: unexpected error: %s", exc)


class UpdateFieldsAPIView(MethodView):
    """API endpoint to trigger and monitor custom fields update."""

    def get(self):
        """Check the current update status."""
        if not administration_permission.can():
            return jsonify({"error": "Permission denied"}), 403

        with _status_lock:
            return jsonify(dict(_update_status)), 200

    def post(self):
        """Trigger the custom fields update.

        Query params:
            fields: comma-separated list of field keys to update (optional)

        Returns:
            202 Accepted, or 409 if already running.
        """
        if not administration_permission.can():
            return jsonify({"error": "Permission denied"}), 403

        fields_param = request.args.get("fields", "")
        only_fields = [f.strip() for f in fields_param.split(",") if f.strip()] or None

        with _status_lock:
            if _update_status["status"] == "running":
                return jsonify({
                    "status": "running",
                    "message": "An update is already in progress.",
                    "started_at": _update_status["started_at"],
                }), 409

            _update_status["status"] = "running"
            _update_status["started_at"] = datetime.now(timezone.utc).isoformat()
            _update_status["finished_at"] = None
            fields_desc = ", ".join(only_fields) if only_fields else "all"
            _update_status["message"] = f"Updating custom fields ({fields_desc})..."

        app = current_app._get_current_object()

        thread = threading.Thread(
            target=_run_update,
            args=(app, only_fields),
            daemon=True,
        )
        thread.start()

        return jsonify({
            "status": "running",
            "message": _update_status["message"],
            "started_at": _update_status["started_at"],
        }), 202
