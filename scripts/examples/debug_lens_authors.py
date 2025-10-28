#!/usr/bin/env python3
"""Quick debug script to check author structure."""

import sys
import json
from pathlib import Path

json_file = Path("data/lens.org/publications.json")

with open(json_file) as f:
    data = json.load(f)

first_record = data[0]

print("First record lens_id:", first_record.get("lens_id"))
print("First record title:", first_record.get("title")[:60])
print()
print("Authors field exists:", "authors" in first_record)
print("Number of authors:", len(first_record.get("authors", [])))
print()

if first_record.get("authors"):
    print("First author:")
    print(json.dumps(first_record["authors"][0], indent=2))
