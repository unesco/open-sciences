#!/usr/bin/env python3
"""
Import records from Zenodo.org into InvenioRDM.

This script fetches metadata and files from Zenodo's public API and imports them
into your InvenioRDM instance, preserving all metadata including creators,
contributors, related identifiers, keywords, and files.

Usage:
    python import_from_zenodo.py --record-id 17462748
    python import_from_zenodo.py --record-id 17462748 --skip-files
    python import_from_zenodo.py --record-id 17462748 --dry-run
    python import_from_zenodo.py --search "climate data" --max-results 5
"""

import sys
import os
import click
import requests
from pathlib import Path
from colorama import Fore, Style, init
import tempfile
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

# Add parent directory to path to import invenio_client
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.invenio_client import InvenioRDMClient

# Initialize colorama
init(autoreset=True)

ZENODO_API_BASE = "https://zenodo.org/api"


def fetch_zenodo_record(record_id: str) -> Dict[str, Any]:
    """
    Fetch a record from Zenodo by ID.

    Args:
        record_id: Zenodo record ID (e.g., "17462748")

    Returns:
        Record metadata dictionary
    """
    url = f"{ZENODO_API_BASE}/records/{record_id}"

    print(f"{Fore.CYAN}📡 Fetching record from Zenodo: {record_id}")
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch Zenodo record: {response.status_code} - {response.text}"
        )

    return response.json()


def search_zenodo_records(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search records on Zenodo.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of record metadata dictionaries
    """
    url = f"{ZENODO_API_BASE}/records"
    params = {"q": query, "size": max_results, "sort": "mostrecent"}

    print(f"{Fore.CYAN}🔍 Searching Zenodo: '{query}' (max {max_results} results)")
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception(
            f"Failed to search Zenodo: {response.status_code} - {response.text}"
        )

    data = response.json()
    hits = data.get("hits", {}).get("hits", [])

    print(f"{Fore.GREEN}✅ Found {len(hits)} records")
    return hits


def download_file(url: str, filename: str, temp_dir: Path) -> Path:
    """
    Download a file from Zenodo.

    Args:
        url: File download URL
        filename: Name to save file as
        temp_dir: Temporary directory to save file

    Returns:
        Path to downloaded file
    """
    # Sanitize filename - replace path separators with underscores
    safe_filename = filename.replace("/", "_").replace("\\", "_")
    file_path = temp_dir / safe_filename

    print(f"{Fore.CYAN}   📥 Downloading: {filename}...", end=" ")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    size_mb = total_size / (1024 * 1024)
    print(f"{Fore.GREEN}✓ ({size_mb:.2f} MB)")

    return file_path


def map_zenodo_to_invenio_metadata(zenodo_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Zenodo metadata format to InvenioRDM format.

    Args:
        zenodo_record: Zenodo record dictionary

    Returns:
        InvenioRDM-compatible metadata dictionary
    """
    zenodo_meta = zenodo_record.get("metadata", {})

    # Map creators
    creators = []
    for creator in zenodo_meta.get("creators", []):
        person = {
            "person_or_org": {
                "type": "personal",
                "name": creator.get("name", ""),
                "family_name": (
                    creator.get("name", "").split(",")[0].strip()
                    if "," in creator.get("name", "")
                    else creator.get("name", "").split()[-1]
                ),
                "given_name": (
                    creator.get("name", "").split(",")[1].strip()
                    if "," in creator.get("name", "")
                    else " ".join(creator.get("name", "").split()[:-1])
                ),
            }
        }

        # Add ORCID if available
        if creator.get("orcid"):
            person["person_or_org"]["identifiers"] = [
                {"scheme": "orcid", "identifier": creator["orcid"]}
            ]

        # Add affiliation if available
        if creator.get("affiliation"):
            person["affiliations"] = [{"name": creator["affiliation"]}]

        creators.append(person)

    # Map contributors
    contributors = []
    for contrib in zenodo_meta.get("contributors", []):
        person = {
            "person_or_org": {
                "type": "personal",
                "name": contrib.get("name", ""),
                "family_name": (
                    contrib.get("name", "").split(",")[0].strip()
                    if "," in contrib.get("name", "")
                    else contrib.get("name", "").split()[-1]
                ),
                "given_name": (
                    contrib.get("name", "").split(",")[1].strip()
                    if "," in contrib.get("name", "")
                    else " ".join(contrib.get("name", "").split()[:-1])
                ),
            },
            "role": {"id": contrib.get("type", "other").lower()},
        }

        # Add ORCID if available
        if contrib.get("orcid"):
            person["person_or_org"]["identifiers"] = [
                {"scheme": "orcid", "identifier": contrib["orcid"]}
            ]

        # Add affiliation if available
        if contrib.get("affiliation"):
            person["affiliations"] = [{"name": contrib["affiliation"]}]

        contributors.append(person)

    # Map related identifiers
    related_identifiers = []
    for rel_id in zenodo_meta.get("related_identifiers", []):
        related_identifiers.append(
            {
                "identifier": rel_id.get("identifier", ""),
                "scheme": rel_id.get("scheme", "url").lower(),
                "relation_type": {"id": rel_id.get("relation", "isrelatedto").lower()},
                "resource_type": (
                    {"id": rel_id.get("resource_type", "other")}
                    if rel_id.get("resource_type")
                    else None
                ),
            }
        )

    # Map resource type
    resource_type_data = zenodo_meta.get("resource_type", {})
    if isinstance(resource_type_data, dict):
        resource_type_id = resource_type_data.get("type", "other")
    else:
        resource_type_id = resource_type_data or "other"

    # Map license
    license_data = zenodo_meta.get("license", {})
    license_id = None
    if isinstance(license_data, dict):
        # Try to map Zenodo license to InvenioRDM
        zenodo_license = license_data.get("id", "")
        if zenodo_license == "mit-license":
            license_id = "mit"
        elif zenodo_license.startswith("cc-"):
            license_id = zenodo_license
        else:
            license_id = "cc-by-4.0"  # Default fallback

    # Build InvenioRDM metadata
    metadata = {
        "title": zenodo_meta.get("title", "Untitled"),
        "publication_date": zenodo_meta.get("publication_date", ""),
        "resource_type": {"id": resource_type_id},
        "creators": creators,
        "description": zenodo_meta.get("description", "")
        .replace("<p>", "")
        .replace("</p>", "\n")
        .replace("<ul>", "")
        .replace("</ul>", "")
        .replace("<li>", "- ")
        .replace("</li>", "\n")
        .replace("<strong>", "**")
        .replace("</strong>", "**")
        .replace("<code>", "`")
        .replace("</code>", "`")
        .strip(),
    }

    # Add optional fields
    if contributors:
        metadata["contributors"] = contributors

    if related_identifiers:
        metadata["related_identifiers"] = related_identifiers

    if zenodo_meta.get("keywords"):
        metadata["subjects"] = [{"subject": kw} for kw in zenodo_meta["keywords"]]

    if zenodo_meta.get("version"):
        metadata["version"] = zenodo_meta["version"]

    if license_id:
        metadata["rights"] = [{"id": license_id}]

    # Add publisher info
    metadata["publisher"] = "Zenodo"

    return {
        "access": {"record": "public", "files": "public"},
        "files": {"enabled": True},
        "metadata": metadata,
    }


def import_zenodo_record(
    client: InvenioRDMClient,
    record_id: str,
    skip_files: bool = False,
    dry_run: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Import a single record from Zenodo to InvenioRDM.

    Args:
        client: InvenioRDM client instance
        record_id: Zenodo record ID
        skip_files: If True, don't download and upload files
        dry_run: If True, only show what would be imported

    Returns:
        Created/updated record data or None if dry-run
    """
    # Fetch Zenodo record
    zenodo_record = fetch_zenodo_record(record_id)

    # Display record info
    title = zenodo_record.get("metadata", {}).get("title", "Untitled")
    doi = zenodo_record.get("doi", "N/A")
    files_count = len(zenodo_record.get("files", []))

    print(f"\n{Fore.YELLOW}{'='*70}")
    print(f"{Fore.CYAN}📄 Record: {title}")
    print(f"{Fore.CYAN}🔗 DOI: {doi}")
    print(f"{Fore.CYAN}📦 Files: {files_count}")
    print(f"{Fore.YELLOW}{'='*70}\n")

    # Map metadata
    invenio_data = map_zenodo_to_invenio_metadata(zenodo_record)

    # If skipping files, disable files in metadata
    if skip_files or files_count == 0:
        invenio_data["files"]["enabled"] = False

    if dry_run:
        print(f"{Fore.YELLOW}🔍 DRY RUN - Would import:")
        print(f"{Fore.CYAN}   Title: {invenio_data['metadata']['title']}")
        print(f"{Fore.CYAN}   Creators: {len(invenio_data['metadata']['creators'])}")
        print(
            f"{Fore.CYAN}   Contributors: {len(invenio_data['metadata'].get('contributors', []))}"
        )
        print(
            f"{Fore.CYAN}   Files: {files_count} {'(would skip)' if skip_files else '(would download)'}"
        )
        return None

    # Create draft
    print(f"{Fore.CYAN}📝 Creating draft record...")
    draft = client.create_draft(
        metadata=invenio_data["metadata"],
        access=invenio_data.get("access"),
        files=invenio_data.get("files"),
    )
    draft_id = draft["id"]
    print(f"{Fore.GREEN}✅ Draft created: {draft_id}")

    # Download and upload files if requested
    if not skip_files and files_count > 0:
        print(f"\n{Fore.CYAN}📦 Processing {files_count} file(s)...")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for file_info in zenodo_record.get("files", []):
                filename = file_info.get("key", "")
                file_url = file_info["links"]["self"]

                try:
                    # Download file
                    local_file = download_file(file_url, filename, temp_path)

                    # Upload to InvenioRDM
                    print(f"{Fore.CYAN}   📤 Uploading to InvenioRDM...", end=" ")
                    client.upload_file_to_draft(draft_id, str(local_file))
                    print(f"{Fore.GREEN}✓")

                except Exception as e:
                    print(f"{Fore.RED}✗ Error: {e}")

    # Publish record
    print(f"\n{Fore.CYAN}🚀 Publishing record...")
    published = client.publish_draft(draft_id)
    record_id_new = published["id"]

    print(f"\n{Fore.GREEN}{'='*70}")
    print(f"{Fore.GREEN}✅ Successfully imported!")
    print(f"{Fore.GREEN}🆔 Record ID: {record_id_new}")
    print(f"{Fore.GREEN}🔗 Original Zenodo DOI: {doi}")
    print(f"{Fore.GREEN}{'='*70}\n")

    return published


@click.command()
@click.option("--record-id", "-r", help="Zenodo record ID to import (e.g., 17462748)")
@click.option("--search", "-s", help="Search Zenodo and import results")
@click.option(
    "--max-results",
    "-m",
    default=5,
    type=int,
    help="Maximum number of search results to import (default: 5)",
)
@click.option(
    "--skip-files",
    is_flag=True,
    help="Skip downloading and uploading files (metadata only)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be imported without actually importing",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(record_id, search, max_results, skip_files, dry_run, verbose):
    """
    Import records from Zenodo.org into InvenioRDM.

    Examples:
        # Import a specific record
        python import_from_zenodo.py --record-id 17462748

        # Import without files (metadata only)
        python import_from_zenodo.py --record-id 17462748 --skip-files

        # Dry run (preview what would be imported)
        python import_from_zenodo.py --record-id 17462748 --dry-run

        # Search and import multiple records
        python import_from_zenodo.py --search "climate data" --max-results 3
    """
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}📥 Zenodo to InvenioRDM Importer")
    print(f"{Fore.CYAN}{'='*70}\n")

    if not record_id and not search:
        print(f"{Fore.RED}❌ Error: Must specify either --record-id or --search")
        print(f"{Fore.YELLOW}💡 Try: python import_from_zenodo.py --help")
        sys.exit(1)

    # Initialize client
    try:
        # Load configuration from environment
        base_url = os.getenv("INVENIO_BASE_URL")
        token = os.getenv("INVENIO_TOKEN")

        if not base_url:
            print(f"{Fore.RED}❌ Error: INVENIO_BASE_URL not set in environment")
            print(f"{Fore.YELLOW}💡 Run: make scripts-setup-env")
            sys.exit(1)

        if not token:
            print(f"{Fore.RED}❌ Error: INVENIO_TOKEN not set in environment")
            print(f"{Fore.YELLOW}💡 Run: make scripts-setup-env")
            sys.exit(1)

        client = InvenioRDMClient(base_url=base_url, token=token)
        print(f"{Fore.GREEN}✅ Connected to InvenioRDM\n")
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to connect to InvenioRDM: {e}")
        sys.exit(1)

    try:
        if record_id:
            # Import single record
            import_zenodo_record(client, record_id, skip_files, dry_run)

        elif search:
            # Search and import multiple records
            records = search_zenodo_records(search, max_results)

            if not records:
                print(f"{Fore.YELLOW}⚠️  No records found")
                return

            print(f"\n{Fore.CYAN}📋 Found {len(records)} records to import\n")

            for i, record in enumerate(records, 1):
                zenodo_id = record.get("id") or record.get("recid")
                print(f"\n{Fore.CYAN}{'='*70}")
                print(f"{Fore.CYAN}Processing record {i}/{len(records)}")
                print(f"{Fore.CYAN}{'='*70}")

                try:
                    import_zenodo_record(client, str(zenodo_id), skip_files, dry_run)
                except Exception as e:
                    print(f"{Fore.RED}❌ Error importing record {zenodo_id}: {e}")
                    if verbose:
                        import traceback

                        traceback.print_exc()
                    continue

            if not dry_run:
                print(f"\n{Fore.GREEN}{'='*70}")
                print(
                    f"{Fore.GREEN}✅ Import complete! Imported {len(records)} records"
                )
                print(f"{Fore.GREEN}{'='*70}\n")

    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
