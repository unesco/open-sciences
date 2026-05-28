"""
Base classes and interfaces for Lens.org to InvenioRDM mapping.

This module defines abstract base classes and common interfaces
used by all mapper implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseMapper(ABC):
    """
    Abstract base class for all field mappers.

    All mappers should inherit from this class and implement
    the map() method to transform Lens.org data to InvenioRDM format.
    """

    def __init__(self, config: Optional[object] = None):
        """
        Initialize the mapper.

        Args:
            config: Configuration object (usually LensImportConfig)
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def map(self, lens_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Lens.org record fields to InvenioRDM format.

        Args:
            lens_record: Raw Lens.org publication record

        Returns:
            Mapped data in InvenioRDM format

        Raises:
            ValueError: If required fields are missing
            MappingError: If mapping fails
        """
        pass

    def safe_get(self, data: Dict, *keys: str, default: Any = None) -> Any:
        """
        Safely get a nested value from dictionary.

        Args:
            data: Dictionary to extract from
            *keys: Sequence of keys for nested access
            default: Default value if key not found

        Returns:
            Value at nested key or default

        Example:
            safe_get(data, "source", "title", default="Unknown")
        """
        current = data
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
            if current is None:
                return default
        return current

    def clean_html(self, text: str) -> str:
        """
        Remove HTML tags from text.

        Args:
            text: Text potentially containing HTML

        Returns:
            Plain text without HTML tags
        """
        if not text:
            return ""

        import re

        # Remove HTML tags
        clean = re.sub(r"<[^>]+>", "", text)
        # Replace multiple newlines with double newline
        clean = re.sub(r"\n\s*\n+", "\n\n", clean)
        # Remove excessive whitespace
        clean = re.sub(r"[ \t]+", " ", clean)
        return clean.strip()

    def validate_required(self, data: Dict, *fields: str) -> bool:
        """
        Check if required fields are present.

        Args:
            data: Dictionary to check
            *fields: Required field names

        Returns:
            True if all required fields present, False otherwise
        """
        for field in fields:
            if not data.get(field):
                self.logger.warning(f"Missing required field: {field}")
                return False
        return True

    def log_mapping_info(self, lens_id: str, message: str):
        """Log info message with lens_id context."""
        self.logger.info(f"[{lens_id}] {message}")

    def log_mapping_warning(self, lens_id: str, message: str):
        """Log warning message with lens_id context."""
        self.logger.warning(f"[{lens_id}] {message}")

    def log_mapping_error(self, lens_id: str, message: str):
        """Log error message with lens_id context."""
        self.logger.error(f"[{lens_id}] {message}")


class MappingError(Exception):
    """Exception raised when mapping fails."""

    def __init__(self, message: str, lens_id: str = None, field: str = None):
        """
        Initialize mapping error.

        Args:
            message: Error message
            lens_id: Lens.org ID of the record
            field: Field name that caused the error
        """
        self.lens_id = lens_id
        self.field = field
        super().__init__(f"[{lens_id}] {field}: {message}" if lens_id else message)


class ValidationError(Exception):
    """Exception raised when validation fails."""

    def __init__(self, message: str, lens_id: str = None, errors: List[str] = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            lens_id: Lens.org ID of the record
            errors: List of specific validation errors
        """
        self.lens_id = lens_id
        self.errors = errors or []
        error_details = "\n  - ".join(self.errors) if self.errors else ""
        full_message = f"[{lens_id}] {message}" if lens_id else message
        if error_details:
            full_message += f"\n  - {error_details}"
        super().__init__(full_message)


class ImportResult:
    """
    Container for import operation results.

    Tracks success/failure status and provides detailed statistics.
    """

    def __init__(self):
        """Initialize empty result."""
        self.total_records = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.imported_ids: List[str] = []
        self.failed_ids: List[str] = []

    def record_success(self, lens_id: str, invenio_id: str = None):
        """
        Record a successful import.

        Args:
            lens_id: Lens.org ID
            invenio_id: InvenioRDM record ID
        """
        self.successful += 1
        self.imported_ids.append({"lens_id": lens_id, "invenio_id": invenio_id})

    def record_failure(self, lens_id: str, error: str, details: Dict = None):
        """
        Record a failed import.

        Args:
            lens_id: Lens.org ID
            error: Error message
            details: Additional error details
        """
        self.failed += 1
        self.failed_ids.append(lens_id)
        self.errors.append(
            {"lens_id": lens_id, "error": error, "details": details or {}}
        )

    def record_skip(self, lens_id: str, reason: str):
        """
        Record a skipped record.

        Args:
            lens_id: Lens.org ID
            reason: Reason for skipping
        """
        self.skipped += 1
        self.warnings.append({"lens_id": lens_id, "warning": reason})

    def record_warning(self, lens_id: str, warning: str):
        """
        Record a warning.

        Args:
            lens_id: Lens.org ID
            warning: Warning message
        """
        self.warnings.append({"lens_id": lens_id, "warning": warning})

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary.

        Returns:
            Dictionary representation of results
        """
        return {
            "summary": {
                "total_records": self.total_records,
                "successful": self.successful,
                "failed": self.failed,
                "skipped": self.skipped,
                "success_rate": (
                    f"{(self.successful / self.total_records * 100):.1f}%"
                    if self.total_records > 0
                    else "0%"
                ),
            },
            "imported_records": self.imported_ids,
            "failed_records": self.failed_ids,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def __str__(self) -> str:
        """String representation of results."""
        return (
            f"Import Results:\n"
            f"  Total: {self.total_records}\n"
            f"  Successful: {self.successful}\n"
            f"  Failed: {self.failed}\n"
            f"  Skipped: {self.skipped}\n"
            f"  Success Rate: {(self.successful / self.total_records * 100):.1f}%"
            if self.total_records > 0
            else "No records processed"
        )
