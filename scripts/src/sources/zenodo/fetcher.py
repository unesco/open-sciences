"""
Zenodo API client for fetching records and files.

This module handles all interactions with Zenodo's public API,
including searching records, fetching metadata, and downloading files.
"""

import logging
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from .config import ZENODO_API_BASE

logger = logging.getLogger(__name__)


class ZenodoFetcher:
    """Client for fetching data from Zenodo API."""

    def __init__(self, api_base: str = ZENODO_API_BASE):
        """
        Initialize Zenodo fetcher.

        Args:
            api_base: Zenodo API base URL
        """
        self.api_base = api_base
        logger.info(f"Initialized Zenodo fetcher: {api_base}")

    def fetch_record(self, record_id: str) -> Dict[str, Any]:
        """
        Fetch a record from Zenodo by ID.

        Args:
            record_id: Zenodo record ID (e.g., "17462748")

        Returns:
            Record metadata dictionary

        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.api_base}/records/{record_id}"
        logger.info(f"Fetching Zenodo record: {record_id}")

        response = requests.get(url)
        response.raise_for_status()

        record = response.json()
        logger.debug(
            f"Fetched record: {record.get('metadata', {}).get('title', 'Untitled')}"
        )
        return record

    def search_records(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search records on Zenodo.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of record metadata dictionaries

        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.api_base}/records"
        params = {"q": query, "size": max_results, "sort": "mostrecent"}

        logger.info(f"Searching Zenodo: '{query}' (max {max_results} results)")
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        hits = data.get("hits", {}).get("hits", [])

        logger.info(f"Found {len(hits)} records")
        return hits

    def download_file(
        self,
        url: str,
        filename: str,
        temp_dir: Path,
        progress_callback: Optional[callable] = None,
    ) -> Path:
        """
        Download a file from Zenodo.

        Args:
            url: File download URL
            filename: Name to save file as
            temp_dir: Temporary directory to save file
            progress_callback: Optional callback function for progress updates

        Returns:
            Path to downloaded file

        Raises:
            requests.HTTPError: If the download fails
        """
        # Sanitize filename - replace path separators with underscores
        safe_filename = filename.replace("/", "_").replace("\\", "_")
        file_path = temp_dir / safe_filename

        logger.info(f"Downloading file: {filename}")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        with open(file_path, "wb") as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)

                if progress_callback:
                    progress_callback(downloaded, total_size)

        size_mb = total_size / (1024 * 1024)
        logger.info(f"Downloaded {filename}: {size_mb:.2f} MB")

        return file_path


def create_fetcher(api_base: str = ZENODO_API_BASE) -> ZenodoFetcher:
    """
    Create a Zenodo fetcher instance.

    Args:
        api_base: Zenodo API base URL

    Returns:
        Configured ZenodoFetcher instance
    """
    return ZenodoFetcher(api_base=api_base)
