#!/usr/bin/env python3
"""
Example script: Get statistics from InvenioRDM

This script demonstrates how to:
1. Retrieve various statistics from InvenioRDM
2. Display them in a formatted way
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invenio_client import create_client_from_env
import click
import json
from colorama import Fore, Style, init
from tabulate import tabulate

# Initialize colorama for colored output
init()


@click.command()
@click.option("--record-id", "-r", help="Get statistics for a specific record")
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json"]),
    help="Output format",
)
def get_statistics(record_id, output_format):
    """Get and display InvenioRDM statistics."""

    try:
        # Create client from environment variables
        client = create_client_from_env()

        print(f"{Fore.BLUE}📊 Retrieving InvenioRDM statistics...{Style.RESET_ALL}")

        if record_id:
            print(f"For record: {record_id}")

            # Get statistics for a specific record
            queries = {
                "views": {"stat": "record-view", "params": {"recid": record_id}},
                "downloads": {
                    "stat": "record-download",
                    "params": {"recid": record_id},
                },
            }
        else:
            print("General statistics")

            # Get general statistics
            queries = {
                "total_records": {"stat": "total-records", "params": {}},
                "total_users": {"stat": "total-users", "params": {}},
            }

        print("-" * 50)

        try:
            # Get statistics
            stats = client.get_statistics(queries)

            if output_format == "json":
                print(json.dumps(stats, indent=2))
            else:
                display_stats_table(stats, record_id)

        except Exception as api_error:
            print(
                f"{Fore.YELLOW}⚠️  Statistics API may not be available or configured{Style.RESET_ALL}"
            )
            print(f"Error: {api_error}")

            # Try to get alternative information
            print(
                f"\n{Fore.BLUE}📋 Getting alternative information...{Style.RESET_ALL}"
            )

            if record_id:
                try:
                    record = client.get_record(record_id)
                    display_record_info(record)
                except Exception as e:
                    print(
                        f"{Fore.RED}❌ Could not retrieve record: {e}{Style.RESET_ALL}"
                    )
            else:
                try:
                    # Search for some records to show system activity
                    results = client.search_records(size=5)
                    display_system_info(results)
                except Exception as e:
                    print(
                        f"{Fore.RED}❌ Could not retrieve system info: {e}{Style.RESET_ALL}"
                    )

    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


def display_stats_table(stats, record_id=None):
    """Display statistics in table format."""

    if not stats:
        print(f"{Fore.YELLOW}No statistics data available{Style.RESET_ALL}")
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

    headers = ["Statistic", "Value"]
    print(f"\n{Fore.GREEN}📊 Statistics Results{Style.RESET_ALL}")
    if record_id:
        print(f"For record: {record_id}")
    print()
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def display_record_info(record):
    """Display detailed record information."""
    metadata = record.get("metadata", {})
    stats = record.get("stats", {})

    print(f"\n{Fore.GREEN}📄 Record Information{Style.RESET_ALL}")
    print(f"ID: {record.get('id', 'N/A')}")
    print(f"Title: {metadata.get('title', 'No title')}")
    print(f"Status: {'Published' if record.get('is_published') else 'Draft'}")
    print(f"Created: {record.get('created', 'N/A')}")
    print(f"Updated: {record.get('updated', 'N/A')}")

    if stats:
        print(f"\n{Fore.CYAN}📈 Record Statistics{Style.RESET_ALL}")

        # This version stats
        this_version = stats.get("this_version", {})
        if this_version:
            table_data = [
                ["Views", this_version.get("views", 0)],
                ["Unique Views", this_version.get("unique_views", 0)],
                ["Downloads", this_version.get("downloads", 0)],
                ["Unique Downloads", this_version.get("unique_downloads", 0)],
                ["Data Volume", f"{this_version.get('data_volume', 0)} bytes"],
            ]

            print("This Version:")
            print(tabulate(table_data, headers=["Metric", "Value"], tablefmt="simple"))

        # All versions stats
        all_versions = stats.get("all_versions", {})
        if all_versions and all_versions != this_version:
            table_data = [
                ["Views", all_versions.get("views", 0)],
                ["Unique Views", all_versions.get("unique_views", 0)],
                ["Downloads", all_versions.get("downloads", 0)],
                ["Unique Downloads", all_versions.get("unique_downloads", 0)],
                ["Data Volume", f"{all_versions.get('data_volume', 0)} bytes"],
            ]

            print("\nAll Versions:")
            print(tabulate(table_data, headers=["Metric", "Value"], tablefmt="simple"))


def display_system_info(search_results):
    """Display general system information."""
    hits = search_results.get("hits", {})
    total_records = hits.get("total", 0)
    records = hits.get("hits", [])

    print(f"\n{Fore.GREEN}🏠 System Information{Style.RESET_ALL}")
    print(f"Total Records: {total_records}")
    print(f"Recent Records: {len(records)}")

    if records:
        print(f"\n{Fore.CYAN}📋 Recent Records{Style.RESET_ALL}")
        table_data = []

        for record in records[:5]:  # Show only first 5
            metadata = record.get("metadata", {})
            table_data.append(
                [
                    record.get("id", "N/A"),
                    metadata.get("title", "No title")[:50]
                    + ("..." if len(metadata.get("title", "")) > 50 else ""),
                    record.get("created", "N/A")[:10],  # Just the date part
                ]
            )

        headers = ["ID", "Title", "Created"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))


if __name__ == "__main__":
    get_statistics()
