"""
Allow running the Lens.org importer as a module.

This enables execution via: python -m src.sources.lens
"""

from .main import main

if __name__ == "__main__":
    main()
