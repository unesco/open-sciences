#!/usr/bin/env python3
"""
InvenioRDM Scripts - Main entry point

This script provides a simple interface to run various InvenioRDM operations.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


# Check if required environment variables are set
def check_environment():
    """Check if required environment variables are configured."""
    if not os.getenv("INVENIO_BASE_URL"):
        print("❌ Error: INVENIO_BASE_URL environment variable is required")
        print(
            "Please copy config/.env.example to config/.env and configure your settings"
        )
        sys.exit(1)


def main():
    """Main entry point for the InvenioRDM scripts."""
    check_environment()

    print("🚀 InvenioRDM API Scripts")
    print("=" * 40)
    print("Available commands:")
    print("1. Search records: python examples/search_records.py --help")
    print("2. Create record: python examples/create_record.py --help")
    print("3. Get statistics: python examples/get_statistics.py --help")
    print("4. CLI tool: python examples/invenio_cli.py --help")
    print()
    print("Example usage:")
    print("  python examples/search_records.py -q 'climate data' -s 5")
    print("  python examples/create_record.py -t 'My Dataset' --creator 'John Doe'")
    print("  python examples/invenio_cli.py search -q 'test'")
    print()
    print("For detailed help on any command, add --help")


if __name__ == "__main__":
    main()
