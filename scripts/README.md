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
make scripts-run CMD='python -m src.tools.cli test-connection'
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
# Basic search
make scripts-run CMD='python -m src.tools.search -q "climate data" -s 10'

# Detailed view
make scripts-run CMD='python -m src.tools.search -q "test" --detailed'

# With pagination
make scripts-run CMD='python -m src.tools.search -q "dataset" --page 2 --size 20'
```

### View Record Details

```bash
# View formatted output
make scripts-run CMD='python -m src.tools.view abc-123'

# View as JSON
make scripts-run CMD='python -m src.tools.view abc-123 --format json'
```

### Get Statistics

```bash
# Record statistics
make scripts-run CMD='python -m src.tools.stats --record-id abc-123'

# System statistics
make scripts-run CMD='python -m src.tools.stats'
```

### Manage Records

```bash
# Delete all records (with confirmation)
make scripts-delete-all

# Delete all (dry-run)
make scripts-run CMD='python -m src.tools.cleanup --dry-run'

# Delete with confirmation flag
make scripts-run CMD='python -m src.tools.cleanup --confirm'
```

### Use CLI Tool

```bash
# Test connection
make scripts-run CMD='python -m src.tools.cli test-connection'

# Search records
make scripts-run CMD='python -m src.tools.cli search -q "machine learning" -s 5'

# Get record details
make scripts-run CMD='python -m src.tools.cli get abc-123'

# Create a new record
make scripts-run CMD='python -m src.tools.cli create \
  --title "New Dataset" \
  --creator "Jane Smith" \
  --type dataset \
  --publish'
```

### Interactive Development

```bash
# Open interactive shell for development
make scripts-shell

# Inside the container, you can run tools directly:
python -m src.tools.search -q test
python -m src.tools.view abc-123
```

### Import Records from CSV

Import or update records in bulk from a CSV file:

```bash
# Import records from the example CSV
make scripts-import-csv FILE='src/sources/csv/data/publications.csv'

# Import with dry-run mode (validate without creating records)
make scripts-import-csv FILE='src/sources/csv/data/publications.csv' OPTS='--dry-run'

# Import with options
make scripts-import-csv FILE='src/sources/csv/data/publications.csv' OPTS='--skip-errors --verbose'

# Import with custom delimiter
make scripts-import-csv FILE='data/publications.tsv' OPTS="--delimiter $'\t'"
```

**CSV File Format**

The CSV file should contain the following columns:

**Required columns:**

- `title`: Record title
- `creators`: Semicolon and pipe-separated list of creators
  - Format: `"Given Family; ORCID; Affiliation | Given2 Family2; ORCID2; Affiliation2"`
  - ORCID and Affiliation are optional
  - Example: `"John Doe;0000-0001-2345-6789;MIT | Jane Smith;;Harvard"`

**Optional columns:**

- `record_id`: Existing record ID for updates (leave empty for new records)
- `description`: Record description
- `resource_type`: Resource type (default: `dataset`)
  - Options: `dataset`, `publication-article`, `software`, `image-photo`, etc.
- `publication_date`: Publication date in YYYY-MM-DD format (default: today)
- `access_record`: Record access level (`public` or `restricted`, default: `public`)
- `access_files`: Files access level (`public` or `restricted`, default: `public`)
- `file_paths`: Semicolon-separated list of file paths to upload
  - Example: `"/path/to/file1.csv;/path/to/file2.txt"`
- `publish`: Whether to publish immediately (`yes`/`no`, default: `no`)

**Example CSV:**

```csv
title,description,creators,resource_type,publication_date,access_record,access_files,publish
"Climate Dataset","Climate change data","Maria Rossi;0000-0001-2345-6789;University of Rome",dataset,2024-01-15,public,public,yes
"AI Research","Deep learning study","Alice Smith;;MIT | Bob Johnson;0000-0002-3456-7890;Stanford",publication-article,2024-02-20,public,restricted,no
```

See `scripts/data/sample_records.csv` for a complete example.

**Import Options:**

- `--dry-run`: Validate CSV and show what would be created without making changes
- `--skip-errors`: Continue processing even if some records fail
- `--verbose`: Show detailed information for each record
- `--delimiter`: Specify CSV delimiter (default: comma)

### Import from External Data Sources

Import publication records from various external data sources:

#### Lens.org

Import publications from Lens.org JSON exports:

```bash
# Validate without creating records (dry-run)
make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--dry-run'

# Import all records from JSON file
make scripts-import-lens FILE='src/sources/lens/data/publications.json'

# Import first 10 records
make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 10'

# Import with offset (skip first 10, import next 20)
make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--offset 10 --limit 20'

# Custom batch size with verbose output
make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--batch-size 5 --verbose'

# Force reimport of existing records
make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--no-skip-existing'
```

**Lens.org Import Features:**

- ✅ Standard metadata (title, creators, publication_date, publisher, description)
- ✅ Author identifiers (ORCID)
- ✅ Institutional affiliations (ROR IDs)
- ⚠️ Custom fields (requires InvenioRDM configuration)
- ⚠️ Related identifiers (DOI, PMID, PMCID, arXiv, etc.)
- ⚠️ Subject classification (MeSH terms, ASJC codes)

#### Zenodo

Import records from Zenodo.org via their public API:

```bash
# Import a specific record by ID
make scripts-import-zenodo RECORD_ID='17462748'

# Import without files (metadata only)
make scripts-import-zenodo RECORD_ID='17462748' OPTS='--skip-files'

# Dry run (validate without importing)
make scripts-import-zenodo RECORD_ID='17462748' OPTS='--dry-run'

# Search and import multiple records
make scripts-import-zenodo QUERY='climate data' MAX=5

# Search with file skipping
make scripts-import-zenodo QUERY='COVID-19' MAX=3 OPTS='--skip-files'

# Verbose output
make scripts-import-zenodo RECORD_ID='17462748' OPTS='--verbose'
```

**Zenodo Import Features:**

- ✅ Import by Zenodo record ID
- ✅ Search and bulk import
- ✅ Complete metadata (creators, contributors, identifiers, keywords)
- ✅ Automatic file download and upload
- ✅ ORCID identifier preservation
- ✅ License mapping
- ✅ HTML description cleaning
- ✅ Related identifiers (DOI, arXiv, etc.)
- ✅ Dry-run mode for validation

### Reset Records (Delete All + Import)

The `scripts-reset` command combines record deletion with import from any source:

```bash
# Reset with CSV import
make scripts-reset CSV='src/sources/csv/data/publications.csv'
make scripts-reset CSV='data/my_records.csv' OPTS='--verbose'

# Reset with Lens import
make scripts-reset LENS='src/sources/lens/data/publications.json'
make scripts-reset LENS='data/my_lens_export.json' OPTS='--limit 10'

# Reset with Zenodo import (by record ID)
make scripts-reset ZENODO_ID='17462748'
make scripts-reset ZENODO_ID='17462748' OPTS='--skip-files'

# Reset with Zenodo import (by search query)
make scripts-reset ZENODO_QUERY='climate data' MAX=5
make scripts-reset ZENODO_QUERY='COVID-19' MAX=3 OPTS='--skip-files --verbose'
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
make scripts-setup-env

# Build the container
make scripts-build

# Run tools
make scripts-run CMD='python -m src.tools.search -q test'

# Interactive shell
make scripts-shell

# Show all available commands
make scripts-help
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
make scripts-setup-env

# Build the development container
make scripts-build
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
make scripts-run CMD='python -m src.tools.your_new_tool'

# Test import sources
make scripts-import-zenodo DRY_RUN=true

# Use interactive shell for development
make scripts-shell
# Inside container:
python -m src.tools.search -q test
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
make scripts-run CMD='python -m src.tools.my_new_tool -q test'
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
scripts-import-datacite:
	@echo "🔬 Importing from DataCite..."
	@CMD="python -m src.sources.datacite --file $(FILE)"; \
	if [ -n "$(OPTS)" ]; then \
		CMD="$$CMD $(OPTS)"; \
	fi; \
	docker-compose -f docker-compose.scripts.yml run --rm scripts-cli $$CMD
```

**5. Test your importer:**

```bash
make scripts-import-datacite FILE='src/sources/datacite/data/sample.json' OPTS='--dry-run'
```

See `src/sources/README.md` for detailed documentation and patterns.

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
make scripts-run CMD='python -m src.tools.cli test-connection'
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
