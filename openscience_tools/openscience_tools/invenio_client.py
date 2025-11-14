"""
InvenioRDM REST API Client

A comprehensive Python client for interacting with InvenioRDM REST API.
Supports authentication, records management, file uploads, and more.
"""

import os
import requests
import json
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvenioRDMClient:
    """
    A Python client for interacting with InvenioRDM REST API.

    This client provides methods for:
    - Authentication with Bearer tokens
    - Records and drafts management
    - File uploads and management
    - Statistics retrieval
    - Users and communities management
    """

    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        Initialize the InvenioRDM client.

        Args:
            base_url: Base URL of the InvenioRDM instance (e.g., 'https://your-rdm.example.com')
            token: API Bearer token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_url = urljoin(self.base_url, "/api/")
        self.token = token
        self.session = requests.Session()

        # Disable SSL verification for development with self-signed certificates
        self.session.verify = False

        # Suppress SSL warnings for self-signed certificates
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Set default headers
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to /api/)
            **kwargs: Additional arguments passed to requests

        Returns:
            requests.Response object

        Raises:
            requests.RequestException: For HTTP errors
        """
        url = urljoin(self.api_url, endpoint.lstrip("/"))

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            error_msg = f"Request failed: {method} {url} - {e}"
            try:
                error_details = response.json()
                logger.error(f"{error_msg}\nDetails: {json.dumps(error_details, indent=2)}")
            except:
                logger.error(error_msg)
            raise

    def get_info(self) -> Dict[str, Any]:
        """
        Get basic information about the InvenioRDM instance.

        Returns:
            Dictionary containing instance information
        """
        # Use a working endpoint to test connectivity
        response = self._make_request("GET", "/records", params={"size": 1})
        return {
            "api_available": True,
            "total_records": response.json().get("hits", {}).get("total", 0),
            "api_base_url": self.api_url,
        }

    # =====================================
    # RECORDS API
    # =====================================

    def search_records(self, q: str = "", **params) -> Dict[str, Any]:
        """
        Search published records.

        Args:
            q: Search query string
            **params: Additional query parameters (sort, size, page, etc.)

        Returns:
            Search results with records and metadata
        """
        params["q"] = q
        response = self._make_request("GET", "/records", params=params)
        return response.json()

    def get_record(self, record_id: str) -> Dict[str, Any]:
        """
        Get a specific published record by ID.

        Args:
            record_id: Record identifier

        Returns:
            Record data
        """
        response = self._make_request("GET", f"/records/{record_id}")
        return response.json()

    def get_record_files(self, record_id: str) -> Dict[str, Any]:
        """
        Get files associated with a record.

        Args:
            record_id: Record identifier

        Returns:
            Files information
        """
        response = self._make_request("GET", f"/records/{record_id}/files")
        return response.json()

    # =====================================
    # DRAFTS API
    # =====================================

    def create_draft(
        self,
        metadata: Dict[str, Any],
        access: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new draft record.

        Args:
            metadata: Record metadata
            access: Access settings for the record
            files: Files configuration
            custom_fields: Custom fields metadata

        Returns:
            Created draft data
        """
        data = {"metadata": metadata}

        if access:
            data["access"] = access
        if files:
            data["files"] = files
        if custom_fields:
            data["custom_fields"] = custom_fields

        response = self._make_request("POST", "/records", json=data)
        return response.json()

    def create_draft_from_record(self, record_id: str) -> Dict[str, Any]:
        """
        Create a new draft from an existing published record (for editing).

        Args:
            record_id: Published record identifier

        Returns:
            Created draft data
        """
        response = self._make_request("POST", f"/records/{record_id}/draft")
        return response.json()

    def get_draft(self, record_id: str) -> Dict[str, Any]:
        """
        Get a draft record by ID.

        Args:
            record_id: Record identifier

        Returns:
            Draft record data
        """
        response = self._make_request("GET", f"/records/{record_id}/draft")
        return response.json()

    def update_draft(
        self,
        record_id: str,
        metadata: Dict[str, Any],
        custom_fields: Optional[Dict[str, Any]] = None,
        access: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update a draft record.

        Args:
            record_id: Record identifier
            metadata: Updated metadata
            custom_fields: Updated custom fields
            access: Updated access settings
            files: Updated files configuration

        Returns:
            Updated draft data
        """
        data = {"metadata": metadata}

        if custom_fields:
            data["custom_fields"] = custom_fields
        if access:
            data["access"] = access
        if files:
            data["files"] = files

        response = self._make_request("PUT", f"/records/{record_id}/draft", json=data)
        return response.json()

    def publish_draft(self, record_id: str) -> Dict[str, Any]:
        """
        Publish a draft record.

        Args:
            record_id: Record identifier

        Returns:
            Published record data
        """
        response = self._make_request("POST", f"/records/{record_id}/draft/actions/publish")
        return response.json()

    def delete_draft(self, record_id: str) -> bool:
        """
        Delete a draft record.

        Args:
            record_id: Record identifier

        Returns:
            True if deletion was successful
        """
        try:
            self._make_request("DELETE", f"/records/{record_id}/draft")
            return True
        except requests.RequestException:
            return False

    def delete_record(self, record_id: str) -> bool:
        """
        Delete a published record.

        Args:
            record_id: Record identifier

        Returns:
            True if deletion was successful
        """
        try:
            self._make_request("DELETE", f"/records/{record_id}")
            return True
        except requests.RequestException:
            return False

    # =====================================
    # FILES API
    # =====================================

    def init_draft_files(self, record_id: str, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Initialize file uploads for a draft.

        Args:
            record_id: Record identifier
            files: List of files to initialize (each with 'key' field)

        Returns:
            Files initialization response
        """
        response = self._make_request("POST", f"/records/{record_id}/draft/files", json=files)
        return response.json()

    def upload_draft_file(self, record_id: str, filename: str, file_data: bytes) -> Dict[str, Any]:
        """
        Upload file content to a draft.

        Args:
            record_id: Record identifier
            filename: Name of the file
            file_data: File content as bytes

        Returns:
            Upload response
        """
        headers = {"Content-Type": "application/octet-stream"}
        response = self.session.put(
            urljoin(self.api_url, f"records/{record_id}/draft/files/{filename}/content"),
            data=file_data,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def commit_draft_file(self, record_id: str, filename: str) -> Dict[str, Any]:
        """
        Commit an uploaded file for a draft.

        Args:
            record_id: Record identifier
            filename: Name of the file to commit

        Returns:
            Commit response
        """
        response = self._make_request("POST", f"/records/{record_id}/draft/files/{filename}/commit")
        return response.json()

    # =====================================
    # STATISTICS API
    # =====================================

    def get_statistics(self, queries: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics for records, views, downloads, etc.

        Args:
            queries: Dictionary of named queries with their configurations
                    Example: {
                        "views": {
                            "stat": "record-view",
                            "params": {"recid": "abcd-1234"}
                        }
                    }

        Returns:
            Statistics results
        """
        response = self._make_request("POST", "/stats", json=queries)
        return response.json()

    # =====================================
    # USERS API
    # =====================================

    def search_users(
        self, q: str = "", sort: str = "bestmatch", size: int = 10, page: int = 1
    ) -> Dict[str, Any]:
        """
        Search for users.

        Args:
            q: Search query
            sort: Sort order
            size: Number of results per page
            page: Page number

        Returns:
            User search results
        """
        params = {"q": q, "sort": sort, "size": size, "page": page}
        response = self._make_request("GET", "/users", params=params)
        return response.json()

    # =====================================
    # COMMUNITIES API
    # =====================================

    def search_communities(self, q: str = "", **params) -> Dict[str, Any]:
        """
        Search communities.

        Args:
            q: Search query
            **params: Additional query parameters

        Returns:
            Community search results
        """
        params["q"] = q
        response = self._make_request("GET", "/communities", params=params)
        return response.json()

    def get_community(self, community_id: str) -> Dict[str, Any]:
        """
        Get a specific community by ID.

        Args:
            community_id: Community identifier

        Returns:
            Community data
        """
        response = self._make_request("GET", f"/communities/{community_id}")
        return response.json()

    # =====================================
    # UTILITY METHODS
    # =====================================

    def create_simple_record(
        self,
        title: str,
        creators: List[Dict[str, Any]],
        description: str = "",
        resource_type: str = "dataset",
        publication_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a simple record with minimal metadata.

        Args:
            title: Record title
            creators: List of creators
            description: Record description
            resource_type: Type of resource
            publication_date: Publication date (ISO format)

        Returns:
            Created draft record
        """
        from datetime import datetime

        if not publication_date:
            publication_date = datetime.now().strftime("%Y-%m-%d")

        metadata = {
            "title": title,
            "creators": creators,
            "resource_type": {"id": resource_type},
            "publication_date": publication_date,
        }

        if description:
            metadata["description"] = description

        return self.create_draft(metadata)

    def upload_file_to_draft(self, record_id: str, filepath: str) -> Dict[str, Any]:
        """
        Upload a file from local filesystem to a draft.

        Args:
            record_id: Record identifier
            filepath: Path to local file

        Returns:
            Upload result information
        """
        import os

        filename = os.path.basename(filepath)

        # Initialize file upload
        self.init_draft_files(record_id, [{"key": filename}])

        # Upload file content
        with open(filepath, "rb") as f:
            file_data = f.read()

        upload_result = self.upload_draft_file(record_id, filename, file_data)

        # Commit the file
        commit_result = self.commit_draft_file(record_id, filename)

        return {"upload": upload_result, "commit": commit_result}


def create_client_from_env() -> InvenioRDMClient:
    """
    Create an InvenioRDM client using environment variables.

    Environment variables:
    - INVENIO_BASE_URL: Base URL of the InvenioRDM instance
    - INVENIO_TOKEN: API Bearer token

    Returns:
        Configured InvenioRDMClient instance
    """
    from dotenv import load_dotenv

    load_dotenv()

    base_url = os.getenv("INVENIO_BASE_URL")
    token = os.getenv("INVENIO_TOKEN")

    if not base_url:
        raise ValueError("INVENIO_BASE_URL environment variable is required")

    return InvenioRDMClient(base_url, token)
