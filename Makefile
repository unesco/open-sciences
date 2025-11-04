# UNESCO Science Portal - InvenioRDM Makefile
# Commands for managing the InvenioRDM instance

# Default shell
SHELL := /bin/bash

# Virtual environment path
VENV_PATH = ./.venv
VENV_ACTIVATE = source $(VENV_PATH)/bin/activate

USER_PASSWORD = Passw0rd!

.PHONY: help destroy init init-custom-fields up stop stop-all build users ssl-certs check tools-build tools-up tools-stop tools-run tools-shell tools-help tools-setup-env tools-status tools-import

# Default target
help:
	@echo "UNESCO Science Portal - Available commands:"
	@echo "  init         - Initialize the project (create virtualenv and setup)"
	@echo "  init-custom-fields - Initialize custom fields in InvenioRDM database"
	@echo "  ssl-certs    - Generate SSL certificates for development"
	@echo "  users        - Create ready-to-use users with predefined passwords"
	@echo "  up           - Start the development server and services"
	@echo "  stop         - Stop all services and processes"
	@echo "  stop-all     - Force stop all services, containers and processes"
	@echo "  build        - Build assets (CSS, JS, etc.)"
	@echo "  check        - Check and fix Docker services if needed"
	@echo "  destroy      - Completely destroy the instance and virtualenv"
	@echo ""
	@echo "OpenScience Tools Commands:"
	@echo "  tools-setup-env      - Auto-setup environment with API token generation"
	@echo "  tools-status         - Check tools microservice configuration status"
	@echo "  tools-build          - Build the tools microservice container"
	@echo "  tools-up             - Start the tools microservice"
	@echo "  tools-stop           - Stop the tools microservice containers"
	@echo "  tools-run            - Run a specific script or tool"
	@echo "  tools-import-lens    - Import from Lens.org (use FILE='path/to/file.json')"
	@echo "  tools-reset          - Delete all + import from source (Lens)"
	@echo "  tools-shell          - Open an interactive shell in the tools container"
	@echo "  tools-help           - Show tools microservice help and examples"
	@echo ""
	@echo "Usage: make [command]"
	@echo "Example: make tools-run CMD='python -m src.tools.search -q test'"

# Initialize the project
init:
	@echo "🚀 Initializing UNESCO Science Portal..."
	@echo "🔍 Checking Docker environment..."
	$(MAKE) check
	@echo "📦 Creating Python virtual environment..."
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
	@echo "� Initializing custom fields..."
	$(MAKE) init-custom-fields
	@echo "�👥 Creating ready-to-use users..."
	$(MAKE) users
	@echo "✅ Initialization complete! Use 'make up' to start the server."

# Initialize custom fields in database
init-custom-fields:
	@echo "🔧 Initializing custom fields in InvenioRDM..."
	$(VENV_ACTIVATE) && invenio rdm-records custom-fields init
	@echo "✅ Custom fields initialized successfully!"

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
	@echo "📦 Stopping OpenScience Tools microservice containers..."
	-docker-compose -f docker-compose.openscience-tools.yml stop
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

# OpenScience Tools microservice targets

tools-status:
	@echo "📊 OpenScience Tools Microservice Status"
	@echo "==============================="
	@echo ""
	@echo "🔍 Checking environment configuration..."
	@if [ -f openscience-tools/config/.env ]; then \
		echo "✅ Configuration file exists: openscience-tools/config/.env"; \
		if grep -q "INVENIO_TOKEN=.*[A-Za-z0-9]" openscience-tools/config/.env 2>/dev/null; then \
			echo "✅ API token configured"; \
		else \
			echo "❌ API token not configured or empty"; \
		fi; \
		if grep -q "INVENIO_BASE_URL=https" openscience-tools/config/.env 2>/dev/null; then \
			echo "✅ HTTPS URL configured"; \
		else \
			echo "⚠️  HTTP URL configured (HTTPS recommended)"; \
		fi; \
	else \
		echo "❌ Configuration file missing: openscience-tools/config/.env"; \
		echo "   Run 'make tools-setup-env' to configure automatically"; \
	fi
	@echo ""
	@echo "🐳 Checking Docker container..."
	@if docker images sc-openscience-tools:latest --format "table {{.Repository}}" 2>/dev/null | grep -q "sc-openscience-tools"; then \
		echo "✅ Docker container built"; \
	else \
		echo "❌ Docker container not built"; \
		echo "   Run 'make tools-build' to build the container"; \
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

tools-setup-env:
	@echo "🔧 Automatic environment configuration for OpenScience Tools Microservice..."
	@echo "🔑 Generating API token and configuring .env..."
	$(VENV_ACTIVATE) && python openscience-tools/setup_env.py
	@echo "✅ Environment setup completed!"

tools-build:
	@echo "🔨 Building InvenioRDM OpenScience Tools microservice..."
	docker-compose -f docker-compose.openscience-tools.yml build openscience-tools
	@echo "✅ OpenScience Tools microservice built successfully!"

tools-up:
	@echo "🚀 Starting InvenioRDM OpenScience Tools microservice..."
	@echo "📋 Starting with interactive help..."
	docker-compose -f docker-compose.openscience-tools.yml up openscience-tools

tools-stop:
	@echo "⏹️  Stopping OpenScience Tools microservice..."
	@echo "🐳 Stopping tools containers..."
	-docker-compose -f docker-compose.openscience-tools.yml down 2>/dev/null || true
	@echo "✅ OpenScience Tools microservice stopped."

tools-run:
	@echo "🏃 Running tools command: $(CMD)"
	@if [ -z "$(CMD)" ]; then \
		echo "❌ Error: Please specify CMD='command to run'"; \
		echo "Example: make tools-run CMD='python -m src.tools.search -q test'"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.openscience-tools.yml run --rm openscience-tools-cli $(CMD)

tools-shell:
	@echo "🐚 Opening interactive shell in tools container..."
	docker-compose -f docker-compose.openscience-tools.yml run --rm openscience-tools-cli /bin/bash

tools-delete-all:
	@echo "🗑️  Deleting all records from InvenioRDM..."
	@if [ -n "$(OPTS)" ]; then \
		docker-compose -f docker-compose.openscience-tools.yml run --rm openscience-tools-cli python -m src.tools.cleanup $(OPTS); \
	else \
		docker-compose -f docker-compose.openscience-tools.yml run --rm openscience-tools-cli python -m src.tools.cleanup; \
	fi

tools-reset:
	@echo "🔄 Resetting InvenioRDM records..."
	@if [ -z "$(LENS)" ]; then \
		echo "❌ Error: Source parameter required"; \
		echo "Usage:"; \
		echo "  Lens:   make tools-reset LENS='data/publications.json'"; \
		echo ""; \
		echo "With options:"; \
		echo "  make tools-reset LENS='data/publications.json' OPTS='--limit 10'"; \
		exit 1; \
	fi
	@echo ""
	@echo "📋 Step 1/2: Deleting all existing records..."
	@docker-compose -f docker-compose.openscience-tools.yml run --rm openscience-tools-cli python -m src.tools.cleanup --confirm
	@echo ""
	@echo "📋 Step 2/2: Importing fresh records..."
	@if [ -n "$(LENS)" ]; then \
		echo "🔬 Importing from Lens: $(LENS)"; \
		CMD="python -m src.sources.lens --file $(LENS)"; \
		if [ -n "$(OPTS)" ]; then \
			CMD="$$CMD $(OPTS)"; \
		fi; \
		docker-compose -f docker-compose.openscience-tools.yml run --rm openscience-tools-cli $$CMD; \
	fi
	@echo ""
	@echo "✅ Reset complete!"

tools-import-lens:
	@echo "🔬 Importing from Lens.org..."
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: FILE parameter required"; \
		echo "Usage:"; \
		echo "  make tools-import-lens FILE='src/sources/lens/data/publications.json'"; \
		echo "  make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--dry-run'"; \
		echo "  make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 10 --verbose'"; \
		exit 1; \
	fi
	@CMD="python -m src.sources.lens --file $(FILE:src/%=/project/%)"; \
	if [ -n "$(OPTS)" ]; then \
		CMD="$$CMD $(OPTS)"; \
	fi; \
	docker-compose -f docker-compose.openscience-tools.yml run --rm openscience-tools-cli $$CMD

tools-help:
	@echo "📚 InvenioRDM OpenScience Tools Microservice Help"
	@echo "======================================"
	@echo ""
	@echo "🚀 Quick Start (Automated Setup):"
	@echo "1. Ensure InvenioRDM is running: make up"
	@echo "2. Automatically configure environment: make tools-setup-env"
	@echo "3. Build the container: make tools-build"
	@echo "4. Test the connection: make tools-run CMD='python -m src.tools.cli test-connection'"
	@echo "5. Stop when done: make tools-stop"
	@echo ""
	@echo "🔧 Manual Setup (if needed):"
	@echo "1. Copy the template: cp openscience-tools/config/.env.example openscience-tools/config/.env"
	@echo "2. Edit openscience-tools/config/.env with your settings"
	@echo "3. Build the container: make tools-build"
	@echo ""
	@echo "📊 Diagnostics and Status:"
	@echo "  tools-status    - Check system configuration and status"
	@echo "  tools-setup-env - Regenerate configuration and API token"
	@echo ""
	@echo "🗑️  Record Management:"
	@echo "  Delete all records:"
	@echo "    make tools-delete-all OPTS='--dry-run'  # Preview deletions"
	@echo "    make tools-delete-all OPTS='--confirm'  # Delete without prompt"
	@echo ""
	@echo "  Reset records (delete all + import from source):"
	@echo "    make tools-reset LENS='data/publications.json'"
	@echo ""
	@echo "  Reset with options:"
	@echo "    make tools-reset LENS='data/publications.json' OPTS='--limit 10'"
	@echo ""
	@echo "🔬 Import from Lens.org:"
	@echo "  Import publications from Lens.org JSON export:"
	@echo "    make tools-import-lens FILE='src/sources/lens/data/publications.json'"
	@echo "    make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--dry-run'  # Validate only"
	@echo "    make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 10' # Import first 10"
	@echo ""
	@echo "  Advanced options:"
	@echo "    make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 20 --offset 10'  # Skip first 10"
	@echo "    make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--batch-size 5 --verbose' # Custom batch"
	@echo "    make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--no-skip-existing'     # Reimport all"
	@echo ""
	@echo ""
		@echo "  Use the CLI tool:"
	@echo "    make tools-run CMD='python -m src.tools.cli test-connection'"
	@echo "    make tools-run CMD='python -m src.tools.cli search -q test'"
	@echo "    make tools-run CMD='python -m src.tools.cli get abcd-1234'"
	@echo ""
	@echo "🐚 Interactive Shell:"
	@echo "    make tools-shell"
	@echo ""
	@echo "🔄 Regenerate Token:"
	@echo "    make tools-setup-env"
	@echo ""
	@echo "🔧 Environment Variables (automatically configured in openscience-tools/config/.env):"
	@echo "  INVENIO_BASE_URL - Your InvenioRDM instance URL"
	@echo "  INVENIO_TOKEN    - API Bearer token (automatically generated)"
	@echo ""
	@echo "📖 For more details, see openscience-tools/README.md"
