"""
Update custom fields on existing InvenioRDM records by re-deriving values
from data already stored in each record (metadata + custom_fields).

No external source file needed — iterates all records via the API, computes
new custom field values from existing record data, and patches any that changed.

Use this when you:
- Add a new derived custom field
- Change derivation logic for existing fields
- Need to backfill a field across all records

Usage:
    python -m my_site.tools.update_custom_fields \
        --url https://localhost:5000 \
        --token <API_TOKEN> \
        [--dry-run] \
        [--fields publication:affiliation_region,publication:year]
"""

import argparse
import json
import logging
import os
import re
import time

import requests

# Suppress SSL warnings for self-signed certs
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


# ============================================================
# Derivation functions
#
# Each function takes (metadata, custom_fields) from the existing
# record and returns a dict of custom field key -> value to set.
# Return {} for fields that can't be derived.
#
# To add a new derived field, just add a new function here and
# register it in DERIVATIONS below.
# ============================================================

def derive_affiliation_region(metadata: dict, custom_fields: dict) -> dict:
    """Derive publication:affiliation_region from publication:country."""
    countries = custom_fields.get("publication:country", [])
    if not countries:
        return {}

    from my_site.tools.patch_affiliation_region import (
        load_country_code_to_region,
        build_country_name_to_codes,
        derive_regions,
    )

    code_to_region = load_country_code_to_region()
    name_to_code = build_country_name_to_codes()
    regions = derive_regions(countries, name_to_code, code_to_region)
    if regions:
        return {"publication:affiliation_region": regions}
    return {}


def derive_year(metadata: dict, custom_fields: dict) -> dict:
    """Derive publication:year from metadata.publication_date."""
    pub_date = metadata.get("publication_date", "")
    if pub_date:
        match = re.match(r"^(\d{4})", str(pub_date))
        if match:
            return {"publication:year": match.group(1)}
    return {}


def derive_is_open_access(metadata: dict, custom_fields: dict) -> dict:
    """Derive publication:is_open_access from lens:open_access data."""
    oa_raw = custom_fields.get("lens:open_access", "")
    if not oa_raw:
        return {}
    try:
        oa_data = json.loads(oa_raw) if isinstance(oa_raw, str) else oa_raw
        # If we have open_access data with a colour, it's OA
        if isinstance(oa_data, dict) and oa_data.get("colour"):
            return {"publication:is_open_access": "true"}
    except (json.JSONDecodeError, TypeError):
        pass
    return {}


def derive_open_access_colour(metadata: dict, custom_fields: dict) -> dict:
    """Derive publication:open_access_colour from lens:open_access data."""
    oa_raw = custom_fields.get("lens:open_access", "")
    if not oa_raw:
        return {}
    try:
        oa_data = json.loads(oa_raw) if isinstance(oa_raw, str) else oa_raw
        if isinstance(oa_data, dict):
            colour = oa_data.get("colour")
            if colour:
                return {"publication:open_access_colour": colour}
    except (json.JSONDecodeError, TypeError):
        pass
    return {}


def derive_funding_org(metadata: dict, custom_fields: dict) -> dict:
    """Derive publication:funding_org from metadata.funding."""
    funding = metadata.get("funding", [])
    if not funding:
        return {}
    orgs = []
    for f in funding:
        if isinstance(f, dict):
            funder = f.get("funder", {})
            if isinstance(funder, dict):
                name = funder.get("name")
                if name and name not in orgs:
                    orgs.append(name)
    if orgs:
        return {"publication:funding_org": orgs}
    return {}


def derive_unesco_relation(metadata: dict, custom_fields: dict) -> dict:
    """Derive publication:unesco_relation from metadata (creators, funding, publisher)."""
    UNESCO_PATTERNS = [
        "unesco",
        "united nations educational, scientific and cultural",
        "ictp",
        "international centre for theoretical physics",
    ]

    def matches_unesco(text):
        if not text:
            return False
        text_lower = text.lower()
        return any(pat in text_lower for pat in UNESCO_PATTERNS)

    relations = set()

    # Check funding orgs
    funding = metadata.get("funding", [])
    for f in funding:
        if isinstance(f, dict):
            funder = f.get("funder", {})
            if isinstance(funder, dict) and matches_unesco(funder.get("name", "")):
                relations.add("Funded by UNESCO")
                break

    # Check publisher
    if matches_unesco(metadata.get("publisher", "")):
        relations.add("Published by UNESCO")

    # Check creators for affiliated/collective author
    for creator in metadata.get("creators", []):
        if not isinstance(creator, dict):
            continue
        person = creator.get("person_or_org", {})
        if isinstance(person, dict):
            name = person.get("name", "")
            family = person.get("family_name", "")
            given = person.get("given_name", "")
            if matches_unesco(name) or matches_unesco(family) or matches_unesco(given):
                relations.add("UNESCO Collective Author")
        for aff in creator.get("affiliations", []):
            if isinstance(aff, dict) and matches_unesco(aff.get("name", "")):
                relations.add("UNESCO Affiliated Author")
                break

    if relations:
        return {"publication:unesco_relation": sorted(relations)}
    return {}


# Register all derivation functions.
# Each entry maps a custom field key to the function that derives it.
# A function may derive multiple fields at once.
DERIVATIONS = {
    "publication:affiliation_region": derive_affiliation_region,
    "publication:year": derive_year,
    "publication:is_open_access": derive_is_open_access,
    "publication:open_access_colour": derive_open_access_colour,
    "publication:funding_org": derive_funding_org,
    "publication:unesco_relation": derive_unesco_relation,
}


class UpdateClient:
    """Minimal API client for reading and patching records."""

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


def update_records(
    base_url: str,
    token: str,
    dry_run: bool = False,
    only_fields: list = None,
) -> str:
    """
    Iterate all records and re-derive custom fields from existing data.

    Args:
        base_url: InvenioRDM base URL
        token: API bearer token
        dry_run: If True, show changes without modifying records
        only_fields: If set, only run derivations for these field keys

    Returns:
        Summary string
    """
    client = UpdateClient(base_url, token)

    # Determine which derivation functions to run
    if only_fields:
        derivations = {k: v for k, v in DERIVATIONS.items() if k in only_fields}
        if not derivations:
            return f"No derivation functions found for fields: {only_fields}"
        logger.info(f"Updating fields: {list(derivations.keys())}")
    else:
        derivations = DERIVATIONS
        logger.info(f"Updating all derived fields: {list(derivations.keys())}")

    # Deduplicate functions (one function may handle multiple fields)
    unique_fns = list(dict.fromkeys(derivations.values()))

    page = 1
    size = 100
    updated = 0
    skipped = 0
    errors = 0

    while True:
        result = client.search_records(page=page, size=size)
        hits = result.get("hits", {}).get("hits", [])
        total = result.get("hits", {}).get("total", 0)

        if not hits:
            break

        logger.info(f"Page {page}: processing {len(hits)} records (total: {total})")

        for record in hits:
            record_id = record["id"]
            metadata = record.get("metadata", {})
            existing_cf = record.get("custom_fields", {})

            # Run all selected derivation functions
            new_cf = {}
            for fn in unique_fns:
                try:
                    derived = fn(metadata, existing_cf)
                    new_cf.update(derived)
                except Exception as e:
                    logger.warning(f"Record {record_id}: derivation {fn.__name__} failed: {e}")

            # Filter to only requested fields
            if only_fields:
                new_cf = {k: v for k, v in new_cf.items() if k in only_fields}

            if not new_cf:
                skipped += 1
                continue

            # Check what actually changed
            changes = {}
            for key, new_val in new_cf.items():
                old_val = existing_cf.get(key)
                if old_val != new_val:
                    changes[key] = {"old": old_val, "new": new_val}

            if not changes:
                skipped += 1
                continue

            if dry_run:
                change_keys = list(changes.keys())
                logger.info(f"[DRY RUN] Record {record_id}: would update {change_keys}")
                for k, v in changes.items():
                    logger.info(f"  {k}: {_truncate(v['old'])} -> {_truncate(v['new'])}")
                updated += 1
                continue

            # Patch: create draft -> merge custom fields -> update -> publish
            try:
                draft = client.create_draft_from_record(record_id)
                draft_cf = draft.get("custom_fields", {})
                draft_cf.update(new_cf)

                update_data = {
                    "metadata": draft.get("metadata", {}),
                    "custom_fields": draft_cf,
                    "access": draft.get("access", {}),
                    "files": draft.get("files", {}),
                }
                client.update_draft(record_id, update_data)
                client.publish_draft(record_id)

                updated += 1
                logger.info(f"Record {record_id}: updated {list(changes.keys())}")
                time.sleep(0.2)

            except Exception as e:
                logger.error(f"Record {record_id}: failed to update - {e}")
                client.delete_draft(record_id)
                errors += 1

        page += 1

    summary = f"Done. Updated: {updated}, Skipped: {skipped}, Errors: {errors}"
    logger.info(summary)
    return summary


def _truncate(val, max_len=80):
    """Truncate a value for display."""
    s = str(val)
    return s if len(s) <= max_len else s[:max_len] + "..."


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Update custom fields on existing InvenioRDM records by re-deriving from stored data"
    )
    parser.add_argument("--url", required=True, help="InvenioRDM base URL")
    parser.add_argument("--token", required=True, help="API Bearer token")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without modifying")
    parser.add_argument(
        "--fields",
        help="Comma-separated list of custom field keys to update (e.g. publication:affiliation_region,publication:year). If omitted, updates all derived fields.",
    )
    args = parser.parse_args()

    only_fields = None
    if args.fields:
        only_fields = [f.strip() for f in args.fields.split(",")]

    update_records(args.url, args.token, dry_run=args.dry_run, only_fields=only_fields)


if __name__ == "__main__":
    main()

