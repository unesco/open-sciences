#
# ============================================================================
# UNESCO Open Science Portal - k3s Production Deployment
# ============================================================================
#
# Usage:
#   make deploy          # Full first-time deployment
#   make upgrade         # Upgrade after code changes
#   make status          # Check cluster health
#   make backup          # Manual database backup
#   make restore FILE=.. # Restore from backup
#
# See 'make help' for all available targets.
# ============================================================================

SHELL := /bin/bash

.PHONY: help check env-check deploy deploy-services deploy-secrets deploy-helm \
        init create-admin upgrade status logs shell restart backup restore \
        tls-setup backup-schedule destroy port-forward helm-versions

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# Load .env if it exists
-include .env
export

NAMESPACE         ?= unesco-rdm
HELM_RELEASE      ?= unesco-rdm
HELM_INVENIO_VER  ?= 0.8.1
VALUES_FILE       ?= values.yaml
KUBECONFIG        ?= /etc/rancher/k3s/k3s.yaml

# Docker image (built from repo root)
DOCKER_REGISTRY   ?= registry.example.org/sc/sc-openscience
DOCKER_IMAGE_TAG  ?= latest
IMAGE             := $(DOCKER_REGISTRY):$(DOCKER_IMAGE_TAG)

# Backup
BACKUP_DIR        ?= /opt/backups/unesco-rdm

# --------------------------------------------------------------------------
# Help
# --------------------------------------------------------------------------

help: ## Show this help
	@echo ""
	@echo "UNESCO Open Science Portal - k3s Deployment"
	@echo "============================================"
	@echo ""
	@echo "First-time setup:"
	@echo "  make deploy            Full deployment (services + helm + init)"
	@echo ""
	@echo "Daily operations:"
	@echo "  make status            Cluster & pod health"
	@echo "  make logs              Tail web pod logs"
	@echo "  make logs-worker       Tail worker pod logs"
	@echo "  make shell             Shell into web pod"
	@echo "  make restart           Rolling restart of InvenioRDM"
	@echo ""
	@echo "Updates:"
	@echo "  make upgrade           Upgrade InvenioRDM (rebuild image + helm)"
	@echo "  make deploy-helm       Re-deploy Helm chart only"
	@echo "  make build-image       Build Docker image on server"
	@echo ""
	@echo "Backup & Restore:"
	@echo "  make backup            Manual database backup"
	@echo "  make restore FILE=...  Restore from backup file"
	@echo "  make backup-schedule   Install automated daily backups"
	@echo "  make backup-list       List available backups"
	@echo ""
	@echo "TLS & Security:"
	@echo "  make tls-setup         Install cert-manager + Let's Encrypt"
	@echo "  make tls-status        Check certificate status"
	@echo ""
	@echo "Cleanup:"
	@echo "  make destroy           Remove everything (DESTRUCTIVE)"
	@echo ""

# --------------------------------------------------------------------------
# Pre-flight checks
# --------------------------------------------------------------------------

check: ## Verify k3s, kubectl, helm are installed
	@echo "Checking required tools..."
	@command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl not found. Install k3s first: make install-k3s"; exit 1; }
	@command -v helm    >/dev/null 2>&1 || { echo "ERROR: helm not found. Run: make install-k3s"; exit 1; }
	@kubectl get nodes  >/dev/null 2>&1 || { echo "ERROR: Cannot reach k3s cluster. Is k3s running?"; exit 1; }
	@echo "  kubectl: OK"
	@echo "  helm:    OK"
	@echo "  k3s:     $$(kubectl get nodes -o jsonpath='{.items[0].status.nodeInfo.kubeletVersion}')"
	@echo "All checks passed."

env-check: ## Verify .env file exists and has required values
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found!"; \
		echo "  cp .env.example .env"; \
		echo "  Then edit .env with your values."; \
		exit 1; \
	fi
	@echo "Checking required .env variables..."
	@missing=0; \
	for var in DOMAIN SECRET_KEY SECURITY_LOGIN_SALT POSTGRES_PASSWORD RABBITMQ_PASSWORD; do \
		val=$$(grep "^$$var=" .env | cut -d= -f2-); \
		if [ -z "$$val" ] || echo "$$val" | grep -q "CHANGE_ME"; then \
			echo "  MISSING: $$var"; \
			missing=1; \
		fi; \
	done; \
	if [ $$missing -eq 1 ]; then \
		echo ""; \
		echo "ERROR: Some required variables are not set in .env"; \
		echo "  Generate secrets with: openssl rand -hex 32"; \
		exit 1; \
	fi
	@echo "All required variables are set."

# --------------------------------------------------------------------------
# Installation
# --------------------------------------------------------------------------

install-k3s: ## Install k3s on this server
	@echo "Running k3s installation script..."
	@chmod +x scripts/install-k3s.sh
	@sudo scripts/install-k3s.sh

# --------------------------------------------------------------------------
# Full Deployment
# --------------------------------------------------------------------------

deploy: check env-check deploy-services deploy-secrets deploy-helm init create-admin ## Full first-time deployment
	@echo ""
	@echo "============================================"
	@echo "  Deployment complete!"
	@echo "============================================"
	@echo ""
	@echo "  Domain:  $(DOMAIN)"
	@echo "  Admin:   $(ADMIN_USER_EMAIL)"
	@echo ""
	@echo "  Next steps:"
	@echo "    1. Set up TLS:  make tls-setup"
	@echo "    2. Set up backups: make backup-schedule"
	@echo "    3. Check status:   make status"
	@echo ""
	@echo "  Access (no TLS yet): http://$(DOMAIN)"
	@echo ""

# --------------------------------------------------------------------------
# Services (PostgreSQL, Redis, RabbitMQ, OpenSearch)
# --------------------------------------------------------------------------

deploy-services: check ## Deploy external services (DB, cache, search, queue)
	@echo "Deploying external services..."
	@kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@kubectl config set-context --current --namespace=$(NAMESPACE)
	@echo ""
	@echo "Creating service secrets..."
	@kubectl create secret generic $(HELM_RELEASE)-db-secrets \
		--from-literal=POSTGRES_USER=$(POSTGRES_USER) \
		--from-literal=POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		--from-literal=POSTGRES_DB=$(POSTGRES_DB) \
		--namespace=$(NAMESPACE) \
		--dry-run=client -o yaml | kubectl apply -f -
	@kubectl create secret generic $(HELM_RELEASE)-mq-secrets \
		--from-literal=RABBITMQ_DEFAULT_USER=$(RABBITMQ_USER) \
		--from-literal=RABBITMQ_DEFAULT_PASS=$(RABBITMQ_PASSWORD) \
		--namespace=$(NAMESPACE) \
		--dry-run=client -o yaml | kubectl apply -f -
	@echo ""
	@echo "Applying external-services.yaml..."
	@kubectl apply -f external-services.yaml -n $(NAMESPACE)
	@echo ""
	@echo "Waiting for services to be ready (up to 3 minutes)..."
	@kubectl wait --for=condition=ready pod -l app=redis        -n $(NAMESPACE) --timeout=180s 2>/dev/null || echo "  WARN: Redis not ready yet"
	@kubectl wait --for=condition=ready pod -l app=postgresql    -n $(NAMESPACE) --timeout=180s 2>/dev/null || echo "  WARN: PostgreSQL not ready yet"
	@kubectl wait --for=condition=ready pod -l app=rabbitmq      -n $(NAMESPACE) --timeout=180s 2>/dev/null || echo "  WARN: RabbitMQ not ready yet"
	@kubectl wait --for=condition=ready pod -l app=opensearch    -n $(NAMESPACE) --timeout=180s 2>/dev/null || echo "  WARN: OpenSearch not ready yet"
	@echo ""
	@echo "External services deployed."
	@kubectl get pods -n $(NAMESPACE)

# --------------------------------------------------------------------------
# Secrets
# --------------------------------------------------------------------------

deploy-secrets: check env-check ## Create K8s secrets from .env
	@echo "Creating InvenioRDM secrets..."
	@kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@kubectl create secret generic $(HELM_RELEASE)-secrets \
		--from-literal=SECRET_KEY=$(SECRET_KEY) \
		--from-literal=SECURITY_LOGIN_SALT=$(SECURITY_LOGIN_SALT) \
		--from-literal=SQLALCHEMY_DATABASE_URI="postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgresql:5432/$(POSTGRES_DB)" \
		--from-literal=CELERY_BROKER_URL="amqp://$(RABBITMQ_USER):$(RABBITMQ_PASSWORD)@rabbitmq:5672/" \
		--from-literal=CACHE_REDIS_URL="redis://redis:6379/0" \
		--namespace=$(NAMESPACE) \
		--dry-run=client -o yaml | kubectl apply -f -
	@echo "Secrets created."
	@echo ""
	@# Create registry pull secret if credentials are provided
	@if [ -n "$(REGISTRY_USER)" ] && [ -n "$(REGISTRY_PASSWORD)" ]; then \
		echo "Creating image pull secret..."; \
		kubectl create secret docker-registry regcred \
			--docker-server=$(DOCKER_REGISTRY) \
			--docker-username=$(REGISTRY_USER) \
			--docker-password=$(REGISTRY_PASSWORD) \
			--namespace=$(NAMESPACE) \
			--dry-run=client -o yaml | kubectl apply -f -; \
		echo "Pull secret created."; \
	fi

# --------------------------------------------------------------------------
# Helm
# --------------------------------------------------------------------------

deploy-helm: check ## Install/upgrade InvenioRDM Helm chart
	@echo "Setting up Helm repositories..."
	@helm repo add invenio https://inveniosoftware.github.io/helm-invenio/ 2>/dev/null || true
	@helm repo update
	@echo ""
	@echo "Generating Helm values..."
	@# Substitute .env variables into values.yaml
	@envsubst < $(VALUES_FILE) > /tmp/values-rendered.yaml
	@echo ""
	@echo "Deploying InvenioRDM (chart v$(HELM_INVENIO_VER))..."
	helm upgrade --install $(HELM_RELEASE) invenio/invenio \
		--version $(HELM_INVENIO_VER) \
		--namespace $(NAMESPACE) \
		--create-namespace \
		--values /tmp/values-rendered.yaml \
		--wait \
		--timeout 10m
	@rm -f /tmp/values-rendered.yaml
	@echo ""
	@echo "Helm chart deployed."

helm-versions: ## List available Helm chart versions
	@helm repo add invenio https://inveniosoftware.github.io/helm-invenio/ 2>/dev/null || true
	@helm search repo invenio/invenio --versions | head -15

# --------------------------------------------------------------------------
# Initialization
# --------------------------------------------------------------------------

init: check ## Initialize database, indices, vocabularies
	@echo "Waiting for web pod..."
	@kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=web \
		-n $(NAMESPACE) --timeout=300s 2>/dev/null || \
		{ echo "ERROR: Web pod not ready. Check: make status"; exit 1; }
	@echo ""
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	echo "Initializing database..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio db init 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio db create 2>/dev/null || true" ; \
	echo ""; \
	echo "Initializing search indices..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index destroy --force --yes-i-know 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index init 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index queue init purge 2>/dev/null || true" ; \
	echo ""; \
	echo "Initializing custom fields..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio rdm-records custom-fields init 2>/dev/null || true" ; \
	echo ""; \
	echo "Creating file storage location..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio files location create --default 'default-location' /opt/invenio/var/instance/data 2>/dev/null || true" ; \
	echo ""; \
	echo "Loading vocabularies and fixtures..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio rdm-records fixtures 2>/dev/null || true" ; \
	echo "Waiting for vocabularies to be processed (30s)..."; \
	sleep 30; \
	echo ""; \
	echo "Initialization complete."

create-admin: check ## Create admin user
	@echo "Creating admin user..."
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c \
		"invenio users create $(ADMIN_USER_EMAIL) --password='$(ADMIN_USER_PASSWORD)' --active --confirm 2>/dev/null || echo 'User may already exist'" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c \
		"invenio roles add $(ADMIN_USER_EMAIL) admin 2>/dev/null || echo 'Role may already be assigned'" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c \
		"invenio access allow superuser-access role admin 2>/dev/null || echo 'Permission may already exist'" ; \
	echo ""; \
	echo "Admin user created: $(ADMIN_USER_EMAIL)"

# --------------------------------------------------------------------------
# Build & Upgrade
# --------------------------------------------------------------------------

build-image: ## Build Docker image on the server
	@echo "Building Docker image..."
	@echo "  Image: $(IMAGE)"
	@echo "  Dockerfile: ../Dockerfile"
	@cd .. && docker build -t $(IMAGE) -f Dockerfile .
	@echo ""
	@echo "Image built: $(IMAGE)"
	@echo "  To push: docker push $(IMAGE)"

push-image: build-image ## Build and push Docker image
	@echo "Pushing image to registry..."
	docker push $(IMAGE)
	@echo "Image pushed: $(IMAGE)"

upgrade: check env-check ## Upgrade InvenioRDM (pull new image + helm upgrade)
	@echo "Upgrading InvenioRDM..."
	@echo ""
	@echo "Step 1/3: Backing up database..."
	@$(MAKE) backup || echo "WARN: Backup failed - continuing with upgrade"
	@echo ""
	@echo "Step 2/3: Upgrading Helm release..."
	@$(MAKE) deploy-helm
	@echo ""
	@echo "Step 3/3: Restarting pods to pick up new image..."
	@$(MAKE) restart
	@echo ""
	@echo "Upgrade complete. Check: make status"

# --------------------------------------------------------------------------
# Operations
# --------------------------------------------------------------------------

status: check ## Show cluster and pod status
	@echo "=== Nodes ==="
	@kubectl get nodes -o wide
	@echo ""
	@echo "=== Pods ($(NAMESPACE)) ==="
	@kubectl get pods -n $(NAMESPACE) -o wide
	@echo ""
	@echo "=== Services ==="
	@kubectl get svc -n $(NAMESPACE)
	@echo ""
	@echo "=== Ingress ==="
	@kubectl get ingress -n $(NAMESPACE)
	@echo ""
	@echo "=== PVCs ==="
	@kubectl get pvc -n $(NAMESPACE)
	@echo ""
	@echo "=== Resource Usage ==="
	@kubectl top pods -n $(NAMESPACE) 2>/dev/null || echo "(metrics-server not available)"

logs: check ## Tail web pod logs
	@echo "Tailing web pod logs (Ctrl+C to stop)..."
	@kubectl logs -f -l app.kubernetes.io/component=web -n $(NAMESPACE) --all-containers=true --tail=100

logs-worker: check ## Tail worker pod logs
	@echo "Tailing worker pod logs (Ctrl+C to stop)..."
	@kubectl logs -f -l app.kubernetes.io/component=worker -n $(NAMESPACE) --all-containers=true --tail=100

logs-services: check ## Tail external service logs
	@echo "Which service? [postgresql/redis/rabbitmq/opensearch]"
	@read svc; kubectl logs -f -l app=$$svc -n $(NAMESPACE) --tail=100

shell: check ## Open a shell in the web pod
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	echo "Opening shell in $$WEB_POD..."; \
	kubectl exec -it -n $(NAMESPACE) $$WEB_POD -c web -- bash

restart: check ## Rolling restart of InvenioRDM (keeps services running)
	@echo "Restarting InvenioRDM pods..."
	@kubectl rollout restart deployment -l app.kubernetes.io/component=web          -n $(NAMESPACE) 2>/dev/null || true
	@kubectl rollout restart deployment -l app.kubernetes.io/component=worker       -n $(NAMESPACE) 2>/dev/null || true
	@kubectl rollout restart deployment -l app.kubernetes.io/component=worker-beat  -n $(NAMESPACE) 2>/dev/null || true
	@echo "Waiting for rollout..."
	@kubectl rollout status deployment -l app.kubernetes.io/component=web -n $(NAMESPACE) --timeout=3m 2>/dev/null || true
	@echo "Restart complete."
	@kubectl get pods -n $(NAMESPACE)

restart-all: check ## Restart EVERYTHING (including external services)
	@echo "WARNING: This restarts all services including the database."
	@read -p "Continue? [y/N] " -n 1 -r; echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		kubectl rollout restart deployment -n $(NAMESPACE); \
		echo "All deployments restarting..."; \
		kubectl wait --for=condition=available deployment --all -n $(NAMESPACE) --timeout=5m 2>/dev/null || true; \
		kubectl get pods -n $(NAMESPACE); \
	else \
		echo "Cancelled."; \
	fi

port-forward: check ## Port-forward to localhost:8080 (for testing without ingress)
	@echo "Port forwarding to http://localhost:8080 (Ctrl+C to stop)"
	@kubectl port-forward -n $(NAMESPACE) svc/$(HELM_RELEASE)-invenio-web 8080:80

# --------------------------------------------------------------------------
# TLS
# --------------------------------------------------------------------------

tls-setup: check env-check ## Install cert-manager and configure Let's Encrypt
	@echo "Setting up TLS..."
	@chmod +x scripts/setup-tls.sh
	@if [ "$(TLS_MODE)" = "selfsigned" ]; then \
		echo "TLS_MODE=selfsigned - skipping cert-manager"; \
		echo "Using k3s default self-signed cert."; \
	else \
		scripts/setup-tls.sh --domain $(DOMAIN) --email $(LETSENCRYPT_EMAIL) --namespace $(NAMESPACE); \
	fi
	@echo ""
	@echo "TLS setup complete."

tls-status: check ## Check TLS certificate status
	@echo "=== Certificates ==="
	@kubectl get certificates -n $(NAMESPACE) 2>/dev/null || echo "No certificates found"
	@echo ""
	@echo "=== Certificate Requests ==="
	@kubectl get certificaterequests -n $(NAMESPACE) 2>/dev/null || echo "No requests"
	@echo ""
	@echo "=== ClusterIssuers ==="
	@kubectl get clusterissuers 2>/dev/null || echo "No issuers"

# --------------------------------------------------------------------------
# Backup & Restore
# --------------------------------------------------------------------------

backup: check ## Manual database backup
	@echo "Running database backup..."
	@chmod +x scripts/backup.sh
	@scripts/backup.sh
	@echo ""
	@echo "Done. List backups: make backup-list"

restore: check ## Restore database from backup (FILE=path/to/dump)
	@if [ -z "$(FILE)" ]; then \
		echo "ERROR: Specify backup file: make restore FILE=/opt/backups/unesco-rdm/db/dump.sql"; \
		echo ""; \
		echo "Available backups:"; \
		ls -lhrt $(BACKUP_DIR)/db/*.dump 2>/dev/null || echo "  (none found)"; \
		exit 1; \
	fi
	@chmod +x scripts/restore.sh
	@scripts/restore.sh --backup-file $(FILE)

backup-schedule: check ## Install automated daily backup CronJob
	@echo "Installing backup CronJob..."
	@kubectl apply -f backup-cronjob.yaml -n $(NAMESPACE)
	@echo ""
	@echo "Backup CronJob installed."
	@kubectl get cronjobs -n $(NAMESPACE)

backup-list: ## List available backups
	@echo "=== Available Backups ==="
	@if [ -d "$(BACKUP_DIR)/db" ]; then \
		ls -lhrt $(BACKUP_DIR)/db/*.dump 2>/dev/null || echo "No backups found"; \
		echo ""; \
		echo "Total: $$(ls $(BACKUP_DIR)/db/*.dump 2>/dev/null | wc -l) backup(s)"; \
		echo "Space: $$(du -sh $(BACKUP_DIR) 2>/dev/null | cut -f1)"; \
	else \
		echo "Backup directory not found: $(BACKUP_DIR)"; \
		echo "Run 'make backup' to create the first backup."; \
	fi

# --------------------------------------------------------------------------
# Data Import (uses openscience_tools)
# --------------------------------------------------------------------------

import-lens: check ## Import Lens.org data (FILE=path OPTS=--limit 10)
	@echo "Importing Lens.org publications..."
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	echo "Generating API token..."; \
	TOKEN=$$(kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- \
		invenio tokens create -n 'Import Token' -u $(ADMIN_USER_EMAIL) 2>/dev/null | \
		grep -E '^[A-Za-z0-9_-]{40,}$$' | head -1); \
	if [ -z "$$TOKEN" ]; then \
		echo "ERROR: Failed to generate token. Is admin user created?"; \
		exit 1; \
	fi; \
	FILE=$${FILE:-../openscience_tools/openscience_tools/sources/lens/data/publications.json}; \
	OPTS=$${OPTS:-}; \
	echo "Importing from: $$FILE"; \
	source ../openscience_tools/.venv/bin/activate 2>/dev/null && \
		openscience-tools --base-url https://$(DOMAIN) --token "$$TOKEN" import-lens --file "$$FILE" $$OPTS; \
	echo "Import complete."

# --------------------------------------------------------------------------
# Destroy
# --------------------------------------------------------------------------

destroy: check ## Remove EVERYTHING from the cluster (DESTRUCTIVE!)
	@echo ""
	@echo "!!! WARNING: This will permanently delete:"
	@echo "    - All InvenioRDM data"
	@echo "    - Database and search indices"
	@echo "    - Uploaded files"
	@echo "    - TLS certificates"
	@echo ""
	@read -p "Type 'DESTROY' to confirm: " confirm; \
	if [ "$$confirm" = "DESTROY" ]; then \
		echo ""; \
		echo "Removing Helm release..."; \
		helm uninstall $(HELM_RELEASE) -n $(NAMESPACE) 2>/dev/null || true; \
		echo "Removing external services..."; \
		kubectl delete -f external-services.yaml -n $(NAMESPACE) 2>/dev/null || true; \
		echo "Removing backup CronJob..."; \
		kubectl delete -f backup-cronjob.yaml -n $(NAMESPACE) 2>/dev/null || true; \
		echo "Removing secrets..."; \
		kubectl delete secret --all -n $(NAMESPACE) 2>/dev/null || true; \
		echo "Removing PVCs..."; \
		kubectl delete pvc --all -n $(NAMESPACE) 2>/dev/null || true; \
		echo "Removing namespace..."; \
		kubectl delete namespace $(NAMESPACE) 2>/dev/null || true; \
		echo ""; \
		echo "All resources removed."; \
		echo "Backups in $(BACKUP_DIR) are preserved."; \
	else \
		echo "Cancelled."; \
	fi

# --------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------

db-shell: check ## Open psql shell in PostgreSQL
	@PG_POD=$$(kubectl get pods -n $(NAMESPACE) -l app=postgresql -o jsonpath='{.items[0].metadata.name}'); \
	kubectl exec -it -n $(NAMESPACE) $$PG_POD -- psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

search-shell: check ## Open shell in OpenSearch pod
	@OS_POD=$$(kubectl get pods -n $(NAMESPACE) -l app=opensearch -o jsonpath='{.items[0].metadata.name}'); \
	kubectl exec -it -n $(NAMESPACE) $$OS_POD -- bash

rebuild-index: check ## Rebuild search indices
	@echo "Rebuilding search indices..."
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index destroy --force --yes-i-know && invenio index init" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio rdm-records custom-fields init" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio rdm-records rebuild-index" ; \
	echo "Index rebuild started. Workers will process in background."

generate-secrets: ## Generate random secrets for .env
	@echo "Generated secrets (copy to .env):"
	@echo ""
	@echo "  SECRET_KEY=$$(openssl rand -hex 32)"
	@echo "  SECURITY_LOGIN_SALT=$$(openssl rand -hex 32)"
	@echo "  POSTGRES_PASSWORD=$$(openssl rand -hex 16)"
	@echo "  RABBITMQ_PASSWORD=$$(openssl rand -hex 16)"
