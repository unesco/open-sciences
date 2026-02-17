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
#   .env.<ENV>     — per-environment settings (committed, no secrets)
#   .env.secrets   — generated credentials (NOT committed)
#
# See 'make help' for all available targets.
# ============================================================================

SHELL := /bin/bash

.PHONY: help check env-check deploy deploy-services deploy-secrets deploy-helm \
        init reinit create-admin upgrade status logs shell restart backup restore \
        tls-setup backup-schedule destroy port-forward helm-versions \
        reset-lens import-lens \
        generate-secrets render-config build-image load-image push-image

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# Environment selection: local | staging | production
ENV ?= local

# Load environment config, then secrets (both optional via -include)
-include .env.$(ENV)
-include .env.secrets
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
REGISTRY_IMAGE    := $(if $(DOCKER_REGISTRY),$(DOCKER_REGISTRY):$(DOCKER_IMAGE_TAG),)

# k3d cluster name (for local testing on macOS/Linux desktop)
K3D_CLUSTER_NAME  ?= unesco-rdm

# Backup
BACKUP_DIR        ?= /opt/backups/unesco-rdm

# --------------------------------------------------------------------------
# Help
# --------------------------------------------------------------------------

help: ## Show this help
	@echo ""
	@echo "UNESCO Open Science Portal - Kubernetes Deployment"
	@echo "===================================================="
	@echo "  Active environment: ENV=$(ENV)  (.env.$(ENV))"
	@echo ""
	@echo "First-time setup:"
	@echo "  make generate-secrets        Generate .env.secrets"
	@echo "  make deploy ENV=local        Full deployment (services + helm + init)"
	@echo ""
	@echo "Daily operations:"
	@echo "  make status                  Cluster & pod health"
	@echo "  make logs                    Tail web pod logs"
	@echo "  make logs-worker             Tail worker pod logs"
	@echo "  make shell                   Shell into web pod"
	@echo "  make restart                 Rolling restart of InvenioRDM"
	@echo ""
	@echo "Updates:"
	@echo "  make upgrade                 Upgrade InvenioRDM (rebuild image + helm)"
	@echo "  make deploy-helm             Re-deploy Helm chart only"
	@echo "  make build-image             Build Docker image (renders invenio.cfg)"
	@echo "  make render-config           Render invenio.cfg from template"
	@echo "  make load-image              Build + load image into k3d cluster"
	@echo "  make push-image              Build + push to registry"
	@echo ""
	@echo "Backup & Restore:"
	@echo "  make backup                  Manual database backup"
	@echo "  make restore FILE=...        Restore from backup file"
	@echo "  make backup-schedule         Install automated daily backups"
	@echo "  make backup-list             List available backups"
	@echo ""
	@echo "TLS & Security:"
	@echo "  make tls-setup               Install cert-manager + Let's Encrypt"
	@echo "  make tls-status              Check certificate status"
	@echo ""
	@echo "Data Import:"
	@echo "  make reset-lens              Delete all records + import Lens.org data"
	@echo "  make import-lens             Import Lens.org data (FILE=... OPTS=...)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make reinit                  Re-initialize DB + indices from scratch"
	@echo ""
	@echo "Cleanup:"
	@echo "  make destroy                 Remove everything (DESTRUCTIVE)"
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

env-check: ## Verify environment config files exist and have required values
	@if [ ! -f .env.$(ENV) ]; then \
		echo "ERROR: .env.$(ENV) not found!"; \
		echo "  Available environments: local, staging, production"; \
		exit 1; \
	fi
	@if [ ! -f .env.secrets ]; then \
		echo "ERROR: .env.secrets not found!"; \
		echo "  Run: make generate-secrets"; \
		exit 1; \
	fi
	@echo "Checking required secrets..."
	@missing=0; \
	for var in SECRET_KEY SECURITY_LOGIN_SALT POSTGRES_PASSWORD RABBITMQ_PASSWORD; do \
		val=$$(grep "^$$var=" .env.secrets 2>/dev/null | cut -d= -f2-); \
		if [ -z "$$val" ]; then \
			echo "  MISSING in .env.secrets: $$var"; \
			missing=1; \
		fi; \
	done; \
	if [ $$missing -eq 1 ]; then \
		echo ""; \
		echo "ERROR: Some required secrets are missing."; \
		echo "  Regenerate with: make generate-secrets"; \
		exit 1; \
	fi
	@echo "Environment '$(ENV)' ready (domain=$(DOMAIN), protocol=$(SITE_PROTOCOL))."

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
	@echo "  Deployment complete!  (ENV=$(ENV))"
	@echo "============================================"
	@echo ""
	@echo "  Domain:   $(DOMAIN)"
	@echo "  Protocol: $(SITE_PROTOCOL)"
	@echo "  Admin:    $(ADMIN_USER_EMAIL)"
	@echo ""
	@echo "  Next steps:"
	@echo "    1. Check status:    make status"
	if [ "$(TLS_MODE)" != "none" ]; then \
		echo "    2. Set up TLS:      make tls-setup"; \
		echo "    3. Set up backups:  make backup-schedule"; \
	fi
	@echo ""
	@echo "  Access: $(SITE_UI_URL)"
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
		$(if $(filter true,$(INGRESS_TLS_ENABLED)),\
			--set 'ingress.annotations.cert-manager\.io/cluster-issuer=letsencrypt-prod' \
			--set 'ingress.tls[0].secretName=unesco-rdm-tls' \
			--set 'ingress.tls[0].hosts[0]=$(DOMAIN)' \
		) \
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
	echo "Step 1/6: Initializing database..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio db init 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio db create 2>/dev/null || true" ; \
	echo ""; \
	echo "Step 2/6: Initializing search indices..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index destroy --force --yes-i-know 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index init 2>/dev/null || true" ; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio index queue init purge 2>/dev/null || true" ; \
	echo ""; \
	echo "Step 3/6: Initializing custom fields..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio rdm-records custom-fields init 2>/dev/null || true" ; \
	echo ""; \
	echo "Step 4/6: Creating file storage location..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio files location create --default 'default-location' /opt/invenio/var/instance/data 2>/dev/null || true" ; \
	echo ""; \
	echo "Step 5/6: Loading vocabularies (synchronous, no Celery dependency)..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- python3 -c "from invenio_app.factory import create_app; app = create_app(); ctx = app.app_context(); ctx.push(); from invenio_access.permissions import system_identity; from invenio_rdm_records.fixtures.vocabularies import PrioritizedVocabulariesFixtures; from pathlib import Path; import flask; app_data = Path(flask.current_app.instance_path) / 'app_data'; pkg = Path('/usr/local/lib/python3.12/site-packages/invenio_rdm_records/fixtures/data'); pv = PrioritizedVocabulariesFixtures(system_identity, app_data_folder=app_data, pkg_data_folder=pkg, delay=False); pv.load(); print('Vocabularies created in database.')" 2>&1 | tail -5 ; \
	echo ""; \
	echo "Step 6/6: Indexing vocabularies in OpenSearch..."; \
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

reinit: check ## Destroy DB + indices and re-initialize everything (DESTRUCTIVE!)
	@echo "WARNING: This will destroy the database and search indices!"
	@echo "         All records, users, and vocabularies will be lost."
	@echo ""
	@read -p "Continue? [y/N] " -n 1 -r; echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then echo "Cancelled."; exit 0; fi
	@echo ""
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	echo "Destroying database..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio db destroy --yes-i-know 2>/dev/null || true" ; \
	echo ""
	@$(MAKE) init ENV=$(ENV)
	@$(MAKE) create-admin ENV=$(ENV)
	@echo ""
	@echo "Re-initialization complete."

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
	@echo "  Dockerfile: ../k8s/Dockerfile"
	@echo "  Context: repo root (..)"
	docker build -t $(IMAGE) -f ../k8s/Dockerfile ..
	@echo ""
	@echo "Image built: $(IMAGE)"
	@docker images $(IMAGE)

load-image: build-image ## Build image and load into k3d cluster
	@echo "Loading image into k3d cluster..."
	@if command -v k3d >/dev/null 2>&1; then \
		k3d image import $(IMAGE) --cluster $(K3D_CLUSTER_NAME); \
		echo "Image loaded into k3d cluster: $(K3D_CLUSTER_NAME)"; \
	else \
		echo "k3d not found. On a k3s server, push to registry instead:"; \
		echo "  docker tag $(IMAGE) $(REGISTRY_IMAGE)"; \
		echo "  docker push $(REGISTRY_IMAGE)"; \
	fi

push-image: build-image ## Build and push Docker image to registry
	@echo "Tagging and pushing to registry..."
	docker tag $(IMAGE) $(REGISTRY_IMAGE)
	docker push $(REGISTRY_IMAGE)
	@echo "Image pushed: $(REGISTRY_IMAGE)"

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

reset-lens: check ## Delete all records and re-import Lens.org data
	@echo "Resetting InvenioRDM records with Lens.org data..."
	@echo ""
	@echo "Checking connectivity on localhost:8080..."
	@if ! curl -s --max-time 5 -o /dev/null http://localhost:8080/ping; then \
		echo "ERROR: Cannot reach http://localhost:8080"; \
		echo "  For k3d, ensure port mapping is configured."; \
		echo "  Or start port-forward: make port-forward"; \
		exit 1; \
	fi
	@echo "  localhost:8080 reachable."
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
	echo "Step 1/2: Deleting all existing records..."; \
	openscience-tools --base-url http://localhost:8080 --token "$$TOKEN" cleanup --confirm; \
	echo ""; \
	echo "Step 2/2: Importing Lens.org publications..."; \
	FILE=$${FILE:-../openscience_tools/openscience_tools/sources/lens/data/publications.json}; \
	OPTS=$${OPTS:-}; \
	openscience-tools --base-url http://localhost:8080 --token "$$TOKEN" import-lens --file "$$FILE" $$OPTS; \
	echo ""; \
	echo "Revoking temporary token..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- \
		invenio tokens delete "$$TOKEN" 2>/dev/null || true; \
	echo ""; \
	echo "Reset complete!"; \
	echo "  Access at: http://localhost:8080"

import-lens: check ## Import Lens.org data (FILE=path OPTS='--limit 10')
	@echo "Importing Lens.org publications..."
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	echo "Generating API token..."; \
	TOKEN=$$(kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- \
		invenio tokens create -n 'Import Token' -u $(ADMIN_USER_EMAIL) 2>/dev/null | \
		grep -v "WARNING\|UserWarning\|pkg_resources\|deprecated" | \
		grep -E '^[A-Za-z0-9_-]{40,}$$' | head -1); \
	if [ -z "$$TOKEN" ]; then \
		echo "ERROR: Failed to generate token. Is admin user created?"; \
		exit 1; \
	fi; \
	FILE=$${FILE:-../openscience_tools/openscience_tools/sources/lens/data/publications.json}; \
	OPTS=$${OPTS:-}; \
	echo "Importing from: $$FILE"; \
	openscience-tools --base-url http://localhost:8080 --token "$$TOKEN" import-lens --file "$$FILE" $$OPTS; \
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

generate-secrets: ## Generate .env.secrets with random credentials
	@echo "Generating .env.secrets..."
	@echo "# Auto-generated secrets — DO NOT commit to Git" > .env.secrets
	@echo "# Generated on: $$(date -Iseconds)" >> .env.secrets
	@echo "" >> .env.secrets
	@echo "SECRET_KEY=$$(openssl rand -hex 32)" >> .env.secrets
	@echo "SECURITY_LOGIN_SALT=$$(openssl rand -hex 32)" >> .env.secrets
	@echo "POSTGRES_PASSWORD=$$(openssl rand -hex 16)" >> .env.secrets
	@echo "RABBITMQ_PASSWORD=$$(openssl rand -hex 16)" >> .env.secrets
	@chmod 600 .env.secrets
	@echo "Secrets written to .env.secrets (mode 600)."
