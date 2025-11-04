"""
Record viewer tool for InvenioRDM.

This module provides utilities for viewing record details
in various formats (JSON, formatted text).

Usage:
    python -m src.tools.view --record-id abc-123
    python -m src.tools.view abc-123 --format json
"""

import sys
import logging
import json
import click
from colorama import Fore, Style, init
from typing import Optional, Dict, Any

from src.invenio_client import create_client_from_env

# Initialize colorama
init(autoreset=True)

# Configure logging
logger = logging.getLogger(__name__)


def display_record_formatted(record: Dict[str, Any]) -> None:
    """
    Display record in a human-readable formatted view.

    Args:
        record: Record dictionary
    """
    metadata = record.get("metadata", {})

    print(f"\n{Fore.GREEN}{'='*70}")
    print(f"📄 Record Details")
    print(f"{'='*70}{Style.RESET_ALL}\n")

    # Basic info
    print(f"{Fore.YELLOW}Record ID:{Style.RESET_ALL} {record.get('id', 'N/A')}")
    print(
        f"{Fore.YELLOW}Status:{Style.RESET_ALL} {'Published' if record.get('is_published') else 'Draft'}"
    )
    print(f"{Fore.YELLOW}Created:{Style.RESET_ALL} {record.get('created', 'N/A')}")
    print(f"{Fore.YELLOW}Updated:{Style.RESET_ALL} {record.get('updated', 'N/A')}")

    # DOI if available
    pids = record.get("pids", {})
    if pids.get("doi"):
        doi = pids["doi"].get("identifier", "N/A")
        print(f"{Fore.YELLOW}DOI:{Style.RESET_ALL} {doi}")

    print()

    # Metadata
    print(f"{Fore.CYAN}{'─'*70}")
    print(f"Metadata")
    print(f"{'─'*70}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}Title:{Style.RESET_ALL}")
    print(f"  {metadata.get('title', 'No title')}\n")

    # Creators
    creators = metadata.get("creators", [])
    if creators:
        print(f"{Fore.YELLOW}Creators:{Style.RESET_ALL}")
        for creator in creators:
            person = creator.get("person_or_org", {})
            name = person.get("name", "Unknown")

            # ORCID
            identifiers = person.get("identifiers", [])
            orcid = next(
                (i["identifier"] for i in identifiers if i.get("scheme") == "orcid"),
                None,
            )

            # Affiliations
            affiliations = creator.get("affiliations", [])
            affil_names = [a.get("name", "") for a in affiliations]

            print(f"  - {name}")
            if orcid:
                print(f"    ORCID: {orcid}")
            if affil_names:
                print(f"    Affiliation(s): {', '.join(affil_names)}")
        print()

    # Description
    description = metadata.get("description")
    if description:
        print(f"{Fore.YELLOW}Description:{Style.RESET_ALL}")
        print(f"  {description}\n")

    # Resource type
    resource_type = metadata.get("resource_type", {})
    type_id = resource_type.get("id", "Unknown")
    type_title = resource_type.get("title", {})
    if isinstance(type_title, dict):
        type_display = type_title.get("en", type_id)
    else:
        type_display = type_id
    print(f"{Fore.YELLOW}Resource Type:{Style.RESET_ALL} {type_display}")

    # Dates
    pub_date = metadata.get("publication_date", "N/A")
    print(f"{Fore.YELLOW}Publication Date:{Style.RESET_ALL} {pub_date}")

    # Publisher
    publisher = metadata.get("publisher")
    if publisher:
        print(f"{Fore.YELLOW}Publisher:{Style.RESET_ALL} {publisher}")

    # Version
    version = metadata.get("version")
    if version:
        print(f"{Fore.YELLOW}Version:{Style.RESET_ALL} {version}")

    print()

    # Access
    access = record.get("access", {})
    print(f"{Fore.CYAN}{'─'*70}")
    print(f"Access")
    print(f"{'─'*70}{Style.RESET_ALL}\n")
    print(f"  Record: {access.get('record', 'unknown')}")
    print(f"  Files: {access.get('files', 'unknown')}\n")

    # Files
    files = record.get("files", {})
    if files.get("enabled"):
        entries = files.get("entries", [])
        if entries:
            print(f"{Fore.CYAN}{'─'*70}")
            print(f"Files ({len(entries)})")
            print(f"{'─'*70}{Style.RESET_ALL}\n")

            for entry in entries:
                key = entry.get("key", "unknown")
                size = entry.get("size", 0)
                size_mb = size / (1024 * 1024)
                checksum = (
                    entry.get("checksum", "").split(":")[-1][:8]
                    if entry.get("checksum")
                    else "N/A"
                )

                print(f"  - {key}")
                print(f"    Size: {size_mb:.2f} MB ({size:,} bytes)")
                print(f"    Checksum: {checksum}...")
            print()

    # Links
    links = record.get("links", {})
    if links:
        print(f"{Fore.CYAN}{'─'*70}")
        print(f"Links")
        print(f"{'─'*70}{Style.RESET_ALL}\n")

        if links.get("self_html"):
            print(f"  View: {links['self_html']}")
        if links.get("self"):
            print(f"  API: {links['self']}")
        print()

    print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")


def view_record(
    record_id: str,
    output_format: str = "text",
    verbose: bool = False,
) -> None:
    """
    View record details.

    Args:
        record_id: Record ID to view
        output_format: Output format (text or json)
        verbose: Enable verbose output

    Raises:
        SystemExit: If an error occurs
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        # Create client
        client = create_client_from_env()

        logger.info(f"Fetching record {record_id}")
        print(f"\n{Fore.BLUE}📥 Fetching record {record_id}...{Style.RESET_ALL}")

        # Get record
        record = client.get_record(record_id)

        # Display based on format
        if output_format == "json":
            print(json.dumps(record, indent=2, ensure_ascii=False))
        else:
            display_record_formatted(record)

    except Exception as e:
        logger.error(f"Failed to fetch record: {e}", exc_info=verbose)
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


@click.command()
@click.argument("record_id")
@click.option(
    "--format",
    "output_format",
    default="text",
    type=click.Choice(["text", "json"]),
    help="Output format: text (default) or json",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(record_id: str, output_format: str, verbose: bool):
    """
    View InvenioRDM record details.

    RECORD_ID: The ID of the record to view

    Examples:

    \b
    # View record in formatted text
    python -m src.tools.view abc-123

    \b
    # View record as JSON
    python -m src.tools.view abc-123 --format json

    \b
    # View with verbose output
    python -m src.tools.view abc-123 --verbose
    """
    view_record(
        record_id=record_id,
        output_format=output_format,
        verbose=verbose,
    )


if __name__ == "__main__":
    main()
