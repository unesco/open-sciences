"""
Export tool for InvenioRDM records.

This module provides command-line export functionality for InvenioRDM,
allowing users to export all records to CSV format.

Usage:
    openscience-tools export --output records.csv
    openscience-tools export -o records.csv --query "climate" --all-fields
"""

import sys
import csv
import logging
import click
from colorama import Fore, Style, init
from typing import List, Dict, Any, Optional
from pathlib import Path

# Initialize colorama
init(autoreset=True)

# Configure logging
logger = logging.getLogger(__name__)


def flatten_creators(creators: List[Dict[str, Any]]) -> str:
    """
    Flatten creators list to a comma-separated string.

    Args:
        creators: List of creator dictionaries

    Returns:
        Comma-separated string of creator names
    """
    names = []
    for creator in creators:
        person = creator.get("person_or_org", {})
        name = person.get(
            "name",
            f"{person.get('given_name', '')} {person.get('family_name', '')}".strip(),
        )
        if name:
            names.append(name)
    return "; ".join(names) if names else ""


def flatten_affiliations(creators: List[Dict[str, Any]]) -> str:
    """
    Flatten affiliations from creators to a comma-separated string.

    Args:
        creators: List of creator dictionaries

    Returns:
        Comma-separated string of affiliations
    """
    affiliations = set()
    for creator in creators:
        for affiliation in creator.get("affiliations", []):
            name = affiliation.get("name")
            if name:
                affiliations.add(name)
    return "; ".join(sorted(affiliations)) if affiliations else ""


def get_resource_type(metadata: Dict[str, Any]) -> str:
    """
    Extract resource type from metadata.

    Args:
        metadata: Record metadata

    Returns:
        Resource type string
    """
    resource_type = metadata.get("resource_type", {})
    title = resource_type.get("title", {})
    if isinstance(title, dict):
        return title.get("en", resource_type.get("id", "Unknown"))
    return resource_type.get("id", "Unknown")


def flatten_identifiers(metadata: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract identifiers from metadata.

    Args:
        metadata: Record metadata

    Returns:
        Dictionary with DOI, ISBN, etc.
    """
    identifiers = metadata.get("identifiers", [])
    result = {"doi": "", "isbn": "", "issn": ""}

    for identifier in identifiers:
        scheme = identifier.get("scheme", "").lower()
        value = identifier.get("identifier", "")
        if scheme == "doi":
            result["doi"] = value
        elif scheme == "isbn":
            result["isbn"] = value
        elif scheme == "issn":
            result["issn"] = value

    return result


def flatten_related_identifiers(metadata: Dict[str, Any]) -> str:
    """
    Extract related identifiers from metadata.

    Args:
        metadata: Record metadata

    Returns:
        String with related identifiers
    """
    related = metadata.get("related_identifiers", [])
    if not related:
        return ""

    items = []
    for rel in related:
        scheme = rel.get("scheme", "")
        identifier = rel.get("identifier", "")
        relation_type = rel.get("relation_type", {}).get("id", "")
        if identifier:
            items.append(f"{relation_type}:{scheme}:{identifier}")

    return "; ".join(items) if items else ""


def flatten_subjects(metadata: Dict[str, Any]) -> str:
    """
    Extract subjects/keywords from metadata.

    Args:
        metadata: Record metadata

    Returns:
        Comma-separated string of subjects
    """
    subjects = metadata.get("subjects", [])
    keywords = []
    for subject in subjects:
        if isinstance(subject, dict):
            keyword = subject.get("subject", "")
            if keyword:
                keywords.append(keyword)
        elif isinstance(subject, str):
            keywords.append(subject)

    return "; ".join(keywords) if keywords else ""


def record_to_csv_row(record: Dict[str, Any], all_fields: bool = False) -> Dict[str, Any]:
    """
    Convert a record to a CSV row dictionary.

    Args:
        record: Record dictionary
        all_fields: Include all available fields

    Returns:
        Dictionary with CSV column values
    """
    metadata = record.get("metadata", {})
    access = record.get("access", {})
    files = record.get("files", {})
    links = record.get("links", {})

    # Basic fields (always included)
    row = {
        "record_id": record.get("id", ""),
        "title": metadata.get("title", ""),
        "creators": flatten_creators(metadata.get("creators", [])),
        "publication_date": metadata.get("publication_date", ""),
        "resource_type": get_resource_type(metadata),
        "description": metadata.get("description", "")[:500] if metadata.get("description") else "",
        "publisher": metadata.get("publisher", ""),
        "version": metadata.get("version", ""),
        "access_record": access.get("record", ""),
        "access_files": access.get("files", ""),
    }

    if all_fields:
        # Additional fields
        identifiers = flatten_identifiers(metadata)
        row.update(
            {
                "affiliations": flatten_affiliations(metadata.get("creators", [])),
                "doi": identifiers["doi"],
                "isbn": identifiers["isbn"],
                "issn": identifiers["issn"],
                "subjects": flatten_subjects(metadata),
                "related_identifiers": flatten_related_identifiers(metadata),
                "language": (
                    metadata.get("languages", [{}])[0].get("id", "")
                    if metadata.get("languages")
                    else ""
                ),
                "rights": "; ".join(
                    [r.get("title", {}).get("en", "") for r in metadata.get("rights", [])]
                ),
                "files_enabled": str(files.get("enabled", False)),
                "files_count": len(files.get("entries", [])),
                "created": record.get("created", ""),
                "updated": record.get("updated", ""),
                "url": links.get("self_html", ""),
            }
        )

    return row


def export_records(
    base_url: str,
    token: str,
    output: str,
    query: str = "",
    all_fields: bool = False,
    verbose: bool = False,
) -> None:
    """
    Export InvenioRDM records to CSV.

    Args:
        base_url: InvenioRDM base URL
        token: API authentication token
        output: Output CSV file path
        query: Search query string (empty for all records)
        all_fields: Include all available fields
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

        # Display export parameters
        print(f"\n{Fore.BLUE}{'='*70}")
        print(f"📤 Exporting InvenioRDM Records to CSV")
        print(f"{'='*70}{Style.RESET_ALL}\n")

        if query:
            print(f"Query: '{query}'")
        else:
            print("Query: <all records>")

        print(f"Output: {output}")
        print(f"Fields: {'All fields' if all_fields else 'Basic fields'}")
        print()

        # Fetch all records with pagination
        all_records = []
        page = 1
        size = 100  # Fetch 100 records per page

        print(f"{Fore.CYAN}Fetching records...{Style.RESET_ALL}")

        while True:
            logger.debug(f"Fetching page {page} (size={size})")
            results = client.search_records(q=query, size=size, page=page)

            hits = results.get("hits", {})
            total = hits.get("total", 0)
            records = hits.get("hits", [])

            if not records:
                break

            all_records.extend(records)
            print(f"  Fetched {len(all_records)}/{total} records...", end="\r")

            # Check if we've fetched all records
            if len(all_records) >= total:
                break

            page += 1

        print()  # New line after progress

        if not all_records:
            print(f"{Fore.YELLOW}⚠ No records found matching your criteria.{Style.RESET_ALL}")
            return

        print(f"{Fore.GREEN}✓ Fetched {len(all_records)} total records{Style.RESET_ALL}\n")

        # Convert records to CSV rows
        print(f"{Fore.CYAN}Converting records to CSV format...{Style.RESET_ALL}")
        csv_rows = []
        for record in all_records:
            try:
                row = record_to_csv_row(record, all_fields=all_fields)
                csv_rows.append(row)
            except Exception as e:
                logger.warning(f"Failed to convert record {record.get('id', 'unknown')}: {e}")
                continue

        if not csv_rows:
            print(f"{Fore.RED}❌ Failed to convert any records to CSV format{Style.RESET_ALL}")
            sys.exit(1)

        # Determine CSV columns
        if csv_rows:
            fieldnames = list(csv_rows[0].keys())
        else:
            fieldnames = []

        # Write to CSV
        print(f"{Fore.CYAN}Writing to {output}...{Style.RESET_ALL}")

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        print(
            f"\n{Fore.GREEN}✓ Successfully exported {len(csv_rows)} records to {output}{Style.RESET_ALL}"
        )
        print(f"  Columns: {len(fieldnames)}")
        print(f"  File size: {output_path.stat().st_size / 1024:.2f} KB\n")

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=verbose)
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


@click.command()
@click.option(
    "--output",
    "-o",
    default="records.csv",
    help="Output CSV file path (default: records.csv)",
)
@click.option(
    "--query",
    "-q",
    default="",
    help="Search query string (leave empty for all records)",
)
@click.option(
    "--all-fields",
    "-a",
    is_flag=True,
    help="Include all available fields in the export",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx, output: str, query: str, all_fields: bool, verbose: bool):
    """
    Export InvenioRDM records to CSV format.

    Examples:

    \b
    # Export all records to default file
    openscience-tools export

    \b
    # Export to specific file
    openscience-tools export --output my_records.csv

    \b
    # Export only climate-related records
    openscience-tools export -q "climate" -o climate_records.csv

    \b
    # Export with all available fields
    openscience-tools export --all-fields -o full_export.csv

    \b
    # Export specific query with verbose output
    openscience-tools export -q "dataset" -o datasets.csv --verbose
    """
    export_records(
        base_url=ctx.obj["base_url"],
        token=ctx.obj["token"],
        output=output,
        query=query,
        all_fields=all_fields,
        verbose=verbose,
    )


if __name__ == "__main__":
    main()
