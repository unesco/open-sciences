# Lens.org Source Tests

Tests for the Lens.org data source integration with InvenioRDM.

## Test Coverage

### Integration Tests (`@pytest.mark.integration`)
- **TestInsert** - Insert operations
  - Minimal and full records
  - Published vs draft modes
  - Duplicate handling
  
- **TestUpdate** - Update operations
  - Existing records with custom_fields preservation
  - Nonexistent record handling
  - Automatic deduplication
  
- **TestDelete** - Delete operations
  - Single record deletion
  - Bulk duplicate deletion
  - Nonexistent record handling
  
- **TestSearch** - Search operations
  - Search by lens_id (exact match)
  - Search by title (partial, case-insensitive)
  - Pagination and sorting
  - Empty results handling
  
- **TestIntegrationWorkflow** - End-to-end workflows
  - Complete CRUD cycle
  - Batch import operations

### Unit Tests (`@pytest.mark.unit`)
- **TestMetadataMapping** - Metadata transformation
  - Minimal record mapping
  - Custom fields mapping (lens:id, lens:open_access, etc.)
  - Authors with ORCID identifiers
  - Related identifiers (DOI, PMID, ISSN)
  
- **TestValidation** - Data validation
  - Required fields validation
  - Error handling

## Fixtures

Lens-specific fixtures in `conftest.py`:
- `lens_importer` - LensOrgImporter instance
- `sample_lens_record` - Single real Lens.org record
- `sample_lens_records` - Multiple (5) real records
- `minimal_lens_record` - Minimal synthetic test record

Shared fixtures from `tests/conftest.py`:
- `test_env` - Environment config (base_url, token)
- `clean_database` - Database cleanup fixture
- `invenio_client` - InvenioRDMClient instance

## Running Tests

```bash
# All Lens tests
make tools-test OPTS="tests/sources/lens/ -v"

# Only integration tests
make tools-test OPTS="tests/sources/lens/ -m integration -v"

# Only unit tests
make tools-test OPTS="tests/sources/lens/ -m unit -v"

# Specific test class
make tools-test OPTS="tests/sources/lens/test_lens.py::TestInsert -v"

# Single test
make tools-test OPTS="tests/sources/lens/test_lens.py::TestInsert::test_insert_minimal_record -v"
```

## Test Data

Real test data from `openscience_tools/sources/lens/data/publications.json` (26 Lens.org records).
