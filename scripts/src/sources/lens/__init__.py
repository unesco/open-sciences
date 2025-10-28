"""
Lens.org data source importer.

This package provides functionality to import publication records from Lens.org
into InvenioRDM, including:
- JSON file reader
- Standard fields mapping (title, creators, dates, etc.)
- Custom fields mapping (Lens-specific metadata)
- Related identifiers mapping (DOI, PMID, etc.)
"""

from .reader import JSONFileReader, LensAPIReader, create_reader
from .importer import LensOrgImporter, create_importer
from .config import LensImportConfig

__all__ = [
    "JSONFileReader",
    "LensAPIReader",
    "create_reader",
    "LensOrgImporter",
    "create_importer",
    "LensImportConfig",
]
