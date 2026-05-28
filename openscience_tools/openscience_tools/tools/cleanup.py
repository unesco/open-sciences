"""
Cleanup tool for InvenioRDM records.

This module provides utilities for deleting records from InvenioRDM,
useful for resetting instances or cleaning up test data.

Usage:
    python -m src.tools.cleanup --confirm
    python -m src.tools.cleanup --dry-run
"""

import sys
import logging
import click
from colorama import Fore, Style, init
from typing import List, Dict, Any, Tuple

from ..invenio_client import InvenioRDMClient

# Initialize colorama
init(autoreset=True)

# Configure logging
logger = logging.getLogger(__name__)


def fetch_all_records(
    client: InvenioRDMClient, batch_size: int = 100, verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Fetch all records from InvenioRDM.

    Args:
        client: InvenioRDM API client
        batch_size: Number of records to fetch per request
        verbose: Show progress information

    Returns:
        List of all record dictionaries

    Raises:
        Exception: If fetching fails
    """
    all_records = []
    page = 1

    while True:
        logger.debug(f"Fetching page {page} (batch size: {batch_size})")
        response = client.search_records(q="", size=batch_size, page=page)
        hits = response.get("hits", {}).get("hits", [])

        if not hits:
            break

        all_records.extend(hits)

        if verbose:
            print(f"{Fore.CYAN}   Fetched page {page}: {len(hits)} records{Style.RESET_ALL}")

        # Check if there are more pages
        total = response.get("hits", {}).get("total", 0)
        if len(all_records) >= total:
            break

        page += 1

    logger.info(f"Fetched {len(all_records)} total records")
    return all_records


def delete_records(
    client: InvenioRDMClient,
    records: List[Dict[str, Any]],
    dry_run: bool = False,
    verbose: bool = False,
) -> Tuple[int, int, List[str]]:
    """
    Delete a list of records.

    Args:
        client: InvenioRDM API client
        records: List of record dictionaries to delete
        dry_run: If True, simulate without actually deleting
        verbose: Show detailed progress

    Returns:
        Tuple of (deleted_count, failed_count, error_messages)
    """
    total = len(records)
    deleted_count = 0
    failed_count = 0
    errors = []

    for idx, record in enumerate(records, 1):
        record_id = record.get("id")
        title = record.get("metadata", {}).get("title", "Untitled")

        try:
            if dry_run:
                if verbose:
                    print(
                        f"{Fore.YELLOW}🔍 Would delete [{idx}/{total}]: "
                        f"{record_id} - {title[:50]}{Style.RESET_ALL}"
                    )
                deleted_count += 1
            else:
                client.delete_record(record_id)
                deleted_count += 1

                if verbose:
                    print(
                        f"{Fore.GREEN}✓ Deleted [{idx}/{total}]: "
                        f"{record_id} - {title[:50]}{Style.RESET_ALL}"
                    )
                elif deleted_count % 10 == 0:
                    print(
                        f"{Fore.GREEN}   Progress: {deleted_count}/{total} deleted...{Style.RESET_ALL}"
                    )

        except Exception as e:
            failed_count += 1
            error_msg = f"Record {record_id} ({title[:30]}): {str(e)}"
            errors.append(error_msg)
            logger.error(f"Failed to delete {record_id}: {e}")

            if verbose:
                print(f"{Fore.RED}✗ Failed [{idx}/{total}]: {error_msg}{Style.RESET_ALL}")

    return deleted_count, failed_count, errors


def cleanup_all_records(
    base_url: str,
    token: str,
    confirm: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    batch_size: int = 100,
) -> None:
    """
    Delete all records from InvenioRDM instance.

    Args:
        base_url: InvenioRDM base URL
        token: API authentication token
        confirm: Skip confirmation prompt
        dry_run: Simulate without actually deleting
        verbose: Show detailed progress
        batch_size: Records to fetch per request

    Raises:
        SystemExit: If an error occurs or user cancels
    """
    # Configure logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Display header
    mode_icon = "🔍" if dry_run else "🗑️"
    mode_text = "DRY RUN MODE" if dry_run else "DELETE MODE"

    print(f"\n{Fore.RED if not dry_run else Fore.YELLOW}{'='*70}")
    print(f"{mode_icon}  InvenioRDM Record Cleanup Tool")
    print(f"{'='*70}{Style.RESET_ALL}\n")

    if dry_run:
        print(f"{Fore.YELLOW}⚠ {mode_text} - No actual deletions will be made{Style.RESET_ALL}\n")

    # Initialize client
    logger.info(f"Connecting to {base_url}")
    client = InvenioRDMClient(base_url=base_url, token=token)

    # Test connection
    try:
        client.search_records(q="", size=1)
        print(f"{Fore.GREEN}✓ Connected to InvenioRDM: {base_url}{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to connect: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # Fetch all records
    try:
        print(f"{Fore.CYAN}📊 Fetching all records...{Style.RESET_ALL}")
        records = fetch_all_records(client, batch_size=batch_size, verbose=verbose)
        total_records = len(records)

        print(f"{Fore.CYAN}📊 Found {total_records} total records{Style.RESET_ALL}\n")

        if total_records == 0:
            print(f"{Fore.GREEN}✓ No records to delete{Style.RESET_ALL}")
            return

    except Exception as e:
        print(f"{Fore.RED}❌ Failed to fetch records: {e}{Style.RESET_ALL}")
        logger.error("Fetch failed", exc_info=True)
        sys.exit(1)

    # Confirmation prompt
    if not confirm and not dry_run:
        print(
            f"{Fore.RED}⚠️  WARNING: This will permanently delete ALL {total_records} records!{Style.RESET_ALL}"
        )
        print(f"{Fore.YELLOW}This action cannot be undone.{Style.RESET_ALL}\n")
        response = input(f"{Fore.YELLOW}Type 'DELETE ALL' to confirm: {Style.RESET_ALL}")

        if response != "DELETE ALL":
            print(f"\n{Fore.YELLOW}❌ Deletion cancelled{Style.RESET_ALL}")
            sys.exit(0)
        print()

    # Delete records
    action = "Simulating deletion of" if dry_run else "Deleting"
    print(f"{Fore.CYAN}{action} {total_records} records...{Style.RESET_ALL}\n")

    deleted_count, failed_count, errors = delete_records(
        client, records, dry_run=dry_run, verbose=verbose
    )

    # Display summary
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"📊 {'Simulation' if dry_run else 'Deletion'} Summary")
    print(f"{'='*70}{Style.RESET_ALL}\n")

    print(f"Total records: {total_records}")
    print(
        f"{Fore.GREEN}✓ {'Would delete' if dry_run else 'Deleted'}: {deleted_count}{Style.RESET_ALL}"
    )

    if failed_count > 0:
        print(f"{Fore.RED}✗ Failed: {failed_count}{Style.RESET_ALL}\n")
        print(f"{Fore.RED}Errors:{Style.RESET_ALL}")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

    if failed_count > 0:
        sys.exit(1)


@click.command()
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt and delete immediately")
@click.option("--dry-run", is_flag=True, help="Simulate deletions without actually deleting")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress information")
@click.option(
    "--batch-size",
    default=100,
    type=int,
    help="Number of records to fetch per request (default: 100)",
)
@click.pass_context
def main(ctx, confirm: bool, dry_run: bool, verbose: bool, batch_size: int):
    """
    Delete all records from InvenioRDM instance.

    This tool is useful for:
    - Resetting a test/development instance
    - Cleaning up before a fresh import
    - Removing all records in bulk

    IMPORTANT: This action is permanent and cannot be undone!

    Examples:

    \b
    # Dry run (see what would be deleted)
    openscience_tools cleanup --dry-run

    \b
    # Delete with confirmation prompt
    openscience_tools cleanup

    \b
    # Delete without confirmation (use with caution!)
    openscience_tools cleanup --confirm

    \b
    # Verbose output
    openscience_tools cleanup --confirm --verbose
    """
    cleanup_all_records(
        base_url=ctx.obj["base_url"],
        token=ctx.obj["token"],
        confirm=confirm,
        dry_run=dry_run,
        verbose=verbose,
        batch_size=batch_size,
    )


if __name__ == "__main__":
    main()
