# UNESCO Science Portal - InvenioRDM Makefile
# Commands for managing the InvenioRDM instance

# Default shell
SHELL := /bin/bash

# Virtual environment path
VENV_PATH = ./.venv
VENV_ACTIVATE = source $(VENV_PATH)/bin/activate

USER_PASSWORD = Passw0rd!

.PHONY: help destroy init up stop stop-all build users ssl-certs check scripts-build scripts-up scripts-stop scripts-run scripts-shell scripts-help scripts-setup-env scripts-status scripts-import

# Default target
help:
	@echo "UNESCO Science Portal - Available commands:"
	@echo "  init         - Initialize the project (create virtualenv and setup)"
	@echo "  ssl-certs    - Generate SSL certificates for development"
	@echo "  users        - Create ready-to-use users with predefined passwords"
	@echo "  up           - Start the development server and services"
	@echo "  stop         - Stop all services and processes"
	@echo "  stop-all     - Force stop all services, containers and processes"
	@echo "  build        - Build assets (CSS, JS, etc.)"
	@echo "  check        - Check and fix Docker services if needed"
	@echo "  destroy      - Completely destroy the instance and virtualenv"
	@echo ""
	@echo "Scripts Microservice Commands:"
	@echo "  scripts-setup-env    - Auto-setup environment with API token generation"
	@echo "  scripts-status       - Check scripts microservice configuration status"
	@echo "  scripts-build        - Build the scripts microservice container"
	@echo "  scripts-up           - Start the scripts microservice"
	@echo "  scripts-stop         - Stop the scripts microservice containers"
	@echo "  scripts-run          - Run a specific script or tool"
	@echo "  scripts-import-csv   - Import records from CSV (use FILE='path/to/file.csv')"
	@echo "  scripts-import-lens  - Import from Lens.org (use FILE='path/to/file.json')"
	@echo "  scripts-import-zenodo - Import from Zenodo (use RECORD_ID or QUERY)"
	@echo "  scripts-reset        - Delete all + import from source (CSV/Lens/Zenodo)"
	@echo "  scripts-shell        - Open an interactive shell in the scripts container"
	@echo "  scripts-help         - Show scripts microservice help and examples"
	@echo ""
	@echo "Usage: make [command]"
	@echo "Example: make scripts-run CMD='python -m src.tools.search -q test'"
	@echo "Example: make scripts-import-csv FILE='data/sample_records.csv'"

# Initialize the project
init:
	@echo "🚀 Initializing UNESCO Science Portal..."
	@echo "� Checking Docker environment..."
	$(MAKE) check
	@echo "�📦 Creating Python virtual environment..."
	python3 -m venv $(VENV_PATH)
	@echo "🔧 Activating virtual environment and installing dependencies..."
	$(VENV_ACTIVATE) && pip install --upgrade pip
	$(VENV_ACTIVATE) && pip install pipenv
	$(VENV_ACTIVATE) && pipenv install --dev
	@echo "🛠️ Installing Invenio packages..."
	$(VENV_ACTIVATE) && invenio-cli install
	@echo "🐳 Setting up containerized services..."
	$(VENV_ACTIVATE) && invenio-cli services setup
	@echo "🔐 Setting up SSL certificates..."
	$(MAKE) ssl-certs
	@echo "👥 Creating ready-to-use users..."
	$(MAKE) users
	@echo "✅ Initialization complete! Use 'make up' to start the server."

# Start the development server
up:
	@echo "🌐 Starting UNESCO Science Portal..."
	@echo "🐳 Starting containerized services..."
	$(VENV_ACTIVATE) && invenio-cli services start
	@echo "🚀 Starting development server..."
	@echo "📍 Server will be available at https://127.0.0.1:5000"
	$(VENV_ACTIVATE) && invenio-cli run

# Stop all services
stop:
	@echo "⏹️  Stopping UNESCO Science Portal..."
	@echo "🐳 Stopping containerized services..."
	-$(VENV_ACTIVATE) && invenio-cli services stop
	@echo "📦 Stopping Scripts microservice containers..."
	-docker-compose -f docker-compose.scripts.yml stop
	@echo "✅ All services and processes stopped."

# Build assets
build:
	@echo "🔨 Building assets for UNESCO Science Portal..."
	$(VENV_ACTIVATE) && invenio-cli assets build
	@echo "✅ Assets built successfully!"

# Create ready-to-use users
users:
	@echo "👥 Creating UNESCO Portal users..."
	@echo "📝 Creating users via CLI as backup..."
	-$(VENV_ACTIVATE) && invenio users create admin@unesco.org --password "$(USER_PASSWORD)" --active --confirm
	-$(VENV_ACTIVATE) && invenio users create scientist@unesco.org --password "$(USER_PASSWORD)" --active --confirm
	-$(VENV_ACTIVATE) && invenio users create demo@unesco.org --password "$(USER_PASSWORD)" --active --confirm
	@echo "🔧 Setting up administrator permissions..."
	-$(VENV_ACTIVATE) && invenio access allow superuser-access user admin@unesco.org
	-$(VENV_ACTIVATE) && invenio access allow administration-access user admin@unesco.org
	@echo "� Users created with predefined passwords:"
	@echo "   📧 admin@unesco.org / $(USER_PASSWORD) (Administrator)"
	@echo "   📧 scientist@unesco.org / $(USER_PASSWORD) (Scientist)"
	@echo "   📧 demo@unesco.org / $(USER_PASSWORD) (Demo User)"
	@echo "✅ All users are active and ready to login!"

# Check and fix Docker services
check:
	@echo "🔍 Checking Docker services status..."
	@echo "🐳 Checking if Docker is running..."
	@if ! docker info > /dev/null 2>&1; then \
		echo "❌ Docker is not running. Please start Docker Desktop."; \
		exit 1; \
	fi
	@echo "✅ Docker is running"
	@echo "🔄 Checking InvenioRDM containers..."
	@if docker ps -a | grep -q "sc-openscience"; then \
		echo "🧹 Found existing containers, cleaning up..."; \
		docker-compose -f docker-compose.full.yml down --remove-orphans 2>/dev/null || true; \
		docker rm -f $$(docker ps -a -q --filter "name=sc-openscience") 2>/dev/null || true; \
	fi
	@echo "🗑️  Removing stale volumes..."
	-docker volume rm $$(docker volume ls -q --filter "name=sc-openscience") 2>/dev/null || true
	@echo "🌐 Removing stale networks..."
	-docker network rm $$(docker network ls -q --filter "name=sc-openscience") 2>/dev/null || true
	@echo "✅ Docker cleanup complete. Ready for fresh setup."

# Generate SSL certificates for development
ssl-certs:
	@echo "🔐 Generating SSL certificates for development..."
	@mkdir -p docker/nginx
	@if [ ! -f docker/nginx/test.crt ] || [ ! -f docker/nginx/test.key ]; then \
		openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
			-keyout docker/nginx/test.key \
			-out docker/nginx/test.crt \
			-subj "/C=US/ST=State/L=City/O=UNESCO/OU=Science Portal/CN=localhost" \
			-addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1"; \
		echo "✅ SSL certificates generated successfully!"; \
	else \
		echo "ℹ️  SSL certificates already exist, skipping generation."; \
	fi

# Completely destroy the instance
destroy:
	@echo "💥 Destroying UNESCO Science Portal instance..."
	@echo "⚠️  This will permanently delete all data!"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ]
	@echo "� Stopping all services first..."
	-$(MAKE) stop-all
	@echo "�🐳 Destroying containerized services..."
	-$(VENV_ACTIVATE) && invenio-cli services destroy
	@echo "🧹 Performing global cleanup..."
	-$(VENV_ACTIVATE) && invenio-cli destroy
	@echo "🗑️  Removing virtual environment..."
	rm -rf $(VENV_PATH)
	@echo "🔐 Removing SSL certificates..."
	rm -f docker/nginx/test.crt docker/nginx/test.key
	@echo "🐋 Cleaning up Docker volumes and networks..."
	-docker volume prune -f
	-docker network prune -f
	@echo "💾 Removing any persistent data..."
	-rm -rf .invenio.private
	@echo "✅ Instance completely destroyed!"

# Scripts microservice targets

scripts-status:
	@echo "📊 Scripts Microservice Status"
	@echo "==============================="
	@echo ""
	@echo "🔍 Checking environment configuration..."
	@if [ -f scripts/config/.env ]; then \
		echo "✅ Configuration file exists: scripts/config/.env"; \
		if grep -q "INVENIO_TOKEN=.*[A-Za-z0-9]" scripts/config/.env 2>/dev/null; then \
			echo "✅ API token configured"; \
		else \
			echo "❌ API token not configured or empty"; \
		fi; \
		if grep -q "INVENIO_BASE_URL=https" scripts/config/.env 2>/dev/null; then \
			echo "✅ HTTPS URL configured"; \
		else \
			echo "⚠️  HTTP URL configured (HTTPS recommended)"; \
		fi; \
	else \
		echo "❌ Configuration file missing: scripts/config/.env"; \
		echo "   Run 'make scripts-setup-env' to configure automatically"; \
	fi
	@echo ""
	@echo "🐳 Checking Docker container..."
	@if docker images sc-openscience-scripts:latest --format "table {{.Repository}}" 2>/dev/null | grep -q "sc-openscience-scripts"; then \
		echo "✅ Docker container built"; \
	else \
		echo "❌ Docker container not built"; \
		echo "   Run 'make scripts-build' to build the container"; \
	fi
	@echo ""
	@echo "🌐 Checking InvenioRDM connectivity..."
	@if curl -k -s --max-time 5 https://127.0.0.1:5000/ > /dev/null 2>&1; then \
		echo "✅ InvenioRDM is running and reachable"; \
	else \
		echo "❌ InvenioRDM is not reachable"; \
		echo "   Run 'make up' to start InvenioRDM"; \
	fi
	@echo ""

scripts-setup-env:
	@echo "🔧 Automatic environment configuration for Scripts Microservice..."
	@echo "🔑 Generating API token and configuring .env..."
	$(VENV_ACTIVATE) && python scripts/setup_env.py
	@echo "✅ Environment setup completed!"

scripts-build:
	@echo "🔨 Building InvenioRDM Scripts microservice..."
	docker-compose -f docker-compose.scripts.yml build scripts
	@echo "✅ Scripts microservice built successfully!"

scripts-up:
	@echo "🚀 Starting InvenioRDM Scripts microservice..."
	@echo "📋 Starting with interactive help..."
	docker-compose -f docker-compose.scripts.yml up scripts

scripts-stop:
	@echo "⏹️  Stopping Scripts microservice..."
	@echo "🐳 Stopping scripts containers..."
	-docker-compose -f docker-compose.scripts.yml down 2>/dev/null || true
	@echo "✅ Scripts microservice stopped."

scripts-run:
	@echo "🏃 Running script command: $(CMD)"
	@if [ -z "$(CMD)" ]; then \
		echo "❌ Error: Please specify CMD='command to run'"; \
		echo "Example: make scripts-run CMD='python -m src.tools.search -q test'"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.scripts.yml run --rm scripts-cli $(CMD)

scripts-shell:
	@echo "🐚 Opening interactive shell in scripts container..."
	docker-compose -f docker-compose.scripts.yml run --rm scripts-cli /bin/bash

scripts-import-csv:
	@echo "📥 Importing records from CSV..."
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: FILE parameter required"; \
		echo "Usage:"; \
		echo "  make scripts-import-csv FILE='src/sources/csv/data/publications.csv'"; \
		echo "  make scripts-import-csv FILE='data/records.csv' OPTS='--dry-run'"; \
		echo "  make scripts-import-csv FILE='data/records.csv' OPTS='--skip-errors --verbose'"; \
		exit 1; \
	fi
	@CMD="python -m src.sources.csv --file $(FILE)"; \
	if [ -n "$(OPTS)" ]; then \
		CMD="$$CMD $(OPTS)"; \
	fi; \
	docker-compose -f docker-compose.scripts.yml run --rm scripts-cli $$CMD

scripts-delete-all:
	@echo "🗑️  Deleting all records from InvenioRDM..."
	@if [ -n "$(OPTS)" ]; then \
		docker-compose -f docker-compose.scripts.yml run --rm scripts-cli python -m src.tools.cleanup $(OPTS); \
	else \
		docker-compose -f docker-compose.scripts.yml run --rm scripts-cli python -m src.tools.cleanup; \
	fi

scripts-reset:
	@echo "🔄 Resetting InvenioRDM records..."
	@if [ -z "$(CSV)" ] && [ -z "$(LENS)" ] && [ -z "$(ZENODO_ID)" ] && [ -z "$(ZENODO_QUERY)" ]; then \
		echo "❌ Error: Source parameter required"; \
		echo "Usage:"; \
		echo "  CSV:    make scripts-reset CSV='data/publications.csv'"; \
		echo "  Lens:   make scripts-reset LENS='data/publications.json'"; \
		echo "  Zenodo: make scripts-reset ZENODO_ID='17462748'"; \
		echo "  Zenodo: make scripts-reset ZENODO_QUERY='climate data' MAX=5"; \
		echo ""; \
		echo "With options:"; \
		echo "  make scripts-reset CSV='data/publications.csv' OPTS='--verbose'"; \
		echo "  make scripts-reset LENS='data/publications.json' OPTS='--limit 10'"; \
		echo "  make scripts-reset ZENODO_ID='17462748' OPTS='--skip-files'"; \
		exit 1; \
	fi
	@echo ""
	@echo "📋 Step 1/2: Deleting all existing records..."
	@docker-compose -f docker-compose.scripts.yml run --rm scripts-cli python -m src.tools.cleanup --confirm
	@echo ""
	@echo "📋 Step 2/2: Importing fresh records..."
	@if [ -n "$(CSV)" ]; then \
		echo "📥 Importing from CSV: $(CSV)"; \
		CMD="python -m src.sources.csv --file $(CSV)"; \
		if [ -n "$(OPTS)" ]; then \
			CMD="$$CMD $(OPTS)"; \
		fi; \
		docker-compose -f docker-compose.scripts.yml run --rm scripts-cli $$CMD; \
	elif [ -n "$(LENS)" ]; then \
		echo "🔬 Importing from Lens: $(LENS)"; \
		CMD="python -m src.sources.lens --file $(LENS)"; \
		if [ -n "$(OPTS)" ]; then \
			CMD="$$CMD $(OPTS)"; \
		fi; \
		docker-compose -f docker-compose.scripts.yml run --rm scripts-cli $$CMD; \
	elif [ -n "$(ZENODO_ID)" ]; then \
		echo "📡 Importing from Zenodo record: $(ZENODO_ID)"; \
		docker-compose -f docker-compose.scripts.yml run --rm scripts-cli python -m src.sources.zenodo --record-id $(ZENODO_ID) $(OPTS); \
	elif [ -n "$(ZENODO_QUERY)" ]; then \
		echo "📡 Importing from Zenodo search: $(ZENODO_QUERY)"; \
		if [ -n "$(MAX)" ]; then \
			docker-compose -f docker-compose.scripts.yml run --rm scripts-cli python -m src.sources.zenodo --search "$(ZENODO_QUERY)" --max-results $(MAX) $(OPTS); \
		else \
			docker-compose -f docker-compose.scripts.yml run --rm scripts-cli python -m src.sources.zenodo --search "$(ZENODO_QUERY)" $(OPTS); \
		fi; \
	fi
	@echo ""
	@echo "✅ Reset complete!"

scripts-import-zenodo:
	@echo "📥 Importing from Zenodo..."
	@if [ -z "$(RECORD_ID)" ] && [ -z "$(QUERY)" ]; then \
		echo "❌ Error: RECORD_ID or QUERY parameter required"; \
		echo "Usage:"; \
		echo "  make scripts-import-zenodo RECORD_ID='17462748'"; \
		echo "  make scripts-import-zenodo QUERY='climate data' MAX=5"; \
		echo "  make scripts-import-zenodo RECORD_ID='17462748' OPTS='--skip-files --dry-run'"; \
		exit 1; \
	fi
	@if [ -n "$(RECORD_ID)" ]; then \
		docker-compose -f docker-compose.scripts.yml run --rm scripts-cli python -m src.sources.zenodo --record-id $(RECORD_ID) $(OPTS); \
	elif [ -n "$(QUERY)" ]; then \
		if [ -n "$(MAX)" ]; then \
			docker-compose -f docker-compose.scripts.yml run --rm scripts-cli python -m src.sources.zenodo --search "$(QUERY)" --max-results $(MAX) $(OPTS); \
		else \
			docker-compose -f docker-compose.scripts.yml run --rm scripts-cli python -m src.sources.zenodo --search "$(QUERY)" $(OPTS); \
		fi; \
	fi

scripts-import-lens:
	@echo "🔬 Importing from Lens.org..."
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: FILE parameter required"; \
		echo "Usage:"; \
		echo "  make scripts-import-lens FILE='src/sources/lens/data/publications.json'"; \
		echo "  make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--dry-run'"; \
		echo "  make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 10 --verbose'"; \
		exit 1; \
	fi
	@CMD="python -m src.sources.lens --file $(FILE)"; \
	if [ -n "$(OPTS)" ]; then \
		CMD="$$CMD $(OPTS)"; \
	fi; \
	docker-compose -f docker-compose.scripts.yml run --rm scripts-cli $$CMD

scripts-help:
	@echo "📚 InvenioRDM Scripts Microservice Help"
	@echo "======================================"
	@echo ""
	@echo "🚀 Quick Start (Automated Setup):"
	@echo "1. Ensure InvenioRDM is running: make up"
	@echo "2. Automatically configure environment: make scripts-setup-env"
	@echo "3. Build the container: make scripts-build"
	@echo "4. Test the connection: make scripts-run CMD='python -m src.tools.cli test-connection'"
	@echo "5. Stop when done: make scripts-stop"
	@echo ""
	@echo "🔧 Manual Setup (if needed):"
	@echo "1. Copy the template: cp scripts/config/.env.example scripts/config/.env"
	@echo "2. Edit scripts/config/.env with your settings"
	@echo "3. Build the container: make scripts-build"
	@echo ""
	@echo "📊 Diagnostics and Status:"
	@echo "  scripts-status    - Check system configuration and status"
	@echo "  scripts-setup-env - Regenerate configuration and API token"
	@echo ""
	@echo "📥 CSV Import:"
	@echo "  Import records from CSV file:"
	@echo "    make scripts-import-csv FILE='data/publications.csv'"
	@echo ""
	@echo "  Import with options:"
	@echo "    make scripts-import-csv FILE='data/my_records.csv' OPTS='--dry-run'"
	@echo "    make scripts-import-csv FILE='data/my_records.csv' OPTS='--skip-errors --verbose'"
	@echo ""
	@echo "🗑️  Record Management:"
	@echo "  Delete all records:"
	@echo "    make scripts-delete-all OPTS='--dry-run'  # Preview deletions"
	@echo "    make scripts-delete-all OPTS='--confirm'  # Delete without prompt"
	@echo ""
	@echo "  Reset records (delete all + import from source):"
	@echo "    make scripts-reset CSV='data/publications.csv'"
	@echo "    make scripts-reset LENS='data/publications.json'"
	@echo "    make scripts-reset ZENODO_ID='17462748'"
	@echo "    make scripts-reset ZENODO_QUERY='climate data' MAX=5"
	@echo ""
	@echo "  Reset with options:"
	@echo "    make scripts-reset CSV='data/publications.csv' OPTS='--verbose'"
	@echo "    make scripts-reset LENS='data/publications.json' OPTS='--limit 10'"
	@echo "    make scripts-reset ZENODO_ID='17462748' OPTS='--skip-files'"
	@echo ""
	@echo "📡 Import from Zenodo:"
	@echo "  Import a specific record by ID:"
	@echo "    make scripts-import-zenodo RECORD_ID='17462748'"
	@echo "    make scripts-import-zenodo RECORD_ID='17462748' OPTS='--skip-files'  # Metadata only"
	@echo "    make scripts-import-zenodo RECORD_ID='17462748' OPTS='--dry-run'     # Preview"
	@echo ""
	@echo "  Search and import multiple records:"
	@echo "    make scripts-import-zenodo QUERY='climate data' MAX=5"
	@echo "    make scripts-import-zenodo QUERY='COVID-19' MAX=3 OPTS='--skip-files'"
	@echo ""
	@echo "🔬 Import from Lens.org:"
	@echo "  Import publications from Lens.org JSON export:"
	@echo "    make scripts-import-lens FILE='src/sources/lens/data/publications.json'"
	@echo "    make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--dry-run'  # Validate only"
	@echo "    make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 10' # Import first 10"
	@echo ""
	@echo "  Advanced options:"
	@echo "    make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 20 --offset 10'  # Skip first 10"
	@echo "    make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--batch-size 5 --verbose' # Custom batch"
	@echo "    make scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--no-skip-existing'     # Reimport all"
	@echo ""
	@echo "  CSV file format (see src/sources/csv/data/publications.csv for example):"
	@echo "    Required columns: title, creators"
	@echo "    Optional: description, resource_type, publication_date, access_record,"
	@echo "              access_files, file_paths, publish, record_id (for updates)"
	@echo ""
	@echo "💡 Usage Examples:"
	@echo "  Search records:"
	@echo "    make scripts-run CMD='python -m src.tools.search -q \"climate data\" -s 5 --detailed'"
	@echo ""
	@echo "  Create a record:"
	@echo "    make scripts-run CMD='python examples/create_record.py -t \"My Dataset\" --creator \"John Doe\" --description \"Test record\"'"
	@echo ""
	@echo "  Get statistics:"
	@echo "    make scripts-run CMD='python -m src.tools.stats --record-id abcd-1234'"
	@echo ""
		@echo "  Use the CLI tool:"
	@echo "    make scripts-run CMD='python -m src.tools.cli test-connection'"
	@echo "    make scripts-run CMD='python -m src.tools.cli search -q test'"
	@echo "    make scripts-run CMD='python -m src.tools.cli get abcd-1234'"
	@echo ""
	@echo "🐚 Interactive Shell:"
	@echo "    make scripts-shell"
	@echo ""
	@echo "🔄 Regenerate Token:"
	@echo "    make scripts-setup-env"
	@echo ""
	@echo "🔧 Environment Variables (automatically configured in scripts/config/.env):"
	@echo "  INVENIO_BASE_URL - Your InvenioRDM instance URL"
	@echo "  INVENIO_TOKEN    - API Bearer token (automatically generated)"
	@echo ""
	@echo "📖 For more details, see scripts/README.md"