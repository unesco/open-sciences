# CSV Data Source Importer

Import records into InvenioRDM from CSV files.

## Features

- ✅ Standard bibliographic metadata
- ✅ Creators and contributors with ORCID
- ✅ Related identifiers (DOI, ISBN, etc.)
- ✅ File uploads
- ✅ Publishing workflow
- ✅ Create new or update existing records
- ✅ Batch processing with error handling
- ✅ Dry-run validation mode

## Usage

### Via Makefile (Recommended)

```bash
# Dry run validation
make scripts-import FILE='src/sources/csv/data/publications.csv' OPTS='--dry-run'

# Import all records
make scripts-import FILE='src/sources/csv/data/publications.csv'

# Skip errors and continue
make scripts-import FILE='src/sources/csv/data/publications.csv' OPTS='--skip-errors'

# Custom delimiter (tab-separated)
make scripts-import FILE='data/records.tsv' OPTS="--delimiter $'\t'"
```

### Direct Module Execution

```bash
# Basic import
python -m src.sources.csv --file data/records.csv

# Dry run
python -m src.sources.csv --file data/records.csv --dry-run

# Verbose output
python -m src.sources.csv --file data/records.csv --verbose

# Custom delimiter
python -m src.sources.csv --file data/records.tsv --delimiter $'\t'
```

### Programmatic Usage

```python
from src.sources.csv import create_reader, create_importer

# Read CSV
reader = create_reader("data/records.csv")
records = reader.read_records()

# Import
importer = create_importer()
result = importer.import_records(records, dry_run=False)

print(f"Imported {result.successful} records")
```

## CSV Format

### Required Columns

- **title**: Record title (string)
- **creators**: Creators in format: `"Given Family; ORCID; Affiliation | Given2 Family2; ..."`

### Optional Columns

- **record_id**: Existing record ID for updates
- **description**: Record description
- **resource_type**: Resource type (default: `dataset`)
- **publication_date**: Date in `YYYY-MM-DD` format (default: today)
- **access_record**: Record access level (`public` or `restricted`)
- **access_files**: Files access level (`public` or `restricted`)
- **publisher**: Publisher name
- **version**: Version string
- **languages**: Semicolon-separated ISO 639-3 codes (e.g., `eng;ita`)
- **subjects**: Semicolon-separated keywords (e.g., `climate;data analysis`)
- **license**: License ID (e.g., `cc-by-4.0`)
- **additional_descriptions**: Pipe-separated descriptions with types (e.g., `"Abstract text; abstract | Methods; methods"`)
- **references**: Semicolon-separated reference strings
- **contributors**: Pipe-separated contributors (e.g., `"John Doe; University; DataCurator; 0000-0001-2345-6789 | Jane Smith; ..."`)
- **related_identifiers**: Pipe-separated identifiers (e.g., `"10.1234/zenodo.123; doi; cites | ..."`)
- **file_paths**: Semicolon-separated file paths to upload
- **publish**: Publish immediately (`yes` or `no`)

### Example CSV

```csv
title,description,creators,resource_type,publication_date,subjects,license
"Sample Dataset","A test dataset","John Doe;0000-0001-2345-6789;University",dataset,2024-01-15,"climate;data",cc-by-4.0
"Research Article","Example article","Jane Smith;;Institute|Bob Johnson;0000-0002-3456-7890;University",publication,2024-02-20,"AI;ML",cc-by-nc-4.0
```

## Field Format Details

### Creators and Contributors

**Creators**: `"Given Family; ORCID; Affiliation | Given2 Family2; ORCID2; Affiliation2"`

- Pipe (`|`) separates multiple creators
- Semicolon (`;`) separates: Name, ORCID (optional), Affiliation (optional)
- ORCID can include or omit the `https://orcid.org/` prefix

**Contributors**: `"Given Family; Affiliation; Role; ORCID | ..."`

- Format: Name, Affiliation (optional), Role (optional), ORCID (optional)
- Role examples: `DataCurator`, `ContactPerson`, `Researcher`, etc.

### Related Identifiers

Format: `"identifier; scheme; relation_type | identifier2; scheme2; relation_type2"`

- Scheme: `doi`, `isbn`, `pmid`, `url`, etc.
- Relation type: `cites`, `references`, `isSupplementTo`, etc.

### Lists

Most list fields use semicolon (`;`) as separator:

- **languages**: `eng;fra;ita`
- **subjects**: `climate change;data analysis;modeling`
- **file_paths**: `/path/to/file1.pdf;/path/to/file2.csv`

## Configuration

See `config.py` for:

- Resource type mappings
- Contributor role mappings
- Relation type mappings
- Identifier schemes
- Other configuration constants

## Module Structure

```
csv/
├── __init__.py       # Public API
├── __main__.py       # Module execution support
├── main.py           # CLI and import orchestration
├── config.py         # Configuration and constants
├── reader.py         # CSV file reading
├── parsers.py        # Field value parsers
├── mapper.py         # CSV to InvenioRDM mapping
├── importer.py       # Import orchestration
└── data/
    └── publications.csv  # Example CSV file
```

## Error Handling

By default, import stops on first error. Use `--skip-errors` to continue:

```bash
make scripts-import FILE='data/records.csv' OPTS='--skip-errors'
```

Errors and warnings are reported in the final summary.

## See Also

- Main documentation: `../../README.md`
- Data sources guide: `../README.md`
- Scripts documentation: `../../scripts/README.md`
