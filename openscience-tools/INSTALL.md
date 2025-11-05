# OpenScience Tools - Package Installation Guide

## 📦 Installation Options

### Option 1: Install from GitLab Package Registry (Recommended)

```bash
# Install the latest version
pip install openscience-tools \
  --index-url https://repository.unesco.org/api/v4/projects/PROJECT_ID/packages/pypi/simple

# With authentication token
pip install openscience-tools \
  --index-url https://<token-name>:<token>@repository.unesco.org/api/v4/projects/PROJECT_ID/packages/pypi/simple
```

### Option 2: Install from Source (Development)

```bash
# Clone the repository
cd openscience-tools

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Option 3: Install from Git Repository

```bash
pip install git+https://repository.unesco.org/gitlab/sc/sc-openscience.git#subdirectory=openscience-tools
```

## 🚀 Quick Start

### Using the Python API

```python
from openscience_tools import InvenioRDMClient

# Initialize client
client = InvenioRDMClient(
    base_url="https://127.0.0.1:5000",
    token="your-api-token"
)

# Search records
results = client.search_records(q="climate data", size=10)
print(f"Found {results['hits']['total']} records")

# Get a record
record = client.get_record("abc-123")
print(record["metadata"]["title"])

# Create a draft
draft = client.create_draft({
    "metadata": {
        "title": "New Dataset",
        "resource_type": {"id": "dataset"},
        "creators": [{"person_or_org": {"name": "Jane Smith"}}],
        "publication_date": "2024-01-01"
    }
})
print(f"Created draft: {draft['id']}")
```

### Using Command-Line Tools

After installation, several CLI tools are available:

```bash
# Main CLI
openscience-tools --help

# Search records
ost-search -q "machine learning" -s 10

# View record details
ost-view abc-123

# Get statistics
ost-stats --record-id abc-123

# Import from Lens.org
ost-import-lens data/publications.json --limit 10

# Import from CSV
ost-import-csv data/records.csv

# Import from Zenodo
ost-import-zenodo --record-id 17462748

# Cleanup records
ost-cleanup --dry-run
```

## 🔧 Configuration

Create a configuration file or use environment variables:

### Environment Variables

```bash
export INVENIO_BASE_URL="https://127.0.0.1:5000"
export INVENIO_TOKEN="your-api-token"
```

### Configuration File

Create `~/.openscience-tools/config.yaml`:

```yaml
invenio:
  base_url: "https://127.0.0.1:5000"
  token: "your-api-token"
  verify_ssl: false
```

## 📚 Usage Examples

### Python API Examples

#### Search and Filter

```python
# Advanced search with filters
results = client.search_records(
    q="climate",
    filters={"resource_type": "dataset"},
    sort="mostrecent",
    size=20,
    page=1
)

# Iterate through results
for hit in results["hits"]["hits"]:
    print(f"{hit['id']}: {hit['metadata']['title']}")
```

#### Record Management

```python
# Create, update, and publish
draft = client.create_draft(metadata)
client.upload_file(draft["id"], "data.csv", "/path/to/data.csv")
client.publish_draft(draft["id"])

# Update existing record
updated = client.update_record("abc-123", new_metadata)
```

#### Statistics

```python
# Get record statistics
stats = client.get_record_stats("abc-123")
print(f"Views: {stats['views']}, Downloads: {stats['downloads']}")
```

### CLI Examples

#### Batch Import from Multiple Sources

```bash
# Import from Lens.org with progress
ost-import-lens publications.json --batch-size 10 --verbose

# Import from CSV with validation
ost-import-csv records.csv --dry-run

# Import from Zenodo search
ost-import-zenodo --query "COVID-19" --max 50
```

#### Record Management

```bash
# Search with detailed output
ost-search -q "test" --detailed --format json > results.json

# View multiple records
for id in abc-123 def-456 ghi-789; do
    ost-view $id
done

# Cleanup with confirmation
ost-cleanup --confirm
```

## 🧪 Testing Your Installation

```bash
# Run in Python
python -c "from openscience_tools import InvenioRDMClient; print('✅ Installation OK')"

# Test CLI
openscience-tools --version

# Test connection
python -c "
from openscience_tools import InvenioRDMClient
client = InvenioRDMClient('https://127.0.0.1:5000', 'token')
print('Connected!' if client.ping() else 'Connection failed')
"
```

## 🔐 Authentication

### Generate API Token

```bash
# In your InvenioRDM instance
invenio tokens create -n "openscience-tools" -u admin@example.org

# Or use the setup script
python setup_env.py
```

### Use Token in Code

```python
import os
from openscience_tools import InvenioRDMClient

token = os.getenv("INVENIO_TOKEN")
client = InvenioRDMClient("https://127.0.0.1:5000", token)
```

## 📖 Documentation

- [Main README](README.md) - Full documentation
- [API Reference](docs/api.md) - Detailed API documentation
- [CLI Reference](docs/cli.md) - Command-line tools guide
- [Examples](examples/) - Usage examples

## 🐛 Troubleshooting

### SSL Certificate Errors

```python
# Disable SSL verification (development only)
client = InvenioRDMClient(
    base_url="https://127.0.0.1:5000",
    token="token",
    verify_ssl=False
)
```

### Import Errors

```bash
# Ensure package is installed
pip show openscience-tools

# Reinstall if needed
pip install --force-reinstall openscience-tools
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.
