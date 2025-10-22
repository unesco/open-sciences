#!/usr/bin/env python3
"""
Example script: Search and list InvenioRDM records

This script demonstrates how to:
1. Connect to InvenioRDM API
2. Search for records
3. Display results in a formatted table
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invenio_client import create_client_from_env
import click
from tabulate import tabulate
from colorama import Fore, Style, init

# Initialize colorama for colored output
init()


@click.command()
@click.option("--query", "-q", default="", help="Search query")
@click.option("--size", "-s", default=10, help="Number of results to display")
@click.option("--sort", default="bestmatch", help="Sort order")
@click.option("--page", "-p", default=1, help="Page number")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed information")
def search_records(query, size, sort, page, detailed):
    """Search and display InvenioRDM records."""

    try:
        # Create client from environment variables
        client = create_client_from_env()

        print(f"{Fore.BLUE}🔍 Searching InvenioRDM records...{Style.RESET_ALL}")
        if query:
            print(f"Query: '{query}'")
        print(f"Size: {size}, Sort: {sort}, Page: {page}")
        print("-" * 50)

        # Search records
        results = client.search_records(q=query, size=size, sort=sort, page=page)

        hits = results.get("hits", {})
        total = hits.get("total", 0)
        records = hits.get("hits", [])

        print(f"{Fore.GREEN}✅ Found {total} total records{Style.RESET_ALL}")
        print(f"Showing {len(records)} records on page {page}")
        print()

        if not records:
            print(
                f"{Fore.YELLOW}No records found matching your criteria.{Style.RESET_ALL}"
            )
            return

        # Prepare data for table display
        if detailed:
            display_detailed_records(records)
        else:
            display_summary_records(records)

    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


def display_summary_records(records):
    """Display records in a summary table format."""
    table_data = []

    for record in records:
        metadata = record.get("metadata", {})

        record_id = record.get("id", "N/A")
        title = metadata.get("title", "No title")

        # Get first creator name
        creators = metadata.get("creators", [])
        if creators:
            creator = creators[0].get("person_or_org", {})
            creator_name = creator.get(
                "name",
                creator.get("given_name", "") + " " + creator.get("family_name", ""),
            )
        else:
            creator_name = "Unknown"

        # Get resource type
        resource_type = metadata.get("resource_type", {}).get("title", {})
        if isinstance(resource_type, dict):
            resource_type = resource_type.get(
                "en", metadata.get("resource_type", {}).get("id", "Unknown")
            )

        # Get publication date
        pub_date = metadata.get("publication_date", "Unknown")

        # Get access status
        access = record.get("access", {})
        access_status = access.get("record", "unknown")

        table_data.append(
            [
                record_id,
                title[:50] + ("..." if len(title) > 50 else ""),
                creator_name[:30] + ("..." if len(creator_name) > 30 else ""),
                resource_type,
                pub_date,
                access_status,
            ]
        )

    headers = ["ID", "Title", "Creator", "Type", "Date", "Access"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def display_detailed_records(records):
    """Display records with detailed information."""
    for i, record in enumerate(records, 1):
        metadata = record.get("metadata", {})

        print(f"{Fore.CYAN}📄 Record {i}: {record.get('id', 'N/A')}{Style.RESET_ALL}")
        print(f"Title: {metadata.get('title', 'No title')}")

        # Creators
        creators = metadata.get("creators", [])
        if creators:
            print("Creators:")
            for creator in creators:
                person = creator.get("person_or_org", {})
                name = person.get(
                    "name",
                    f"{person.get('given_name', '')} {person.get('family_name', '')}",
                )
                affiliations = creator.get("affiliations", [])
                affil_names = [a.get("name", "") for a in affiliations]
                print(
                    f"  - {name}"
                    + (f" ({', '.join(affil_names)})" if affil_names else "")
                )

        # Description
        description = metadata.get("description")
        if description:
            desc_text = description[:200] + ("..." if len(description) > 200 else "")
            print(f"Description: {desc_text}")

        # Resource type and date
        resource_type = metadata.get("resource_type", {})
        if isinstance(resource_type.get("title"), dict):
            type_name = resource_type["title"].get(
                "en", resource_type.get("id", "Unknown")
            )
        else:
            type_name = resource_type.get("id", "Unknown")

        print(f"Type: {type_name}")
        print(f"Publication Date: {metadata.get('publication_date', 'Unknown')}")

        # Access information
        access = record.get("access", {})
        print(
            f"Access: Record={access.get('record', 'unknown')}, Files={access.get('files', 'unknown')}"
        )

        # Files information
        files = record.get("files", {})
        if files.get("enabled") and files.get("entries"):
            print(f"Files: {len(files.get('entries', []))} files available")

        # Links
        links = record.get("links", {})
        if links.get("self_html"):
            print(f"View: {links['self_html']}")

        print("-" * 60)


if __name__ == "__main__":
    search_records()
