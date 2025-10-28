"""
CSV data source importer for InvenioRDM.

This package provides functionality to import records from CSV files
into InvenioRDM, including:
- CSV file reading and parsing
- Metadata field mapping and validation
- Creator, contributor, and identifier parsing
- Batch processing with error handling
- CLI for direct execution

Public API:
    - create_reader: Create a CSV data reader
    - create_importer: Create a CSV importer
    - CSVImportConfig: Configuration constants
    - run_import: Run import programmatically
    - main: CLI entry point
"""

from .reader import CSVReader, create_reader
from .importer import CSVImporter, create_importer
from .config import CSVImportConfig
from .main import run_import, main

__all__ = [
    "CSVReader",
    "create_reader",
    "CSVImporter",
    "create_importer",
    "CSVImportConfig",
    "run_import",
    "main",
]
