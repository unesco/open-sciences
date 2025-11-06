"""
Statistics tool for InvenioRDM.

This module provides utilities for retrieving and displaying
statistics from InvenioRDM, including record views, downloads,
and system-wide metrics.

Usage:
    python -m src.tools.stats --record-id abc-123
    python -m src.tools.stats --format json
"""

import sys
import logging
import json
import click
from colorama import Fore, Style, init
from tabulate import tabulate
from typing import Dict, Any, Optional

from ..invenio_client import create_client_from_env

# Initialize colorama
init(autoreset=True)

# Configure logging
logger = logging.getLogger(__name__)


def display_stats_table(stats: Dict[str, Any], record_id: Optional[str] = None) -> None:
    """
    Display statistics in table format.

    Args:
        stats: Statistics dictionary
        record_id: Optional record ID for context
    """
    if not stats:
        print(f"{Fore.YELLOW}⚠ No statistics data available{Style.RESET_ALL}")
        return

    table_data = []

    for stat_name, stat_data in stats.items():
        if isinstance(stat_data, dict):
            value = stat_data.get("value", "N/A")
            description = stat_name.replace("_", " ").title()
        else:
            value = stat_data
            description = stat_name.replace("_", " ").title()

        table_data.append([description, value])

    print(f"\n{Fore.GREEN}{'='*70}")
    print(f"📊 Statistics Results")
    if record_id:
        print(f"Record ID: {record_id}")
    print(f"{'='*70}{Style.RESET_ALL}\n")

    headers = ["Statistic", "Value"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def display_record_stats(record: Dict[str, Any]) -> None:
    """
    Display detailed record statistics and information.

    Args:
        record: Record dictionary with metadata and stats
    """
    metadata = record.get("metadata", {})
    stats = record.get("stats", {})

    print(f"\n{Fore.GREEN}{'='*70}")
    print(f"📄 Record Information")
    print(f"{'='*70}{Style.RESET_ALL}\n")

    # Basic info
    print(f"{Fore.YELLOW}Basic Information:{Style.RESET_ALL}")
    print(f"  ID: {record.get('id', 'N/A')}")
    print(f"  Title: {metadata.get('title', 'No title')}")
    print(f"  Status: {'Published' if record.get('is_published') else 'Draft'}")
    print(f"  Created: {record.get('created', 'N/A')}")
    print(f"  Updated: {record.get('updated', 'N/A')}")

    if stats:
        print(f"\n{Fore.YELLOW}Statistics:{Style.RESET_ALL}")

        # This version stats
        this_version = stats.get("this_version", {})
        if this_version:
            views = this_version.get("views", 0)
            unique_views = this_version.get("unique_views", 0)
            downloads = this_version.get("downloads", 0)
            unique_downloads = this_version.get("unique_downloads", 0)
            data_volume = this_version.get("data_volume", 0)

            table_data = [
                ["Views", views],
                ["Unique Views", unique_views],
                ["Downloads", downloads],
                ["Unique Downloads", unique_downloads],
                [
                    "Data Volume",
                    f"{data_volume:,} bytes ({data_volume / (1024**2):.2f} MB)",
                ],
            ]

            print("\n  This Version:")
            print(
                tabulate(
                    table_data,
                    headers=["Metric", "Value"],
                    tablefmt="simple",
                    colalign=("left", "right"),
                )
            )

        # All versions stats
        all_versions = stats.get("all_versions", {})
        if all_versions and all_versions != this_version:
            views = all_versions.get("views", 0)
            unique_views = all_versions.get("unique_views", 0)
            downloads = all_versions.get("downloads", 0)
            unique_downloads = all_versions.get("unique_downloads", 0)
            data_volume = all_versions.get("data_volume", 0)

            table_data = [
                ["Views", views],
                ["Unique Views", unique_views],
                ["Downloads", downloads],
                ["Unique Downloads", unique_downloads],
                [
                    "Data Volume",
                    f"{data_volume:,} bytes ({data_volume / (1024**2):.2f} MB)",
                ],
            ]

            print("\n  All Versions:")
            print(
                tabulate(
                    table_data,
                    headers=["Metric", "Value"],
                    tablefmt="simple",
                    colalign=("left", "right"),
                )
            )
    else:
        print(
            f"\n{Fore.YELLOW}⚠ No statistics available for this record{Style.RESET_ALL}"
        )


def display_system_info(search_results: Dict[str, Any]) -> None:
    """
    Display general system information.

    Args:
        search_results: Search results containing records
    """
    hits = search_results.get("hits", {})
    total_records = hits.get("total", 0)
    records = hits.get("hits", [])

    print(f"\n{Fore.GREEN}{'='*70}")
    print(f"🏠 System Information")
    print(f"{'='*70}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}Overview:{Style.RESET_ALL}")
    print(f"  Total Records: {total_records:,}")
    print(f"  Fetched Records: {len(records)}")

    if records:
        print(f"\n{Fore.YELLOW}Recent Records:{Style.RESET_ALL}\n")
        table_data = []

        for record in records[:10]:  # Show first 10
            metadata = record.get("metadata", {})
            title = metadata.get("title", "No title")
            title_display = title[:60] + ("..." if len(title) > 60 else "")

            # Get creators
            creators = metadata.get("creators", [])
            if creators:
                creator = creators[0].get("person_or_org", {})
                creator_name = creator.get("name", "Unknown")[:25]
            else:
                creator_name = "Unknown"

            table_data.append(
                [
                    record.get("id", "N/A"),
                    title_display,
                    creator_name,
                    record.get("created", "N/A")[:10],  # Just date
                ]
            )

        headers = ["ID", "Title", "Creator", "Created"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))


def get_statistics(
    record_id: Optional[str] = None,
    output_format: str = "table",
    verbose: bool = False,
) -> None:
    """
    Get and display InvenioRDM statistics.

    Args:
        record_id: Optional specific record ID
        output_format: Output format (table or json)
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

        print(f"\n{Fore.BLUE}{'='*70}")
        print(f"📊 InvenioRDM Statistics")
        print(f"{'='*70}{Style.RESET_ALL}\n")

        if record_id:
            print(f"Mode: Record-specific statistics")
            print(f"Record ID: {record_id}\n")
        else:
            print(f"Mode: System-wide statistics\n")

        # Try to get statistics via API
        try:
            if record_id:
                queries = {
                    "views": {"stat": "record-view", "params": {"recid": record_id}},
                    "downloads": {
                        "stat": "record-download",
                        "params": {"recid": record_id},
                    },
                }
            else:
                queries = {
                    "total_records": {"stat": "total-records", "params": {}},
                    "total_users": {"stat": "total-users", "params": {}},
                }

            logger.debug(f"Querying statistics: {queries}")
            stats = client.get_statistics(queries)

            if output_format == "json":
                print(json.dumps(stats, indent=2))
            else:
                display_stats_table(stats, record_id)

        except Exception as api_error:
            logger.warning(f"Statistics API not available: {api_error}")
            print(
                f"{Fore.YELLOW}⚠ Statistics API not available or not configured{Style.RESET_ALL}"
            )
            print(f"   {str(api_error)}\n")

            # Try alternative methods
            print(
                f"{Fore.BLUE}📋 Retrieving alternative information...{Style.RESET_ALL}\n"
            )

            if record_id:
                try:
                    record = client.get_record(record_id)
                    if output_format == "json":
                        print(json.dumps(record, indent=2))
                    else:
                        display_record_stats(record)
                except Exception as e:
                    logger.error(f"Failed to retrieve record: {e}")
                    print(
                        f"{Fore.RED}❌ Could not retrieve record: {e}{Style.RESET_ALL}"
                    )
                    sys.exit(1)
            else:
                try:
                    results = client.search_records(size=10, sort="newest")
                    if output_format == "json":
                        print(json.dumps(results, indent=2))
                    else:
                        display_system_info(results)
                except Exception as e:
                    logger.error(f"Failed to retrieve system info: {e}")
                    print(
                        f"{Fore.RED}❌ Could not retrieve system info: {e}{Style.RESET_ALL}"
                    )
                    sys.exit(1)

    except Exception as e:
        logger.error(f"Statistics retrieval failed: {e}", exc_info=verbose)
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


@click.command()
@click.option("--record-id", "-r", help="Get statistics for a specific record ID")
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json"]),
    help="Output format: table (default) or json",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(record_id: Optional[str], output_format: str, verbose: bool):
    """
    Get and display InvenioRDM statistics.

    This tool can retrieve:
    - Record-specific statistics (views, downloads)
    - System-wide statistics (total records, users)
    - Alternative information if stats API is unavailable

    Examples:

    \b
    # Get statistics for a specific record
    python -m src.tools.stats --record-id abc-123

    \b
    # Get system-wide statistics
    python -m src.tools.stats

    \b
    # Get output in JSON format
    python -m src.tools.stats -r abc-123 --format json

    \b
    # Verbose output
    python -m src.tools.stats --verbose
    """
    get_statistics(
        record_id=record_id,
        output_format=output_format,
        verbose=verbose,
    )


if __name__ == "__main__":
    main()
