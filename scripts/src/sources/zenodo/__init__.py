"""
Zenodo.org data source for InvenioRDM.

This module provides functionality to fetch and import records from Zenodo.org
into InvenioRDM, preserving all metadata including creators, contributors,
related identifiers, keywords, and files.

Public API:
    - create_fetcher(): Create a Zenodo API client
    - create_importer(): Create an import orchestrator
    - run_import(): High-level import function
    - main(): CLI entry point
"""

from .fetcher import ZenodoFetcher, create_fetcher
from .importer import ZenodoImporter, create_importer
from .main import run_import, main

__all__ = [
    "ZenodoFetcher",
    "create_fetcher",
    "ZenodoImporter",
    "create_importer",
    "run_import",
    "main",
]
