# InvenioRDM API Scripts

A containerized Python microservice for interacting with InvenioRDM REST API.

## Features

- **Comprehensive API Client**: Full-featured Python client for InvenioRDM REST API
- **Search & Discovery**: Search records, users, and communities
- **Record Management**: Create, update, and publish record drafts
- **File Management**: Upload and manage files associated with records
- **Statistics**: Retrieve usage statistics and analytics
- **CLI Tools**: Command-line interface for common operations
- **Containerized**: Ready to run in Docker containers
- **Auto-Setup**: Automatic environment configuration with API token generation

## Quick Start

### 1. Automated Setup (Recommended)

From the project root directory:

```bash
# Ensure InvenioRDM is running
make up

# Auto-configure environment with API token generation
make scripts-setup-env

# Build the microservice container
make scripts-build

# Test the connection
make scripts-run CMD='python examples/invenio_cli.py test-connection'
```

This automated setup will:

- Check if InvenioRDM is running
- Create an API token for the admin user
- Generate the `.env` configuration file automatically
- No manual token creation required!

### 2. Manual Setup (if needed)

If you prefer manual configuration:

```bash
cp config/.env.example config/.env
# Edit config/.env with your settings
make scripts-build
```

## Usage Examples

### Search Records

```bash
make scripts-run CMD='python examples/search_records.py -q "climate data" -s 10 --detailed'
```

### Create a New Record

```bash
make scripts-run CMD='python examples/create_record.py \
  --title "My Research Dataset" \
  --creator "John Doe" \
  --creator-affiliation "University Example" \
  --description "This is a sample dataset" \
  --publish'
```

### Get Statistics

```bash
make scripts-run CMD='python examples/get_statistics.py --record-id abcd-1234'
```

### Use CLI Tool

```bash
# Test connection
make scripts-run CMD='python examples/invenio_cli.py test-connection'

# Search records
make scripts-run CMD='python examples/invenio_cli.py search -q "machine learning" -s 5'

# Get record details
make scripts-run CMD='python examples/invenio_cli.py get abcd-1234'

# Create a new record
make scripts-run CMD='python examples/invenio_cli.py create \
  --title "New Dataset" \
  --creator "Jane Smith" \
  --type dataset \
  --publish'
```

### Interactive Development

```bash
# Open interactive shell for development
make scripts-shell

# Inside the container, you can run any Python script:
python examples/search_records.py -q test
```

## Docker Usage

### Using Make Commands (Recommended)

The project includes convenient Make commands for Docker operations:

```bash
# Auto-setup environment (generates .env with API token)
make scripts-setup-env

# Build the container
make scripts-build

# Run scripts
make scripts-run CMD='python examples/search_records.py -q test'

# Interactive shell
make scripts-shell

# Show all available examples
make scripts-help
```

### Direct Docker Commands

If you prefer using Docker directly:

```bash
# Build the container
docker build -t invenio-scripts .

# Run with environment file (after setup)
docker run --env-file config/.env invenio-scripts python examples/search_records.py -q "test"

# With inline environment variables
docker run -e INVENIO_BASE_URL=https://your-rdm.example.com \
           -e INVENIO_TOKEN=your_token \
           invenio-scripts python examples/invenio_cli.py test-connection
```

### Using Docker Compose

```bash
# Build and run with Docker Compose
docker-compose -f ../docker-compose.scripts.yml build
docker-compose -f ../docker-compose.scripts.yml run scripts python main.py
```

## API Client Usage

### Basic Client Usage

```python
from src.invenio_client import InvenioRDMClient

# Initialize client
client = InvenioRDMClient(
    base_url="https://your-rdm.example.com",
    token="your_bearer_token"
)

# Search records
results = client.search_records(q="climate data", size=10)

# Get a specific record
record = client.get_record("abcd-1234")

# Create a new draft
draft = client.create_draft({
    "title": "My Dataset",
    "creators": [{
        "person_or_org": {
            "given_name": "John",
            "family_name": "Doe",
            "type": "personal"
        }
    }],
    "resource_type": {"id": "dataset"},
    "publication_date": "2024-01-15"
})
```

### Using Environment Variables

```python
from src.invenio_client import create_client_from_env

# Create client from environment variables
client = create_client_from_env()

# Now use the client
results = client.search_records(q="test")
```

## Available Scripts

### Core Examples

- **search_records.py**: Search and display InvenioRDM records
- **create_record.py**: Create new record drafts with files
- **get_statistics.py**: Retrieve and display statistics
- **invenio_cli.py**: Comprehensive CLI tool

### Script Options

Most scripts support these common options:

- `--help`: Show detailed help
- `--verbose`: Enable verbose output
- `--format`: Choose output format (table, json, etc.)
- `--size`: Number of results to return
- `--query`: Search query string

## Development

### Setting Up Development Environment

```bash
# From project root, start InvenioRDM first
make up

# Auto-configure the scripts environment
make scripts-setup-env

# Build the development container
make scripts-build
```

### Development Workflow

**1. Making Changes to Scripts**

Edit files in the `scripts/` directory:

- **API Client**: Modify `src/invenio_client.py` for new API features
- **Examples**: Add new scripts in `examples/` directory
- **Configuration**: Update `config/.env` if needed

**2. Testing Changes**

```bash
# Test individual scripts
make scripts-run CMD='python examples/your_new_script.py'

# Use interactive shell for development
make scripts-shell
# Inside container:
python your_script.py
```

**3. Rebuilding After Changes**

If you modify the Dockerfile or requirements.txt:

```bash
make scripts-build
```

**4. Environment Regeneration**

If you need a fresh API token or environment:

```bash
make scripts-setup-env
```

### Creating New Scripts

**Template for a new script:**

```python
#!/usr/bin/env python3
"""
New script example
"""

import sys
import argparse
from src.invenio_client import create_client_from_env

def main():
    parser = argparse.ArgumentParser(description='Your script description')
    parser.add_argument('-q', '--query', help='Search query')
    args = parser.parse_args()

    # Create client from environment
    client = create_client_from_env()

    # Your logic here
    try:
        results = client.search_records(q=args.query)
        print(f"Found {results.get('hits', {}).get('total', 0)} results")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Add to examples directory:**

```bash
# Create your script
nano scripts/examples/my_new_script.py

# Test it
make scripts-run CMD='python examples/my_new_script.py -q test'
```

### Available Development Tools

**Interactive Python Shell:**

```bash
make scripts-shell
# Inside container:
python3
>>> from src.invenio_client import create_client_from_env
>>> client = create_client_from_env()
>>> results = client.search_records(q="test")
```

**Direct Script Execution:**

```bash
# Run any Python command in the container
make scripts-run CMD='python -c "from src.invenio_client import create_client_from_env; print(create_client_from_env().base_url)"'
```

**Environment Debugging:**

```bash
# Check environment variables
make scripts-run CMD='python -c "import os; print(os.environ.get(\"INVENIO_BASE_URL\"))"'

# Test connection
make scripts-run CMD='python examples/invenio_cli.py test-connection'
```

## API Coverage

This client supports most InvenioRDM REST API endpoints:

### Records

- ✅ Search published records
- ✅ Get record details
- ✅ Get record files
- ✅ Create drafts
- ✅ Update drafts
- ✅ Publish drafts
- ✅ Delete drafts

### Files

- ✅ Initialize file uploads
- ✅ Upload file content
- ✅ Commit files
- ✅ Helper methods for complete upload workflow

### Statistics

- ✅ Get record statistics
- ✅ Custom statistics queries

### Users & Communities

- ✅ Search users
- ✅ Search communities
- ✅ Get community details

### Utilities

- ✅ Simple record creation helpers
- ✅ File upload helpers
- ✅ Environment-based configuration

## Error Handling

All API methods include proper error handling:

```python
try:
    record = client.get_record("invalid-id")
except requests.RequestException as e:
    print(f"API Error: {e}")
```

## Contributing

1. Add new features to `src/invenio_client.py`
2. Create example scripts in `examples/`
3. Update this README with new functionality
4. Test with your InvenioRDM instance

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check your `INVENIO_BASE_URL` and network connectivity
2. **Authentication Errors**: Verify your `INVENIO_TOKEN` is valid and has necessary permissions
3. **Permission Errors**: Ensure your token has the required scopes for the operations you're performing

### Debug Mode

Enable verbose output in CLI tools:

```bash
python examples/invenio_cli.py --verbose test-connection
```

### API Debugging

Set logging level to DEBUG:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project follows the same license as InvenioRDM (MIT License).
