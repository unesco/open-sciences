"""
CSV file reader for InvenioRDM import.

This module provides functionality to read and parse CSV files
containing record metadata for InvenioRDM.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .config import CSVImportConfig

logger = logging.getLogger(__name__)


class CSVReader:
    """
    Reader for CSV files containing InvenioRDM record data.

    This class handles reading CSV files and validating column structure.
    """

    def __init__(
        self, file_path: str, delimiter: str = CSVImportConfig.DEFAULT_DELIMITER
    ):
        """
        Initialize CSV reader.

        Args:
            file_path: Path to CSV file
            delimiter: CSV delimiter character (default: comma)
        """
        self.file_path = Path(file_path)
        self.delimiter = delimiter
        self.fieldnames: Optional[List[str]] = None
        self._validate_file()

        logger.info(
            f"Initialized CSV reader for: {self.file_path.name} (delimiter: '{delimiter}')"
        )

    def _validate_file(self):
        """Validate that the file exists and can be opened."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {self.file_path}")

    def get_file_info(self) -> Dict[str, Any]:
        """
        Get information about the CSV file.

        Returns:
            Dictionary containing file information
        """
        size_bytes = self.file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        # Count rows
        with open(self.file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            row_count = sum(1 for _ in reader)

        return {
            "path": str(self.file_path),
            "name": self.file_path.name,
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "row_count": row_count,
            "delimiter": self.delimiter,
        }

    def validate_columns(self) -> Dict[str, Any]:
        """
        Validate CSV columns against required fields.

        Returns:
            Dictionary with validation results
        """
        with open(self.file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            self.fieldnames = reader.fieldnames or []

        present_columns = set(self.fieldnames)
        required_columns = CSVImportConfig.REQUIRED_COLUMNS
        missing_columns = required_columns - present_columns
        extra_columns = present_columns - CSVImportConfig.ALL_COLUMNS

        is_valid = len(missing_columns) == 0

        return {
            "valid": is_valid,
            "present_columns": list(present_columns),
            "required_columns": list(required_columns),
            "missing_columns": list(missing_columns),
            "extra_columns": list(extra_columns),
        }

    def read_records(self) -> List[Dict[str, str]]:
        """
        Read all records from the CSV file.

        Returns:
            List of records as dictionaries

        Raises:
            ValueError: If required columns are missing
        """
        logger.info(f"Reading records from: {self.file_path}")

        # Validate columns first
        validation = self.validate_columns()
        if not validation["valid"]:
            missing = ", ".join(validation["missing_columns"])
            raise ValueError(f"CSV missing required columns: {missing}")

        records = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)

            for row_num, row in enumerate(
                reader, start=2
            ):  # Start from 2 (1 is header)
                # Add row number for error reporting
                row["_row_number"] = row_num
                records.append(row)

        logger.info(f"Loaded {len(records)} records from CSV")
        return records

    def read_batch(self, offset: int = 0, limit: int = 10) -> List[Dict[str, str]]:
        """
        Read a batch of records from the CSV file.

        Args:
            offset: Number of rows to skip
            limit: Maximum number of rows to read

        Returns:
            List of records as dictionaries
        """
        all_records = self.read_records()
        return all_records[offset : offset + limit]


def create_reader(
    file_path: str, delimiter: str = CSVImportConfig.DEFAULT_DELIMITER
) -> CSVReader:
    """
    Factory function to create a CSV reader.

    Args:
        file_path: Path to CSV file
        delimiter: CSV delimiter character (default: comma)

    Returns:
        CSVReader instance
    """
    return CSVReader(file_path, delimiter=delimiter)
