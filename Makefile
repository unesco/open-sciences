# UNESCO Science Portal - InvenioRDM Makefile
# Commands for managing the InvenioRDM instance

# Default shell
SHELL := /bin/bash

# Virtual environment path
VENV_PATH = ./.venv
VENV_ACTIVATE = source $(VENV_PATH)/bin/activate

USER_PASSWORD = Passw0rd!

.PHONY: help destroy init up stop build users ssl-certs scripts-build scripts-up scripts-stop scripts-run scripts-shell scripts-help scripts-setup-env scripts-status

# Default target
help:
	@echo "UNESCO Science Portal - Available commands:"
	@echo "  init         - Initialize the project (create virtualenv and setup)"
	@echo "  ssl-certs    - Generate SSL certificates for development"
	@echo "  users        - Create ready-to-use users with predefined passwords"
	@echo "  up           - Start the development server and services"
	@echo "  stop         - Stop all services and processes"
	@echo "  build        - Build assets (CSS, JS, etc.)"
	@echo "  destroy      - Completely destroy the instance and virtualenv"
	@echo ""
	@echo "Scripts Microservice Commands:"
	@echo "  scripts-setup-env - Auto-setup environment with API token generation"
	@echo "  scripts-status    - Check scripts microservice configuration status"
	@echo "  scripts-build     - Build the scripts microservice container"
	@echo "  scripts-up        - Start the scripts microservice"
	@echo "  scripts-stop      - Stop the scripts microservice containers"
	@echo "  scripts-run       - Run a specific script (use CMD='python examples/...')"
	@echo "  scripts-shell     - Open an interactive shell in the scripts container"
	@echo "  scripts-help      - Show scripts microservice help and examples"
	@echo ""
	@echo "Usage: make [command]"
	@echo "Example: make scripts-run CMD='python examples/search_records.py -q test'"

# Initialize the project
init:
	@echo "🚀 Initializing UNESCO Science Portal..."
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
	@echo "� Setting up SSL certificates..."
	$(MAKE) ssl-certs
	@echo "�👥 Creating ready-to-use users..."
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
	@echo "🐳 Destroying containerized services..."
	-$(VENV_ACTIVATE) && invenio-cli services destroy
	@echo "🧹 Performing global cleanup..."
	-$(VENV_ACTIVATE) && invenio-cli destroy
	@echo "🗑️  Removing virtual environment..."
	rm -rf $(VENV_PATH)
	@echo "🔐 Removing SSL certificates..."
	rm -f docker/nginx/test.crt docker/nginx/test.key
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
		echo "Example: make scripts-run CMD='python examples/search_records.py -q test'"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.scripts.yml run --rm scripts-cli $(CMD)

scripts-shell:
	@echo "🐚 Opening interactive shell in scripts container..."
	docker-compose -f docker-compose.scripts.yml run --rm scripts-cli /bin/bash

scripts-help:
	@echo "📚 InvenioRDM Scripts Microservice Help"
	@echo "======================================"
	@echo ""
	@echo "🚀 Quick Start (Automated Setup):"
	@echo "1. Ensure InvenioRDM is running: make up"
	@echo "2. Automatically configure environment: make scripts-setup-env"
	@echo "3. Build the container: make scripts-build"
	@echo "4. Test the connection: make scripts-run CMD='python examples/invenio_cli.py test-connection'"
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
	@echo " Usage Examples:"
	@echo "  Search records:"
	@echo "    make scripts-run CMD='python examples/search_records.py -q \"climate data\" -s 5 --detailed'"
	@echo ""
	@echo "  Create a record:"
	@echo "    make scripts-run CMD='python examples/create_record.py -t \"My Dataset\" --creator \"John Doe\" --description \"Test record\"'"
	@echo ""
	@echo "  Get statistics:"
	@echo "    make scripts-run CMD='python examples/get_statistics.py --record-id abcd-1234'"
	@echo ""
	@echo "  Use the unified CLI:"
	@echo "    make scripts-run CMD='python examples/invenio_cli.py test-connection'"
	@echo "    make scripts-run CMD='python examples/invenio_cli.py search -q test'"
	@echo "    make scripts-run CMD='python examples/invenio_cli.py get abcd-1234'"
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