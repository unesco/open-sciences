# UNESCO Open Science Portal

Welcome to the UNESCO Open Science Portal powered by InvenioRDM - a modern research data management platform.

## Start the user guide

Info on how to start this application module are given in its own user guide. To see it, follow these steps:

- Install Docker
- Clone the repo
- Run `docker-compose -f docker-compose.docs.yaml up`
- Access [http://localhost:9000](http://localhost:9000) to see the user guide

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

### Docker Configuration

- Docker Desktop must be running
- User must have permissions to run Docker commands
- At least 4GB of memory allocated to Docker

## Quick Start

This project includes a Makefile for easy development workflow management. All commands automatically handle virtual environment activation.

### Initial Setup

For first-time setup, initialize the project:

```bash
make init
```

This command will:

- Check and clean Docker environment
- Create a Python virtual environment (`.venv`)
- Install all required dependencies
- Setup containerized services (PostgreSQL, OpenSearch, Redis, RabbitMQ)
- Prepare the InvenioRDM instance

**Note**: If you encounter issues with services not starting (especially Redis), run `make check` first to clean up Docker, then retry `make init`.

### Development Workflow

**1. Start the development server:**

```bash
make up
```

Visit https://127.0.0.1:5000 in your browser.

**2. (Optional) Reset with curated data:**

After the server is running, you can optionally reset all records and load fresh data from various sources. First wait for some minutes after the first `make up` (to let Invenio finish the default data import), then run:

```bash
make tools-setup-env
```

and select `N` to generate a new token that will be used to interact with Invenio's API. After that, you can:

```bash
# Reset with Lens.org publications
make tools-reset FILE='openscience_tools/openscience_tools/sources/lens/data/publications.json'
```

This command:

- ✅ Deletes all existing records
- ✅ Imports fresh, curated data
- ✅ Gives you full programmatic control over your dataset
- ✅ Perfect for development and testing

**3. Stop the server:**

```bash
make stop
```

### Login Credentials

The system comes with three ready-to-use user accounts:

| Email                  | Password    | Role          | Description                                     |
| ---------------------- | ----------- | ------------- | ----------------------------------------------- |
| `admin@unesco.org`     | `Passw0rd!` | Administrator | Full system access including admin panel        |
| `scientist@unesco.org` | `Passw0rd!` | Scientist     | Standard user for creating and managing records |
| `demo@unesco.org`      | `Passw0rd!` | Demo User     | Basic user for demonstration purposes           |

**Note**: All users are pre-confirmed and active, so no email verification is required.

**Stop all services:**

```bash
make stop
```

**Build assets (CSS, JS, templates):**

```bash
make build
```

**Complete cleanup (⚠️ destroys all data):**

```bash
make destroy
```

## Development

### Making Changes

When customizing the portal, you can modify:

- **Templates**: `templates/` directory (HTML/Jinja2)
- **Styles**: `assets/less/` (LESS/CSS files)
- **JavaScript**: `assets/js/`
- **Configuration**: `invenio.cfg`
- **Static files**: `static/images/`

### Build Assets

After modifying templates, styles, or JavaScript:

```bash
make build
```

Then refresh your browser (Ctrl+F5 or Cmd+Shift+R).

### Development Loop

```bash
# 1. Start server (once)
make up

# 2. Make changes to templates/assets/styles

# 3. Build assets
make build

# 4. Refresh browser at https://127.0.0.1:5000

# Repeat steps 2-4 as needed
```

**Note**: Python code changes reload automatically, but assets require `make build`.

## OpenScience Tools

The project includes a Python package for programmatic interaction with InvenioRDM.

### Quick Setup

```bash
# 1. Start InvenioRDM
make up

# 2. Install the tools package
make tools-install

# 3. Generate API token and configure environment
make tools-setup-env
```

### SDK Examples

**Run Example Scripts:**

```bash
# Single record demo (insert/update/delete)
make tools-examples

# Batch import all publications
make tools-examples EXAMPLE=batch_import
```

### Common Operations

**Search Records:**

```bash
# Search all records
make tools-search

# Search with query
make tools-search QUERY='climate data'

# Search with options
make tools-search QUERY='test' OPTS='--detailed --size 20'
```

**View Record Details:**

```bash
# View specific record
make tools-view RECORD_ID='abc-123'

# View as JSON
make tools-view RECORD_ID='abc-123' OPTS='--format json'
```

**Export Records:**

```bash
# Export all records to CSV
make tools-export OUTPUT='records.csv'

# Export with all available fields
make tools-export OUTPUT='full_records.csv' OPTS='--all-fields'

# Export filtered records
make tools-export OUTPUT='climate.csv' OPTS='--query "climate"'

# Export from different instance (e.g., dev environment at https://open-science-dev.unesco.org)
make tools-export OUTPUT='dev_records.csv' BASE_URL='https://open-science-dev.unesco.org' TOKEN='your-token'
```

**Import Data:**

```bash
# Import from Lens.org JSON export
make tools-import-lens FILE='openscience_tools/openscience_tools/sources/lens/data/publications.json'

# Import with limit
make tools-import-lens FILE='openscience_tools/openscience_tools/sources/lens/data/publications.json' OPTS='--limit 10'

# Dry run (preview without importing)
make tools-import-lens FILE='openscience_tools/openscience_tools/sources/lens/data/publications.json' OPTS='--dry-run'
```

**Delete Records:**

```bash
# Preview deletions
make tools-cleanup OPTS='--dry-run'

# Delete all records (requires confirmation)
make tools-cleanup OPTS='--confirm'
```

**Reset Data:**

```bash
# Delete all records and import fresh data from Lens.org
make tools-reset FILE='openscience_tools/openscience_tools/sources/lens/data/publications.json'

# Reset with limited records
make tools-reset FILE='openscience_tools/openscience_tools/sources/lens/data/publications.json' OPTS='--limit 10'
```

### Available Commands

| Command                  | Description                                  |
| ------------------------ | -------------------------------------------- |
| `make tools-install`     | Install openscience_tools Python package     |
| `make tools-setup-env`   | Generate API token and configure environment |
| `make tools-search`      | Search records (use QUERY='...')             |
| `make tools-view`        | View record details (use RECORD_ID='...')    |
| `make tools-export`      | Export records to CSV (use OUTPUT='...')     |
| `make tools-cleanup`     | Delete all records                           |
| `make tools-import-lens` | Import from Lens.org (use FILE='...')        |
| `make tools-reset`       | Delete all + import from Lens                |
| `make tools-help`        | Show detailed help with examples             |

### Override Credentials (Optional)

You can override the default credentials stored in `.env`:

```bash
# Use different InvenioRDM instance
make tools-search QUERY='test' BASE_URL='https://myinstance.org' TOKEN='my-token'

# Reset data on different instance
make tools-reset FILE='data.json' BASE_URL='https://myinstance.org' TOKEN='my-token'
```

### Documentation

For complete documentation, see:

- `openscience_tools/README.md` - Full package documentation with installation, usage, and troubleshooting

## Available Make Commands

| Command         | Description                                         |
| --------------- | --------------------------------------------------- |
| `make init`     | Initialize project with virtualenv and setup        |
| `make users`    | Create ready-to-use users with predefined passwords |
| `make up`       | Start development server and services               |
| `make stop`     | Stop all services and processes                     |
| `make stop-all` | Force stop all services, containers and processes   |
| `make build`    | Build frontend assets                               |
| `make check`    | Check and fix Docker services if needed             |
| `make destroy`  | Completely destroy instance and virtualenv          |
| `make help`     | Show available commands                             |

## Project Structure

| Directory/File             | Description                                        |
| -------------------------- | -------------------------------------------------- |
| `Dockerfile`               | Container image definition                         |
| `Pipfile` / `Pipfile.lock` | Python dependencies managed by pipenv              |
| `app_data/`                | Application data (vocabularies, pages)             |
| `assets/`                  | Frontend assets (CSS, JavaScript, LESS, templates) |
| `docker/`                  | Docker configuration files                         |
| `invenio.cfg`              | Main InvenioRDM configuration                      |
| `static/`                  | Static files served as-is                          |
| `templates/`               | Custom Jinja2 templates                            |
| `.venv/`                   | Python virtual environment                         |

## Important Notes

- **SSL Certificate**: The development server uses a self-signed SSL certificate. Your browser will show a security warning that you need to bypass.
- **Virtual Environment**: All Invenio commands must be run within the activated virtual environment. The Makefile handles this automatically.
- **First Run**: Initial setup and first server start may take several minutes as Docker images are downloaded.

## Customizations

This UNESCO Science Portal instance includes:

- Custom UNESCO branding and colors
- Inter font family (UNESCO's official typeface)
- Custom footer with UNESCO links
- Favicon and logo customizations

## 🚀 Production Deployment

For production and Kubernetes deployment guides, see the complete documentation:

```bash
# Start the documentation server
docker-compose -f docker-compose.docs.yaml up

# Access the user guide at http://localhost:9000
```

The documentation includes:

- Complete development guide
- Kubernetes/Kind deployment guide
- Production deployment procedures
- Troubleshooting tips

## Documentation

For detailed InvenioRDM documentation, visit:

- [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/)
- [InvenioRDM CLI Reference](https://inveniordm.docs.cern.ch/reference/cli/)
