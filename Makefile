# UNESCO Science Portal - InvenioRDM Makefile
# Commands for managing the InvenioRDM instance

# Default shell
SHELL := /bin/bash

# Virtual environment path
VENV_PATH = ./.venv
VENV_ACTIVATE = source $(VENV_PATH)/bin/activate

USER_PASSWORD = Passw0rd!

.PHONY: help destroy init up stop build users ssl-certs

# Default target
help:
	@echo "UNESCO Science Portal - Available commands:"
	@echo "  init     - Initialize the project (create virtualenv and setup)"
	@echo "  ssl-certs- Generate SSL certificates for development"
	@echo "  users    - Create ready-to-use users with predefined passwords"
	@echo "  up       - Start the development server and services"
	@echo "  stop     - Stop all services and the development server"
	@echo "  build    - Build assets (CSS, JS, etc.)"
	@echo "  destroy  - Completely destroy the instance and virtualenv"
	@echo ""
	@echo "Usage: make [command]"

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