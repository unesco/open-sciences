# -*- coding: utf-8 -*-
#
# Copyright (C) 2024-2025 UNESCO.
#
# UNESCO Science Portal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Reindex API endpoint.

Triggers rebuilding of OpenSearch indices for RDM records.
- POST /data/reindex - Trigger full reindex
- GET  /data/reindex - Check reindex status
"""

import subprocess
import threading
from datetime import datetime, timezone

from flask import current_app, jsonify
from flask.views import MethodView
from invenio_administration.permissions import administration_permission

# In-memory reindex status (shared across requests within the same process)
_reindex_status = {
    "status": "idle",       # idle | running | completed | failed
    "started_at": None,
    "finished_at": None,
    "message": "",
}
_status_lock = threading.Lock()


def _run_reindex(app):
    """Run the reindex process in a background thread with app context."""
    with app.app_context():
        try:
            # Step 1: Destroy existing indices
            app.logger.info("Reindex: Destroying existing indices...")
            destroy_result = subprocess.run(
                ["invenio", "index", "destroy", "--force", "--yes-i-know"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if destroy_result.returncode != 0:
                app.logger.warning(
                    "Reindex: index destroy failed (rc=%d). stderr: %s",
                    destroy_result.returncode,
                    destroy_result.stderr,
                )

            # Step 2: Create fresh indices
            app.logger.info("Reindex: Creating fresh indices...")
            init_result = subprocess.run(
                ["invenio", "index", "init"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if init_result.returncode != 0:
                app.logger.warning(
                    "Reindex: index init failed (rc=%d). stderr: %s",
                    init_result.returncode,
                    init_result.stderr,
                )

            # Step 3: Initialize custom fields (must be AFTER index init)
            app.logger.info("Reindex: Initializing custom fields...")
            cf_result = subprocess.run(
                ["invenio", "rdm-records", "custom-fields", "init"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if cf_result.returncode != 0:
                cf_failed = True
                app.logger.warning(
                    "Reindex: custom-fields init failed (rc=%d). stderr: %s",
                    cf_result.returncode,
                    cf_result.stderr,
                )
            else:
                cf_failed = False
                app.logger.info("Reindex: custom-fields init completed successfully.")

            # Step 4: Rebuild index
            app.logger.info("Reindex: Rebuilding index...")
            result = subprocess.run(
                ["invenio", "rdm-records", "rebuild-index"],
                input="y\n",
                capture_output=True,
                text=True,
                timeout=600,
            )

            with _status_lock:
                _reindex_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                if result.returncode == 0:
                    _reindex_status["status"] = "completed"
                    if cf_failed:
                        _reindex_status["message"] = (
                            "Custom fields init failed, but index rebuild completed successfully."
                        )
                    else:
                        _reindex_status["message"] = "Reindex completed successfully."
                    app.logger.info("Reindex: rebuild-index completed successfully.")
                else:
                    _reindex_status["status"] = "failed"
                    _reindex_status["message"] = (
                        f"Reindex failed (exit code {result.returncode}). "
                        f"{result.stderr[:500] if result.stderr else ''}"
                    )
                    app.logger.error(
                        "Reindex: rebuild-index failed (rc=%d). stderr: %s",
                        result.returncode,
                        result.stderr,
                    )
        except subprocess.TimeoutExpired:
            with _status_lock:
                _reindex_status["status"] = "failed"
                _reindex_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                _reindex_status["message"] = "Reindex timed out after 600 seconds."
            app.logger.error("Reindex: rebuild-index timed out after 600s.")
        except Exception as exc:
            with _status_lock:
                _reindex_status["status"] = "failed"
                _reindex_status["finished_at"] = datetime.now(timezone.utc).isoformat()
                _reindex_status["message"] = f"Unexpected error: {exc}"
            app.logger.exception("Reindex: unexpected error: %s", exc)


class ReindexAPIView(MethodView):
    """API endpoint to trigger and monitor OpenSearch reindexing."""

    def get(self):
        """Check the current reindex status.

        Returns:
            JSON with status, timestamps, and message.
        """
        if not administration_permission.can():
            return jsonify({"error": "Permission denied"}), 403

        with _status_lock:
            return jsonify(dict(_reindex_status)), 200

    def post(self):
        """Trigger a full reindex of RDM records.

        Requires administration permissions. The reindex runs
        asynchronously in a background thread.

        Returns:
            202 Accepted with a status message, or 409 if already running.
        """
        if not administration_permission.can():
            return jsonify({"error": "Permission denied"}), 403

        with _status_lock:
            if _reindex_status["status"] == "running":
                return jsonify({
                    "status": "running",
                    "message": "A reindex is already in progress.",
                    "started_at": _reindex_status["started_at"],
                }), 409

            _reindex_status["status"] = "running"
            _reindex_status["started_at"] = datetime.now(timezone.utc).isoformat()
            _reindex_status["finished_at"] = None
            _reindex_status["message"] = "Reindex process is running..."

        app = current_app._get_current_object()

        thread = threading.Thread(
            target=_run_reindex,
            args=(app,),
            daemon=True,
        )
        thread.start()

        return jsonify({
            "status": "accepted",
            "message": "Reindex process has been started. This may take several minutes.",
        }), 202
