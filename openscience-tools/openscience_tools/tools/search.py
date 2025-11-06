"""
Search tool for InvenioRDM records.

This module provides command-line search functionality for InvenioRDM,
allowing users to query and display records in various formats.

Usage:
    python -m src.tools.search --query "climate" --size 10
    python -m src.tools.search -q "test" --detailed
"""

import sys
import logging
import click
from tabulate import tabulate
from colorama import Fore, Style, init
from typing import List, Dict, Any

# Initialize colorama
init(autoreset=True)

# Configure logging
logger = logging.getLogger(__name__)


def display_summary_table(records: List[Dict[str, Any]]) -> None:
    """
    Display records in a summary table format.

    Args:
        records: List of record dictionaries
    """
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
                f"{creator.get('given_name', '')} {creator.get('family_name', '')}".strip(),
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

        # Truncate long fields
        title_display = title[:50] + ("..." if len(title) > 50 else "")
        creator_display = creator_name[:30] + ("..." if len(creator_name) > 30 else "")

        table_data.append(
            [
                record_id,
                title_display,
                creator_display,
                resource_type,
                pub_date,
                access_status,
            ]
        )

    headers = ["ID", "Title", "Creator", "Type", "Date", "Access"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def display_detailed_view(records: List[Dict[str, Any]]) -> None:
    """
    Display records with detailed information.

    Args:
        records: List of record dictionaries
    """
    for i, record in enumerate(records, 1):
        metadata = record.get("metadata", {})

        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"📄 Record {i}: {record.get('id', 'N/A')}")
        print(f"{'='*70}{Style.RESET_ALL}\n")

        # Title
        print(f"{Fore.YELLOW}Title:{Style.RESET_ALL}")
        print(f"  {metadata.get('title', 'No title')}\n")

        # Creators
        creators = metadata.get("creators", [])
        if creators:
            print(f"{Fore.YELLOW}Creators:{Style.RESET_ALL}")
            for creator in creators:
                person = creator.get("person_or_org", {})
                name = person.get(
                    "name",
                    f"{person.get('given_name', '')} {person.get('family_name', '')}".strip(),
                )
                affiliations = creator.get("affiliations", [])
                affil_names = [a.get("name", "") for a in affiliations]
                affil_text = f" ({', '.join(affil_names)})" if affil_names else ""
                print(f"  - {name}{affil_text}")
            print()

        # Description
        description = metadata.get("description")
        if description:
            print(f"{Fore.YELLOW}Description:{Style.RESET_ALL}")
            desc_text = description[:300] + ("..." if len(description) > 300 else "")
            print(f"  {desc_text}\n")

        # Resource type and date
        resource_type = metadata.get("resource_type", {})
        if isinstance(resource_type.get("title"), dict):
            type_name = resource_type["title"].get("en", resource_type.get("id", "Unknown"))
        else:
            type_name = resource_type.get("id", "Unknown")

        print(f"{Fore.YELLOW}Metadata:{Style.RESET_ALL}")
        print(f"  Type: {type_name}")
        print(f"  Publication Date: {metadata.get('publication_date', 'Unknown')}")

        # Publisher
        publisher = metadata.get("publisher")
        if publisher:
            print(f"  Publisher: {publisher}")

        # Version
        version = metadata.get("version")
        if version:
            print(f"  Version: {version}")
        print()

        # Access information
        access = record.get("access", {})
        print(f"{Fore.YELLOW}Access:{Style.RESET_ALL}")
        print(f"  Record: {access.get('record', 'unknown')}")
        print(f"  Files: {access.get('files', 'unknown')}\n")

        # Files information
        files = record.get("files", {})
        if files.get("enabled"):
            entries = files.get("entries", [])
            if entries:
                print(f"{Fore.YELLOW}Files ({len(entries)}):{Style.RESET_ALL}")
                for entry in entries[:5]:  # Show first 5 files
                    key = entry.get("key", "unknown")
                    size = entry.get("size", 0)
                    size_mb = size / (1024 * 1024)
                    print(f"  - {key} ({size_mb:.2f} MB)")
                if len(entries) > 5:
                    print(f"  ... and {len(entries) - 5} more files")
                print()

        # Links
        links = record.get("links", {})
        if links.get("self_html"):
            print(f"{Fore.YELLOW}View:{Style.RESET_ALL}")
            print(f"  {links['self_html']}\n")

        print(f"{Fore.CYAN}{'-'*70}{Style.RESET_ALL}")


def search_records(
    base_url: str,
    token: str,
    query: str = "",
    size: int = 10,
    sort: str = "bestmatch",
    page: int = 1,
    detailed: bool = False,
    verbose: bool = False,
) -> None:
    """
    Search and display InvenioRDM records.

    Args:
        base_url: InvenioRDM base URL
        token: API authentication token
        query: Search query string
        size: Number of results to display
        sort: Sort order (bestmatch, newest, oldest, etc.)
        page: Page number
        detailed: Show detailed information
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
        from ..invenio_client import InvenioRDMClient

        client = InvenioRDMClient(base_url, token)

        # Display search parameters
        print(f"\n{Fore.BLUE}{'='*70}")
        print(f"🔍 Searching InvenioRDM Records")
        print(f"{'='*70}{Style.RESET_ALL}\n")

        if query:
            print(f"Query: '{query}'")
        else:
            print("Query: <all records>")

        print(f"Size: {size}, Sort: {sort}, Page: {page}")
        print(f"View: {'Detailed' if detailed else 'Summary'}")
        print()

        # Execute search
        logger.debug(f"Executing search: q={query}, size={size}, sort={sort}, page={page}")
        results = client.search_records(q=query, size=size, sort=sort, page=page)

        # Extract results
        hits = results.get("hits", {})
        total = hits.get("total", 0)
        records = hits.get("hits", [])

        # Display summary
        print(f"{Fore.GREEN}✓ Found {total} total records{Style.RESET_ALL}")
        print(f"  Showing {len(records)} records on page {page}\n")

        if not records:
            print(f"{Fore.YELLOW}⚠ No records found matching your criteria.{Style.RESET_ALL}")
            return

        # Display records
        if detailed:
            display_detailed_view(records)
        else:
            display_summary_table(records)

        # Display pagination info
        if total > size:
            total_pages = (total + size - 1) // size
            print(f"\n{Fore.CYAN}Page {page} of {total_pages}{Style.RESET_ALL}")
            if page < total_pages:
                print(f"Use --page {page + 1} to see next page")

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=verbose)
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


@click.command()
@click.option(
    "--query",
    "-q",
    default="",
    help="Search query string (leave empty for all records)",
)
@click.option(
    "--size",
    "-s",
    default=10,
    type=int,
    help="Number of results to display (default: 10)",
)
@click.option(
    "--sort",
    default="bestmatch",
    help="Sort order: bestmatch, newest, oldest (default: bestmatch)",
)
@click.option("--page", "-p", default=1, type=int, help="Page number (default: 1)")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed information for each record")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx, query: str, size: int, sort: str, page: int, detailed: bool, verbose: bool):
    """
    Search and display InvenioRDM records.

    Examples:

    \b
    # Search for climate-related records
    openscience-tools search --query "climate"

    \b
    # Show detailed view with 5 results
    openscience-tools search -q "test" -s 5 --detailed

    \b
    # Browse all records, page 2
    openscience-tools search --page 2 --size 20

    \b
    # Sort by newest
    openscience-tools search --sort newest
    """
    search_records(
        base_url=ctx.obj["base_url"],
        token=ctx.obj["token"],
        query=query,
        size=size,
        sort=sort,
        page=page,
        detailed=detailed,
        verbose=verbose,
    )


if __name__ == "__main__":
    main()
