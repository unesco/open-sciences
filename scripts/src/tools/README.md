# InvenioRDM Management Tools

Comprehensive command-line utilities for managing and interacting with InvenioRDM.

## Overview

The `tools` module provides a collection of utilities for:

- **Searching** records
- **Viewing** record details
- **Managing** statistics
- **Cleaning up** records
- **Comprehensive CLI** for all operations

All tools are organized as Python modules and can be executed via `python -m src.tools.<tool>`.

## Available Tools

### 1. Search Tool (`search.py`)

Search and browse InvenioRDM records with flexible filtering and display options.

```bash
# Basic search
python -m src.tools.search --query "climate"

# Show detailed information
python -m src.tools.search -q "test" -s 5 --detailed

# Browse all records with pagination
python -m src.tools.search --page 2 --size 20

# Sort by newest
python -m src.tools.search --sort newest
```

**Features:**

- Full-text search
- Pagination support
- Summary and detailed views
- Customizable sort options
- Colored tabular output

**Options:**

- `--query, -q`: Search query string
- `--size, -s`: Number of results (default: 10)
- `--sort`: Sort order (bestmatch, newest, oldest)
- `--page, -p`: Page number
- `--detailed, -d`: Show detailed view
- `--verbose, -v`: Enable verbose logging

---

### 2. View Tool (`view.py`)

View detailed information about specific records.

```bash
# View record in formatted text
python -m src.tools.view abc-123

# View as JSON
python -m src.tools.view abc-123 --format json

# Verbose output
python -m src.tools.view abc-123 --verbose
```

**Features:**

- Human-readable formatted display
- JSON output option
- Shows metadata, creators, files, access settings
- DOI and identifier display
- File information with checksums

**Options:**

- `RECORD_ID`: Record ID to view (required)
- `--format`: Output format (text or json)
- `--verbose, -v`: Enable verbose logging

---

### 3. Statistics Tool (`stats.py`)

Retrieve and display statistics for records or the entire system.

```bash
# Get statistics for a specific record
python -m src.tools.stats --record-id abc-123

# Get system-wide statistics
python -m src.tools.stats

# Get output in JSON format
python -m src.tools.stats -r abc-123 --format json
```

**Features:**

- Record-specific statistics (views, downloads)
- System-wide metrics
- Alternative information if stats API unavailable
- JSON and table output formats

**Options:**

- `--record-id, -r`: Specific record ID
- `--format`: Output format (table or json)
- `--verbose, -v`: Enable verbose logging

**Metrics Shown:**

- Views (total and unique)
- Downloads (total and unique)
- Data volume
- Version-specific stats

---

### 4. Cleanup Tool (`cleanup.py`)

Delete all records from InvenioRDM (useful for resetting test instances).

```bash
# Dry run (see what would be deleted)
python -m src.tools.cleanup --dry-run

# Delete with confirmation prompt
python -m src.tools.cleanup

# Delete without confirmation (use with caution!)
python -m src.tools.cleanup --confirm

# Verbose output
python -m src.tools.cleanup --confirm --verbose
```

**Features:**

- Bulk record deletion
- Dry-run mode for safety
- Confirmation prompt
- Batch processing
- Progress reporting
- Error handling and summary

**Options:**

- `--confirm`: Skip confirmation prompt
- `--dry-run`: Simulate without deleting
- `--verbose, -v`: Show detailed progress
- `--batch-size`: Records per request (default: 100)

⚠️ **WARNING**: This action is permanent and cannot be undone!

---

### 5. CLI Tool (`cli.py`)

Comprehensive command-line interface combining all operations.

```bash
# Test connection
python -m src.tools.cli test-connection

# Search records
python -m src.tools.cli search -q "machine learning" -s 5

# Get record details
python -m src.tools.cli get abc-123

# Create a new record
python -m src.tools.cli create \
  --title "New Dataset" \
  --creator "Jane Smith" \
  --type dataset \
  --publish
```

**Available Commands:**

- `test-connection`: Test InvenioRDM API connection
- `search`: Search for records
- `get`: Get record details
- `create`: Create a new record draft
- `delete`: Delete a record
- `list-records`: List all records

Use `python -m src.tools.cli --help` for full documentation.

---

## Makefile Integration

All tools are integrated into the Makefile for convenience:

```bash
# Search records
make scripts-run CMD='python -m src.tools.search -q "climate"'

# View record
make scripts-run CMD='python -m src.tools.view abc-123'

# Get statistics
make scripts-run CMD='python -m src.tools.stats -r abc-123'

# Cleanup (with confirmation)
make scripts-run CMD='python -m src.tools.cleanup --dry-run'

# Use CLI
make scripts-run CMD='python -m src.tools.cli test-connection'
```

Or update the Makefile with dedicated targets (recommended).

## Architecture

Each tool follows a consistent structure:

```python
# Module structure
src/tools/<tool>.py
├── Functions for core logic
├── Display/formatting functions
├── Main function with business logic
└── Click CLI definition
```

**Design Principles:**

1. **Separation of Concerns**: Logic separate from presentation
2. **Reusability**: Functions can be imported and used programmatically
3. **Consistency**: All tools use similar patterns and interfaces
4. **Error Handling**: Graceful error handling with informative messages
5. **Flexibility**: Support for different output formats and verbosity levels

## Programmatic Usage

All tools can be used programmatically in Python code:

```python
from src.tools.search import search_records
from src.tools.view import view_record
from src.tools.stats import get_statistics
from src.tools.cleanup import cleanup_all_records

# Search records
search_records(query="climate", size=10, detailed=True)

# View record
view_record(record_id="abc-123", output_format="json")

# Get statistics
get_statistics(record_id="abc-123")

# Cleanup (dry run)
cleanup_all_records(dry_run=True, verbose=True)
```

## Environment Configuration

All tools require environment variables:

```bash
INVENIO_BASE_URL=https://127.0.0.1:5000
INVENIO_TOKEN=your-api-token
```

Set up with:

```bash
make scripts-setup-env
```

## Error Handling

All tools provide:

- Clear error messages with colored output
- Graceful failure with appropriate exit codes
- Verbose mode for debugging
- Suggestions for common problems

## Output Formats

Most tools support multiple output formats:

- **Text**: Human-readable formatted output (default)
- **JSON**: Machine-readable JSON output
- **Table**: Tabular format using `tabulate`

## Logging

Tools use Python's `logging` module:

- Default: INFO level
- Verbose mode: DEBUG level
- Logs include module names and levels

## Future Enhancements

Potential additions:

1. **Export Tool**: Export records to various formats (CSV, BibTeX, etc.)
2. **Batch Tool**: Batch operations on multiple records
3. **Backup Tool**: Backup and restore functionality
4. **Validation Tool**: Validate metadata against schemas
5. **Migration Tool**: Migrate records between instances

## Related Documentation

- [Data Sources](../sources/README.md) - Import tools for external data
- [InvenioRDM Client](../invenio_client.py) - Low-level API client
- [Scripts README](../../README.md) - Overall scripts documentation

## Contributing

When adding new tools:

1. Follow the existing module structure
2. Include comprehensive docstrings
3. Support both CLI and programmatic use
4. Add examples to this README
5. Update Makefile if needed
6. Test with dry-run modes when applicable
