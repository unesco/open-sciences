"""
CLI and main entry point for Zenodo importer.

This module provides a command-line interface for importing records
from Zenodo.org into InvenioRDM. It supports:
- Importing specific records by ID
- Searching and importing multiple records
- Dry-run mode for validation
- File upload control

Usage:
    # As module
    python -m src.sources.zenodo --record-id 17462748
    python -m src.sources.zenodo --search "climate data" --max-results 5

    # Via Makefile
    make scripts-import-zenodo RECORD_ID=17462748
    make scripts-import-zenodo QUERY="climate data" MAX=5
"""

import os
import sys
import logging
import click
from pathlib import Path
from colorama import Fore, Style, init
from typing import Optional, List
from dotenv import load_dotenv

from src.invenio_client import InvenioRDMClient
from .fetcher import create_fetcher
from .mapper import create_mapper
from .importer import create_importer, ImportResult

# Initialize colorama
init(autoreset=True)

# Configure logging
logger = logging.getLogger(__name__)


def setup_environment() -> None:
    """Load environment variables from .env file."""
    # Try to load from config/.env
    env_path = Path(__file__).parent.parent.parent.parent / "config" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from: {env_path}")
    else:
        logger.warning(f"Environment file not found: {env_path}")


def configure_logging(verbose: bool = False) -> None:
    """
    Configure logging settings.

    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s:%(name)s:%(message)s",
    )


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}{title:^70}")
    print(f"{Fore.CYAN}{'='*70}\n")


def print_result_summary(results: List[ImportResult], dry_run: bool = False) -> None:
    """
    Print summary of import results.

    Args:
        results: List of import results
        dry_run: Whether this was a dry run
    """
    successful = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    total_files = sum(r.files_count for r in results if r.success)

    print(f"\n{Fore.YELLOW}{'='*70}")
    print(f"{Fore.YELLOW}{'IMPORT RESULTS':^70}")
    print(f"{Fore.YELLOW}{'='*70}\n")

    print(f"Total records processed: {len(results)}")
    print(f"Successful imports:      {Fore.GREEN}{successful}{Style.RESET_ALL}")
    print(
        f"Failed imports:          {Fore.RED if failed > 0 else Fore.GREEN}{failed}{Style.RESET_ALL}"
    )

    if not dry_run and successful > 0:
        print(f"Files uploaded:          {total_files}")

    # Show failed records
    if failed > 0:
        print(f"\n{Fore.RED}Failed records:")
        for result in results:
            if not result.success:
                print(f"{Fore.RED}  - Zenodo ID {result.zenodo_id}: {result.error}")

    # Show successful records
    if successful > 0 and not dry_run:
        print(f"\n{Fore.GREEN}Successfully imported:")
        for result in results:
            if result.success:
                print(f"{Fore.GREEN}  ✓ {result.title}")
                print(f"{Fore.CYAN}    Zenodo DOI: {result.doi}")
                print(f"{Fore.CYAN}    InvenioRDM ID: {result.invenio_id}")

    if dry_run:
        print(f"\n{Fore.GREEN}✓ Dry run completed - validation successful!")
    else:
        print(f"\n{Fore.GREEN}✓ Import completed!")

    print(f"\n{Fore.YELLOW}{'='*70}\n")


def run_import(
    record_id: Optional[str] = None,
    search_query: Optional[str] = None,
    max_results: int = 5,
    skip_files: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    skip_errors: bool = True,
) -> List[ImportResult]:
    """
    High-level import function.

    Args:
        record_id: Specific Zenodo record ID to import
        search_query: Search query for finding records
        max_results: Maximum number of search results to import
        skip_files: Skip file downloads
        dry_run: Validation only, don't create records
        verbose: Enable verbose logging
        skip_errors: Continue on errors

    Returns:
        List of import results

    Raises:
        ValueError: If neither record_id nor search_query is provided
        RuntimeError: If environment is not configured
    """
    # Configure logging
    configure_logging(verbose)

    # Setup environment
    setup_environment()

    # Validate inputs
    if not record_id and not search_query:
        raise ValueError("Must specify either record_id or search_query")

    # Get configuration
    base_url = os.getenv("INVENIO_BASE_URL")
    token = os.getenv("INVENIO_TOKEN")

    if not base_url or not token:
        raise RuntimeError(
            "Environment not configured. Missing INVENIO_BASE_URL or INVENIO_TOKEN. "
            "Run: make scripts-setup-env"
        )

    logger.info(f"Environment configured: {base_url}")

    # Initialize components
    invenio_client = InvenioRDMClient(base_url=base_url, token=token)
    zenodo_fetcher = create_fetcher()
    mapper = create_mapper()
    importer = create_importer(invenio_client, zenodo_fetcher, mapper)

    # Print configuration
    print(f"{Fore.CYAN}ℹ Mode: {'DRY RUN (validation only)' if dry_run else 'IMPORT'}")
    print(f"{Fore.CYAN}ℹ Skip files: {'Yes' if skip_files else 'No'}")
    print(f"{Fore.CYAN}ℹ Skip errors: {'Yes' if skip_errors else 'No'}")

    # Execute import
    if record_id:
        print(f"{Fore.CYAN}ℹ Record ID: {record_id}\n")
        result = importer.import_record(record_id, skip_files, dry_run)
        results = [result]
    else:
        print(f"{Fore.CYAN}ℹ Search query: '{search_query}'")
        print(f"{Fore.CYAN}ℹ Max results: {max_results}\n")
        results = importer.search_and_import(
            search_query, max_results, skip_files, dry_run, skip_errors
        )

    return results


@click.command()
@click.option(
    "--record-id",
    "-r",
    help="Zenodo record ID to import (e.g., 17462748)",
)
@click.option(
    "--search",
    "-s",
    help="Search query for finding records on Zenodo",
)
@click.option(
    "--max-results",
    "-m",
    default=5,
    type=int,
    help="Maximum number of search results to import (default: 5)",
)
@click.option(
    "--skip-files",
    is_flag=True,
    help="Skip downloading and uploading files (metadata only)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate records without importing (dry run mode)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output (DEBUG logging)",
)
@click.option(
    "--skip-errors",
    is_flag=True,
    default=True,
    help="Continue importing on errors (default: True)",
)
def main(
    record_id: Optional[str],
    search: Optional[str],
    max_results: int,
    skip_files: bool,
    dry_run: bool,
    verbose: bool,
    skip_errors: bool,
) -> None:
    """
    Import records from Zenodo.org into InvenioRDM.

    This tool fetches metadata and files from Zenodo's public API and imports them
    into your InvenioRDM instance, preserving all metadata including creators,
    contributors, related identifiers, keywords, and files.

    Examples:

    \b
    # Import a specific record
    python -m src.sources.zenodo --record-id 17462748

    \b
    # Import without files (metadata only)
    python -m src.sources.zenodo --record-id 17462748 --skip-files

    \b
    # Dry run (preview what would be imported)
    python -m src.sources.zenodo --record-id 17462748 --dry-run

    \b
    # Search and import multiple records
    python -m src.sources.zenodo --search "climate data" --max-results 3

    \b
    # Via Makefile
    make scripts-import-zenodo RECORD_ID=17462748
    make scripts-import-zenodo QUERY="climate" MAX=5 OPTS="--skip-files"
    """
    print_header("ZENODO TO INVENIO RDM IMPORTER")

    try:
        # Run import
        results = run_import(
            record_id=record_id,
            search_query=search,
            max_results=max_results,
            skip_files=skip_files,
            dry_run=dry_run,
            verbose=verbose,
            skip_errors=skip_errors,
        )

        # Print summary
        print_result_summary(results, dry_run)

        # Exit with error code if any failed
        failed = sum(1 for r in results if not r.success)
        if failed > 0:
            sys.exit(1)

    except ValueError as e:
        print(f"{Fore.RED}❌ Error: {e}")
        print(f"{Fore.YELLOW}💡 Try: python -m src.sources.zenodo --help")
        sys.exit(1)

    except RuntimeError as e:
        print(f"{Fore.RED}❌ {e}")
        sys.exit(1)

    except Exception as e:
        print(f"{Fore.RED}❌ Unexpected error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
