"""
Delete all records from InvenioRDM instance.

This script fetches all records and deletes them one by one.
Useful for resetting the instance before a fresh import.
"""

import sys
from pathlib import Path
import click
from colorama import Fore, Style, init

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invenio_client import InvenioRDMClient
import os

# Initialize colorama
init(autoreset=True)


@click.command()
@click.option(
    "--confirm",
    is_flag=True,
    help="Skip confirmation prompt and delete all records immediately",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed progress information",
)
def main(confirm: bool, dry_run: bool, verbose: bool):
    """Delete all records from InvenioRDM instance."""

    print(
        f"{Fore.RED}{'🗑️  ' if not dry_run else '🔍 '} InvenioRDM Record Deletion Tool"
    )
    if dry_run:
        print(f"{Fore.YELLOW}🔍 DRY RUN MODE - No actual deletions will be made")
    print("-" * 70)

    # Load configuration
    base_url = os.getenv("INVENIO_BASE_URL", "https://127.0.0.1:5000")
    token = os.getenv("INVENIO_TOKEN")

    if not token:
        print(f"{Fore.RED}❌ Error: INVENIO_TOKEN environment variable not set")
        sys.exit(1)

    # Initialize client
    client = InvenioRDMClient(base_url=base_url, token=token)

    try:
        # Test connection
        client.search_records(q="", size=1)
        print(f"{Fore.GREEN}✅ Connected to InvenioRDM")
        print()
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to connect: {e}")
        sys.exit(1)

    # Fetch all records
    try:
        print(f"{Fore.CYAN}📊 Fetching all records...")

        all_records = []
        page = 1
        size = 100  # Fetch in batches

        while True:
            response = client.search_records(q="", size=size, page=page)
            hits = response.get("hits", {}).get("hits", [])

            if not hits:
                break

            all_records.extend(hits)

            if verbose:
                print(f"{Fore.CYAN}   Fetched page {page}: {len(hits)} records")

            # Check if there are more pages
            total = response.get("hits", {}).get("total", 0)
            if len(all_records) >= total:
                break

            page += 1

        total_records = len(all_records)
        print(f"{Fore.CYAN}📊 Found {total_records} total records")
        print()

        if total_records == 0:
            print(f"{Fore.GREEN}✅ No records to delete")
            return

    except Exception as e:
        print(f"{Fore.RED}❌ Failed to fetch records: {e}")
        sys.exit(1)

    # Confirmation prompt
    if not confirm and not dry_run:
        print(f"{Fore.YELLOW}⚠️  WARNING: This will delete ALL {total_records} records!")
        response = input(f"{Fore.YELLOW}Type 'DELETE ALL' to confirm: ")
        if response != "DELETE ALL":
            print(f"{Fore.YELLOW}❌ Deletion cancelled")
            sys.exit(0)
        print()

    # Delete records
    print(
        f"{Fore.CYAN}{'Simulating deletion of' if dry_run else 'Deleting'} {total_records} records..."
    )
    print()

    deleted_count = 0
    failed_count = 0
    errors = []

    for idx, record in enumerate(all_records, 1):
        record_id = record.get("id")
        title = record.get("metadata", {}).get("title", "Untitled")

        try:
            if dry_run:
                if verbose:
                    print(
                        f"{Fore.YELLOW}🔍 Would delete [{idx}/{total_records}]: {record_id} - {title}"
                    )
                deleted_count += 1
            else:
                client.delete_record(record_id)
                deleted_count += 1

                if verbose:
                    print(
                        f"{Fore.GREEN}✅ Deleted [{idx}/{total_records}]: {record_id} - {title}"
                    )
                elif deleted_count % 10 == 0:
                    print(
                        f"{Fore.GREEN}   Progress: {deleted_count}/{total_records} deleted..."
                    )

        except Exception as e:
            failed_count += 1
            error_msg = f"Record {record_id} ({title}): {str(e)}"
            errors.append(error_msg)

            if verbose:
                print(f"{Fore.RED}❌ Failed [{idx}/{total_records}]: {error_msg}")

    # Summary
    print()
    print("=" * 70)
    print(f"{Fore.CYAN}📊 {'Simulation' if dry_run else 'Deletion'} Summary")
    print(f"{Fore.GREEN}✅ {'Would delete' if dry_run else 'Deleted'}: {deleted_count}")

    if failed_count > 0:
        print(f"{Fore.RED}❌ Failed: {failed_count}")
        print()
        print(f"{Fore.RED}Errors:")
        for error in errors:
            print(f"  - {error}")

    print("=" * 70)

    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
