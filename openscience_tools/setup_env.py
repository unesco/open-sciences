#!/usr/bin/env python3
"""
Automatic environment setup script for the scripts microservice.
Automatically generates API token and configures .env file
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path


def run_command(cmd, shell=True, capture_output=True, text=True):
    """Executes a command and returns the result"""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=capture_output, text=text, check=True
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing command: {cmd}")
        print(f"   Output: {e.stdout}")
        print(f"   Error: {e.stderr}")
        return None


def check_invenio_running():
    """Checks if InvenioRDM is running"""
    print("🔍 Checking if InvenioRDM is running...")

    # Try to make HTTP request to InvenioRDM
    import requests
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # List of endpoints to try
    endpoints = [
        "https://127.0.0.1:5000/",
        "https://127.0.0.1:5000/records",
        "http://127.0.0.1:5000/",
        "http://127.0.0.1:5000/records",
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, verify=False, timeout=10)
            if response.status_code in [
                200,
                404,
            ]:  # 404 is OK, means server responds
                protocol = "HTTPS" if endpoint.startswith("https") else "HTTP"
                print(f"✅ InvenioRDM is running and reachable ({protocol})")
                return True
        except Exception:
            continue

    print("❌ InvenioRDM does not seem to be running")
    print("   Run 'make up' to start InvenioRDM before continuing")
    return False

def get_existing_token():
    """Searches for existing token in .env file"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("OPENSCIENCE_TOOLS_TOKEN=") and "=" in line:
                    token = line.split("=", 1)[1].strip()
                    if token and token != "your_generated_token_here" and token != "":
                        return token
    return None


def create_api_token():
    """Creates a new API token using InvenioRDM CLI"""
    print("🔑 Creating new API token with full permissions...")

    # Create token for admin user with all necessary scopes
    admin_email = "admin@unesco.org"
    token_name = "Scripts Microservice Token"

    # InvenioRDM requires specific scopes for record operations
    # Common scopes needed for full record management:
    # - user:email (read user email)
    # - For record operations, we typically need to be authenticated admin
    # The -i flag creates an internal token with more permissions
    cmd = f'invenio tokens create -n "{token_name}" -u "{admin_email}" -i'

    output = run_command(cmd)
    if output is None:
        print("❌ Error creating token")
        print("   Make sure user admin@unesco.org exists")
        print("   Run 'make users' to create default users")
        return None

    # Extract token from output
    lines = output.split("\n")
    for line in lines:
        if "Token:" in line or line.strip().startswith("Token"):
            # Search for token in output
            parts = line.split()
            for part in parts:
                if len(part) > 20 and not part.startswith("Token"):  # Token typically long
                    print(f"✅ API token created successfully")
                    return part.strip()

    # If we don't find "Token:" pattern, try extracting from end of output
    # which often contains the token
    clean_lines = [line.strip() for line in lines if line.strip()]
    if clean_lines:
        last_line = clean_lines[-1]
        # If last line is a token (long alphanumeric string)
        if len(last_line) > 20 and last_line.replace("-", "").replace("_", "").isalnum():
            print(f"✅ API token created successfully")
            return last_line

    print("❌ Token not found in command output")
    print(f"Complete output: {output}")
    return None


def create_env_file(token):
    """Updates main .env file with token"""
    print("📝 Updating .env file with OpenScience Tools credentials...")

    env_file = Path(".env")

    if not env_file.exists():
        print("❌ .env file not found. Run 'make config' first.")
        return False

    # Read existing content
    with open(env_file, "r") as f:
        lines = f.readlines()

    # Update or add OPENSCIENCE_TOOLS_TOKEN
    token_found = False
    updated_lines = []

    for line in lines:
        if line.startswith("OPENSCIENCE_TOOLS_TOKEN="):
            updated_lines.append(f"OPENSCIENCE_TOOLS_TOKEN={token}\n")
            token_found = True
        else:
            updated_lines.append(line)

    # If token line not found, add it after OPENSCIENCE_TOOLS_BASE_URL
    if not token_found:
        final_lines = []
        for i, line in enumerate(updated_lines):
            final_lines.append(line)
            if line.startswith("OPENSCIENCE_TOOLS_BASE_URL="):
                final_lines.append(f"OPENSCIENCE_TOOLS_TOKEN={token}\n")
        updated_lines = final_lines

    # Write back
    with open(env_file, "w") as f:
        f.writelines(updated_lines)

    print(f"✅ .env file updated successfully!")
    print(f"   OPENSCIENCE_TOOLS_TOKEN={token[:20]}...")
    return True


def main():
    """Main function"""
    print("🚀 Automatic setup for InvenioRDM Scripts microservice")
    print("=" * 50)

    # Check we're in correct directory
    if not Path("Makefile").exists():
        print("❌ This script must be run from project root")
        sys.exit(1)

    # Check if InvenioRDM is running
    if not check_invenio_running():
        print("\n💡 Suggestions:")
        print("   1. Run 'make init' if you haven't initialized the project yet")
        print("   2. Run 'make up' to start InvenioRDM")
        print("   3. Re-run this script after startup")
        sys.exit(1)

    # Check if valid token already exists
    existing_token = get_existing_token()
    if existing_token:
        print(f"ℹ️  Existing token found: {existing_token[:20]}...")
        response = input("Do you want to use the existing token? (y/N): ").strip().lower()
        if response == "y":
            print("✅ Using existing token")
            return

    # Create new token
    token = create_api_token()
    if not token:
        print("❌ Unable to create API token")
        sys.exit(1)

    # Create .env file
    if not create_env_file(token):
        print("❌ Unable to create .env file")
        sys.exit(1)

    print("\n✅ Setup completed successfully!")
    print("📋 Next steps:")
    print("   1. make tools-search QUERY='test'")
    print("   2. make tools-view RECORD_ID='abc-123'")
    print("   3. make tools-help    # See all available commands")


if __name__ == "__main__":
    main()
