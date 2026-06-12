"""
Patch script to consolidate standalone resource types into publication-other.

Any published record whose ``metadata.resource_type.id`` is one of
``dataset``, ``software`` or ``other`` is migrated to ``publication-other`` so
the resource-type facet shows a single "Other" entry instead of duplicate /
standalone entries.

The update goes through the REST API (edit draft -> update -> publish) so it
passes service validation and is re-indexed automatically, matching the
approach used by patch_affiliation_region.py.

Usage:
    python -m my_site.tools.migrate_resource_types \
        --url https://localhost:5000 \
        --token <API_TOKEN> \
        [--dry-run]
"""

import argparse
import json
import logging
import time
from collections import Counter

import requests

# Suppress SSL warnings for self-signed certs
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# The Lens importer config maps a raw `publication_type` to an InvenioRDM
# resource_type id. Optional: the tool degrades to TARGET_TYPE without it.
try:
    from openscience_tools.sources.lens.config import LensImportConfig
except Exception:  # pragma: no cover
    LensImportConfig = None

logger = logging.getLogger(__name__)

# Standalone resource_type ids that must be folded into publication-other.
TARGETS = {"dataset", "software", "other"}
TARGET_TYPE = "publication-other"


def derive_target_type(record):
    """Determine the correct resource_type id for a target record.

    Prefer re-deriving from the stored raw Lens record
    (``custom_fields['lens:raw_lens_data']`` -> ``publication_type``) so a
    record mis-stored as "other" becomes its accurate type (e.g.
    publication-article) instead of a blanket publication-other. Falls back to
    TARGET_TYPE when the raw data or the importer config is unavailable.
    """
    if LensImportConfig is None:
        return TARGET_TYPE
    raw = (record.get("custom_fields", {}) or {}).get("lens:raw_lens_data")
    if not raw:
        return TARGET_TYPE
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        pub_type = data.get("publication_type")
        if not pub_type:
            return TARGET_TYPE
        return LensImportConfig.get_resource_type(pub_type)
    except Exception:
        return TARGET_TYPE


class PatchClient:
    """Minimal API client for patching records."""

    def __init__(self, base_url: str, token: str, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.api = f"{self.base_url}/api"
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/vnd.inveniordm.v1+json",
            "Authorization": f"Bearer {token}",
        })
        self.timeout = timeout

    def search_records(self, page: int = 1, size: int = 100) -> dict:
        r = self.session.get(
            f"{self.api}/records",
            params={"page": page, "size": size, "sort": "newest"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def create_draft_from_record(self, record_id: str) -> dict:
        r = self.session.post(
            f"{self.api}/records/{record_id}/draft",
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def update_draft(self, record_id: str, data: dict) -> dict:
        r = self.session.put(
            f"{self.api}/records/{record_id}/draft",
            json=data,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def publish_draft(self, record_id: str) -> dict:
        r = self.session.post(
            f"{self.api}/records/{record_id}/draft/actions/publish",
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def delete_draft(self, record_id: str):
        try:
            self.session.delete(
                f"{self.api}/records/{record_id}/draft",
                timeout=self.timeout,
            )
        except Exception:
            pass


def patch_records(base_url: str, token: str, dry_run: bool = False) -> str:
    """Iterate all records and migrate target resource types.

    Returns a summary string of the results.
    """
    client = PatchClient(base_url, token)

    page = 1
    size = 100
    updated = 0
    skipped = 0
    errors = 0
    error_details = []
    dry_run_details = []  # (record_id, "rt_id -> new_type") for dry-run preview

    while True:
        result = client.search_records(page=page, size=size)
        hits = result.get("hits", {}).get("hits", [])
        total = result.get("hits", {}).get("total", 0)

        if not hits:
            break

        logger.info(f"Page {page}: processing {len(hits)} records (total: {total})")

        for record in hits:
            record_id = record["id"]
            rt_id = (
                record.get("metadata", {})
                .get("resource_type", {})
                .get("id")
            )

            # Skip anything that is not a standalone target type
            if rt_id not in TARGETS:
                skipped += 1
                continue

            # Re-derive the accurate type from the stored raw Lens data when
            # available, falling back to publication-other.
            new_type = derive_target_type(record)

            if dry_run:
                logger.info(
                    f"[DRY RUN] Record {record_id}: would change resource_type "
                    f"{rt_id} -> {new_type}"
                )
                dry_run_details.append((record_id, f"{rt_id} -> {new_type}"))
                updated += 1
                continue

            # Patch: create draft -> update -> publish
            try:
                draft = client.create_draft_from_record(record_id)
                metadata = draft.get("metadata", {})
                metadata["resource_type"] = {"id": new_type}

                # Build the full update payload (API requires full metadata + custom_fields)
                update_data = {
                    "metadata": metadata,
                    "custom_fields": draft.get("custom_fields", {}),
                    "access": draft.get("access", {}),
                    "files": draft.get("files", {}),
                }
                client.update_draft(record_id, update_data)
                client.publish_draft(record_id)

                updated += 1
                logger.info(
                    f"Record {record_id}: resource_type {rt_id} -> {new_type}"
                )

                # Small delay to avoid overwhelming the API
                time.sleep(0.2)

            except Exception as e:
                # Surface the real cause: for HTTP errors the validation
                # detail lives in the response body, not in str(e).
                detail = str(e)
                resp = getattr(e, "response", None)
                if resp is not None:
                    try:
                        detail = f"HTTP {resp.status_code}: {resp.text[:500]}"
                    except Exception:
                        pass
                logger.error(f"Record {record_id} ({rt_id}): failed to patch - {detail}")
                error_details.append(f"{record_id} ({rt_id}): {detail}")
                # Try to clean up the draft
                client.delete_draft(record_id)
                errors += 1

        page += 1

    verb = "Would update" if dry_run else "Updated"
    summary = f"Done. {verb}: {updated}, Skipped: {skipped}, Errors: {errors}"
    if dry_run and dry_run_details:
        # Compact breakdown by transition (scales to any count) + per-record sample.
        transitions = Counter(t for _, t in dry_run_details)
        breakdown = ", ".join(f"{t}: {n}" for t, n in transitions.items())
        sample = "; ".join(f"{rid} ({t})" for rid, t in dry_run_details[:10])
        summary += f" | Breakdown [{breakdown}] | e.g. {sample}"
        if len(dry_run_details) > 10:
            summary += f" (+{len(dry_run_details) - 10} more)"
    if error_details:
        summary += " | First errors: " + " || ".join(error_details[:3])
    logger.info(summary)
    return summary


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Migrate dataset/software/other resource types to publication-other"
    )
    parser.add_argument("--url", required=True, help="InvenioRDM base URL (e.g. https://localhost:5000)")
    parser.add_argument("--token", required=True, help="API Bearer token")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying records")
    args = parser.parse_args()

    patch_records(args.url, args.token, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
