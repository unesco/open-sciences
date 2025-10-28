# Data Sources

This directory contains importers for various external data sources into InvenioRDM.

## Structure

Each data source has its own subdirectory with the following organization:

```
sources/
├── __init__.py
├── README.md (this file)
└── <source-name>/
    ├── __init__.py
    ├── base.py           # Base classes and utilities
    ├── config.py         # Configuration and mapping tables
    ├── reader.py         # Data readers (JSON, API, CSV, etc.)
    ├── importer.py       # Main orchestrator
    ├── data/             # Sample data files
    │   └── *.json
    └── mappers/          # Field mappers
        ├── __init__.py
        ├── standard.py   # Standard InvenioRDM fields
        ├── custom.py     # Custom fields
        └── related.py    # Related identifiers
```

## Available Sources

### CSV (`csv/`)

Import records from CSV files with flexible field mapping.

**Features:**

- ✅ Standard metadata (title, creators, dates, publisher, description)
- ✅ Creator/contributor parsing with ORCID and affiliations
- ✅ Related identifiers (DOI, ISBN, PMID, etc.)
- ✅ File uploads
- ✅ Publishing workflow
- ✅ Create new records or update existing ones
- ✅ Batch processing with error handling

**Usage:**

```bash
# Dry run validation
make scripts-import FILE='src/sources/csv/data/publications.csv' OPTS='--dry-run'

# Import all records
make scripts-import FILE='src/sources/csv/data/publications.csv'

# Custom delimiter (tab-separated)
make scripts-import FILE='data/records.tsv' OPTS="--delimiter $'\t'"

# Skip errors and continue
make scripts-import FILE='data/records.csv' OPTS='--skip-errors'

# Direct module execution
python -m src.sources.csv --file data/records.csv --verbose
```

**CSV Format:**

Required columns: `title`, `creators`

Optional columns: `record_id`, `description`, `resource_type`, `publication_date`, `access_record`, `access_files`, `publisher`, `version`, `languages`, `subjects`, `license`, `additional_descriptions`, `references`, `contributors`, `related_identifiers`, `file_paths`, `publish`

See `src/sources/csv/data/publications.csv` for examples.

### Lens.org (`lens/`)

Import publication records from Lens.org JSON exports.

**Features:**

- ✅ Standard metadata (title, creators, dates, publisher, description)
- ✅ Author identifiers (ORCID)
- ✅ Institutional affiliations (ROR)
- ⚠️ Custom fields (requires InvenioRDM configuration)
- ⚠️ Related identifiers (DOI, PMID, PMCID, etc.)
- ⚠️ Subject classification (MeSH, ASJC)

**Usage:**

```bash
# Dry run validation
make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--dry-run'

# Import all records
make scripts-import-lens FILE='src/sources/lens/data/publications.json'

# Import with limits
make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 10'
```

**Data Location:** `src/sources/lens/data/publications.json`

**Documentation:**

- Architecture: `docs/LENS_ORG_MAPPING_ANALYSIS.md`
- Implementation: `docs/LENS_ORG_IMPLEMENTATION_SUMMARY.md`

## Adding a New Data Source

To add a new data source (e.g., "datacite"):

1. **Create directory structure:**

   ```bash
   mkdir -p src/sources/datacite/{data,mappers}
   ```

2. **Implement core modules:**

   - `base.py` - Base classes (can reuse from lens/)
   - `config.py` - Mapping configuration
   - `reader.py` - Data reader implementation
   - `importer.py` - Main orchestrator
   - `mappers/standard.py` - Standard fields mapper
   - `mappers/custom.py` - Custom fields mapper (optional)
   - `mappers/related.py` - Related identifiers mapper (optional)

3. **Add sample data:**

   - Place test files in `data/` directory

4. **Create main.py module:**

   - Add `src/sources/datacite/main.py`
   - Follow the pattern from `src/sources/lens/main.py`
   - Include CLI with Click, environment setup, import orchestration
   - Add `__main__.py` for module execution support

5. **Update Makefile:**

   - Add `scripts-import-datacite` target
   - Use `python -m src.sources.datacite` command
   - Add help documentation

6. **Update this README:**
   - Document the new source
   - Add usage examples

## Design Principles

1. **Separation of Concerns:**

   - Readers: Handle data loading from various sources
   - Mappers: Transform source format to InvenioRDM
   - Importer: Orchestrate the import process

2. **Reusability:**

   - Base classes provide common functionality
   - Mappers can be mixed and matched
   - Configuration-driven transformations

3. **Extensibility:**

   - Easy to add new data sources
   - Pluggable mapper architecture
   - Support for multiple input formats per source

4. **Error Handling:**
   - Graceful degradation
   - Detailed error reporting
   - Batch processing with recovery

## Common Patterns

### Reader Pattern

```python
from .reader import create_reader

reader = create_reader("json", file_path="data.json")
records = reader.read_records()
```

### Mapper Pattern

```python
from .mappers import StandardFieldsMapper
from .config import SourceConfig

config = SourceConfig()
mapper = StandardFieldsMapper(config)
metadata = mapper.map(source_record)
```

### Importer Pattern

```python
from . import create_importer

importer = create_importer(
    base_url="https://localhost:5000",
    token="your-token"
)

result = importer.import_from_source(
    source="json",
    file_path="data.json",
    dry_run=False
)
```

## Testing

Each source should include:

1. **Unit tests** for mappers (test individual field mappings)
2. **Integration tests** for readers (test data loading)
3. **End-to-end tests** for importer (test full import flow)
4. **Test script** for manual validation

Example test script pattern:

```python
# examples/test_<source>_mapping.py
from src.sources.<source> import create_reader, create_mappers

reader = create_reader("json", "test_data.json")
record = reader.read_records()[0]

mapper = create_mappers()
result = mapper.map(record)
print(json.dumps(result, indent=2))
```

## Environment Configuration

All importers use the same environment configuration:

```env
INVENIO_BASE_URL=https://127.0.0.1:5000
INVENIO_TOKEN=your-api-token-here
```

Configuration file location: `scripts/config/.env`

## Performance Considerations

1. **Batch Processing:** Use configurable batch sizes (default: 10)
2. **Parallel Processing:** Future enhancement for multiple workers
3. **Memory Management:** Stream large files instead of loading entirely
4. **Caching:** Cache repeated lookups (ROR, ORCID validation)

## Future Enhancements

- [ ] Add DataCite importer
- [ ] Add Crossref importer
- [ ] Add OpenAlex importer
- [ ] Add PubMed/PMC importer
- [ ] Implement API readers (not just file-based)
- [ ] Add parallel processing support
- [ ] Implement incremental updates
- [ ] Add data validation layer
- [ ] Support for file uploads (PDFs, datasets)
