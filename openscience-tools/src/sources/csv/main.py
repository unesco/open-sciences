"""
Main entry point for CSV import operations.

This module provides the core import functionality for CSV files,
including CLI argument parsing, environment setup, and import orchestration.

Can be run in multiple ways:
    - As package module: python -m src.sources.csv
    - Direct execution: python src/sources/csv/main.py (for development)
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

import click
from colorama import init, Fore, Style

# Handle both direct execution and package import
if __name__ == "__main__" and __package__ is None:
    # Direct execution: add parent to path and use absolute imports
    script_dir = Path(__file__).parent.parent.parent.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from src.sources.csv.config import CSVImportConfig
    from src.sources.csv.reader import create_reader
    from src.sources.csv.importer import create_importer
else:
    # Package import: use relative imports
    from .config import CSVImportConfig
    from .reader import create_reader
    from .importer import create_importer

# Initialize colorama for colored output
init(autoreset=True)

# Configure logging
logger = logging.getLogger(__name__)


def setup_environment():
    """
    Check required environment variables.

    Raises:
        SystemExit: If required variables are missing
    """
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


def run_import(
    file: Path,
    delimiter: str = CSVImportConfig.DEFAULT_DELIMITER,
    dry_run: bool = False,
    skip_errors: bool = False,
    batch_size: Optional[int] = None,
    verbose: bool = False,
) -> int:
    """
    Run the CSV import process.

    Args:
        file: Path to CSV file
        delimiter: CSV delimiter character
        dry_run: If True, validate without creating records
        skip_errors: If True, continue on errors
        batch_size: Number of records per batch
        verbose: Enable verbose logging

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup environment
    setup_environment()

    # Print header
    print_header("CSV TO INVENIO RDM IMPORTER")

    # Print configuration
    print_info(f"CSV file: {file}")
    print_info(f"Delimiter: '{delimiter}'")
    print_info(f"Mode: {'DRY RUN (validation only)' if dry_run else 'LIVE IMPORT'}")
    print_info(f"Skip errors: {'Yes' if skip_errors else 'No'}")
    if batch_size:
        print_info(f"Batch size: {batch_size}")
    print()

    try:
        # Create reader
        reader = create_reader(str(file), delimiter=delimiter)

        # Validate columns
        validation = reader.validate_columns()
        if not validation["valid"]:
            print_error("CSV validation failed!")
            print_error(f"Missing columns: {', '.join(validation['missing_columns'])}")
            return 1

        print_success("CSV columns validated")

        # Get file info
        file_info = reader.get_file_info()
        print_info(f"File size: {file_info['size_mb']:.2f} MB")
        print_info(f"Total rows in file: {file_info['row_count']}")

        if validation["extra_columns"]:
            print_warning(
                f"Extra columns (will be ignored): {', '.join(validation['extra_columns'])}"
            )
        print()

        # Load records
        records = reader.read_records()
        print_success(f"Loaded {len(records)} records to import\n")

        # Create importer
        importer = create_importer()

        # Import records
        if dry_run:
            print_warning("DRY RUN MODE - No records will be created\n")

        result = importer.import_records(
            records,
            dry_run=dry_run,
            skip_errors=skip_errors,
            batch_size=batch_size or CSVImportConfig.BATCH_SIZE,
        )

        # Print results
        print_header("IMPORT RESULTS")

        print(f"Total records processed: {Fore.CYAN}{result.total}")
        print(f"Successful imports:      {Fore.GREEN}{result.successful}")
        print(f"Failed imports:          {Fore.RED}{result.failed}")
        print(f"Skipped records:         {Fore.YELLOW}{result.skipped}")

        if not dry_run:
            print(f"Created:                 {Fore.GREEN}{result.created}")
            print(f"Updated:                 {Fore.BLUE}{result.updated}")
            print(f"Published:               {Fore.GREEN}{result.published}")
        print()

        # Print errors
        if result.errors:
            print_header("ERRORS")
            for i, error in enumerate(result.errors[:10], 1):
                print(f"{i}. {Fore.RED}Row {error['row']}: {error.get('title', 'N/A')}")
                print(f"   Error: {error['error']}")
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
        if result.record_ids and not dry_run:
            print_header("IMPORTED RECORDS")
            print_info(f"Processed {len(result.record_ids)} records:")
            for i, record_id in enumerate(result.record_ids[:10], 1):
                invenio_url = os.getenv("INVENIO_BASE_URL", "").rstrip("/")
                print(f"{i}. {Fore.GREEN}{invenio_url}/records/{record_id}")

            if len(result.record_ids) > 10:
                print_info(f"... and {len(result.record_ids) - 10} more records")
            print()

        # Summary
        if dry_run:
            print_success("Dry run completed - CSV validation successful!")
        else:
            if result.failed == 0:
                print_success("Import completed successfully!")
            elif result.successful > 0:
                print_warning("Import completed with some errors")
            else:
                print_error("Import failed - no records were created")

        # Return exit code
        return 0 if result.failed == 0 else 1

    except FileNotFoundError as e:
        print_error(f"File not found: {e}")
        return 1

    except ValueError as e:
        print_error(f"Validation error: {e}")
        return 1

    except Exception as e:
        logger.exception("Unexpected error during import")
        print_error(f"Import failed: {e}")
        return 1


@click.command()
@click.option(
    "--file",
    "-f",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to CSV file to import",
)
@click.option(
    "--delimiter",
    "-d",
    default=CSVImportConfig.DEFAULT_DELIMITER,
    help=f"CSV delimiter character (default: '{CSVImportConfig.DEFAULT_DELIMITER}')",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Validate CSV without creating records",
)
@click.option(
    "--skip-errors",
    is_flag=True,
    default=False,
    help="Continue processing even if some records fail",
)
@click.option(
    "--batch-size",
    type=int,
    default=None,
    help=f"Number of records per batch (default: {CSVImportConfig.BATCH_SIZE})",
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
    delimiter: str,
    dry_run: bool,
    skip_errors: bool,
    batch_size: Optional[int],
    verbose: bool,
):
    """
    Import or update InvenioRDM records from a CSV file.

    This tool maps CSV data to InvenioRDM format including:

    - Standard bibliographic fields (title, creators, dates, etc.)

    - Contributors with roles and affiliations

    - Related identifiers (DOI, ISBN, etc.)

    - File uploads and publishing

    \b
    Required CSV columns:
        - title: Record title
        - creators: Creators (format: "Given Family; ORCID; Affiliation | ...")

    \b
    Optional CSV columns:
        - record_id: Existing record ID for updates
        - description: Record description
        - resource_type: Resource type (default: dataset)
        - publication_date: Date in YYYY-MM-DD format
        - access_record: Record access (public/restricted)
        - access_files: Files access (public/restricted)
        - publisher: Publisher name
        - version: Version string
        - languages: Semicolon-separated ISO 639-3 codes
        - subjects: Semicolon-separated keywords
        - license: License ID
        - additional_descriptions: Pipe-separated "text; type"
        - references: Semicolon-separated references
        - contributors: Pipe-separated "Name; Affiliation; Role; ORCID"
        - related_identifiers: Pipe-separated "identifier; scheme; relation"
        - file_paths: Semicolon-separated file paths
        - publish: Publish immediately (yes/no)

    \b
    Examples:
        # Import all records
        python -m src.sources.csv --file records.csv

        # Dry run validation
        python -m src.sources.csv --file records.csv --dry-run

        # Custom delimiter (tab-separated)
        python -m src.sources.csv --file records.tsv --delimiter $'\\t'

        # Continue on errors
        python -m src.sources.csv --file records.csv --skip-errors

        # Verbose output
        python -m src.sources.csv --file records.csv --verbose
    """
    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Run import and exit with appropriate code
    exit_code = run_import(
        file=file,
        delimiter=delimiter,
        dry_run=dry_run,
        skip_errors=skip_errors,
        batch_size=batch_size,
        verbose=verbose,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    # Add parent directory to path for direct execution
    script_dir = Path(__file__).parent.parent.parent.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    main()
