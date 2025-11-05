# UNESCO Science Portal - InvenioRDM Makefile
# Commands for managing the InvenioRDM instance

# Default shell
SHELL := /bin/bash

# Virtual environment path
VENV_PATH = ./.venv
VENV_ACTIVATE = source $(VENV_PATH)/bin/activate

USER_PASSWORD = Passw0rd!

.PHONY: help destroy init init-custom-fields up stop build users ssl-certs check config tools-build tools-up tools-stop tools-run tools-shell tools-help tools-setup-env tools-status tools-import

# Default target
help:
	@echo "UNESCO Science Portal - Available commands:"
	@echo "  init         - Initialize the project (config, virtualenv, services)"
	@echo "  config       - Generate .env and invenio.cfg from templates"
	@echo "  init-custom-fields - Initialize custom fields in InvenioRDM database"
	@echo "  ssl-certs    - Generate SSL certificates for development"
	@echo "  users        - Create ready-to-use users with predefined passwords"
	@echo "  up           - Start the development server and services"
	@echo "  stop         - Stop all services and processes"
	@echo "  build        - Build assets (CSS, JS, etc.)"
	@echo "  check        - Check and fix Docker services if needed"
	@echo "  destroy      - Completely destroy the instance and virtualenv"
	@echo ""
	@echo "OpenScience Tools Commands:"
	@echo "  tools-install        - Install openscience-tools package"
	@echo "  tools-setup-env      - Setup environment variables for tools"
	@echo "  tools-search         - Search records (use QUERY='search term')"
	@echo "  tools-view           - View record details (use RECORD_ID='abc-123')"
	@echo "  tools-cleanup        - Delete all records"
	@echo "  tools-import-lens    - Import from Lens.org (use FILE='path/to/file.json')"
	@echo "  tools-reset          - Delete all + import from Lens (use FILE='path/to/file.json')"
	@echo "  tools-help           - Show tools help and examples"
	@echo ""
	@echo "Usage: make [command]"
	@echo "Example: make tools-search QUERY='climate data'"

# Initialize the project
init:
	@echo "🚀 Initializing UNESCO Science Portal..."
	@echo "⚙️  Generating configuration files..."
	$(MAKE) config
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
	@echo "📋 Initializing custom fields..."
	$(MAKE) init-custom-fields
	@echo "👥 Creating ready-to-use users..."
	$(MAKE) users
	@echo "🔧 Installing openscience-tools package..."
	$(MAKE) tools-install
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
	@echo "✅ All services stopped."

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

# Generate configuration files (.env and invenio.cfg) from templates
config:
	@echo "⚙️  Generating configuration files from templates..."
	@if [ ! -f .env.example ]; then \
		echo "❌ .env.example file not found."; \
		exit 1; \
	fi
	@if [ ! -f invenio.cfg.template ]; then \
		echo "❌ invenio.cfg.template not found."; \
		exit 1; \
	fi
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "✅ .env created successfully!"; \
	else \
		echo "ℹ️  .env already exists, skipping creation."; \
	fi
	@echo "📝 Loading environment variables and generating invenio.cfg..."
	@while IFS='=' read -r key value; do \
		if [ -n "$$key" ] && [ "$${key:0:1}" != "#" ]; then \
			export "$$key=$$value"; \
		fi; \
	done < .env && \
	envsubst < invenio.cfg.template > invenio.cfg
	@echo "✅ invenio.cfg generated successfully!"
	@echo "⚠️  Remember: Both .env and invenio.cfg are gitignored. Do not commit sensitive data!"

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
	-$(MAKE) stop
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

# OpenScience Tools package targets

tools-install:
	@echo "� Installing openscience-tools package..."
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "❌ Virtual environment not found. Run 'make init' first."; \
		exit 1; \
	fi
	$(VENV_ACTIVATE) && cd openscience-tools && pip install -e .
	@echo "✅ openscience-tools installed successfully!"

tools-setup-env:
	@echo "🔧 Setting up environment variables for OpenScience Tools..."
	@echo "🔑 Generating API token..."
	$(VENV_ACTIVATE) && python openscience-tools/setup_env.py
	@echo ""
	@echo "✅ Environment setup completed!"
	@echo "💡 Credentials stored in .env file"
	@echo "   OPENSCIENCE_TOOLS_BASE_URL and OPENSCIENCE_TOOLS_TOKEN"

tools-search:
	@echo "🔍 Searching InvenioRDM records..."
	@if [ -z "$(QUERY)" ]; then \
		QUERY=""; \
	fi; \
	if [ -f .env ]; then \
		BASE_URL=$${BASE_URL:-$$(grep OPENSCIENCE_TOOLS_BASE_URL .env | cut -d= -f2)}; \
		TOKEN=$${TOKEN:-$$(grep OPENSCIENCE_TOOLS_TOKEN .env | cut -d= -f2)}; \
		if [ -z "$$TOKEN" ] || [ "$$TOKEN" = "your_generated_token_here" ]; then \
			echo "❌ Token not configured. Run 'make tools-setup-env' first."; \
			exit 1; \
		fi; \
		$(VENV_ACTIVATE) && openscience-tools --base-url "$$BASE_URL" --token "$$TOKEN" search -q "$$QUERY" $(OPTS); \
	else \
		echo "❌ .env file not found. Run 'make config' first."; \
		exit 1; \
	fi

tools-view:
	@echo "👁️  Viewing record details..."
	@if [ -z "$(RECORD_ID)" ]; then \
		echo "❌ Error: RECORD_ID parameter required"; \
		echo "Usage: make tools-view RECORD_ID='abc-123'"; \
		exit 1; \
	fi; \
	if [ -f .env ]; then \
		BASE_URL=$${BASE_URL:-$$(grep OPENSCIENCE_TOOLS_BASE_URL .env | cut -d= -f2)}; \
		TOKEN=$${TOKEN:-$$(grep OPENSCIENCE_TOOLS_TOKEN .env | cut -d= -f2)}; \
		if [ -z "$$TOKEN" ] || [ "$$TOKEN" = "your_generated_token_here" ]; then \
			echo "❌ Token not configured. Run 'make tools-setup-env' first."; \
			exit 1; \
		fi; \
		$(VENV_ACTIVATE) && openscience-tools --base-url "$$BASE_URL" --token "$$TOKEN" view $(RECORD_ID) $(OPTS); \
	else \
		echo "❌ .env file not found. Run 'make config' first."; \
		exit 1; \
	fi

tools-cleanup:
	@echo "🗑️  Deleting all records from InvenioRDM..."
	@if [ -f .env ]; then \
		BASE_URL=$${BASE_URL:-$$(grep OPENSCIENCE_TOOLS_BASE_URL .env | cut -d= -f2)}; \
		TOKEN=$${TOKEN:-$$(grep OPENSCIENCE_TOOLS_TOKEN .env | cut -d= -f2)}; \
		if [ -z "$$TOKEN" ] || [ "$$TOKEN" = "your_generated_token_here" ]; then \
			echo "❌ Token not configured. Run 'make tools-setup-env' first."; \
			exit 1; \
		fi; \
		$(VENV_ACTIVATE) && openscience-tools --base-url "$$BASE_URL" --token "$$TOKEN" cleanup $(OPTS); \
	else \
		echo "❌ .env file not found. Run 'make config' first."; \
		exit 1; \
	fi

tools-import-lens:
	@echo "🔬 Importing from Lens.org..."
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: FILE parameter required"; \
		echo "Usage:"; \
		echo "  make tools-import-lens FILE='path/to/publications.json'"; \
		echo "  make tools-import-lens FILE='path/to/publications.json' OPTS='--dry-run'"; \
		echo "  make tools-import-lens FILE='path/to/publications.json' OPTS='--limit 10'"; \
		exit 1; \
	fi; \
	if [ -f .env ]; then \
		BASE_URL=$${BASE_URL:-$$(grep OPENSCIENCE_TOOLS_BASE_URL .env | cut -d= -f2)}; \
		TOKEN=$${TOKEN:-$$(grep OPENSCIENCE_TOOLS_TOKEN .env | cut -d= -f2)}; \
		if [ -z "$$TOKEN" ] || [ "$$TOKEN" = "your_generated_token_here" ]; then \
			echo "❌ Token not configured. Run 'make tools-setup-env' first."; \
			exit 1; \
		fi; \
		$(VENV_ACTIVATE) && openscience-tools --base-url "$$BASE_URL" --token "$$TOKEN" import-lens --file $(FILE) $(OPTS); \
	else \
		echo "❌ .env file not found. Run 'make config' first."; \
		exit 1; \
	fi

tools-reset:
	@echo "🔄 Resetting InvenioRDM records (delete all + import from Lens)..."
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: FILE parameter required"; \
		echo "Usage:"; \
		echo "  make tools-reset FILE='path/to/publications.json'"; \
		echo "  make tools-reset FILE='path/to/publications.json' OPTS='--limit 10'"; \
		echo "  make tools-reset FILE='path/to/publications.json' BASE_URL='https://...' TOKEN='...'"; \
		exit 1; \
	fi
	@if [ -f .env ]; then \
		BASE_URL=$${BASE_URL:-$$(grep OPENSCIENCE_TOOLS_BASE_URL .env | cut -d= -f2)}; \
		TOKEN=$${TOKEN:-$$(grep OPENSCIENCE_TOOLS_TOKEN .env | cut -d= -f2)}; \
		if [ -z "$$TOKEN" ] || [ "$$TOKEN" = "your_generated_token_here" ]; then \
			echo "❌ Token not configured. Run 'make tools-setup-env' first."; \
			exit 1; \
		fi; \
		echo ""; \
		echo "📋 Step 1/2: Deleting all existing records..."; \
		$(VENV_ACTIVATE) && openscience-tools --base-url "$$BASE_URL" --token "$$TOKEN" cleanup --confirm; \
		echo ""; \
		echo "📋 Step 2/2: Importing fresh records from Lens..."; \
		$(VENV_ACTIVATE) && openscience-tools --base-url "$$BASE_URL" --token "$$TOKEN" import-lens --file $(FILE) $(OPTS); \
		echo ""; \
		echo "✅ Reset complete!"; \
	else \
		echo "❌ .env file not found. Run 'make config' first."; \
		exit 1; \
	fi

tools-help:
	@echo "📚 OpenScience Tools - Usage Guide"
	@echo "======================================"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "1. Ensure InvenioRDM is running: make up"
	@echo "2. Install the package: make tools-install"
	@echo "3. Setup environment: make tools-setup-env"
	@echo "4. Use the tools: make tools-search QUERY='test'"
	@echo ""
	@echo "� Search Records:"
	@echo "  make tools-search QUERY='climate data'"
	@echo "  make tools-search QUERY='test' OPTS='--detailed'"
	@echo "  make tools-search OPTS='--size 20 --page 2'"
	@echo ""
	@echo "�️  View Record Details:"
	@echo "  make tools-view RECORD_ID='abc-123'"
	@echo "  make tools-view RECORD_ID='abc-123' OPTS='--format json'"
	@echo ""
	@echo "🗑️  Delete All Records:"
	@echo "  make tools-cleanup OPTS='--dry-run'   # Preview deletions"
	@echo "  make tools-cleanup OPTS='--confirm'   # Delete all"
	@echo ""
	@echo "🔬 Import from Lens.org:"
	@echo "  make tools-import-lens FILE='data/publications.json'"
	@echo "  make tools-import-lens FILE='data/publications.json' OPTS='--dry-run'"
	@echo "  make tools-import-lens FILE='data/publications.json' OPTS='--limit 10'"
	@echo "  make tools-import-lens FILE='data/publications.json' OPTS='--offset 10 --limit 20'"
	@echo ""
	@echo "� Reset (Delete All + Import from Lens):"
	@echo "  make tools-reset FILE='data/publications.json'"
	@echo "  make tools-reset FILE='data/publications.json' OPTS='--limit 10'"
	@echo ""
	@echo " Override Credentials (optional):"
	@echo "  make tools-search QUERY='test' BASE_URL='https://...' TOKEN='...'"
	@echo "  make tools-reset FILE='data.json' BASE_URL='https://...' TOKEN='...'"
	@echo ""
	@echo "💻 Direct CLI Usage:"
	@echo "  $(VENV_ACTIVATE) && openscience-tools --base-url \$$(grep OPENSCIENCE_TOOLS_BASE_URL .env | cut -d= -f2) --token \$$(grep OPENSCIENCE_TOOLS_TOKEN .env | cut -d= -f2) search -q test"
	@echo ""
	@echo "🔄 Regenerate API Token:"
	@echo "  make tools-setup-env"
	@echo ""
	@echo "📖 For more details, see openscience-tools/README.md"
