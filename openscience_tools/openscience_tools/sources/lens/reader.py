"""
Data readers for loading Lens.org publication data.

This module provides classes to read Lens.org data from various sources:
- JSON files
- Lens.org API (future)
- CSV exports (future)
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Iterator, Optional

logger = logging.getLogger(__name__)


class LensDataReader:
    """
    Base class for reading Lens.org publication data.

    Supports reading from JSON files exported from Lens.org.
    """

    def __init__(self, source: str):
        """
        Initialize the data reader.

        Args:
            source: Path to data file or API endpoint
        """
        self.source = source
        self.logger = logging.getLogger(self.__class__.__name__)

    def read_records(self) -> List[Dict[str, Any]]:
        """
        Read all records from the source.

        Returns:
            List of Lens.org publication records

        Raises:
            FileNotFoundError: If source file doesn't exist
            json.JSONDecodeError: If JSON is malformed
        """
        raise NotImplementedError("Subclasses must implement read_records()")

    def iter_records(self, batch_size: int = 10) -> Iterator[List[Dict[str, Any]]]:
        """
        Iterate over records in batches.

        Args:
            batch_size: Number of records per batch

        Yields:
            Batches of records
        """
        records = self.read_records()
        for i in range(0, len(records), batch_size):
            yield records[i : i + batch_size]

    def count_records(self) -> int:
        """
        Count total number of records.

        Returns:
            Number of records in source
        """
        return len(self.read_records())


class JSONFileReader(LensDataReader):
    """
    Reader for Lens.org JSON export files.

    Handles JSON files exported from Lens.org's web interface
    or API responses saved as JSON.
    """

    def __init__(self, json_file: str):
        """
        Initialize JSON file reader.

        Args:
            json_file: Path to JSON file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        super().__init__(json_file)
        self.json_file = Path(json_file)

        if not self.json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file}")

        if not self.json_file.is_file():
            raise ValueError(f"Not a file: {json_file}")

        self.logger.info(f"Initialized JSON reader for: {self.json_file.name}")

    def read_records(self) -> List[Dict[str, Any]]:
        """
        Read all records from JSON file.

        Returns:
            List of Lens.org publication records

        Raises:
            json.JSONDecodeError: If JSON is malformed
            ValueError: If JSON structure is unexpected
        """
        self.logger.info(f"Reading records from: {self.json_file}")

        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                # Direct list of records
                records = data
            elif isinstance(data, dict):
                # Check common wrapper structures
                if "data" in data:
                    records = data["data"]
                elif "results" in data:
                    records = data["results"]
                elif "records" in data:
                    records = data["records"]
                else:
                    # Assume single record
                    records = [data]
            else:
                raise ValueError(f"Unexpected JSON structure in {self.json_file}")

            self.logger.info(f"Loaded {len(records)} records from JSON")
            return records

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {self.json_file}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error reading {self.json_file}: {e}")
            raise

    def read_record_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Read a single record by index.

        Args:
            index: Zero-based index of record

        Returns:
            Record at index or None if out of bounds
        """
        records = self.read_records()
        if 0 <= index < len(records):
            return records[index]
        return None

    def read_records_by_lens_id(self, lens_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Read specific records by their Lens.org IDs.

        Args:
            lens_ids: List of Lens.org IDs to retrieve

        Returns:
            List of matching records
        """
        all_records = self.read_records()
        lens_ids_set = set(lens_ids)

        matching = [
            record for record in all_records if record.get("lens_id") in lens_ids_set
        ]

        self.logger.info(f"Found {len(matching)} records matching {len(lens_ids)} IDs")
        return matching

    def get_file_info(self) -> Dict[str, Any]:
        """
        Get information about the JSON file.

        Returns:
            Dict with file metadata
        """
        return {
            "path": str(self.json_file.absolute()),
            "name": self.json_file.name,
            "size_mb": self.json_file.stat().st_size / (1024 * 1024),
            "record_count": self.count_records(),
        }


class LensAPIReader(LensDataReader):
    """
    Reader for Lens.org Scholarly API.

    Future implementation to read directly from Lens.org API.
    Requires API token and subscription.
    """

    def __init__(
        self, api_token: str, api_url: str = "https://api.lens.org/scholarly/search"
    ):
        """
        Initialize API reader.

        Args:
            api_token: Lens.org API access token
            api_url: API endpoint URL
        """
        super().__init__(api_url)
        self.api_token = api_token
        self.api_url = api_url
        self.logger.warning("Lens API reader not yet implemented")

    def read_records(self) -> List[Dict[str, Any]]:
        """Read records from Lens.org API."""
        raise NotImplementedError(
            "Lens.org API reader not yet implemented. "
            "Please use JSONFileReader with exported data."
        )

    def search_records(
        self, query: str, max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search Lens.org and return results.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of matching records
        """
        raise NotImplementedError("API search not yet implemented")


def create_reader(source: str, source_type: str = "auto") -> LensDataReader:
    """
    Factory function to create appropriate reader based on source type.

    Args:
        source: Path to file or API endpoint
        source_type: Type of source ('json', 'api', 'auto')

    Returns:
        Appropriate LensDataReader instance

    Raises:
        ValueError: If source_type is unknown or unsupported
    """
    if source_type == "auto":
        # Auto-detect based on file extension or URL
        source_path = Path(source)
        if source_path.exists() and source_path.suffix.lower() == ".json":
            source_type = "json"
        elif source.startswith("http"):
            source_type = "api"
        else:
            raise ValueError(
                f"Cannot auto-detect source type for: {source}. "
                "Please specify source_type explicitly."
            )

    if source_type == "json":
        return JSONFileReader(source)
    elif source_type == "api":
        return LensAPIReader(source)
    else:
        raise ValueError(f"Unknown source type: {source_type}")
