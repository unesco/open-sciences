#
# ============================================================================
# UNESCO Open Science Portal - Kubernetes Deployment
# ============================================================================
#
# Supports multiple environments via ENV variable:
#   make deploy ENV=local       # k3d on macOS/Linux desktop
#   make deploy ENV=staging     # Staging server
#   make deploy ENV=production  # Production server
#
# Configuration loaded from:
#   .env.<ENV>     — per-environment settings (includes generated secrets)
#
# See 'make help' for all available targets.
# ============================================================================

SHELL := /bin/bash

.PHONY: help install check env-check deploy deploy-services deploy-secrets deploy-helm \
        init init-app create-admin status logs shell up stop \
        backup restore list-backups deploy-backup-cronjob \
        destroy reset-lens render-config build-image load-image

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# Environment selection: local | staging | production
ENV ?= local

# Load environment config (optional via -include)
-include .env.$(ENV)
export

# Derived variables (computed from .env.<ENV> values)
SITE_UI_URL  := $(SITE_PROTOCOL)://$(DOMAIN)
SITE_API_URL := $(SITE_PROTOCOL)://$(DOMAIN)/api
APP_RDM_ADMIN_EMAIL_RECIPIENT ?= $(ADMIN_EMAIL)
SQLALCHEMY_DATABASE_URI := postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgresql:5432/$(POSTGRES_DB)

NAMESPACE         ?= unesco-rdm
HELM_RELEASE      ?= unesco-rdm
HELM_INVENIO_VER  ?= 0.8.1
VALUES_FILE       ?= values.yaml

# Backup Configuration
BACKUP_ENABLED ?= false
BACKUP_SCHEDULE ?= 0 2 * * *
BACKUP_RETENTION_DAYS ?= 10
BACKUP_PATH ?= backups/$(ENV)
BACKUP_STORAGE_SIZE ?= 100Gi

# Export variables for envsubst in backup-cronjob.yaml
export BACKUP_ENABLED BACKUP_SCHEDULE BACKUP_RETENTION_DAYS BACKUP_PATH BACKUP_STORAGE_SIZE

# On a k3s server: /etc/rancher/k3s/k3s.yaml
# On k3d or Docker Desktop: uses default ~/.kube/config
# Override with: make deploy KUBECONFIG=/path/to/kubeconfig
ifdef KUBECONFIG
export KUBECONFIG
endif

# Docker image
DOCKER_IMAGE_NAME ?= sc-openscience
DOCKER_IMAGE_TAG  ?= latest
IMAGE             := $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)

# k3d cluster name (for local testing on macOS/Linux desktop)
K3D_CLUSTER_NAME  ?= unesco-rdm

# --------------------------------------------------------------------------
# Help
# --------------------------------------------------------------------------

help: ## Show this help
	@echo ""
	@echo "UNESCO Open Science Portal - Kubernetes Deployment"
	@echo "===================================================="
	@echo "  Active environment: ENV=$(ENV)  (.env.$(ENV))"
	@echo ""
	@echo "First-time complete setup:"
	@echo "  make install ENV=local       Complete setup: tools → config → k3d → build → deploy → init"
	@echo ""
	@echo "CI/CD deployment (code updates):"
	@echo "  make deploy ENV=local        Rebuild image, upgrade Helm release, restart pods"
	@echo ""
	@echo "Initialization (manual):"
	@echo "  make init-app ENV=local      Reinitialize database + search (when needed)"
	@echo "  make create-admin ENV=local  Create admin user (standalone)"
	@echo ""
	@echo "Daily operations:"
	@echo "  make status                  Cluster & pod health"
	@echo "  make logs                    Tail web pod logs"
	@echo "  make shell                   Shell into web pod"
	@echo "  make up                      Start InvenioRDM"
	@echo "  make stop                    Stop InvenioRDM (keeps data)"
	@echo ""
	@echo "Build (low-level):"
	@echo "  make build-image             Build Docker image (renders invenio.cfg)"
	@echo "  make load-image              Build + load image into k3d cluster"
	@echo "  make render-config           Render invenio.cfg from template"
	@echo ""
	@echo "Backup & Restore:"
	@echo "  make backup ENV=<env>            Create backup of all data"
	@echo "  make restore BACKUP=<ts> ENV=<e> Restore from backup (timestamp)"
	@echo "  make list-backups ENV=<env>      List available backups"
	@echo "  make deploy-backup-cronjob       Deploy automated backup CronJob"
	@echo ""
	@echo "Data:"
	@echo "  make reset-lens              Delete all records + import Lens.org data"
	@echo ""
	@echo "Cleanup:"
	@echo "  make destroy                 Remove everything (DESTRUCTIVE)"
	@echo ""

# --------------------------------------------------------------------------
# Pre-flight checks
# --------------------------------------------------------------------------

check: ## Verify k3s, kubectl, helm are installed
	@echo "Checking required tools..."
	@command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl not found."; exit 1; }
	@command -v helm    >/dev/null 2>&1 || { echo "ERROR: helm not found."; exit 1; }
	@kubectl get nodes  >/dev/null 2>&1 || { echo "ERROR: Cannot reach k3s cluster. Is k3s running?"; exit 1; }
	@echo "  kubectl: OK"
	@echo "  helm:    OK"
	@echo "  k3s:     $$(kubectl get nodes -o jsonpath='{.items[0].status.nodeInfo.kubeletVersion}')"
	@echo "All checks passed."

env-check: ## Verify environment config files exist and have required values
	@if [ ! -f .env.$(ENV) ]; then \
		echo "ERROR: .env.$(ENV) not found!"; \
		echo "  Run: make install ENV=$(ENV)"; \
		exit 1; \
	fi
	@echo "Checking required secrets..."
	@missing=0; \
	for var in SECRET_KEY SECURITY_LOGIN_SALT POSTGRES_PASSWORD RABBITMQ_PASSWORD; do \
		val=$$(grep "^$$var=" .env.$(ENV) 2>/dev/null | cut -d= -f2- | grep -v CHANGE_ME); \
		if [ -z "$$val" ]; then \
			echo "  MISSING or not generated in .env.$(ENV): $$var"; \
			missing=1; \
		fi; \
	done; \
	if [ $$missing -eq 1 ]; then \
		echo ""; \
		echo "ERROR: Some required secrets are missing or contain placeholder values."; \
		echo "  Regenerate with: make install ENV=$(ENV)"; \
		exit 1; \
	fi
	@echo "Environment '$(ENV)' ready (domain=$(DOMAIN), protocol=$(SITE_PROTOCOL))."

# --------------------------------------------------------------------------
# Deployment
# --------------------------------------------------------------------------

# Private target: Install Helm chart (called by 'install' during first-time setup)
install-helm: check env-check deploy-services deploy-secrets deploy-helm
	@echo "Helm installation complete."

# CI/CD deployment: Rebuild image + upgrade Helm + restart pods
deploy: check env-check ## CI/CD deployment (rebuild image + upgrade + restart)
	@echo "Deploying InvenioRDM updates (CI/CD workflow)..."
	@echo ""
	@echo "Step 1/3: Rebuilding and loading image..."
	@$(MAKE) load-image ENV=$(ENV)
	@echo ""
	@echo "Step 2/3: Upgrading Helm release..."
	@$(MAKE) deploy-helm ENV=$(ENV)
	@echo ""
	@echo "Step 3/3: Restarting pods to pick up new image..."
	@kubectl rollout restart deployment -l app.kubernetes.io/component=web -n $(NAMESPACE) 2>/dev/null || true
	@kubectl rollout restart deployment -l app.kubernetes.io/component=worker -n $(NAMESPACE) 2>/dev/null || true
	@kubectl rollout restart deployment -l app.kubernetes.io/component=worker-beat -n $(NAMESPACE) 2>/dev/null || true
	@kubectl rollout status deployment -l app.kubernetes.io/component=web -n $(NAMESPACE) --timeout=3m 2>/dev/null || true
	@echo ""
	@echo "============================================"
	@echo "  Deployment complete!  (ENV=$(ENV))"
	@echo "============================================"
	@echo ""
	@echo "  Access: $(SITE_UI_URL)"
	@echo ""
	@echo "Check status: make status"

# --------------------------------------------------------------------------
# Services (PostgreSQL, Redis, RabbitMQ, OpenSearch)
# --------------------------------------------------------------------------

deploy-services: check ## Deploy external services (DB, cache, search, queue)
	@echo "Deploying external services..."
	@kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@kubectl config set-context --current --namespace=$(NAMESPACE)
	@echo ""
	@echo "Creating service secrets..."
	@kubectl create secret generic $(HELM_RELEASE)-secrets \
		--from-literal=POSTGRES_USER=$(POSTGRES_USER) \
		--from-literal=POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		--from-literal=POSTGRES_DB=$(POSTGRES_DB) \
		--from-literal=RABBITMQ_USER=$(RABBITMQ_USER) \
		--from-literal=RABBITMQ_PASSWORD=$(RABBITMQ_PASSWORD) \
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

deploy-secrets: check env-check ## Create K8s secrets from environment config
	@echo "Creating InvenioRDM secrets..."
	@kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@kubectl create secret generic $(HELM_RELEASE)-secrets \
		--from-literal=POSTGRES_USER=$(POSTGRES_USER) \
		--from-literal=POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		--from-literal=POSTGRES_DB=$(POSTGRES_DB) \
		--from-literal=RABBITMQ_USER=$(RABBITMQ_USER) \
		--from-literal=RABBITMQ_PASSWORD=$(RABBITMQ_PASSWORD) \
		--from-literal=SECRET_KEY=$(SECRET_KEY) \
		--from-literal=SECURITY_LOGIN_SALT=$(SECURITY_LOGIN_SALT) \
		--from-literal=SQLALCHEMY_DATABASE_URI="postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgresql:5432/$(POSTGRES_DB)" \
		--from-literal=CELERY_BROKER_URL="amqp://$(RABBITMQ_USER):$(RABBITMQ_PASSWORD)@rabbitmq:5672/" \
		--from-literal=CACHE_REDIS_URL="redis://redis:6379/0" \
		--namespace=$(NAMESPACE) \
		--dry-run=client -o yaml | kubectl apply -f -
	@echo "Secrets created."
	@echo ""

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

# --------------------------------------------------------------------------
# Initialization
# --------------------------------------------------------------------------

init-app: check ## Reinitialize database, indices, vocabularies (manual operation)
	@echo "Reinitializing InvenioRDM application..."
	@echo "Waiting for web pod..."
	@kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=web \
		-n $(NAMESPACE) --timeout=300s 2>/dev/null || \
		{ echo "ERROR: Web pod not ready. Check: make status"; exit 1; }
	@echo ""
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	echo "Step 1/7: Initializing database..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio db init 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio db create 2>/dev/null || true" ; \
	echo ""; \
	echo "Step 2/7: Initializing search indices..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index destroy --force --yes-i-know 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index init 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index queue init purge 2>/dev/null || true" ; \
	echo ""; \
	echo "Step 3/7: Initializing custom fields..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio rdm-records custom-fields init 2>/dev/null || true" ; \
	echo ""; \
	echo "Step 4/7: Creating file storage location..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio files location create --default 'default-location' /opt/invenio/var/instance/data 2>/dev/null || true" ; \
	echo ""; \
	echo "Waiting for OpenSearch to be ready..."; \
	for i in $$(seq 1 30); do \
		if kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- curl -s -f http://opensearch:9200/_cluster/health >/dev/null 2>&1; then \
			echo "  ✓ OpenSearch is ready"; \
			break; \
		fi; \
		echo "  Waiting for OpenSearch... ($$i/30)"; \
		sleep 2; \
		if [ $$i -eq 30 ]; then \
			echo "  ERROR: OpenSearch not ready after 60s"; \
			exit 1; \
		fi; \
	done; \
	echo ""; \
	echo "Step 5/7: Loading vocabularies (synchronous, no Celery dependency)..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- python3 -c "from invenio_app.factory import create_app; app = create_app(); ctx = app.app_context(); ctx.push(); from invenio_access.permissions import system_identity; from invenio_rdm_records.fixtures.vocabularies import PrioritizedVocabulariesFixtures; from pathlib import Path; import flask; app_data = Path(flask.current_app.instance_path) / 'app_data'; pkg = Path('/usr/local/lib/python3.12/site-packages/invenio_rdm_records/fixtures/data'); pv = PrioritizedVocabulariesFixtures(system_identity, app_data_folder=app_data, pkg_data_folder=pkg, delay=False); pv.load(); print('Vocabularies created in database.')" 2>&1 | tail -5 ; \
	echo ""; \
	echo "Step 6/7: Indexing vocabularies in OpenSearch..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "echo y | invenio index reindex --pid-type vcf 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index run 2>/dev/null || true" ; \
	echo "  Waiting 10s for OpenSearch to settle..."; \
	sleep 10; \
	echo ""; \
	echo "Verifying vocabularies..."; \
	TOTAL=$$(kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- python3 -c "from invenio_app.factory import create_app; app = create_app(); ctx = app.app_context(); ctx.push(); from invenio_access.permissions import system_identity; from invenio_vocabularies.proxies import current_service; r = current_service.search(system_identity, type='resourcetypes'); print(r.total)" 2>/dev/null | tail -1); \
	echo "  resourcetypes: $$TOTAL"; \
	if [ "$$TOTAL" -gt 0 ] 2>/dev/null; then \
		echo "  Vocabularies OK."; \
	else \
		echo "  WARN: 0 resourcetypes indexed. Trying full reindex..."; \
		kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c " \
			echo y | invenio index reindex --pid-type vcf 2>/dev/null; \
			invenio index run 2>/dev/null" ; \
		sleep 15; \
		TOTAL2=$$(kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- python3 -c "from invenio_app.factory import create_app; app = create_app(); ctx = app.app_context(); ctx.push(); from invenio_access.permissions import system_identity; from invenio_vocabularies.proxies import current_service; r = current_service.search(system_identity, type='resourcetypes'); print(r.total)" 2>/dev/null | tail -1); \
		echo "  resourcetypes (retry): $$TOTAL2"; \
	fi; \
	echo ""; \
	echo "Step 7/7: Loading CMS fixtures (header, footer, static pages)..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio cms load-fixtures" ; \
	echo ""; \
	echo "Reinitialization complete."

init: init-app ## Alias for init-app (backward compatibility)

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

render-config: ## Render invenio.cfg from template using current environment
	@echo "Rendering invenio.cfg (ENV=$(ENV))..."
	@if [ ! -f ../invenio.cfg.template ]; then \
		echo "ERROR: ../invenio.cfg.template not found!"; \
		exit 1; \
	fi
	@envsubst < ../invenio.cfg.template > ../invenio.cfg
	@echo "  invenio.cfg written (domain=$(DOMAIN), protocol=$(SITE_PROTOCOL))."

build-image: render-config ## Build Docker image (renders invenio.cfg, then builds)
	@echo "Building Docker image..."
	@echo "  Image: $(IMAGE)"
	@echo "  Dockerfile: Dockerfile"
	@echo "  Context: repo root (..)"
	docker build -t $(IMAGE) -f Dockerfile ..
	@echo ""
	@echo "Image built: $(IMAGE)"
	@docker images $(IMAGE)

load-image: build-image ## Build image and load into k3d cluster
	@echo "Loading image into k3d cluster..."
	@if command -v k3d >/dev/null 2>&1; then \
		k3d image import $(IMAGE) --cluster $(K3D_CLUSTER_NAME); \
		echo "Image loaded into k3d cluster: $(K3D_CLUSTER_NAME)"; \
	else \
		echo "k3d not found. Skipping image load."; \
	fi

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

logs: check ## Tail web pod logs
	@echo "Tailing web pod logs (Ctrl+C to stop)..."
	@kubectl logs -f -l app.kubernetes.io/component=web -n $(NAMESPACE) --all-containers=true --tail=100

shell: check ## Open a shell in the web pod
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	echo "Opening shell in $$WEB_POD..."; \
	kubectl exec -it -n $(NAMESPACE) $$WEB_POD -c web -- bash

up: check ## Start InvenioRDM (scale up deployments)
	@echo "Starting InvenioRDM..."
	@kubectl scale deployment -l app.kubernetes.io/component=web --replicas=1 -n $(NAMESPACE) 2>/dev/null || true
	@kubectl scale deployment -l app.kubernetes.io/component=worker --replicas=1 -n $(NAMESPACE) 2>/dev/null || true
	@kubectl scale deployment -l app.kubernetes.io/component=worker-beat --replicas=1 -n $(NAMESPACE) 2>/dev/null || true
	@echo "Waiting for pods to be ready..."
	@kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=web -n $(NAMESPACE) --timeout=3m 2>/dev/null || echo "  WARN: Web pod not ready yet"
	@echo "InvenioRDM started."
	@kubectl get pods -n $(NAMESPACE)

stop: check ## Stop InvenioRDM (scale down deployments, keeps data)
	@echo "Stopping InvenioRDM..."
	@kubectl scale deployment -l app.kubernetes.io/component=web --replicas=0 -n $(NAMESPACE) 2>/dev/null || true
	@kubectl scale deployment -l app.kubernetes.io/component=worker --replicas=0 -n $(NAMESPACE) 2>/dev/null || true
	@kubectl scale deployment -l app.kubernetes.io/component=worker-beat --replicas=0 -n $(NAMESPACE) 2>/dev/null || true
	@echo "InvenioRDM stopped (data preserved)."
	@kubectl get pods -n $(NAMESPACE)

# --------------------------------------------------------------------------
# Backup & Restore
# --------------------------------------------------------------------------

backup: check env-check ## Create a backup of PostgreSQL, OpenSearch, and files
	@echo "Creating backup..."
	@if [ ! -d "$(BACKUP_PATH)" ]; then \
		mkdir -p "$(BACKUP_PATH)"; \
		echo "  Created backup directory: $(BACKUP_PATH)"; \
	fi
	@bash scripts/backup.sh $(NAMESPACE) $(BACKUP_PATH)
	@echo ""
	@echo "Running retention cleanup (keeping last $(BACKUP_RETENTION_DAYS) days)..."
	@bash scripts/backup-retention.sh $(BACKUP_PATH) $(BACKUP_RETENTION_DAYS)

restore: check env-check ## Restore from a backup (use BACKUP=<timestamp>)
	@if [ -z "$(BACKUP)" ]; then \
		echo "ERROR: BACKUP parameter required."; \
		echo ""; \
		echo "Usage: make restore BACKUP=<timestamp> ENV=$(ENV)"; \
		echo ""; \
		echo "Available backups:"; \
		$(MAKE) list-backups ENV=$(ENV); \
		exit 1; \
	fi
	@if [ ! -d "$(BACKUP_PATH)/$(BACKUP)" ]; then \
		echo "ERROR: Backup not found: $(BACKUP_PATH)/$(BACKUP)"; \
		echo ""; \
		$(MAKE) list-backups ENV=$(ENV); \
		exit 1; \
	fi
	@bash scripts/restore.sh $(NAMESPACE) $(BACKUP_PATH)/$(BACKUP)

list-backups: env-check ## List available backups
	@echo "Available backups in: $(BACKUP_PATH)"
	@echo ""
	@if [ ! -d "$(BACKUP_PATH)" ]; then \
		echo "  No backups found (directory doesn't exist)"; \
		echo ""; \
		echo "  Create one with: make backup ENV=$(ENV)"; \
	else \
		BACKUPS=$$(ls -1t "$(BACKUP_PATH)" 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}$$' || true); \
		if [ -z "$$BACKUPS" ]; then \
			echo "  No backups found"; \
			echo ""; \
			echo "  Create one with: make backup ENV=$(ENV)"; \
		else \
			echo "$$BACKUPS" | head -10 | while read backup; do \
				if [ -d "$(BACKUP_PATH)/$$backup" ]; then \
					SIZE=$$(du -sh "$(BACKUP_PATH)/$$backup" 2>/dev/null | cut -f1); \
					echo "  $$backup  ($$SIZE)"; \
				fi; \
			done; \
			COUNT=$$(echo "$$BACKUPS" | wc -l | tr -d ' '); \
			if [ $$COUNT -gt 10 ]; then \
				echo "  ... and $$(($$COUNT - 10)) more"; \
			fi; \
			echo ""; \
			echo "To restore: make restore BACKUP=<timestamp> ENV=$(ENV)"; \
		fi; \
	fi
	@echo ""

deploy-backup-cronjob: check env-check ## Deploy automated backup CronJob (staging/production)
	@echo "Deploying backup CronJob..."
	@envsubst < backup-cronjob.yaml > /tmp/backup-cronjob-rendered.yaml
	@kubectl apply -f /tmp/backup-cronjob-rendered.yaml
	@rm -f /tmp/backup-cronjob-rendered.yaml
	@echo "Backup CronJob deployed (schedule: $(BACKUP_SCHEDULE))."
	@echo ""
	@kubectl get cronjob -n $(NAMESPACE)

# --------------------------------------------------------------------------
# Data Import (uses openscience_tools)
# --------------------------------------------------------------------------

reset-lens: check ## Delete all records and re-import Lens.org data
	@echo "Resetting InvenioRDM records with Lens.org data..."
	@echo ""
	@echo "Checking connectivity on localhost..."
	@if ! curl -s --max-time 5 -o /dev/null http://localhost/ping; then \
		echo "ERROR: Cannot reach http://localhost"; \
		echo "  For k3d, ensure port mapping is configured."; \
		exit 1; \
	fi
	@echo "  localhost reachable."
	@echo ""
	@echo "Generating temporary API token..."
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	TOKEN=$$(kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- \
		invenio tokens create -n 'Temp Import Token' -u $(ADMIN_USER_EMAIL) 2>/dev/null | \
		grep -v "WARNING\|UserWarning\|pkg_resources\|deprecated" | \
		grep -E '^[A-Za-z0-9_-]{40,}$$' | head -1); \
	if [ -z "$$TOKEN" ]; then \
		echo "ERROR: Failed to generate token. Is admin user created?"; \
		echo "  Run: make create-admin ENV=$(ENV)"; \
		exit 1; \
	fi; \
	echo "  Token generated: $${TOKEN:0:20}..."; \
	echo ""; \
	echo "Step 1/3: Deleting all existing records..."; \
	openscience-tools --base-url http://localhost --token "$$TOKEN" cleanup --confirm; \
	echo ""; \
	echo "Step 2/3: Importing Lens.org publications..."; \
	FILE=$${FILE:-../openscience_tools/openscience_tools/sources/lens/data/publications.json}; \
	OPTS=$${OPTS:-}; \
	openscience-tools --base-url http://localhost --token "$$TOKEN" import-lens --file "$$FILE" $$OPTS; \
	echo ""; \
	echo "Step 3/3: Reindexing records for facet aggregations..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "echo y | invenio index reindex --pid-type recid 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index run 2>/dev/null || true" ; \
	echo "  Waiting 10s for OpenSearch to process..."; \
	sleep 10; \
	echo ""; \
	echo "Revoking temporary token..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- \
		invenio tokens delete "$$TOKEN" 2>/dev/null || true; \
	echo ""; \
	echo "Reset complete!"; \
	echo "  Access at: http://localhost"

# --------------------------------------------------------------------------
# Destroy
# --------------------------------------------------------------------------

destroy: check ## Remove EVERYTHING from the cluster (DESTRUCTIVE!)
	@echo ""
	@echo "!!! WARNING: This will permanently delete:"
	@echo "    - All InvenioRDM data"
	@echo "    - Database and search indices"
	@echo "    - Uploaded files"
	@echo ""
	@read -p "Type 'DESTROY' to confirm: " confirm; \
	if [ "$$confirm" = "DESTROY" ]; then \
		echo ""; \
		echo "Removing Helm release..."; \
		helm uninstall $(HELM_RELEASE) -n $(NAMESPACE) 2>/dev/null || true; \
		echo "Removing external services..."; \
		kubectl delete -f external-services.yaml -n $(NAMESPACE) 2>/dev/null || true; \
		echo "Removing secrets..."; \
		kubectl delete secret --all -n $(NAMESPACE) 2>/dev/null || true; \
		echo "Removing PVCs..."; \
		kubectl delete pvc --all -n $(NAMESPACE) 2>/dev/null || true; \
		echo "Removing namespace..."; \
		kubectl delete namespace $(NAMESPACE) 2>/dev/null || true; \
		echo ""; \
		echo "All resources removed."; \
	else \
		echo "Cancelled."; \
	fi

# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------

install: ## Complete first-time setup: tools → config → k3d → build → deploy → init
	@echo "UNESCO Open Science Portal - Complete Installation"
	@echo "===================================================="
	@echo "Environment: $(ENV)"
	@echo ""
	@echo "[1/6] Checking required tools..."
	@command -v docker   >/dev/null 2>&1 || { echo "  ERROR: docker not found. Install Docker Desktop or colima."; exit 1; }; echo "  ✓ docker"
	@command -v kubectl  >/dev/null 2>&1 || { echo "  ERROR: kubectl not found. Run: brew install kubectl"; exit 1; }; echo "  ✓ kubectl"
	@command -v helm     >/dev/null 2>&1 || { echo "  ERROR: helm not found. Run: brew install helm"; exit 1; }; echo "  ✓ helm"
	@command -v envsubst >/dev/null 2>&1 || { echo "  ERROR: envsubst not found. Run: brew install gettext && brew link --force gettext"; exit 1; }; echo "  ✓ envsubst"
	@command -v openssl  >/dev/null 2>&1 || { echo "  ERROR: openssl not found."; exit 1; }; echo "  ✓ openssl"
	@if [ "$(ENV)" = "local" ]; then \
		command -v k3d >/dev/null 2>&1 || { echo "  ERROR: k3d not found. Run: brew install k3d"; exit 1; }; \
		echo "  ✓ k3d"; \
	fi
	@echo ""
	@echo "[2/6] Setting up .env.$(ENV)..."
	@if [ -f .env.$(ENV) ]; then \
		echo "  .env.$(ENV) already exists."; \
		if grep -q "CHANGE_ME" .env.$(ENV) 2>/dev/null; then \
			echo "  Regenerating secrets (found CHANGE_ME placeholders)..."; \
			cp .env.$(ENV) .env.$(ENV).bak; \
			sed -i.tmp "s/SECRET_KEY=.*/SECRET_KEY=$$(openssl rand -hex 32)/" .env.$(ENV); \
			sed -i.tmp "s/SECURITY_LOGIN_SALT=.*/SECURITY_LOGIN_SALT=$$(openssl rand -hex 32)/" .env.$(ENV); \
			sed -i.tmp "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$$(openssl rand -hex 16)/" .env.$(ENV); \
			sed -i.tmp "s/RABBITMQ_PASSWORD=.*/RABBITMQ_PASSWORD=$$(openssl rand -hex 16)/" .env.$(ENV); \
			rm -f .env.$(ENV).tmp; \
			echo "  ✓ Secrets regenerated (backup saved to .env.$(ENV).bak)"; \
		else \
			echo "  ✓ Using existing configuration"; \
		fi; \
	else \
		if [ ! -f .env.example ]; then \
			echo "  ERROR: .env.example not found!"; \
			exit 1; \
		fi; \
		echo "  Creating .env.$(ENV) from .env.example..."; \
		cp .env.example .env.$(ENV); \
		sed -i.tmp "s/SECRET_KEY=.*/SECRET_KEY=$$(openssl rand -hex 32)/" .env.$(ENV); \
		sed -i.tmp "s/SECURITY_LOGIN_SALT=.*/SECURITY_LOGIN_SALT=$$(openssl rand -hex 32)/" .env.$(ENV); \
		sed -i.tmp "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$$(openssl rand -hex 16)/" .env.$(ENV); \
		sed -i.tmp "s/RABBITMQ_PASSWORD=.*/RABBITMQ_PASSWORD=$$(openssl rand -hex 16)/" .env.$(ENV); \
		rm -f .env.$(ENV).tmp; \
		chmod 600 .env.$(ENV); \
		echo "  ✓ .env.$(ENV) created with random secrets"; \
	fi
	@echo ""
	@if [ "$(ENV)" = "local" ]; then \
		echo "[3/6] Setting up k3d cluster..."; \
		if k3d cluster list | grep -q "$(K3D_CLUSTER_NAME)"; then \
			echo "  k3d cluster '$(K3D_CLUSTER_NAME)' already exists."; \
			echo "  ✓ Using existing cluster"; \
		else \
			echo "  Creating k3d cluster '$(K3D_CLUSTER_NAME)'..."; \
			k3d cluster create $(K3D_CLUSTER_NAME) \
				--port "80:80@loadbalancer" \
				--port "8443:443@loadbalancer" \
				--agents 0; \
			echo "  ✓ k3d cluster created"; \
		fi; \
	else \
		echo "[3/6] Skipping k3d setup (ENV=$(ENV))"; \
	fi
	@echo ""
	@echo "[4/6] Building and loading Docker image..."
	@$(MAKE) load-image ENV=$(ENV)
	@echo ""
	@echo "[5/6] Deploying services and Helm chart..."
	@$(MAKE) install-helm ENV=$(ENV)
	@echo ""
	@echo "[6/6] Initializing application..."
	@$(MAKE) init-app ENV=$(ENV)
	@$(MAKE) create-admin ENV=$(ENV)
	@echo ""
	@echo "===================================================="
	@echo "  Installation complete!  (ENV=$(ENV))"
	@echo "===================================================="
	@echo ""
	@echo "  Domain:   $(DOMAIN)"
	@echo "  Protocol: $(SITE_PROTOCOL)"
	@echo "  Admin:    $(ADMIN_USER_EMAIL)"
	@echo ""
	@echo "  Access: $(SITE_UI_URL)"
	@echo ""
	@echo "Next steps:"
	@echo "  - Load sample data: make reset-lens ENV=$(ENV)"
	@echo "  - Check status: make status"
	@echo "  - View logs: make logs"
	@echo ""
