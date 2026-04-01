"""
Patch script to populate publication:affiliation_region on existing records.

Derives affiliation_region from publication:country (already stored in records)
by reverse-mapping country names to ISO codes, then mapping codes to UNESCO regions.

Usage:
    python -m my_site.tools.patch_affiliation_region \
        --url https://localhost:5000 \
        --token <API_TOKEN> \
        [--dry-run]
"""

import argparse
import json
import logging
import os
import sys
import time

import requests

# Suppress SSL warnings for self-signed certs
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Region display names (must match site/my_site/constants.py and the mapper)
REGION_DISPLAY_NAMES = {
    "EUROPE_NORTH_AMERICA": "Europe & North America",
    "ARAB_STATES": "Arab States",
    "AFRICA": "Africa",
    "LATIN_AMERICA_CARIBBEAN": "Latin America & the Caribbean",
    "ASIA_PACIFIC": "Asia & the Pacific",
}


def load_country_code_to_region() -> dict:
    """Load country_code -> region display name mapping from the JSON file."""
    json_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "filters", "data", "country_code_region_mapping.json")
    )

    if not os.path.exists(json_path):
        logger.warning("country_code_region_mapping.json not found at %s, using empty mapping", json_path)
        return {}

    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {
        code: REGION_DISPLAY_NAMES[region_key]
        for code, region_key in raw.items()
        if region_key in REGION_DISPLAY_NAMES
    }


def build_country_name_to_codes() -> dict:
    """Build a mapping of country name (lowercase) -> ISO alpha-2 code using pycountry."""
    try:
        import pycountry
    except ImportError:
        logger.error("pycountry not installed. Run: pip install pycountry")
        return {}

    mapping = {}
    for country in pycountry.countries:
        mapping[country.name.lower()] = country.alpha_2
        if hasattr(country, "common_name"):
            mapping[country.common_name.lower()] = country.alpha_2
        if hasattr(country, "official_name"):
            mapping[country.official_name.lower()] = country.alpha_2
    return mapping


def derive_regions(country_names: list, name_to_code: dict, code_to_region: dict) -> list:
    """Given a list of country names, return sorted list of unique region display names."""
    regions = set()
    for name in country_names:
        code = name_to_code.get(name.lower())
        if code:
            region = code_to_region.get(code)
            if region:
                regions.add(region)
            else:
                logger.debug(f"No region mapping for code {code} (country: {name})")
        else:
            logger.debug(f"Cannot resolve country name to code: {name}")
    return sorted(regions)


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
    """Iterate all records and patch missing affiliation_region.

    Returns a summary string of the results.
    """
    code_to_region = load_country_code_to_region()
    name_to_code = build_country_name_to_codes()
    client = PatchClient(base_url, token)

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
            cf = record.get("custom_fields", {})
            countries = cf.get("publication:country", [])
            existing_regions = cf.get("publication:affiliation_region", [])

            # Skip if regions already set
            if existing_regions:
                skipped += 1
                continue

            # Skip if no country data to derive from
            if not countries:
                skipped += 1
                continue

            # Derive regions
            regions = derive_regions(countries, name_to_code, code_to_region)
            if not regions:
                logger.warning(f"Record {record_id}: could not derive regions from countries {countries}")
                skipped += 1
                continue

            if dry_run:
                logger.info(f"[DRY RUN] Record {record_id}: would set affiliation_region={regions} (from countries={countries})")
                updated += 1
                continue

            # Patch: create draft -> update -> publish
            try:
                draft = client.create_draft_from_record(record_id)
                draft_cf = draft.get("custom_fields", {})
                draft_cf["publication:affiliation_region"] = regions

                # Build the full update payload (API requires full metadata + custom_fields)
                update_data = {
                    "metadata": draft.get("metadata", {}),
                    "custom_fields": draft_cf,
                    "access": draft.get("access", {}),
                    "files": draft.get("files", {}),
                }
                client.update_draft(record_id, update_data)
                client.publish_draft(record_id)

                updated += 1
                logger.info(f"Record {record_id}: patched affiliation_region={regions}")

                # Small delay to avoid overwhelming the API
                time.sleep(0.2)

            except Exception as e:
                logger.error(f"Record {record_id}: failed to patch - {e}")
                # Try to clean up the draft
                client.delete_draft(record_id)
                errors += 1

        page += 1

    summary = f"Done. Updated: {updated}, Skipped: {skipped}, Errors: {errors}"
    logger.info(summary)
    return summary


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    parser = argparse.ArgumentParser(description="Patch affiliation_region on existing InvenioRDM records")
    parser.add_argument("--url", required=True, help="InvenioRDM base URL (e.g. https://localhost:5000)")
    parser.add_argument("--token", required=True, help="API Bearer token")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying records")
    args = parser.parse_args()

    patch_records(args.url, args.token, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
