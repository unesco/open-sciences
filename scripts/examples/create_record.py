#!/usr/bin/env python3
"""
Example script: Create a new record draft

This script demonstrates how to:
1. Create a new record draft with metadata
2. Upload files to the draft
3. Publish the draft
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
from datetime import datetime

# Initialize colorama for colored output
init()


@click.command()
@click.option("--title", "-t", required=True, help="Record title")
@click.option("--description", "-d", default="", help="Record description")
@click.option(
    "--creator-name",
    "--creator",
    required=True,
    help='Creator name (format: "Given Family")',
)
@click.option("--creator-affiliation", default="", help="Creator affiliation")
@click.option("--creator-orcid", default="", help="Creator ORCID ID")
@click.option(
    "--resource-type", default="dataset", help="Resource type (default: dataset)"
)
@click.option(
    "--publication-date",
    default="",
    help="Publication date (YYYY-MM-DD, default: today)",
)
@click.option(
    "--file",
    "-f",
    multiple=True,
    help="Files to upload (can be specified multiple times)",
)
@click.option(
    "--access-record", default="public", help="Record access level (public/restricted)"
)
@click.option(
    "--access-files", default="public", help="Files access level (public/restricted)"
)
@click.option("--publish", is_flag=True, help="Publish the draft immediately")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without actually creating it",
)
def create_record(
    title,
    description,
    creator_name,
    creator_affiliation,
    creator_orcid,
    resource_type,
    publication_date,
    file,
    access_record,
    access_files,
    publish,
    dry_run,
):
    """Create a new InvenioRDM record draft."""

    try:
        # Parse creator name
        name_parts = creator_name.strip().split()
        if len(name_parts) < 2:
            print(
                f"{Fore.RED}❌ Creator name must include both given and family name{Style.RESET_ALL}"
            )
            sys.exit(1)

        given_name = " ".join(name_parts[:-1])
        family_name = name_parts[-1]

        # Set publication date
        if not publication_date:
            publication_date = datetime.now().strftime("%Y-%m-%d")

        # Prepare creator metadata
        creator = {
            "person_or_org": {
                "given_name": given_name,
                "family_name": family_name,
                "type": "personal",
                "name": f"{family_name}, {given_name}",
            }
        }

        # Add ORCID if provided
        if creator_orcid:
            creator["person_or_org"]["identifiers"] = [
                {"identifier": creator_orcid, "scheme": "orcid"}
            ]

        # Add affiliation if provided
        if creator_affiliation:
            creator["affiliations"] = [{"name": creator_affiliation}]

        # Prepare metadata
        metadata = {
            "title": title,
            "creators": [creator],
            "resource_type": {"id": resource_type},
            "publication_date": publication_date,
        }

        if description:
            metadata["description"] = description

        # Prepare access settings
        access = {"record": access_record, "files": access_files}

        # Prepare files settings
        files_config = {"enabled": len(file) > 0}

        # Display what will be created
        print(f"{Fore.BLUE}📝 Creating new record draft...{Style.RESET_ALL}")
        print(f"Title: {title}")
        print(f"Creator: {creator_name}")
        if creator_affiliation:
            print(f"Affiliation: {creator_affiliation}")
        if creator_orcid:
            print(f"ORCID: {creator_orcid}")
        print(f"Resource Type: {resource_type}")
        print(f"Publication Date: {publication_date}")
        if description:
            print(f"Description: {description}")
        print(f"Access: Record={access_record}, Files={access_files}")
        if file:
            print(f"Files to upload: {', '.join(file)}")
        print("-" * 50)

        if dry_run:
            print(
                f"{Fore.YELLOW}🔍 Dry run mode - no actual creation performed{Style.RESET_ALL}"
            )
            print("\nMetadata that would be sent:")
            print(json.dumps(metadata, indent=2))
            return

        # Create client from environment variables
        client = create_client_from_env()

        # Create the draft
        draft = client.create_draft(
            metadata=metadata, access=access, files=files_config
        )

        record_id = draft["id"]
        print(f"{Fore.GREEN}✅ Draft created successfully!{Style.RESET_ALL}")
        print(f"Record ID: {record_id}")
        print(f"Draft URL: {draft.get('links', {}).get('self_html', 'N/A')}")

        # Upload files if specified
        if file:
            print(f"\n{Fore.BLUE}📎 Uploading files...{Style.RESET_ALL}")

            for file_path in file:
                if not os.path.exists(file_path):
                    print(
                        f"{Fore.YELLOW}⚠️  File not found: {file_path}{Style.RESET_ALL}"
                    )
                    continue

                try:
                    print(f"Uploading: {os.path.basename(file_path)}")
                    result = client.upload_file_to_draft(record_id, file_path)
                    print(
                        f"{Fore.GREEN}✅ Uploaded: {os.path.basename(file_path)}{Style.RESET_ALL}"
                    )
                except Exception as e:
                    print(
                        f"{Fore.RED}❌ Failed to upload {file_path}: {e}{Style.RESET_ALL}"
                    )

        # Publish if requested
        if publish:
            print(f"\n{Fore.BLUE}🚀 Publishing draft...{Style.RESET_ALL}")
            try:
                published = client.publish_draft(record_id)
                print(f"{Fore.GREEN}✅ Record published successfully!{Style.RESET_ALL}")
                print(
                    f"Published Record URL: {published.get('links', {}).get('self_html', 'N/A')}"
                )

                # Show DOI if available
                pids = published.get("pids", {})
                if "doi" in pids:
                    doi = pids["doi"]["identifier"]
                    print(f"DOI: {doi}")

            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Failed to publish: {e}{Style.RESET_ALL}")
                print(
                    f"Draft saved as: {draft.get('links', {}).get('self_html', 'N/A')}"
                )
        else:
            print(f"\n{Fore.BLUE}💾 Draft saved (not published){Style.RESET_ALL}")
            print(
                f"You can edit and publish later at: {draft.get('links', {}).get('self_html', 'N/A')}"
            )

    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    create_record()
