````markdown
# OpenScience Tools

A Python package providing command-line tools for interacting with InvenioRDM REST API.

## Features

- **Comprehensive API Client**: Full-featured Python client for InvenioRDM REST API
- **Search & Discovery**: Search and browse records
- **Record Management**: View record details and cleanup operations
- **Lens.org Import**: Import publications from Lens.org JSON exports
- **CLI Tools**: Unified command-line interface for all operations
- **Flexible Configuration**: Pass credentials via environment variables or command-line options

## Installation

### From GitLab Package Registry

```bash
pip install openscience-tools --index-url https://gitlab.example.com/api/v4/projects/YOUR_PROJECT_ID/packages/pypi/simple
```

### From Source (Development)

```bash
# Clone the repository
git clone https://gitlab.example.com/your-group/sc-openscience.git
cd sc-openscience/openscience-tools

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

## Quick Start

All commands require InvenioRDM connection credentials:

- `--base-url`: InvenioRDM instance URL (e.g., `https://127.0.0.1:5000`)
- `--token`: InvenioRDM API token

These can be provided via:

1. Command-line options: `openscience-tools --base-url URL --token TOKEN <command>`
2. Environment variables: `export INVENIO_BASE_URL=URL INVENIO_TOKEN=TOKEN`

## Usage Examples

### Search Records

```bash
# Using environment variables
export INVENIO_BASE_URL=https://127.0.0.1:5000
export INVENIO_TOKEN=your-api-token

# Basic search
openscience-tools search -q "climate data" -s 10

# Detailed view
openscience-tools search -q "test" --detailed

# With pagination
openscience-tools search -q "dataset" --page 2 --size 20

# Or pass credentials as options
openscience-tools --base-url https://127.0.0.1:5000 --token your-token search -q "test"
```

### View Record Details

```bash
# View formatted output
openscience-tools view abc-123

# View as JSON
openscience-tools view abc-123 --format json
```

### Manage Records

```bash
# Delete all records (dry-run)
openscience-tools cleanup --dry-run

# Delete all (with confirmation)
openscience-tools cleanup --confirm

# Verbose output
openscience-tools cleanup --confirm --verbose
```

### Import from Lens.org

Import publications from Lens.org JSON exports:

```bash
# Validate without creating records (dry-run)
openscience-tools import-lens --file publications.json --dry-run

# Import all records from JSON file
openscience-tools import-lens --file publications.json

# Import first 10 records
openscience-tools import-lens --file publications.json --limit 10

# Import with offset (skip first 10, import next 20)
openscience-tools import-lens --file publications.json --offset 10 --limit 20

# Custom batch size with verbose output
openscience-tools import-lens --file publications.json --batch-size 5 --verbose

# Force reimport of existing records
openscience-tools import-lens --file publications.json --no-skip-existing
```

**Lens.org Import Features:**

- ✅ Standard metadata (title, creators, publication_date, publisher, description)
- ✅ Author identifiers (ORCID)
- ✅ Institutional affiliations (ROR IDs)
- ✅ Related identifiers (DOI, PMID, PMCID, arXiv, etc.)
- ✅ Subject classification (MeSH terms, ASJC codes)
- ✅ Custom fields mapping (requires InvenioRDM configuration)
````
