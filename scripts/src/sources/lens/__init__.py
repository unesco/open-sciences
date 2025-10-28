"""
Lens.org data source importer.

This package provides functionality to import publication records from Lens.org
into InvenioRDM, including:
- JSON file reader
- Standard fields mapping (title, creators, dates, etc.)
- Custom fields mapping (Lens-specific metadata)
- Related identifiers mapping (DOI, PMID, etc.)
- CLI for direct execution

Public API:
    - create_reader: Create a Lens.org data reader
    - create_importer: Create a Lens.org importer
    - LensImportConfig: Configuration constants
    - run_import: Run import programmatically
    - main: CLI entry point
"""

from .reader import JSONFileReader, LensAPIReader, create_reader
from .importer import LensOrgImporter, create_importer
from .config import LensImportConfig
from .main import run_import, main

__all__ = [
    "JSONFileReader",
    "LensAPIReader",
    "create_reader",
    "LensOrgImporter",
    "create_importer",
    "LensImportConfig",
    "run_import",
    "main",
]
