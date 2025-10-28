"""
Lens.org to InvenioRDM Importer Package

This package provides a comprehensive, modular system for importing publication data
from Lens.org into InvenioRDM instances.

Architecture:
- Config: Configuration and mapping tables
- Readers: Data loading from various sources (JSON, API)
- Mappers: Field mapping logic (standard, custom, related identifiers)
- Importers: Orchestration and import workflow
- Reporters: Logging, statistics, and error reporting

Usage:
    from lens_org import LensOrgImporter

    importer = LensOrgImporter(
        invenio_client=client,
        json_file="publications.json"
    )

    results = importer.import_records(dry_run=False)
"""

__version__ = "1.0.0"
__author__ = "InvenioRDM Team"

from .config import LensImportConfig
from .importer import LensOrgImporter, create_importer
from .reader import create_reader, JSONFileReader
from .base import ImportResult

__all__ = [
    "LensImportConfig",
    "LensOrgImporter",
    "create_importer",
    "create_reader",
    "JSONFileReader",
    "ImportResult",
]
