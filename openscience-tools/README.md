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
make tools-setup-env

# Build the microservice container
make tools-build

# Test the connection
make tools-run CMD='python -m src.tools.cli test-connection'
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
make tools-build
```

## Usage Examples

### Search Records

```bash
# Basic search
make tools-run CMD='python -m src.tools.search -q "climate data" -s 10'

# Detailed view
make tools-run CMD='python -m src.tools.search -q "test" --detailed'

# With pagination
make tools-run CMD='python -m src.tools.search -q "dataset" --page 2 --size 20'
```

### View Record Details

```bash
# View formatted output
make tools-run CMD='python -m src.tools.view abc-123'

# View as JSON
make tools-run CMD='python -m src.tools.view abc-123 --format json'
```

### Get Statistics

```bash
# Record statistics
make tools-run CMD='python -m src.tools.stats --record-id abc-123'

# System statistics
make tools-run CMD='python -m src.tools.stats'
```

### Manage Records

```bash
# Delete all records (with confirmation)
make tools-delete-all

# Delete all (dry-run)
make tools-run CMD='python -m src.tools.cleanup --dry-run'

# Delete with confirmation flag
make tools-run CMD='python -m src.tools.cleanup --confirm'
```

### Use CLI Tool

```bash
# Test connection
make tools-run CMD='python -m src.tools.cli test-connection'

# Search records
make tools-run CMD='python -m src.tools.cli search -q "machine learning" -s 5'

# Get record details
make tools-run CMD='python -m src.tools.cli get abc-123'

# Create a new record
make tools-run CMD='python -m src.tools.cli create \
  --title "New Dataset" \
  --creator "Jane Smith" \
  --type dataset \
  --publish'
```

### Interactive Development

```bash
# Open interactive shell for development
make tools-shell

# Inside the container, you can run tools directly:
python -m src.tools.search -q test
python -m src.tools.view abc-123
```

### Import from External Data Sources

Import publication records from various external data sources:

#### Lens.org

Import publications from Lens.org JSON exports:

```bash
# Validate without creating records (dry-run)
make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--dry-run'

# Import all records from JSON file
make tools-import-lens FILE='src/sources/lens/data/publications.json'

# Import first 10 records
make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 10'

# Import with offset (skip first 10, import next 20)
make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--offset 10 --limit 20'

# Custom batch size with verbose output
make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--batch-size 5 --verbose'

# Force reimport of existing records
make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--no-skip-existing'
```

**Lens.org Import Features:**

- ✅ Standard metadata (title, creators, publication_date, publisher, description)
- ✅ Author identifiers (ORCID)
- ✅ Institutional affiliations (ROR IDs)
- ⚠️ Custom fields (requires InvenioRDM configuration)
- ⚠️ Related identifiers (DOI, PMID, PMCID, arXiv, etc.)
- ⚠️ Subject classification (MeSH terms, ASJC codes)

### Reset Records (Delete All + Import)

The `tools-reset` command combines record deletion with import from any source:

```bash
# Reset with CSV import
make tools-reset CSV='src/sources/csv/data/publications.csv'
make tools-reset CSV='data/my_records.csv' OPTS='--verbose'

# Reset with Lens import
make tools-reset LENS='src/sources/lens/data/publications.json'
make tools-reset LENS='data/my_lens_export.json' OPTS='--limit 10'

# Reset with Zenodo import (by record ID)
make tools-reset ZENODO_ID='17462748'
make tools-reset ZENODO_ID='17462748' OPTS='--skip-files'

# Reset with Zenodo import (by search query)
make tools-reset ZENODO_QUERY='climate data' MAX=5
make tools-reset ZENODO_QUERY='COVID-19' MAX=3 OPTS='--skip-files --verbose'
```

**Reset Features:**

- ✅ Deletes all existing records first
- ✅ Imports fresh data from any source (CSV, Lens, or Zenodo)
- ✅ Supports all source-specific options via `OPTS`
- ✅ Useful for development, testing, and data refresh workflows
- ⚠️ **Warning**: Permanently deletes all records before import

**Data Sources Architecture:**

All data source importers are organized under `src/sources/`:

```
src/sources/
├── README.md              # Documentation on adding new sources
├── csv/                   # CSV importer
│   ├── config.py
│   ├── reader.py
│   ├── mapper.py
│   ├── parsers.py
│   ├── importer.py
│   ├── main.py
│   └── data/publications.csv
├── lens/                  # Lens.org importer
│   ├── config.py
│   ├── reader.py
│   ├── importer.py
│   ├── main.py
│   ├── data/publications.json
│   └── mappers/
│       ├── standard.py
│       ├── custom.py
│       └── related.py
└── zenodo/                # Zenodo.org importer
    ├── config.py
    ├── fetcher.py         # API client
    ├── mapper.py
    ├── importer.py
    └── main.py
```

See `src/sources/README.md` for detailed documentation on:

- Adding new data sources
- Architecture and design patterns
- Testing and validation
- Performance considerations

**Future Data Sources:**

The architecture supports easy addition of new sources:

- DataCite
- Crossref
- OpenAlex
- PubMed/PMC
- Custom institutional repositories

## Docker Usage

### Using Make Commands (Recommended)

The project includes convenient Make commands for Docker operations:

```bash
# Auto-setup environment (generates .env with API token)
make tools-setup-env

# Build the container
make tools-build

# Run tools
make tools-run CMD='python -m src.tools.search -q test'

# Interactive shell
make tools-shell

# Show all available commands
make tools-help
```

### Direct Docker Commands

If you prefer using Docker directly:

```bash
# Build the container
docker build -t invenio-scripts .

# Run with environment file (after setup)
docker run --env-file config/.env invenio-scripts python -m src.tools.search -q "test"

# With inline environment variables
docker run -e INVENIO_BASE_URL=https://your-rdm.example.com \
           -e INVENIO_TOKEN=your_token \
           invenio-scripts python -m src.tools.cli test-connection
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

### Management Tools

Located in `src/tools/`, these tools help manage and interact with InvenioRDM:

- **`search.py`**: Search and browse records with pagination and detailed views

  ```bash
  python -m src.tools.search -q "query" --size 10 --detailed
  ```

- **`view.py`**: View detailed record information

  ```bash
  python -m src.tools.view RECORD_ID
  ```

- **`stats.py`**: Get statistics for records or system

  ```bash
  python -m src.tools.stats --record-id abc-123
  ```

- **`cleanup.py`**: Delete all records (for testing/reset)

  ```bash
  python -m src.tools.cleanup --dry-run
  ```

- **`cli.py`**: Comprehensive CLI with all operations
  ```bash
  python -m src.tools.cli test-connection
  python -m src.tools.cli search -q "test"
  ```

See [`src/tools/README.md`](src/tools/README.md) for detailed documentation.

### Data Import Sources

Located in `src/sources/`, these modules import data from various sources:

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
make tools-setup-env

# Build the development container
make tools-build
```

### Development Workflow

**1. Making Changes to Scripts**

Edit files in the `scripts/` directory:

- **API Client**: Modify `src/invenio_client.py` for new API features
- **Tools**: Add new management tools in `src/tools/` directory
- **Sources**: Add new data importers in `src/sources/` directory
- **Configuration**: Update `config/.env` if needed

**2. Testing Changes**

```bash
# Test individual tools
make tools-run CMD='python -m src.tools.your_new_tool'

# Test import sources
make tools-import-zenodo DRY_RUN=true

# Use interactive shell for development
make tools-shell
# Inside container:
python -m src.tools.search -q test
```

**3. Rebuilding After Changes**

If you modify the Dockerfile or requirements.txt:

```bash
make tools-build
```

**4. Environment Regeneration**

If you need a fresh API token or environment:

```bash
make tools-setup-env
```

### Creating New Tools

**Template for a new management tool:**

```python
#!/usr/bin/env python3
"""
New tool example - Tool description
"""

import click
import logging
from colorama import Fore, Style
from src.invenio_client import create_client_from_env

logger = logging.getLogger(__name__)

def core_logic(client, query):
    """Core functionality."""
    try:
        results = client.search_records(q=query)
        return results
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

@click.command()
@click.option('-q', '--query', help='Search query')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def main(query, verbose):
    """
    Your tool description.

    Usage: python -m src.tools.newtool -q "test"
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    client = create_client_from_env()

    try:
        results = core_logic(client, query)
        total = results.get('hits', {}).get('total', 0)
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} Found {total} results")
    except Exception as e:
        print(f"{Fore.RED}✗{Style.RESET_ALL} Error: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
```

**Add to src/tools directory:**

```bash
# Create your tool
nano scripts/src/tools/my_new_tool.py

# Update src/tools/__init__.py to export it
# Add documentation to src/tools/README.md

# Test it
make tools-run CMD='python -m src.tools.my_new_tool -q test'
```

**Creating New Import Sources:**

Follow the modular pattern in `src/sources/`. Example:

```bash
# Create new source directory
mkdir -p scripts/src/sources/newsource

# Add required modules
touch scripts/src/sources/newsource/__init__.py
touch scripts/src/sources/newsource/config.py
touch scripts/src/sources/newsource/fetcher.py
touch scripts/src/sources/newsource/mapper.py
touch scripts/src/sources/newsource/importer.py
touch scripts/src/sources/newsource/main.py

# Add Makefile target
# Add documentation
```

See `src/sources/zenodo/` for a complete implementation example.

### Adding a New Data Source

To add a new data source importer (e.g., DataCite):

**1. Create directory structure:**

```bash
cd scripts/src/sources
mkdir -p datacite/{data,mappers}
```

**2. Implement core modules:**

```bash
# Copy template from lens/ and adapt
cp lens/base.py datacite/
cp lens/config.py datacite/
cp lens/reader.py datacite/
cp lens/importer.py datacite/
cp lens/mappers/*.py datacite/mappers/
```

**3. Create main.py module:**

```bash
# Create src/sources/datacite/main.py
# Follow the pattern from src/sources/lens/main.py
# Include CLI, environment setup, and import orchestration
```

**4. Update Makefile:**

```makefile
tools-import-datacite:
	@echo "🔬 Importing from DataCite..."
	@CMD="python -m src.sources.datacite --file $(FILE)"; \
	if [ -n "$(OPTS)" ]; then \
		CMD="$$CMD $(OPTS)"; \
	fi; \
	docker-compose -f docker-compose.scripts.yml run --rm tools-cli $$CMD
```

**5. Test your importer:**

```bash
make tools-import-datacite FILE='src/sources/datacite/data/sample.json' OPTS='--dry-run'
```

See `src/sources/README.md` for detailed documentation and patterns.

### Available Development Tools

**Interactive Python Shell:**

```bash
make tools-shell
# Inside container:
python3
>>> from src.invenio_client import create_client_from_env
>>> client = create_client_from_env()
>>> results = client.search_records(q="test")
```

**Direct Script Execution:**

```bash
# Run any Python command in the container
make tools-run CMD='python -c "from src.invenio_client import create_client_from_env; print(create_client_from_env().base_url)"'
```

**Environment Debugging:**

```bash
# Check environment variables
make tools-run CMD='python -c "import os; print(os.environ.get(\"INVENIO_BASE_URL\"))"'

# Test connection
make tools-run CMD='python -m src.tools.cli test-connection'
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
2. Create new tools in `src/tools/` or import sources in `src/sources/`
3. Update relevant README files with new functionality
4. Test with your InvenioRDM instance
5. Follow the established modular patterns

See the existing tools and sources for reference implementations.

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check your `INVENIO_BASE_URL` and network connectivity
2. **Authentication Errors**: Verify your `INVENIO_TOKEN` is valid and has necessary permissions
3. **Permission Errors**: Ensure your token has the required scopes for the operations you're performing

### Debug Mode

Enable verbose output in CLI tools:

```bash
python -m src.tools.cli --verbose test-connection
python -m src.tools.search -q test --verbose
```

### API Debugging

Set logging level to DEBUG:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project follows the same license as InvenioRDM (MIT License).
