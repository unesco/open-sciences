# UNESCO Open Science Portal

Welcome to the UNESCO Open Science Portal powered by InvenioRDM - a modern research data management platform.

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
  python3 --version  # Should show Python 3.9 or higher
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

After the server is running, you can optionally reset all records and load fresh data from various sources:

```bash
# Option A: Reset with CSV data (recommended for development)
make scripts-reset CSV='src/sources/csv/data/publications.csv'

# Option B: Reset with Lens.org publications
make scripts-reset LENS='src/sources/lens/data/publications.json'

# Option C: Reset with Zenodo record
make scripts-reset ZENODO_ID='17462748'

# Option D: Reset with Zenodo search results
make scripts-reset ZENODO_QUERY='climate data' MAX=5
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

## Scripts Microservice

The project includes a Python microservice for programmatic interaction with InvenioRDM.

### Quick Setup

```bash
# 1. Start InvenioRDM
make up

# 2. Configure scripts environment (auto-generates API token)
make scripts-setup-env

# 3. Build the scripts container
make scripts-build

# 4. Test connection
make scripts-run CMD='python -m src.tools.cli test-connection'
```

### Common Operations

**Import Data:**

```bash
# From CSV
make scripts-import-csv FILE='src/sources/csv/data/publications.csv'

# From Lens.org JSON export
make scripts-import-lens FILE='src/sources/lens/data/publications.json'

# From Zenodo (by ID)
make scripts-import-zenodo RECORD_ID='17462748'

# From Zenodo (by search)
make scripts-import-zenodo QUERY='climate data' MAX=5
```

**Search and Browse:**

```bash
# Search records
make scripts-run CMD='python -m src.tools.search -q "climate" -s 10'

# View record details
make scripts-run CMD='python -m src.tools.view RECORD_ID'

# Get statistics
make scripts-run CMD='python -m src.tools.stats'
```

**Reset Data:**

```bash
# Delete all records and import from CSV
make scripts-reset CSV='src/sources/csv/data/publications.csv'

# Delete all records and import from Lens.org JSON export
make scripts-reset LENS='src/sources/lens/data/publications.json'

# Delete all records and import a specific Zenodo record
make scripts-reset ZENODO_ID='17462748'

# Delete all records and import from Zenodo search
make scripts-reset ZENODO_QUERY='climate data' MAX=5
```

**Interactive Shell:**

```bash
make scripts-shell
```

### Available Commands

| Command                      | Description                         |
| ---------------------------- | ----------------------------------- |
| `make scripts-setup-env`     | Auto-configure with API token       |
| `make scripts-build`         | Build scripts container             |
| `make scripts-run`           | Run any script or tool              |
| `make scripts-import-csv`    | Import from CSV file                |
| `make scripts-import-lens`   | Import from Lens.org                |
| `make scripts-import-zenodo` | Import from Zenodo                  |
| `make scripts-reset`         | Delete all + import from any source |
| `make scripts-delete-all`    | Delete all records                  |
| `make scripts-shell`         | Interactive shell                   |
| `make scripts-help`          | Detailed help with examples         |

### Documentation

For complete documentation, see:

- `scripts/README.md` - Full scripts documentation
- `scripts/src/tools/README.md` - Management tools guide
- `scripts/src/sources/README.md` - Data importers guide

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

## Documentation

For detailed InvenioRDM documentation, visit:

- [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/)
- [InvenioRDM CLI Reference](https://inveniordm.docs.cern.ch/reference/cli/)

## Troubleshooting

### Common Issues

#### Redis/Services Not Starting After Destroy

If you encounter errors like "Unable to boot up redis" after running `make destroy`:

**Problem**: Docker containers or volumes remain in an inconsistent state.

**Solution**:

```bash
# Method 1: Use the check command to clean up
make check

# Then re-initialize
make init

# Method 2: Manual cleanup
docker-compose -f docker-compose.full.yml down --remove-orphans
docker volume prune -f
docker network prune -f
make init
```

#### Permission Issues

**Problem**: Ensure Docker is running and you have proper permissions.

**Solution**:

- Make sure Docker Desktop is running
- Check that your user has Docker permissions
- On Linux, you may need to add your user to the docker group: `sudo usermod -aG docker $USER`

#### Port Conflicts

**Problem**: Default ports (5000, 5432, 9200, 6379) must be available.

**Solution**:

```bash
# Check which process is using a port
lsof -i :5000  # Replace 5000 with the conflicting port

# Stop all services to free ports
make stop-all
```

#### Memory Issues

**Problem**: Ensure sufficient RAM (minimum 4GB recommended).

**Solution**:

- Increase Docker Desktop memory allocation in Settings → Resources
- Close other memory-intensive applications
- Consider upgrading your system RAM
