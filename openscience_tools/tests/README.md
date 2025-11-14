# OpenScience Tools Test Suite

This directory contains comprehensive tests for the openscience-tools package.

## Test Organization

## Test Organization

```
tests/
├── conftest.py              # Shared pytest fixtures (test_env, clean_database, invenio_client)
├── test_client.py           # Tests for InvenioRDMClient API methods
├── sources/                 # Tests organized by data source
│   └── lens/
│       ├── __init__.py
│       ├── conftest.py      # Lens-specific fixtures (lens_importer, sample_lens_record)
│       └── test_lens.py     # All Lens tests (integration + unit)
└── README.md                # This file
```

**Organization principles:**

- Core client tests in `tests/test_client.py`
- Source-specific tests in `tests/sources/{source}/`
- Each source has its own fixtures in `conftest.py`
- Integration and unit tests combined in single module per source

## Test Types

### Integration Tests (`@pytest.mark.integration`)

- **Require**: Running InvenioRDM instance with valid credentials
- **Test**: Real API interactions, complete workflows
- **Examples**: CRUD operations, search, batch imports
- **Fixture**: Uses `clean_database` to start with empty DB

### Unit Tests (`@pytest.mark.unit`)

- **Require**: No external dependencies
- **Test**: Internal logic, mapping, validation
- **Examples**: Metadata mapping, query building

### Slow Tests (`@pytest.mark.slow`)

- **Mark**: Long-running integration tests
- **Examples**: Batch imports, complete workflows

## Setup

1. **Install package with dev dependencies:**

   ```bash
   # From project root
   make tools-install

   # Or manually
   source .venv/bin/activate
   cd openscience_tools
   pip install -e ".[dev]"
   ```

2. **Environment variables are loaded automatically from .env file**
   - Run `make tools-setup-env` if not configured yet
   - Tests read OPENSCIENCE_TOOLS_BASE_URL and OPENSCIENCE_TOOLS_TOKEN from .env

## Running Tests

### Using Makefile (recommended):

```bash
# All tests (from project root)
make tools-test

# Only integration tests
make tools-test OPTS="-m integration"

# Only unit tests
make tools-test OPTS="-m unit"

# Skip slow tests
make tools-test OPTS="-m 'not slow'"

# With coverage
make tools-test-cov

# Specific test file
make tools-test OPTS="tests/test_sdk_integration.py -v"

# Specific test
make tools-test OPTS="tests/test_sdk_integration.py::TestInsert::test_insert_minimal_record -v"
```

### Direct pytest (from openscience_tools/ directory):

```bash
# All tests
pytest tests/ -v

# Only integration tests
pytest tests/ -v -m integration

# Only unit tests
pytest tests/ -v -m unit

# With coverage
pytest tests/ --cov=openscience_tools --cov-report=html
```

## Test Fixtures

### `test_env`

- Loads environment variables (BASE_URL, TOKEN)
- Session scope (once per test session)

### `invenio_client`

- InvenioRDMClient instance
- Session scope

### `lens_importer`

- LensOrgImporter instance
- Session scope

### `clean_database`

- **IMPORTANT**: Cleans database before each test
- Function scope (runs before each test)
- Uses `cleanup_all_records()` from cleanup tool

### `sample_lens_record`

- Single Lens.org publication record
- Loaded from publications.json

### `sample_lens_records`

- First 5 Lens.org publication records
- For batch testing

### `minimal_lens_record`

- Minimal valid record for quick tests
- Synthetic data

## Test Coverage

The test suite covers:

✅ **Insert Operations**

- Minimal records
- Full records with all fields
- Draft vs published
- Duplicate handling

✅ **Update Operations**

- Updating existing records
- Custom fields preservation (lens_id)
- Nonexistent record handling
- Duplicate cleanup

✅ **Delete Operations**

- Single record deletion
- Nonexistent record handling
- Multiple duplicates deletion

✅ **Search Operations**

- Search by lens_id (exact)
- Search by title (partial, case-insensitive)
- Search all records
- Pagination
- Sorting (bestmatch, newest, oldest)

✅ **Client Methods**

- create_draft()
- publish_draft()
- update_draft() with custom_fields
- delete_record()
- search_records()
- create_draft_from_record()

✅ **End-to-End Workflows**

- Complete CRUD cycle
- Batch import workflows

## Important Notes

⚠️ **Database Cleanup**

- Integration tests use `clean_database` fixture
- **Each test starts with empty database**
- Prevents test interference
- Uses production cleanup tool

⚠️ **Test Isolation**

- Tests should not depend on each other
- Each test is independent
- Use fixtures for setup

⚠️ **Timing**

- Include `time.sleep()` after write operations
- Allows OpenSearch indexing to complete
- Typically 1-2 seconds

## Continuous Integration

For CI/CD pipelines:

```bash
# Run all tests with coverage
pytest tests/ -v --cov=openscience_tools --cov-report=xml

# Run only fast tests
pytest tests/ -v -m "not slow"

# Run with JUnit XML output
pytest tests/ -v --junit-xml=test-results.xml
```

## Troubleshooting

**Tests fail with "OPENSCIENCE_TOOLS_TOKEN not set"**

- Set environment variables before running tests
- Or tests will be skipped automatically

**Tests fail with connection errors**

- Ensure InvenioRDM instance is running
- Check BASE_URL is correct
- Verify network connectivity

**Intermittent search failures**

- Increase `time.sleep()` delays
- OpenSearch may need more time to index

**Tests leave data in database**

- Use `clean_database` fixture
- Check fixture is applied to test

## Adding New Tests

1. **Choose test type**: integration vs unit
2. **Use appropriate fixtures**: `clean_database`, `lens_importer`, etc.
3. **Add markers**: `@pytest.mark.integration`, etc.
4. **Follow naming**: `test_*` functions, `Test*` classes
5. **Include assertions**: Clear, specific assertions
6. **Add docstrings**: Explain what the test does

Example:

```python
@pytest.mark.integration
class TestNewFeature:
    """Test suite for new feature."""

    def test_feature_works(self, lens_importer, clean_database, sample_lens_record):
        """Test that new feature works correctly."""
        # Arrange
        data = sample_lens_record

        # Act
        result = lens_importer.new_feature(data)

        # Assert
        assert result is not None
        assert result['status'] == 'success'
```
