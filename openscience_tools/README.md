# OpenScience Tools

A Python package providing command-line tools for interacting with InvenioRDM REST API.

## Overview

OpenScience Tools is a comprehensive toolkit for managing and importing data into InvenioRDM instances. It provides both a **command-line interface** and a **Python SDK** for programmatic integration.

## Features

- **🐍 Python SDK**: Programmatic insert, update, delete operations for integration into your apps
- **🔍 Search & Discovery**: Search and browse records with flexible filters
- **👁️ Record Management**: View detailed record information and manage records
- **� CSV Export**: Export all records to CSV format for analysis and backup
- **�🗑️ Cleanup Operations**: Delete records with dry-run support
- **📚 Lens.org Import**: Import publications from Lens.org JSON exports with full metadata mapping
- **🔧 Flexible Configuration**: Use environment variables or command-line options
- **⚡ Fast & Lightweight**: No Docker overhead, direct Python package

## Installation

### From Project Root

If you're working within the sc-openscience project:

```bash
# From project root
cd /path/to/sc-openscience

# Ensure virtual environment is created and activated
source .venv/bin/activate

# Install the package in editable mode
cd openscience_tools
pip install -e .

# Or use the Makefile
cd ..
make tools-install
```

### From GitLab Package Registry

To install the published package from the GitLab Package Registry, you need to authenticate with a Personal Access Token.

#### Option 1: Using pip configuration file (Recommended)

Create a `pip.conf` file with your credentials:

```bash
# Create pip.conf
cat > pip.conf << 'EOF'
[global]
index-url = https://gitlab-ci-token:YOUR_TOKEN@repository.unesco.org/gitlab/api/v4/projects/488/packages/pypi/simple
extra-index-url = https://pypi.org/simple
EOF

# Install using the configuration
PIP_CONFIG_FILE=pip.conf pip install openscience-tools
```

#### Option 2: Direct installation with token

```bash
pip install openscience-tools \
  --index-url https://gitlab-ci-token:YOUR_TOKEN@repository.unesco.org/gitlab/api/v4/projects/488/packages/pypi/simple \
  --extra-index-url https://pypi.org/simple
```

> **Note**: Replace `YOUR_TOKEN` with an authentication token. If you don't have one, ask your tech lead for a token. If you have access to the GitLab repository, you can generate a Personal Access Token:
>
> 1. Go to: https://repository.unesco.org/gitlab/-/profile/personal_access_tokens
> 2. Click **"Add new token"**
> 3. Set a **token name** (e.g., `openscience-tools`) and **expiration date**
> 4. Select scopes: **`read_api`** and **`read_repository`**
> 5. Click **"Create personal access token"** and **copy it immediately** (shown only once!)

## Configuration

The package requires two configuration values:

- **Base URL**: Your InvenioRDM instance URL (e.g., `https://127.0.0.1:5000`)
- **API Token**: An InvenioRDM API token with appropriate permissions

### Method 1: Environment Variables

Add these to your `.env` file in the project root:

```bash
OPENSCIENCE_TOOLS_BASE_URL=https://127.0.0.1:5000
OPENSCIENCE_TOOLS_TOKEN=your-api-token-here
```

To generate a token automatically during development, run:

```bash
make tools-setup-env
```

In cases other than development, if you don't have one, ask your tech lead for the above token.

### Method 2: Command-Line Options

Pass credentials directly to each command:

```bash
openscience-tools --base-url https://127.0.0.1:5000 --token your-token search -q "test"
```

## Usage

### Search Records

Search and display records from your InvenioRDM instance:

```bash
# Basic search
openscience-tools search -q "climate data"

# Search with size limit
openscience-tools search -q "test" --size 5

# Detailed view
openscience-tools search -q "machine learning" --detailed

# With pagination
openscience-tools search -q "dataset" --page 2 --size 20

# Sort by newest
openscience-tools search -q "covid" --sort newest
```

**Available sort options**: `bestmatch`, `newest`, `oldest`

### View Record Details

Display detailed information about a specific record:

```bash
# View record (formatted output)
openscience-tools view abc-123

# View as JSON
openscience-tools view abc-123 --format json

# Verbose output with debug info
openscience-tools view abc-123 --verbose
```

### Export Records to CSV

Export all or filtered records from your InvenioRDM instance to CSV format:

```bash
# Export all records to default file (records.csv)
openscience-tools export

# Export to specific file
openscience-tools export --output my_records.csv

# Export only climate-related records
openscience-tools export -q "climate" -o climate_records.csv

# Export with all available fields
openscience-tools export --all-fields -o full_export.csv

# Export specific query with verbose output
openscience-tools export -q "dataset" -o datasets.csv --verbose
```

**CSV Export Features:**

- ✅ Automatic pagination (fetches all records)
- ✅ Basic fields: ID, title, creators, date, type, description, access
- ✅ Extended fields (with `--all-fields`): affiliations, DOI, ISBN, ISSN, subjects, related identifiers, language, rights, files info, URLs
- ✅ Query filtering support
- ✅ Progress tracking
- ✅ UTF-8 encoding for international characters

### Delete Records

Remove all records from your InvenioRDM instance:

```bash
# Dry-run (preview what would be deleted)
openscience-tools cleanup --dry-run

# Delete all records (interactive confirmation)
openscience-tools cleanup

# Delete with automatic confirmation
openscience-tools cleanup --confirm

# Verbose output
openscience-tools cleanup --confirm --verbose
```

⚠️ **Warning**: This operation is irreversible. Always use `--dry-run` first!

### Import from Lens.org

Import publications from Lens.org JSON export files:

```bash
# Validate metadata without creating records (dry-run)
openscience-tools import-lens --file publications.json --dry-run

# Import all records
openscience-tools import-lens --file publications.json

# Import first 10 records
openscience-tools import-lens --file publications.json --limit 10

# Skip first 10, import next 20
openscience-tools import-lens --file publications.json --offset 10 --limit 20

# Custom batch size (default: 10)
openscience-tools import-lens --file publications.json --batch-size 5

# Force reimport of existing records
openscience-tools import-lens --file publications.json --no-skip-existing

# Verbose output with debug info
openscience-tools import-lens --file publications.json --verbose
```

**Lens.org Import Features:**

- ✅ Standard bibliographic metadata (title, authors, date, publisher, description)
- ✅ Author identifiers (ORCID)
- ✅ Institutional affiliations with ROR/GRID IDs
- ✅ Related identifiers (DOI, PMID, PMCID, arXiv, etc.)
- ✅ Subject classification (MeSH terms, ASJC codes)
- ✅ Citation metrics
- ✅ Custom fields mapping (requires InvenioRDM configuration)
- ✅ Automatic DOI duplicate detection
- ✅ Batch processing with progress tracking
- ✅ Comprehensive error reporting

### Python SDK

Use as a library in your Python applications:

```python
from openscience_tools.sources.lens import LensOrgImporter

# Initialize importer
importer = LensOrgImporter(
    base_url="https://127.0.0.1:5000",
    token="your-api-token"
)

# Search records
results = importer.search(lens_id="000-035-558-593-934")
results = importer.search(title="climate change", size=20)

# Insert a new record
status, record_id, msg = importer.insert(data, publish=True)

# Update existing record
status, record_id, msg = importer.update("lens-id-123", data, publish=True)

# Delete record
status, record_id, msg = importer.delete("lens-id-123")
```

**SDK Examples:**

```bash
# Single record demo (insert/update/delete)
make tools-examples

# Batch import all publications
make tools-examples EXAMPLE=batch_import

# Search with filters
make tools-examples EXAMPLE=search_example

# Update specific record
make tools-examples EXAMPLE=update_example

# Delete specific record
make tools-examples EXAMPLE=delete_example
```

## Using with Makefile

If you're working within the sc-openscience project, you can use convenient Makefile commands:

```bash
# Setup (generate API token)
make tools-setup-env

# Search
make tools-search QUERY='climate data'
make tools-search QUERY='test' OPTS='--detailed'

# View record
make tools-view RECORD_ID='abc-123'

# Export to CSV
make tools-export OUTPUT='records.csv'
make tools-export OUTPUT='climate.csv' OPTS='--query "climate" --all-fields'

# Cleanup
make tools-cleanup OPTS='--dry-run'
make tools-cleanup OPTS='--confirm'

# Import from Lens
make tools-import-lens FILE='data/publications.json'
make tools-import-lens FILE='data/publications.json' OPTS='--limit 10'

# Reset (delete all + import)
make tools-reset FILE='data/publications.json'
make tools-reset FILE='data/publications.json' OPTS='--limit 10'

# Override credentials
make tools-search QUERY='test' BASE_URL='https://...' TOKEN='...'

# Batch import all publications
make tools-examples EXAMPLE=batch_import
```

## Publishing to GitLab Package Registry

This package is automatically published to the GitLab Package Registry via CI/CD pipeline.

### Pipeline Overview

The GitLab CI/CD pipeline (`ost_*` jobs) runs on the `openscience_tools` branch and consists of three stages:

1. **ost_prepare** - Builds custom Docker image with twine pre-installed (manual trigger)
2. **ost_build** - Creates distribution packages (.whl and .tar.gz) (automatic)
3. **ost_publish** - Uploads to GitLab Package Registry (manual trigger)

All jobs use the `ost_` prefix to avoid conflicts with other pipelines in the repository.

### How to Publish

#### Step 1: Update the Version

Before publishing, bump the version number in all relevant files:

```bash
cd openscience_tools

# 1. Update version in pyproject.toml
#    Edit: version = "X.Y.Z"

# 2. Update version in ./openscience_tools/__init__.py
#    Edit: __version__ = "X.Y.Z"

# 3. Update version in .gitlab-ci.yml (at repository root)
#    Edit: PACKAGE_VERSION: "X.Y.Z"

# 4. Commit the version bump
git add pyproject.toml openscience_tools/__init__.py ../.gitlab-ci.yml
git commit -m "chore: bump version to X.Y.Z"
```

#### Step 2: Push to the `ost` Branch

Push your changes to the `ost` branch to trigger the CI/CD pipeline:

```bash
git push origin ost
```

This will automatically start the pipeline defined in `.gitlab-ci.yml`.

#### Step 3: Monitor the Pipeline

1. Go to: https://repository.unesco.org/gitlab/sc/sc-openscience/-/pipelines
2. Find the latest pipeline for the `ost` branch
3. The pipeline will execute:
   - **ost_prepare** → Builds the Docker image with publishing tools
   - **ost_build** → Creates distribution packages (.whl and .tar.gz)
   - **ost_publish** → Uploads to GitLab Package Registry

#### Step 4: Verify Publication

Once the pipeline completes successfully:

- View the published package at: https://repository.unesco.org/gitlab/sc/sc-openscience/-/packages
- The new version should appear in the package list

### Pipeline Configuration Details

The pipeline is configured in `.gitlab-ci.yml` at the repository root:

- **Branch**: Only runs on `openscience_tools` branch
- **Proxy**: Configured for UNESCO network (proxy.unesco.org:8080)
- **Docker Images**:
  - Build: `python:3.11`
  - Publish: Custom `ost-publish-tool:latest` (with twine 6.0+)
- **Manual Jobs**: `ost_build_publish_image` and `ost_publish` require manual trigger
- **Artifacts**: Distribution packages stored for 1 week
