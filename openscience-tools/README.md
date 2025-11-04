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
