#!/usr/bin/env python3
"""
Simple connection test script
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests
import json
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_simple_connection():
    """Test a simple connection without the full client."""

    base_url = os.getenv("INVENIO_BASE_URL", "https://127.0.0.1:5000")
    token = os.getenv("INVENIO_TOKEN", "")

    print(f"🔍 Testing connection to: {base_url}")
    print(f"🔑 Using token: {token[:20]}...")

    # Test basic connectivity first
    try:
        print("📡 Testing basic connectivity...")
        response = requests.get(f"{base_url}/", timeout=10, verify=False)
        print(f"✅ Basic connection successful: {response.status_code}")
    except Exception as e:
        print(f"❌ Basic connection failed: {e}")
        return False

    # Test API endpoint
    try:
        print("🔍 Testing API endpoint...")
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        response = requests.get(
            f"{base_url}/api/", headers=headers, timeout=10, verify=False
        )
        print(f"✅ API connection successful: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"📊 API response: {json.dumps(data, indent=2)}")

        return True

    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False


if __name__ == "__main__":
    test_simple_connection()
