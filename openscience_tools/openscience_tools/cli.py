"""
Main CLI entry point for openscience_tools.

Provides a unified command-line interface for all tools.
"""

import click
from .tools import search, view, cleanup
from .sources.lens.main import main as lens_import


@click.group()
@click.option(
    "--base-url",
    envvar="INVENIO_BASE_URL",
    required=True,
    help="InvenioRDM base URL (e.g., https://127.0.0.1:5000)",
)
@click.option(
    "--token",
    envvar="INVENIO_TOKEN",
    required=True,
    help="InvenioRDM API token",
)
@click.pass_context
@click.version_option(version="0.1.0", prog_name="openscience_tools")
def main(ctx, base_url, token):
    """OpenScience Tools - InvenioRDM REST API Tools.

    Requires INVENIO_BASE_URL and INVENIO_TOKEN (can be set as env vars or passed as options).
    """
    # Store in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["base_url"] = base_url
    ctx.obj["token"] = token


# Register subcommands
main.add_command(search.main, name="search")
main.add_command(view.main, name="view")
main.add_command(cleanup.main, name="cleanup")
main.add_command(lens_import, name="import-lens")


if __name__ == "__main__":
    main()
