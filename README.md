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

**Start the development server:**

```bash
make up
```

Visit https://127.0.0.1:5000 in your browser once the server is running.

> **💡 Tip - Reset Records for Full Programmatic Control**  
> After starting the server, you may want to reset all records to use only the curated scientific publications defined in `scripts/data/publications.csv`. This gives you full programmatic control over your dataset:
>
> ```bash
> make scripts-reset CSV='data/publications.csv'
> ```
>
> This command will delete all existing records and import only the high-quality scientific publications from the CSV, ensuring a clean and controlled dataset. See the [Scripts Microservice](#scripts-microservice) section for more details.

> **🌐 Tip - Import from Zenodo.org**  
> You can import records directly from Zenodo.org with all metadata and files:
>
> ```bash
> # Import a specific record by ID
> make scripts-import-zenodo RECORD='17462748'
>
> # Import without downloading files (metadata only)
> make scripts-import-zenodo RECORD='17462748' OPTS='--skip-files'
>
> # Search and import multiple records
> make scripts-import-zenodo SEARCH='climate data' MAX=5
> ```
>
> This allows you to populate your instance with real scientific data from Zenodo, including all creators, contributors, related identifiers, keywords, and files. Perfect for testing or bootstrapping your repository!

> **🔬 Tip - Import from Lens.org**  
> You can also import publications from Lens.org JSON exports with rich metadata:
>
> ```bash
> # Import from Lens.org JSON export
> make scripts-import-lens FILE='data/lens.org/publications.json'
>
> # Dry run to validate without creating records
> make scripts-import-lens FILE='publications.json' OPTS='--dry-run'
>
> # Import first 10 records only
> make scripts-import-lens FILE='publications.json' OPTS='--limit 10'
> ```
>
> Lens.org importer includes support for:
>
> - MeSH terms (Medical Subject Headings)
> - ASJC subjects (journal classification)
> - Chemical substances with CAS registry numbers
> - Citation metrics and funding information
> - Rich affiliation data with ROR/GRID IDs
>
> See `scripts/docs/LENS_ORG_IMPORTER.md` for complete documentation.

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

### Development Workflow

When developing and customizing the UNESCO Science Portal, follow this workflow:

#### 1. **Making Changes**

You can modify various parts of the system:

- **Templates**: Edit files in `templates/` directory for HTML/Jinja2 changes
- **Assets**: Modify files in `assets/` directory:
  - **Stylesheets**: `assets/less/` for LESS/CSS files
  - **JavaScript**: `assets/js/` for JavaScript files
  - **Images**: `static/images/` for static assets
- **Configuration**: Update `invenio.cfg` for system settings
- **Data**: Modify `app_data/` for vocabularies, users, pages

#### 2. **Building Assets**

After making changes to templates, stylesheets, or JavaScript files, you **must** rebuild assets:

```bash
make build
```

This command compiles:

- LESS files into CSS
- JavaScript bundles
- Template changes
- Static file collections

#### 3. **Viewing Changes**

After building assets:

1. **Refresh your browser** at https://127.0.0.1:5000
2. **Clear browser cache** if changes don't appear (Ctrl+F5 or Cmd+Shift+R)
3. **Check browser console** for any JavaScript errors

#### 4. **Common Development Tasks**

**Styling Changes:**

```bash
# Edit LESS files in assets/less/
# Then rebuild:
make build
# Refresh browser to see changes
```

**Template Modifications:**

```bash
# Edit HTML/Jinja2 files in templates/
# Then rebuild:
make build
# Refresh browser to see changes
```

**Configuration Updates:**

```bash
# Edit invenio.cfg
# Restart the server:
make stop
make up
```

**Adding New Users/Data:**

```bash
# Edit app_data/users.yaml or other data files
# Then reload fixtures:
make users
```

#### 5. **Development Server Management**

The development server supports hot-reloading for Python code changes, but **not** for assets:

- **Python code changes**: Automatically detected and reloaded
- **Template/Asset changes**: Require `make build` + browser refresh
- **Configuration changes**: Require server restart (`make stop` + `make up`)

#### 6. **Debugging Tips**

- **Check logs**: Terminal where `make up` is running shows real-time logs
- **Browser DevTools**: Use F12 to inspect CSS/JavaScript issues
- **Asset build errors**: `make build` will show compilation errors
- **Server errors**: Check the terminal output for Python stack traces

### Development Best Practices

1. **Always build after asset changes**: `make build` is required for CSS/JS/template changes
2. **Use browser cache refresh**: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
3. **Test in clean browser session**: Use incognito/private mode to avoid cache issues
4. **Check both logged-in and logged-out views**: Some changes only appear in certain states
5. **Validate responsive design**: Test on different screen sizes

### Hot Development Loop

For efficient development:

```bash
# 1. Start the server (once)
make up

# 2. Make your changes to templates/assets/styles
# 3. Build assets
make build

# 4. Refresh browser at https://127.0.0.1:5000
# 5. Repeat steps 2-4 as needed
```

**Note**: Keep the terminal with `make up` running throughout your development session.

## Scripts Microservice

The project includes a containerized microservice for interacting with InvenioRDM APIs through Python scripts.

### Quick Microservice Setup

**1. Ensure InvenioRDM is running:**

```bash
make up
```

**2. Automatically configure environment (generates API token and .env file):**

```bash
make scripts-setup-env
```

**3. Build the microservice container:**

```bash
make scripts-build
```

**4. Test the connection:**

```bash
make scripts-run CMD='python examples/invenio_cli.py test-connection'
```

### Scripts Usage Examples

**Search records:**

```bash
make scripts-run CMD='python examples/search_records.py -q "climate data" -s 5 --detailed'
```

**Create a new record:**

```bash
make scripts-run CMD='python examples/create_record.py -t "My Dataset" --creator "John Doe" --description "Test record"'
```

**Use the unified CLI:**

```bash
make scripts-run CMD='python examples/invenio_cli.py search -q test'
make scripts-run CMD='python examples/invenio_cli.py get record-id'
```

**Interactive shell for development:**

```bash
make scripts-shell
```

**Import from external data sources:**

```bash
# Import publications from Lens.org
make scripts-import-lens FILE='src/sources/lens/data/publications.json'

# Dry-run validation (no records created)
make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--dry-run'

# Import with limits
make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 10 --verbose'
```

### Available Scripts Commands

| Command                    | Description                               |
| -------------------------- | ----------------------------------------- |
| `make scripts-setup-env`   | Automatic setup with API token generation |
| `make scripts-build`       | Build the microservice container          |
| `make scripts-run`         | Run a specific script                     |
| `make scripts-shell`       | Open interactive shell in container       |
| `make scripts-import-lens` | Import publications from Lens.org         |
| `make scripts-help`        | Show detailed help with examples          |

### Scripts Development

**Microservice structure:**

```
scripts/
├── src/
│   ├── invenio_client.py      # Python client for InvenioRDM API
│   └── sources/               # External data source importers
│       ├── README.md          # Guide for adding new sources
│       └── lens/              # Lens.org importer
│           ├── config.py      # Mapping configuration
│           ├── reader.py      # JSON/API readers
│           ├── importer.py    # Main orchestrator
│           ├── data/          # Sample data files
│           │   └── publications.json
│           └── mappers/       # Field mappers
│               ├── standard.py    # Standard InvenioRDM fields
│               ├── custom.py      # Custom fields
│               └── related.py     # Related identifiers
├── examples/
│   ├── search_records.py      # Search examples
│   ├── create_record.py       # Record creation
│   ├── import_from_lens.py    # Lens.org importer CLI
│   ├── test_lens_mapping.py   # Test Lens.org mapping
│   ├── get_statistics.py      # Statistics
│   └── invenio_cli.py         # Unified CLI
├── config/
│   ├── .env                   # Configuration (auto-generated)
│   └── .env.example           # Example template
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
└── README.md                  # Detailed documentation
```

**Data source importers:**

The `src/sources/` directory contains importers for external data sources:

- **Lens.org** (`lens/`): Import publication records from Lens.org JSON exports
  - Standard metadata mapping (titles, creators, dates)
  - Author identifiers (ORCID) and affiliations (ROR)
  - Custom fields support (MeSH terms, ASJC subjects, metrics)
  - Related identifiers (DOI, PMID, PMCID, arXiv)

See `src/sources/README.md` for:

- Architecture and design patterns
- How to add new data sources
- Testing and validation guidelines

**To develop new scripts:**

1. Enter the container shell: `make scripts-shell`
2. Your scripts can use `from src.invenio_client import InvenioRDMClient`
3. Configuration is automatically loaded from environment variables
4. See `scripts/README.md` for complete API documentation

**Regenerate API token:**

If you need a new token (for example, after database reset):

```bash
make scripts-setup-env
```

This command will detect if InvenioRDM is running, create a new token for the admin user, and automatically update the `.env` file.

For more details, see the complete documentation in `scripts/README.md`.

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
