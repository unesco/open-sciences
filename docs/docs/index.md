# UNESCO Open Science Portal

Welcome to the UNESCO Open Science Portal powered by InvenioRDM - a modern research data management platform.

## Overview

This repository contains:

- **InvenioRDM instance**: Full-featured research data repository
- **OpenScience Tools**: Python SDK and CLI for programmatic access to InvenioRDM
  - Insert, update, delete records via SDK
  - Batch import from Lens.org
  - Search and manage records

## Prerequisites

Before setting up the UNESCO Open Science Portal, ensure your system meets these requirements:

### System Requirements

- **Operating System**: macOS, Linux, or Windows with WSL2
- **Memory**: Minimum 4GB RAM (8GB recommended for optimal performance)
- **Storage**: At least 5GB free disk space
- **Internet**: Stable connection for downloading dependencies

### Required Software

- **Python 3.9+**: Required for InvenioRDM
  ```bash
  python3 --version  # Should show Python 3.9 or higher.
  ```
- **Docker & Docker Compose**: For containerized services
  ```bash
  docker --version && docker compose version
  ```
- **Git**: For version control
  ```bash
  git --version
  ```

### Port Availability

Ensure these ports are available (not used by other applications):

- **5000**: Development server
- **5432**: PostgreSQL database
- **9200**: OpenSearch
- **6379**: Redis cache
- **5672**: RabbitMQ message queue

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd sc-openscience
```

### 2. Start the Development Environment

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Access the Portal

Once services are running, access:

- **Portal**: [http://localhost:5000](http://localhost:5000)
- **Admin Panel**: [http://localhost:5000/administration](http://localhost:5000/administration)

## OpenScience Tools

The OpenScience Tools provide a Python SDK and CLI for programmatic access to InvenioRDM.

### Installation

```bash
cd openscience_tools
pip install -e .
```

### Usage Examples

#### SDK Usage

```python
from openscience_tools import OpenScienceClient

# Initialize client
client = OpenScienceClient(base_url="http://localhost:5000", token="your-token")

# Create a record
record = client.create_record({
    "metadata": {
        "title": "My Research Data",
        "description": "Description of the research data"
    }
})

# Search records
results = client.search_records(query="research")
```

#### CLI Usage

```bash
# Search for records
openscience-cli search "research data"

# Import from Lens.org
openscience-cli import-lens --query "open science"

# Create a record
openscience-cli create-record --file record.json
```

## Development

### Project Structure

```
sc-openscience/
├── app_data/          # Initial data and vocabularies
├── assets/            # Frontend assets
├── docker/            # Docker configurations
├── openscience_tools/ # Python SDK and CLI
├── site/              # Site-specific customizations
├── static/            # Static files
└── templates/         # Custom templates
```

### Configuration

The main configuration file is `invenio.cfg`. You can customize:

- Site name and branding
- Authentication providers
- Storage backends
- Email settings
- Custom vocabularies

### Running Tests

```bash
# Run OpenScience Tools tests
cd openscience_tools
pytest
```

## Deployment

For production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Support

For issues and questions:

- Create an issue in the repository
- Contact the development team

## License

This project is licensed under the terms specified in the LICENSE file.
