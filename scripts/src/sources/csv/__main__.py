"""
Allow running the CSV importer as a module.

This enables execution via: python -m src.sources.csv
"""

from .main import main

if __name__ == "__main__":
    main()
