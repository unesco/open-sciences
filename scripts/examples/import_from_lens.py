#!/usr/bin/env python3
"""
Import publications from Lens.org into InvenioRDM.

This script provides a command-line interface to import publication data
from Lens.org JSON exports into InvenioRDM.

Features:
- Import from JSON files exported from Lens.org
- Dry-run mode for validation without creating records
- Skip existing records (by DOI)
- Batch processing with configurable batch size
- Detailed logging and error reporting
- Support for custom fields and rich metadata

Examples:
    # Import all records from JSON file
    python import_from_lens.py --file publications.json

    # Dry run to validate without creating records
    python import_from_lens.py --file publications.json --dry-run

    # Import specific number of records
    python import_from_lens.py --file publications.json --limit 10

    # Custom batch size
    python import_from_lens.py --file publications.json --batch-size 5

    # Don't skip existing records
    python import_from_lens.py --file publications.json --no-skip-existing
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

import click
from colorama import init, Fore, Style

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lens_org import create_importer, create_reader
from src.lens_org.config import LensImportConfig

# Initialize colorama for colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def setup_environment():
    """Check required environment variables."""
    # Environment variables are loaded by docker-compose via env_file
    # No need to load .env manually when running in container

    # Check required environment variables
    required_vars = ["INVENIO_BASE_URL", "INVENIO_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        logger.error(
            "Please set them in scripts/config/.env or as environment variables"
        )
        sys.exit(1)

    logger.info(f"Environment configured: {os.getenv('INVENIO_BASE_URL')}")


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}{title.center(70)}")
    print(f"{Fore.CYAN}{'=' * 70}\n")


def print_success(message: str):
    """Print a success message."""
    print(f"{Fore.GREEN}✓ {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Fore.RED}✗ {message}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{Fore.YELLOW}⚠ {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"{Fore.BLUE}ℹ {message}")


@click.command()
@click.option(
    "--file",
    "-f",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to Lens.org JSON export file",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Validate metadata without creating records",
)
@click.option(
    "--skip-existing/--no-skip-existing",
    default=True,
    help="Skip records with existing DOI in InvenioRDM",
)
@click.option(
    "--batch-size",
    type=int,
    default=None,
    help=f"Number of records per batch (default: {LensImportConfig.BATCH_SIZE})",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Maximum number of records to import (all by default)",
)
@click.option(
    "--offset",
    type=int,
    default=0,
    help="Number of records to skip from start (default: 0)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose logging (DEBUG level)",
)
def main(
    file: Path,
    dry_run: bool,
    skip_existing: bool,
    batch_size: Optional[int],
    limit: Optional[int],
    offset: int,
    verbose: bool,
):
    """
    Import publications from Lens.org JSON export into InvenioRDM.

    This tool maps Lens.org metadata to InvenioRDM format including:
    - Standard bibliographic fields (title, authors, date, etc.)
    - Custom fields (MeSH terms, ASJC subjects, chemicals, etc.)
    - Related identifiers (DOI, PMID, arXiv, etc.)
    - Rich affiliation data with ROR/GRID IDs
    - Citation metrics and counts
    """
    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Setup environment
    setup_environment()

    # Print header
    print_header("LENS.ORG TO INVENIO RDM IMPORTER")

    # Print configuration
    print_info(f"Source file: {file}")
    print_info(f"Mode: {'DRY RUN (validation only)' if dry_run else 'LIVE IMPORT'}")
    print_info(f"Skip existing: {'Yes' if skip_existing else 'No'}")
    if batch_size:
        print_info(f"Batch size: {batch_size}")
    if limit:
        print_info(f"Record limit: {limit}")
    if offset:
        print_info(f"Starting from record: {offset}")
    print()

    try:
        # Create reader and get file info
        reader = create_reader(str(file), source_type="json")
        file_info = reader.get_file_info()

        print_info(f"File size: {file_info['size_mb']:.2f} MB")
        print_info(f"Total records in file: {file_info['record_count']}")
        print()

        # Load records
        all_records = reader.read_records()

        # Apply offset and limit
        if offset > 0:
            all_records = all_records[offset:]
            print_info(f"Skipped first {offset} records")

        if limit:
            all_records = all_records[:limit]
            print_info(f"Limited to {limit} records")

        if not all_records:
            print_warning("No records to import after applying offset/limit")
            return

        print_success(f"Loaded {len(all_records)} records to import\n")

        # Create importer
        importer = create_importer()

        # Import records
        if dry_run:
            print_warning("DRY RUN MODE - No records will be created\n")

        result = importer._import_records(
            all_records,
            dry_run=dry_run,
            skip_existing=skip_existing,
            batch_size=batch_size or LensImportConfig.BATCH_SIZE,
        )

        # Print results
        print_header("IMPORT RESULTS")

        print(f"Total records processed: {Fore.CYAN}{result.total}")
        print(f"Successful imports:      {Fore.GREEN}{result.successful}")
        print(f"Failed imports:          {Fore.RED}{result.failed}")
        print(f"Skipped records:         {Fore.YELLOW}{result.skipped}")
        print()

        # Print errors
        if result.errors:
            print_header("ERRORS")
            for i, error in enumerate(result.errors[:10], 1):
                print(f"{i}. {Fore.RED}{error['lens_id']}")
                print(f"   Type: {error['error_type']}")
                print(f"   Message: {error['message']}")
                print()

            if len(result.errors) > 10:
                print_warning(f"... and {len(result.errors) - 10} more errors")
                print()

        # Print warnings
        if result.warnings:
            print_header("WARNINGS")
            for i, warning in enumerate(result.warnings[:10], 1):
                print(f"{i}. {Fore.YELLOW}{warning}")

            if len(result.warnings) > 10:
                print_warning(f"... and {len(result.warnings) - 10} more warnings")
                print()

        # Print imported record IDs
        if result.imported_ids and not dry_run:
            print_header("IMPORTED RECORDS")
            print_info(f"Created {len(result.imported_ids)} new records:")
            for i, record_id in enumerate(result.imported_ids[:10], 1):
                invenio_url = os.getenv("INVENIO_BASE_URL", "").rstrip("/")
                print(f"{i}. {Fore.GREEN}{invenio_url}/records/{record_id}")

            if len(result.imported_ids) > 10:
                print_info(f"... and {len(result.imported_ids) - 10} more records")
            print()

        # Summary
        if dry_run:
            print_success("Dry run completed - metadata validation successful!")
        else:
            if result.failed == 0:
                print_success("Import completed successfully!")
            elif result.successful > 0:
                print_warning("Import completed with some errors")
            else:
                print_error("Import failed - no records were created")

        # Exit code based on result
        if result.failed > 0 and result.successful == 0:
            sys.exit(1)

    except FileNotFoundError as e:
        print_error(f"File not found: {e}")
        sys.exit(1)

    except Exception as e:
        logger.exception("Unexpected error during import")
        print_error(f"Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
