#!/usr/bin/env python3
"""
View complete record details in JSON format
"""

import sys
from pathlib import Path
import json

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invenio_client import create_client_from_env

# Create client
client = create_client_from_env()

# Get record
record_id = sys.argv[1] if len(sys.argv) > 1 else "1xa96-qy479"

print(f"Fetching record {record_id}...\n")
record = client.get_record(record_id)

# Print formatted JSON
print(json.dumps(record, indent=2, ensure_ascii=False))
