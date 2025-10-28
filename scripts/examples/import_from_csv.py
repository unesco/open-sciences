#!/usr/bin/env python3
"""
CSV Import Script for InvenioRDM Records

This script imports or updates InvenioRDM records from a CSV file.
It supports:
- Creating new records from CSV data
- Updating existing records by matching identifiers
- Batch processing with error handling
- Progress reporting
- Validation and dry-run mode

CSV Format:
The CSV file should contain the following columns:
- record_id (optional): Existing record ID for updates
- title (required): Record title
- description (optional): Record description
- creators (required): Semicolon-separated list of creators (format: "Given Family; ORCID; Affiliation")
- resource_type (optional): Resource type (default: dataset)
- publication_date (optional): Publication date YYYY-MM-DD (default: today)
- access_record (optional): Record access level (public/restricted, default: public)
- access_files (optional): Files access level (public/restricted, default: public)
- file_paths (optional): Semicolon-separated list of file paths to upload
- publish (optional): Whether to publish immediately (yes/no, default: no)

Example CSV row:
title,description,creators,resource_type,publication_date,access_record,access_files,file_paths,publish
"My Dataset","A sample dataset","John Doe;0000-0001-2345-6789;University;Jane Smith;;Company",dataset,2024-01-15,public,public,/path/to/file1.csv;/path/to/file2.txt,yes
"""

import sys
import os
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invenio_client import create_client_from_env
import click
from colorama import Fore, Style, init

# Initialize colorama for colored output
init()


def parse_creators(creators_str: str) -> List[Dict[str, Any]]:
    """
    Parse creators string into InvenioRDM creator format.

    Format: "Given Family; ORCID; Affiliation | Given2 Family2; ORCID2; Affiliation2"
    ORCID and Affiliation are optional.

    Args:
        creators_str: Semicolon and pipe-separated creator information

    Returns:
        List of creator dictionaries
    """
    creators = []

    # Split by pipe for multiple creators
    creator_groups = creators_str.split("|")

    for group in creator_groups:
        parts = [p.strip() for p in group.split(";")]
        if not parts or not parts[0]:
            continue

        # Parse name (required)
        name_parts = parts[0].strip().split()
        if len(name_parts) < 2:
            print(
                f"{Fore.YELLOW}⚠️  Skipping invalid creator name: {parts[0]}{Style.RESET_ALL}"
            )
            continue

        given_name = " ".join(name_parts[:-1])
        family_name = name_parts[-1]

        creator = {
            "person_or_org": {
                "given_name": given_name,
                "family_name": family_name,
                "type": "personal",
                "name": f"{family_name}, {given_name}",
            }
        }

        # Parse ORCID (optional, second element)
        if len(parts) > 1 and parts[1].strip():
            orcid = parts[1].strip()
            creator["person_or_org"]["identifiers"] = [
                {"identifier": orcid, "scheme": "orcid"}
            ]

        # Parse affiliation (optional, third element)
        if len(parts) > 2 and parts[2].strip():
            creator["affiliations"] = [{"name": parts[2].strip()}]

        creators.append(creator)

    return creators


def parse_file_paths(file_paths_str: str) -> List[str]:
    """
    Parse file paths string into a list of paths.

    Args:
        file_paths_str: Semicolon-separated file paths

    Returns:
        List of file paths
    """
    if not file_paths_str:
        return []

    return [p.strip() for p in file_paths_str.split(";") if p.strip()]


def parse_boolean(value: str, default: bool = False) -> bool:
    """
    Parse a boolean value from string.

    Args:
        value: String value (yes/no, true/false, 1/0)
        default: Default value if empty

    Returns:
        Boolean value
    """
    if not value or not value.strip():
        return default

    value_lower = value.strip().lower()
    return value_lower in ("yes", "true", "1", "y")


def prepare_record_data(
    row: Dict[str, str],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], List[str], bool]:
    """
    Prepare record data from CSV row.

    Args:
        row: CSV row as dictionary

    Returns:
        Tuple of (metadata, access, files_config, file_paths, should_publish)
    """
    # Required fields
    title = row.get("title", "").strip()
    if not title:
        raise ValueError("Title is required")

    creators_str = row.get("creators", "").strip()
    if not creators_str:
        raise ValueError("Creators are required")

    creators = parse_creators(creators_str)
    if not creators:
        raise ValueError("At least one valid creator is required")

    # Optional fields with defaults
    description = row.get("description", "").strip()
    resource_type = row.get("resource_type", "dataset").strip()
    publication_date = row.get("publication_date", "").strip()

    if not publication_date:
        publication_date = datetime.now().strftime("%Y-%m-%d")

    # Prepare metadata
    metadata = {
        "title": title,
        "creators": creators,
        "resource_type": {"id": resource_type},
        "publication_date": publication_date,
    }

    if description:
        metadata["description"] = description

    # Prepare access settings
    access_record = row.get("access_record", "public").strip() or "public"
    access_files = row.get("access_files", "public").strip() or "public"

    access = {"record": access_record, "files": access_files}

    # Parse file paths
    file_paths_str = row.get("file_paths", "").strip()
    file_paths = parse_file_paths(file_paths_str)

    # Files configuration
    files_config = {"enabled": len(file_paths) > 0}

    # Parse publish flag
    should_publish = parse_boolean(row.get("publish", ""), default=False)

    return metadata, access, files_config, file_paths, should_publish


def check_record_exists(client, record_id: str) -> bool:
    """
    Check if a record exists.

    Args:
        client: InvenioRDM client
        record_id: Record identifier

    Returns:
        True if record exists, False otherwise
    """
    try:
        client.get_record(record_id)
        return True
    except Exception:
        return False


def create_or_update_record(
    client, row: Dict[str, str], dry_run: bool = False
) -> Dict[str, Any]:
    """
    Create or update a record from CSV row.

    Args:
        client: InvenioRDM client
        row: CSV row as dictionary
        dry_run: If True, only validate without creating/updating

    Returns:
        Dictionary with operation result
    """
    result = {
        "success": False,
        "operation": None,
        "record_id": None,
        "error": None,
        "title": row.get("title", ""),
    }

    try:
        # Prepare record data
        metadata, access, files_config, file_paths, should_publish = (
            prepare_record_data(row)
        )

        # Check if this is an update or create
        existing_record_id = row.get("record_id", "").strip()

        if dry_run:
            if existing_record_id:
                result["operation"] = "update (dry-run)"
                result["record_id"] = existing_record_id
            else:
                result["operation"] = "create (dry-run)"
            result["success"] = True
            return result

        # Create or update logic
        if existing_record_id and check_record_exists(client, existing_record_id):
            # Update existing record
            result["operation"] = "update"
            result["record_id"] = existing_record_id

            # For updates, we need to create a new draft version
            try:
                draft = client.get_draft(existing_record_id)
            except:
                # If no draft exists, create one from the published record
                # This is a simplified approach - in production you might want to use
                # the edit endpoint to create a new version
                draft = client.create_draft(
                    metadata=metadata, access=access, files=files_config
                )
                result["record_id"] = draft["id"]

            # Update the draft
            draft = client.update_draft(
                result["record_id"],
                metadata=metadata,
                access=access,
                files=files_config,
            )
        else:
            # Create new record
            result["operation"] = "create"
            draft = client.create_draft(
                metadata=metadata, access=access, files=files_config
            )
            result["record_id"] = draft["id"]

        # Upload files if specified
        if file_paths:
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    print(
                        f"{Fore.YELLOW}⚠️  File not found: {file_path}{Style.RESET_ALL}"
                    )
                    continue

                try:
                    client.upload_file_to_draft(result["record_id"], file_path)
                except Exception as e:
                    print(
                        f"{Fore.YELLOW}⚠️  Failed to upload {file_path}: {e}{Style.RESET_ALL}"
                    )

        # Publish if requested
        if should_publish:
            try:
                published = client.publish_draft(result["record_id"])
                result["published"] = True
            except Exception as e:
                result["published"] = False
                result["publish_error"] = str(e)

        result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


@click.command()
@click.argument("csv_file", type=click.Path(exists=True))
@click.option("--delimiter", default=",", help="CSV delimiter (default: comma)")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate CSV without actually creating/updating records",
)
@click.option(
    "--skip-errors", is_flag=True, help="Continue processing even if some records fail"
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed information for each record"
)
def import_csv(
    csv_file: str, delimiter: str, dry_run: bool, skip_errors: bool, verbose: bool
):
    """
    Import or update InvenioRDM records from a CSV file.

    CSV_FILE: Path to the CSV file to import

    The CSV file should contain columns for record metadata.
    See the script docstring for detailed CSV format specification.
    """
    print(f"{Fore.BLUE}📋 InvenioRDM CSV Import Tool{Style.RESET_ALL}")
    print(f"CSV file: {csv_file}")
    print(f"Delimiter: '{delimiter}'")

    if dry_run:
        print(
            f"{Fore.YELLOW}🔍 DRY RUN MODE - No actual changes will be made{Style.RESET_ALL}"
        )

    print("-" * 70)

    # Create client
    try:
        client = create_client_from_env()
        print(f"{Fore.GREEN}✅ Connected to InvenioRDM{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to connect to InvenioRDM: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # Read and process CSV
    records_processed = 0
    records_succeeded = 0
    records_failed = 0
    errors = []

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)

            # Validate required columns
            required_columns = {"title", "creators"}
            if not required_columns.issubset(set(reader.fieldnames or [])):
                missing = required_columns - set(reader.fieldnames or [])
                print(
                    f"{Fore.RED}❌ Missing required columns: {missing}{Style.RESET_ALL}"
                )
                sys.exit(1)

            print(f"\n{Fore.BLUE}Processing records...{Style.RESET_ALL}\n")

            for row_num, row in enumerate(
                reader, start=2
            ):  # Start from 2 (1 is header)
                records_processed += 1

                # Process record
                result = create_or_update_record(client, row, dry_run=dry_run)

                if result["success"]:
                    records_succeeded += 1
                    icon = "✅"
                    color = Fore.GREEN

                    if verbose or dry_run:
                        print(
                            f"{color}{icon} Row {row_num}: {result['operation']} - {result['title']}{Style.RESET_ALL}"
                        )
                        if result.get("record_id"):
                            print(f"   Record ID: {result['record_id']}")
                        if result.get("published"):
                            print(f"   Status: Published")
                        elif result.get("publish_error"):
                            print(
                                f"   {Fore.YELLOW}⚠️  Draft saved but publish failed: {result['publish_error']}{Style.RESET_ALL}"
                            )
                    else:
                        print(
                            f"{color}{icon} Row {row_num}: {result['operation']}{Style.RESET_ALL}"
                        )
                else:
                    records_failed += 1
                    icon = "❌"
                    color = Fore.RED

                    error_msg = f"Row {row_num} ({result['title']}): {result['error']}"
                    errors.append(error_msg)
                    print(f"{color}{icon} {error_msg}{Style.RESET_ALL}")

                    if not skip_errors:
                        print(
                            f"\n{Fore.RED}Stopping due to error. Use --skip-errors to continue on errors.{Style.RESET_ALL}"
                        )
                        break

    except Exception as e:
        print(f"{Fore.RED}❌ Error reading CSV file: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # Print summary
    print("\n" + "=" * 70)
    print(f"{Fore.BLUE}📊 Import Summary{Style.RESET_ALL}")
    print(f"Total records processed: {records_processed}")
    print(f"{Fore.GREEN}✅ Successful: {records_succeeded}{Style.RESET_ALL}")

    if records_failed > 0:
        print(f"{Fore.RED}❌ Failed: {records_failed}{Style.RESET_ALL}")

        if errors:
            print(f"\n{Fore.RED}Errors:{Style.RESET_ALL}")
            for error in errors:
                print(f"  - {error}")

    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if records_failed == 0 else 1)


if __name__ == "__main__":
    import_csv()
