"""
Allow running the Zenodo importer as a module.

Usage:
    python -m src.sources.zenodo --record-id 17462748
    python -m src.sources.zenodo --search "climate data" --max-results 5
"""

from .main import main

if __name__ == "__main__":
    main()
