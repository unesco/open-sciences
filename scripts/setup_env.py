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


def activate_venv_and_run(cmd):
    """Activates virtual environment and executes a command"""
    venv_path = Path.cwd() / ".venv"
    if not venv_path.exists():
        print("❌ Virtual environment not found. Run 'make init' first.")
        return None

    # Command with venv activation
    full_cmd = f"source {venv_path}/bin/activate && {cmd}"
    return run_command(full_cmd, shell=True)


def get_existing_token():
    """Searches for existing token in .env file"""
    env_file = Path("scripts/config/.env")
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith("INVENIO_TOKEN=") and "=" in line:
                    token = line.split("=", 1)[1].strip()
                    if token and token != "your_bearer_token_here":
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

    output = activate_venv_and_run(cmd)
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
                if len(part) > 20 and not part.startswith(
                    "Token"
                ):  # Token typically long
                    print(f"✅ API token created successfully")
                    return part.strip()

    # If we don't find "Token:" pattern, try extracting from end of output
    # which often contains the token
    clean_lines = [line.strip() for line in lines if line.strip()]
    if clean_lines:
        last_line = clean_lines[-1]
        # If last line is a token (long alphanumeric string)
        if (
            len(last_line) > 20
            and last_line.replace("-", "").replace("_", "").isalnum()
        ):
            print(f"✅ API token created successfully")
            return last_line

    print("❌ Token not found in command output")
    print(f"Complete output: {output}")
    return None


def create_env_file(token):
    """Creates or updates .env file with token"""
    print("📝 Creating/updating .env file...")

    config_dir = Path("scripts/config")
    config_dir.mkdir(parents=True, exist_ok=True)

    env_file = config_dir / ".env"

    env_content = f"""# Environment Configuration for InvenioRDM Scripts
# File automatically generated by setup_env.py

# InvenioRDM Instance Configuration
# InvenioRDM uses HTTPS with self-signed certificates in development
INVENIO_BASE_URL=https://127.0.0.1:5000

# API Authentication - Automatically generated token
# Token created for user: admin@unesco.org
INVENIO_TOKEN={token}

# Optional: Default configurations
DEFAULT_RESOURCE_TYPE=dataset
DEFAULT_ACCESS_LEVEL=public

# Logging Configuration
LOG_LEVEL=INFO

# Note: This token was automatically generated
# To regenerate: make scripts-setup-env
"""

    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"✅ .env file created at: {env_file}")
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
        response = (
            input("Do you want to use the existing token? (y/N): ").strip().lower()
        )
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
    print("   1. make scripts-build   # Build the container")
    print("   2. make scripts-help    # See usage examples")
    print("   3. make scripts-run CMD='python examples/invenio_cli.py test-connection'")


if __name__ == "__main__":
    main()
