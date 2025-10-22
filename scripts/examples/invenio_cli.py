#!/usr/bin/env python3
"""
CLI Tool for InvenioRDM API Operations

A comprehensive command-line interface for interacting with InvenioRDM.
Provides commands for searching, creating, and managing records.
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

# Initialize colorama for colored output
init()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose):
    """InvenioRDM API CLI - Interact with InvenioRDM from the command line."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if verbose:
        click.echo(
            f"{Fore.BLUE}🔧 InvenioRDM CLI - Verbose mode enabled{Style.RESET_ALL}"
        )


@cli.command()
@click.pass_context
def test_connection(ctx):
    """Test connection to InvenioRDM instance."""
    try:
        client = create_client_from_env()

        if ctx.obj.get("verbose"):
            click.echo(f"Testing connection to: {client.base_url}")

        info = client.get_info()

        click.echo(f"{Fore.GREEN}✅ Connection successful!{Style.RESET_ALL}")
        if ctx.obj.get("verbose"):
            click.echo(f"Instance info: {json.dumps(info, indent=2)}")
        else:
            click.echo(f"Connected to InvenioRDM at: {client.base_url}")

    except Exception as e:
        click.echo(f"{Fore.RED}❌ Connection failed: {e}{Style.RESET_ALL}")
        sys.exit(1)


@cli.command()
@click.option("--query", "-q", default="", help="Search query")
@click.option("--size", "-s", default=10, help="Number of results")
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json", "ids"]),
    help="Output format",
)
@click.pass_context
def search(ctx, query, size, output_format):
    """Search for records."""
    try:
        client = create_client_from_env()

        if ctx.obj.get("verbose"):
            click.echo(f"Searching with query: '{query}', size: {size}")

        results = client.search_records(q=query, size=size)
        hits = results.get("hits", {})
        total = hits.get("total", 0)
        records = hits.get("hits", [])

        if output_format == "json":
            click.echo(json.dumps(results, indent=2))
        elif output_format == "ids":
            for record in records:
                click.echo(record.get("id", "N/A"))
        else:
            click.echo(f"{Fore.GREEN}Found {total} records{Style.RESET_ALL}")
            for i, record in enumerate(records, 1):
                metadata = record.get("metadata", {})
                click.echo(
                    f"{i}. {record.get('id')} - {metadata.get('title', 'No title')}"
                )

    except Exception as e:
        click.echo(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


@cli.command()
@click.argument("record_id")
@click.option(
    "--format",
    "output_format",
    default="summary",
    type=click.Choice(["summary", "json", "metadata"]),
    help="Output format",
)
@click.pass_context
def get(ctx, record_id, output_format):
    """Get details of a specific record."""
    try:
        client = create_client_from_env()

        if ctx.obj.get("verbose"):
            click.echo(f"Retrieving record: {record_id}")

        record = client.get_record(record_id)

        if output_format == "json":
            click.echo(json.dumps(record, indent=2))
        elif output_format == "metadata":
            click.echo(json.dumps(record.get("metadata", {}), indent=2))
        else:
            metadata = record.get("metadata", {})
            click.echo(f"{Fore.CYAN}📄 Record: {record_id}{Style.RESET_ALL}")
            click.echo(f"Title: {metadata.get('title', 'No title')}")
            click.echo(
                f"Status: {'Published' if record.get('is_published') else 'Draft'}"
            )
            click.echo(f"Created: {record.get('created', 'N/A')}")

            # Creators
            creators = metadata.get("creators", [])
            if creators:
                click.echo("Creators:")
                for creator in creators:
                    person = creator.get("person_or_org", {})
                    name = person.get("name", "Unknown")
                    click.echo(f"  - {name}")

            # Access info
            access = record.get("access", {})
            click.echo(f"Access: {access.get('record', 'unknown')}")

            # Files
            files = record.get("files", {})
            if files.get("enabled"):
                click.echo(f"Files: Available")

            # Links
            links = record.get("links", {})
            if links.get("self_html"):
                click.echo(f"View: {links['self_html']}")

    except Exception as e:
        click.echo(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


@cli.command()
@click.option("--title", "-t", required=True, help="Record title")
@click.option("--creator", "-c", required=True, help="Creator name")
@click.option("--type", "resource_type", default="dataset", help="Resource type")
@click.option("--description", "-d", default="", help="Description")
@click.option("--file", "-f", multiple=True, help="Files to upload")
@click.option("--publish", is_flag=True, help="Publish immediately")
@click.pass_context
def create(ctx, title, creator, resource_type, description, file, publish):
    """Create a new record draft."""
    try:
        client = create_client_from_env()

        # Parse creator name
        name_parts = creator.strip().split()
        if len(name_parts) < 2:
            click.echo(
                f"{Fore.RED}❌ Creator name must include both given and family name{Style.RESET_ALL}"
            )
            sys.exit(1)

        given_name = " ".join(name_parts[:-1])
        family_name = name_parts[-1]

        creators = [
            {
                "person_or_org": {
                    "given_name": given_name,
                    "family_name": family_name,
                    "type": "personal",
                    "name": f"{family_name}, {given_name}",
                }
            }
        ]

        if ctx.obj.get("verbose"):
            click.echo(f"Creating record: {title}")

        draft = client.create_simple_record(
            title=title,
            creators=creators,
            description=description,
            resource_type=resource_type,
        )

        record_id = draft["id"]
        click.echo(f"{Fore.GREEN}✅ Draft created: {record_id}{Style.RESET_ALL}")

        # Upload files if specified
        if file:
            for file_path in file:
                if os.path.exists(file_path):
                    try:
                        client.upload_file_to_draft(record_id, file_path)
                        click.echo(f"📎 Uploaded: {os.path.basename(file_path)}")
                    except Exception as e:
                        click.echo(
                            f"{Fore.YELLOW}⚠️  Failed to upload {file_path}: {e}{Style.RESET_ALL}"
                        )
                else:
                    click.echo(
                        f"{Fore.YELLOW}⚠️  File not found: {file_path}{Style.RESET_ALL}"
                    )

        # Publish if requested
        if publish:
            try:
                published = client.publish_draft(record_id)
                click.echo(f"{Fore.GREEN}🚀 Published: {record_id}{Style.RESET_ALL}")
                if ctx.obj.get("verbose"):
                    links = published.get("links", {})
                    if links.get("self_html"):
                        click.echo(f"View at: {links['self_html']}")
            except Exception as e:
                click.echo(f"{Fore.YELLOW}⚠️  Failed to publish: {e}{Style.RESET_ALL}")

        # Show draft URL
        links = draft.get("links", {})
        if links.get("self_html"):
            click.echo(f"Edit at: {links['self_html']}")

    except Exception as e:
        click.echo(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


@cli.command()
@click.option("--query", "-q", default="", help="Search query")
@click.option("--size", "-s", default=10, help="Number of results")
@click.pass_context
def users(ctx, query, size):
    """Search for users."""
    try:
        client = create_client_from_env()

        if ctx.obj.get("verbose"):
            click.echo(f"Searching users with query: '{query}'")

        results = client.search_users(q=query, size=size)
        hits = results.get("hits", {})
        total = hits.get("total", 0)
        users = hits.get("hits", [])

        click.echo(f"{Fore.GREEN}Found {total} users{Style.RESET_ALL}")
        for i, user in enumerate(users, 1):
            profile = user.get("profile", {})
            username = user.get("username", "N/A")
            full_name = profile.get("full_name", "No name")
            affiliations = profile.get("affiliations", "")

            click.echo(f"{i}. {username} - {full_name}")
            if affiliations:
                click.echo(f"   Affiliations: {affiliations}")

    except Exception as e:
        click.echo(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


@cli.command()
@click.option("--query", "-q", default="", help="Search query")
@click.option("--size", "-s", default=10, help="Number of results")
@click.pass_context
def communities(ctx, query, size):
    """Search for communities."""
    try:
        client = create_client_from_env()

        if ctx.obj.get("verbose"):
            click.echo(f"Searching communities with query: '{query}'")

        results = client.search_communities(q=query, size=size)
        hits = results.get("hits", {})
        total = hits.get("total", 0)
        communities = hits.get("hits", [])

        click.echo(f"{Fore.GREEN}Found {total} communities{Style.RESET_ALL}")
        for i, community in enumerate(communities, 1):
            metadata = community.get("metadata", {})
            title = metadata.get("title", "No title")
            community_id = community.get("id", "N/A")

            click.echo(f"{i}. {community_id} - {title}")

    except Exception as e:
        click.echo(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
