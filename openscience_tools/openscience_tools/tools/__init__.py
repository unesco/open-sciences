"""
InvenioRDM management tools.

This package provides command-line utilities for managing InvenioRDM:

- search: Search and browse records
- cleanup: Delete records (bulk operations)
- stats: View statistics
- view: View record details
- cli: Comprehensive CLI tool

Usage:
    python -m src.tools.search --query "climate"
    python -m src.tools.cleanup --dry-run
    python -m src.tools.stats --record-id abc-123
    python -m src.tools.view abc-123
"""

__all__ = ["search", "cleanup", "stats", "view"]
