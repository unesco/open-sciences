# OpenScience Tools

A Python package providing command-line tools for interacting with InvenioRDM REST API.

## Overview

OpenScience Tools is a comprehensive toolkit for managing and importing data into InvenioRDM instances. It provides a unified command-line interface for common operations such as searching, viewing, managing records, and importing publications from external sources like Lens.org.

## Features

- **🔍 Search & Discovery**: Search and browse records with flexible filters
- **👁️ Record Management**: View detailed record information and manage records
- **🗑️ Cleanup Operations**: Delete records with dry-run support
- **📚 Lens.org Import**: Import publications from Lens.org JSON exports with full metadata mapping
- **🔧 Flexible Configuration**: Use environment variables or command-line options
- **⚡ Fast & Lightweight**: No Docker overhead, direct Python package

## Installation

### From Project Root (Recommended)

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

```bash
pip install openscience_tools --index-url https://gitlab.example.com/api/v4/projects/YOUR_PROJECT_ID/packages/pypi/simple
```

## Configuration

The package requires two configuration values:

- **Base URL**: Your InvenioRDM instance URL (e.g., `https://127.0.0.1:5000`)
- **API Token**: An InvenioRDM API token with appropriate permissions

### Method 1: Environment Variables (Recommended)

Add these to your `.env` file in the project root:

```bash
OPENSCIENCE_TOOLS_BASE_URL=https://127.0.0.1:5000
OPENSCIENCE_TOOLS_TOKEN=your-api-token-here
```

To generate a token automatically:

```bash
make tools-setup-env
```

### Method 2: Command-Line Options

Pass credentials directly to each command:

```bash
openscience_tools --base-url https://127.0.0.1:5000 --token your-token search -q "test"
```

## Usage

### Search Records

Search and display records from your InvenioRDM instance:

```bash
# Basic search
openscience_tools search -q "climate data"

# Search with size limit
openscience_tools search -q "test" --size 5

# Detailed view
openscience_tools search -q "machine learning" --detailed

# With pagination
openscience_tools search -q "dataset" --page 2 --size 20

# Sort by newest
openscience_tools search -q "covid" --sort newest
```

**Available sort options**: `bestmatch`, `newest`, `oldest`

### View Record Details

Display detailed information about a specific record:

```bash
# View record (formatted output)
openscience_tools view abc-123

# View as JSON
openscience_tools view abc-123 --format json

# Verbose output with debug info
openscience_tools view abc-123 --verbose
```

### Delete Records

Remove all records from your InvenioRDM instance:

```bash
# Dry-run (preview what would be deleted)
openscience_tools cleanup --dry-run

# Delete all records (interactive confirmation)
openscience_tools cleanup

# Delete with automatic confirmation
openscience_tools cleanup --confirm

# Verbose output
openscience_tools cleanup --confirm --verbose
```

⚠️ **Warning**: This operation is irreversible. Always use `--dry-run` first!

### Import from Lens.org

Import publications from Lens.org JSON export files:

```bash
# Validate metadata without creating records (dry-run)
openscience_tools import-lens --file publications.json --dry-run

# Import all records
openscience_tools import-lens --file publications.json

# Import first 10 records
openscience_tools import-lens --file publications.json --limit 10

# Skip first 10, import next 20
openscience_tools import-lens --file publications.json --offset 10 --limit 20

# Custom batch size (default: 10)
openscience_tools import-lens --file publications.json --batch-size 5

# Force reimport of existing records
openscience_tools import-lens --file publications.json --no-skip-existing

# Verbose output with debug info
openscience_tools import-lens --file publications.json --verbose
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
```

## API Client

For programmatic access, use the InvenioRDM client directly:

```python
from openscience_tools import InvenioRDMClient

# Initialize client
client = InvenioRDMClient(
    base_url="https://127.0.0.1:5000",
    token="your-api-token"
)

# Search records
results = client.search_records(q="climate", size=10)
for record in results["hits"]["hits"]:
    print(record["metadata"]["title"])

# Get specific record
record = client.get_record("abc-123")
print(record["metadata"]["title"])

# Create draft
draft = client.create_draft({
    "metadata": {
        "title": "My Dataset",
        "resource_type": {"id": "dataset"},
        "creators": [{"person_or_org": {"name": "Smith, John"}}],
        "publication_date": "2024-01-01"
    }
})

# Publish draft
published = client.publish_draft(draft["id"])
```

## Development

### Project Structure

```
openscience_tools/
├── src/                      # Source code
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # CLI entry point
│   ├── invenio_client.py    # InvenioRDM API client
│   ├── tools/               # CLI tools
│   │   ├── search.py        # Search command
│   │   ├── view.py          # View command
│   │   └── cleanup.py       # Cleanup command
│   └── sources/             # Import sources
│       └── lens/            # Lens.org importer
├── pyproject.toml           # Package configuration
├── setup.py                 # Setup script
├── README.md                # This file
└── LICENSE                  # MIT License
```

### Building the Package

```bash
# Install build dependencies
pip install build

# Build distribution files
python -m build

# Output: dist/openscience_tools-0.1.0-py3-none-any.whl
#         dist/openscience_tools-0.1.0.tar.gz
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=openscience_tools
```

## Troubleshooting

### "Command not found: openscience_tools"

Make sure the package is installed and your virtual environment is activated:

```bash
source .venv/bin/activate
pip install -e .
openscience_tools --version
```

### "Missing option '--base-url' / '--token'"

Ensure your `.env` file contains the required variables:

```bash
grep OPENSCIENCE_TOOLS .env

# Should show:
# OPENSCIENCE_TOOLS_BASE_URL=https://127.0.0.1:5000
# OPENSCIENCE_TOOLS_TOKEN=your-token
```

Run `make tools-setup-env` to generate a token automatically.

### "SSL Certificate Verification Failed"

InvenioRDM development instances use self-signed certificates. The client automatically disables SSL verification warnings for localhost/127.0.0.1.

For production instances with valid certificates, ensure your system's CA certificates are up to date.

### Import Fails with "Token not configured"

Generate a new API token:

```bash
make tools-setup-env
```

Or create one manually via InvenioRDM CLI:

```bash
invenio tokens create -n "OpenScience Tools" -u admin@example.org -i
```

## Publishing to GitLab Package Registry

This section explains how to publish the package to GitLab Package Registry for distribution.

### Automatic Publishing via GitLab CI/CD (Recommended)

The project includes a `.gitlab-ci.yml` pipeline that automatically builds and publishes the package.

#### Workflow

1. **On every commit** to any branch:

   - Runs tests (if available)
   - Runs linting checks
   - Builds the package

2. **On `develop` or `main` branches**:

   - Same as above, plus:
   - **Manual action required**: Click "Publish" in GitLab CI/CD pipeline to publish to registry

3. **On Git tags** (e.g., `v0.1.0`):
   - Automatically builds and publishes the release

#### Publishing a New Release

```bash
# 1. Update version in pyproject.toml
# Edit: version = "0.2.0"

# 2. Commit the change
git add pyproject.toml
git commit -m "chore: bump version to 0.2.0"

# 3. Create and push a tag
git tag v0.2.0
git push origin develop  # or main
git push origin v0.2.0

# 4. GitLab CI/CD will automatically build and publish!
```

#### Manual Publish from Branch

```bash
# 1. Push to develop or main
git push origin develop

# 2. Go to GitLab > CI/CD > Pipelines
# 3. Wait for build to complete
# 4. Click the "Play" button on the "publish" job
```

### Manual Publishing (Without CI/CD)

If you prefer to publish manually from your local machine:

#### Prerequisites

```bash
pip install --upgrade build twine
```

#### Build and Publish

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
python -m build

# Verify the build
ls -lh dist/
# Should show:
# openscience_tools-0.1.0-py3-none-any.whl
# openscience_tools-0.1.0.tar.gz

# Set credentials (get token from GitLab: User Settings > Access Tokens)
export TWINE_USERNAME=<your-gitlab-username>
export TWINE_PASSWORD=<your-personal-access-token>
export PROJECT_ID=<your-project-id>  # From GitLab Settings > General

# Publish
python -m twine upload \
  --repository-url https://repository.unesco.org/api/v4/projects/${PROJECT_ID}/packages/pypi \
  dist/*
```

#### Generate GitLab Personal Access Token

1. Go to GitLab > User Settings > Access Tokens
2. Create a new token with scopes: `api`, `write_repository`, `read_repository`
3. Save the token securely

### Installing from GitLab Package Registry

Once published, users can install the package:

#### Option 1: Direct Installation

```bash
pip install openscience_tools \
  --index-url https://repository.unesco.org/api/v4/projects/${PROJECT_ID}/packages/pypi/simple
```

#### Option 2: Configure pip Permanently

Create/edit `~/.pip/pip.conf` (Linux/macOS) or `%APPDATA%\pip\pip.ini` (Windows):

```ini
[global]
extra-index-url = https://repository.unesco.org/api/v4/projects/${PROJECT_ID}/packages/pypi/simple
```

Then install normally:

```bash
pip install openscience_tools
```

#### Option 3: Using requirements.txt

```txt
# requirements.txt
--extra-index-url https://repository.unesco.org/api/v4/projects/${PROJECT_ID}/packages/pypi/simple
openscience_tools==0.1.0
```

### Versioning Strategy

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New features, backwards compatible
- **PATCH** version (0.0.X): Bug fixes, backwards compatible

**Version Bump Guidelines:**

- `0.1.0 → 0.1.1`: Bug fixes only
- `0.1.0 → 0.2.0`: New features added
- `0.1.0 → 1.0.0`: Breaking changes or first stable release

### Publishing Best Practices

1. **Always test locally** before publishing:

   ```bash
   pip install -e ".[dev]"
   pytest tests/  # when tests are available
   ```

2. **Use semantic versioning** consistently

3. **Create Git tags** for all releases

4. **Test installation** after publishing:
   ```bash
   pip install openscience_tools==${NEW_VERSION} --index-url <registry-url>
   ```

### Troubleshooting Publishing

#### "Package already exists" error

Solutions:

1. Bump the version in `pyproject.toml`
2. Delete the package from GitLab (if you have permissions)
3. Use a different version number

#### Authentication errors

```bash
# Verify your token has the right permissions
curl -H "PRIVATE-TOKEN: <your-token>" \
  https://repository.unesco.org/api/v4/projects/${PROJECT_ID}
```

#### Pipeline fails on publish step

Common issues:

1. **Missing permissions**: Ensure GitLab user has `Maintainer` or `Owner` role
2. **Protected branches**: `main`/`develop` might require manual approval
3. **Token expired**: CI/CD tokens are automatically managed by GitLab

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This package is part of the UNESCO Science Portal project. For contributions, please follow the project's contribution guidelines.

## Support

For issues, questions, or contributions, please refer to the main project repository.
