"""
OpenScience Tools - Python tools for InvenioRDM REST API.

A comprehensive Python package for interacting with InvenioRDM repositories,
providing tools for record management, search, statistics, and data import
from various sources.
"""

__version__ = "0.2.1"
__author__ = "UNESCO Science Portal Team"
__email__ = "info@unesco-science-portal.org"
__license__ = "MIT"

from .invenio_client import InvenioRDMClient

__all__ = ["InvenioRDMClient", "__version__"]
