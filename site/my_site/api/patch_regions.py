"""Patch Affiliation Regions API endpoint.

Runs the affiliation region patch script to populate publication:affiliation_region
on existing records by deriving regions from publication:country.

- POST /data/patch-regions - Trigger the patch (optional ?dry_run=true)
- GET  /data/patch-regions - Check patch status
"""

import subprocess
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

            cmd = [
                "python", "-m", "openscience_tools.tools.patch_affiliation_region",
                "--url", base_url,
                "--token", token.access_token,
            ]
            if dry_run:
                cmd.append("--dry-run")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,
            )

            with _status_lock:
                _patch_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                if result.returncode == 0:
                    _patch_status["status"] = "completed"
                    # Extract summary from output
                    lines = (result.stdout or "").strip().split("\n")
                    summary = lines[-1] if lines else "Patch completed."
                    _patch_status["message"] = summary
                    app.logger.info("PatchRegions: completed. %s", summary)
                else:
                    _patch_status["status"] = "failed"
                    _patch_status["message"] = (
                        f"Patch failed (exit code {result.returncode}). "
                        f"{result.stderr[:500] if result.stderr else ''}"
                    )
                    app.logger.error(
                        "PatchRegions: failed (rc=%d). stderr: %s",
                        result.returncode,
                        result.stderr,
                    )
        except subprocess.TimeoutExpired:
            with _status_lock:
                _patch_status["status"] = "failed"
                _patch_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                _patch_status["message"] = "Patch timed out after 1800 seconds."
            app.logger.error("PatchRegions: timed out after 1800s.")
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
