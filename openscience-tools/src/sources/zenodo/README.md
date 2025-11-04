# Zenodo Importer

Import records from [Zenodo.org](https://zenodo.org) into InvenioRDM.

## Overview

This module fetches metadata and files from Zenodo's public API and imports them into your InvenioRDM instance, preserving all metadata including creators, contributors, related identifiers, keywords, and files.

## Features

- ✅ Import individual records by Zenodo ID
- ✅ Search and import multiple records
- ✅ Complete metadata mapping (creators, contributors, identifiers, etc.)
- ✅ Automatic file download and upload
- ✅ Dry-run mode for validation
- ✅ Skip files option for metadata-only import
- ✅ HTML description cleaning
- ✅ ORCID identifier preservation
- ✅ License mapping

## Usage

### Import a Specific Record

```bash
# Via module (recommended)
python -m src.sources.zenodo --record-id 17462748

# Via Makefile
make scripts-import-zenodo RECORD_ID=17462748
```

### Search and Import Multiple Records

```bash
# Search and import up to 5 records
python -m src.sources.zenodo --search "climate data" --max-results 5

# Via Makefile
make scripts-import-zenodo QUERY="climate data" MAX=5
```

### Advanced Options

```bash
# Metadata only (skip files)
python -m src.sources.zenodo --record-id 17462748 --skip-files

# Dry run (validation only)
python -m src.sources.zenodo --record-id 17462748 --dry-run

# Verbose output
python -m src.sources.zenodo --record-id 17462748 --verbose

# Combine options
python -m src.sources.zenodo --search "open data" --max-results 3 --skip-files --dry-run
```

## Command-Line Options

| Option          | Short | Description                         | Default |
| --------------- | ----- | ----------------------------------- | ------- |
| `--record-id`   | `-r`  | Zenodo record ID to import          | -       |
| `--search`      | `-s`  | Search query string                 | -       |
| `--max-results` | `-m`  | Maximum search results to import    | 5       |
| `--skip-files`  | -     | Skip file downloads (metadata only) | False   |
| `--dry-run`     | -     | Validate without importing          | False   |
| `--verbose`     | `-v`  | Enable verbose output               | False   |
| `--skip-errors` | -     | Continue on errors                  | True    |

**Note:** You must specify either `--record-id` OR `--search`, not both.

## Makefile Targets

The Makefile provides convenient shortcuts:

```bash
# Import by record ID
make scripts-import-zenodo RECORD_ID=17462748

# Search and import
make scripts-import-zenodo QUERY="climate data" MAX=5

# With additional options
make scripts-import-zenodo RECORD_ID=17462748 OPTS="--skip-files --dry-run"
```

## Metadata Mapping

### Supported Fields

The importer maps the following Zenodo fields to InvenioRDM:

| Zenodo Field          | InvenioRDM Field               | Notes                           |
| --------------------- | ------------------------------ | ------------------------------- |
| `title`               | `metadata.title`               | Required                        |
| `publication_date`    | `metadata.publication_date`    | ISO format                      |
| `creators`            | `metadata.creators`            | With ORCID and affiliations     |
| `contributors`        | `metadata.contributors`        | With roles, ORCID, affiliations |
| `description`         | `metadata.description`         | HTML cleaned                    |
| `keywords`            | `metadata.subjects`            | As subject terms                |
| `resource_type`       | `metadata.resource_type`       | Mapped to InvenioRDM types      |
| `license`             | `metadata.rights`              | Mapped to InvenioRDM licenses   |
| `version`             | `metadata.version`             | Optional                        |
| `related_identifiers` | `metadata.related_identifiers` | With relation types             |
| `files`               | Files API                      | Downloaded and uploaded         |

### Resource Type Mapping

Common Zenodo resource types are automatically mapped:

- `publication-*` → Corresponding InvenioRDM publication types
- `dataset` → `dataset`
- `image-*` → Corresponding InvenioRDM image types
- `video` → `video`
- `software` → `software`
- Other types → `other`

### License Mapping

Common licenses are mapped automatically:

- `cc-by-4.0` → `cc-by-4.0`
- `mit` / `mit-license` → `mit`
- `apache-2.0` → `apache-2.0`
- Unknown licenses → `cc-by-4.0` (default)

## Architecture

The module follows a modular structure:

```
src/sources/zenodo/
├── __init__.py         # Public API
├── __main__.py         # Module execution
├── main.py             # CLI and orchestration
├── config.py           # Configuration and mappings
├── fetcher.py          # Zenodo API client
├── mapper.py           # Metadata mapping
├── importer.py         # Import orchestration
└── README.md           # This file
```

### Components

- **Fetcher**: Handles all Zenodo API interactions (search, fetch, download)
- **Mapper**: Converts Zenodo metadata to InvenioRDM format
- **Importer**: Orchestrates the complete import workflow
- **Config**: Centralized configuration and type mappings

## Examples

### Example 1: Import a Climate Dataset

```bash
# Import a specific climate dataset with files
python -m src.sources.zenodo --record-id 17462748

# Output:
# ✓ Record: Global Climate Model Data
# ✓ DOI: 10.5281/zenodo.17462748
# ✓ Files: 3
# ✓ Successfully imported!
```

### Example 2: Metadata-Only Import

```bash
# Import metadata without downloading large files
python -m src.sources.zenodo --record-id 17462748 --skip-files

# Useful for:
# - Large datasets
# - Testing imports
# - Metadata-only repositories
```

### Example 3: Bulk Import from Search

```bash
# Find and import recent COVID-19 research
python -m src.sources.zenodo --search "COVID-19 research" --max-results 10

# The importer will:
# 1. Search Zenodo for matching records
# 2. Fetch metadata for each result
# 3. Download files (if not skipped)
# 4. Create records in InvenioRDM
# 5. Show summary of results
```

### Example 4: Dry Run for Testing

```bash
# Test what would be imported without making changes
python -m src.sources.zenodo --record-id 17462748 --dry-run

# Shows:
# - Record title and metadata
# - Number of files
# - Validation results
# - No records created
```

## Programmatic Usage

You can also use the importer programmatically in your Python code:

```python
from src.invenio_client import InvenioRDMClient
from src.sources.zenodo import create_fetcher, create_mapper, create_importer

# Initialize components
client = InvenioRDMClient(base_url="https://127.0.0.1:5000", token="your-token")
fetcher = create_fetcher()
mapper = create_mapper()
importer = create_importer(client, fetcher, mapper)

# Import a record
result = importer.import_record("17462748", skip_files=False, dry_run=False)

# Search and import
results = importer.search_and_import("climate data", max_results=5)

# Check results
for result in results:
    if result.success:
        print(f"✓ Imported: {result.title} (ID: {result.invenio_id})")
    else:
        print(f"✗ Failed: {result.zenodo_id} - {result.error}")
```

## Troubleshooting

### Environment Not Configured

```
❌ Error: INVENIO_BASE_URL not set in environment
💡 Run: make scripts-setup-env
```

**Solution:** Set up your environment with `make scripts-setup-env` or create a `.env` file.

### Record Not Found

```
❌ Error importing record 12345: 404 - Record not found
```

**Solution:** Verify the Zenodo record ID exists at https://zenodo.org/records/{id}

### File Download Failed

```
✗ Error processing file data.csv: Connection timeout
```

**Solution:**

- Check internet connection
- Try with `--skip-files` for metadata-only
- Retry the import

### License Mapping Warning

If you see unmapped licenses in logs, they'll default to `cc-by-4.0`. You can update `LICENSE_MAP` in `config.py` to add custom mappings.

## API Reference

See inline documentation in:

- `fetcher.py` - Zenodo API client methods
- `mapper.py` - Metadata mapping functions
- `importer.py` - Import orchestration
- `main.py` - CLI and high-level functions

## Zenodo API Documentation

For more information about Zenodo's API:

- API Docs: https://developers.zenodo.org/
- Search syntax: https://help.zenodo.org/guides/search/

## Related

- [CSV Importer](../csv/README.md) - Import from CSV files
- [Lens.org Importer](../lens/README.md) - Import from Lens.org
- [InvenioRDM Client](../../invenio_client.py) - Low-level API client
