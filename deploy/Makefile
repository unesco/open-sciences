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
        init create-admin upgrade status logs shell restart destroy \
        reset-lens render-config build-image load-image

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
	@echo "First-time setup:"
	@echo "  make install ENV=local       Check tools, create .env.local, setup k3d cluster"
	@echo "  make load-image ENV=local    Build Docker image + load into k3d"
	@echo "  make deploy ENV=local        Full deployment (services + InvenioRDM + init)"
	@echo ""
	@echo "Daily operations:"
	@echo "  make status                  Cluster & pod health"
	@echo "  make logs                    Tail web pod logs"
	@echo "  make shell                   Shell into web pod"
	@echo "  make restart                 Rolling restart of InvenioRDM"
	@echo ""
	@echo "Updates:"
	@echo "  make upgrade                 Upgrade InvenioRDM (rebuild image + helm)"
	@echo "  make build-image             Build Docker image (renders invenio.cfg)"
	@echo "  make render-config           Render invenio.cfg from template"
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

init: check ## Initialize database, indices, vocabularies
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
		echo "k3d not found. Skipping image load."; \
	fi

upgrade: check env-check ## Upgrade InvenioRDM (rebuild image + helm upgrade)
	@echo "Upgrading InvenioRDM..."
	@echo ""
	@echo "Step 1/3: Rebuilding and loading image..."
	@$(MAKE) load-image ENV=$(ENV)
	@echo ""
	@echo "Step 2/3: Upgrading Helm release..."
	@$(MAKE) deploy-helm ENV=$(ENV)
	@echo ""
	@echo "Step 3/3: Restarting pods to pick up new image..."
	@$(MAKE) restart ENV=$(ENV)
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

logs: check ## Tail web pod logs
	@echo "Tailing web pod logs (Ctrl+C to stop)..."
	@kubectl logs -f -l app.kubernetes.io/component=web -n $(NAMESPACE) --all-containers=true --tail=100

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
	echo "Step 1/3: Deleting all existing records..."; \
	openscience-tools --base-url http://localhost:8080 --token "$$TOKEN" cleanup --confirm; \
	echo ""; \
	echo "Step 2/3: Importing Lens.org publications..."; \
	FILE=$${FILE:-../openscience_tools/openscience_tools/sources/lens/data/publications.json}; \
	OPTS=$${OPTS:-}; \
	openscience-tools --base-url http://localhost:8080 --token "$$TOKEN" import-lens --file "$$FILE" $$OPTS; \
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
	echo "  Access at: http://localhost:8080"

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

install: ## Complete setup: check tools, generate .env.$(ENV), create k3d cluster
	@echo "UNESCO Open Science Portal - Installation"
	@echo "=========================================="
	@echo "Environment: $(ENV)"
	@echo ""
	@echo "[1/3] Checking required tools..."
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
	@echo "[2/3] Setting up .env.$(ENV)..."
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
		echo "[3/3] Setting up k3d cluster..."; \
		if k3d cluster list | grep -q "$(K3D_CLUSTER_NAME)"; then \
			echo "  k3d cluster '$(K3D_CLUSTER_NAME)' already exists."; \
			echo "  ✓ Using existing cluster"; \
		else \
			echo "  Creating k3d cluster '$(K3D_CLUSTER_NAME)'..."; \
			k3d cluster create $(K3D_CLUSTER_NAME) \
				--port "8080:80@loadbalancer" \
				--port "8443:443@loadbalancer" \
				--agents 0; \
			echo "  ✓ k3d cluster created"; \
		fi; \
	else \
		echo "[3/3] Skipping k3d setup (ENV=$(ENV))"; \
	fi
	@echo ""
	@echo "=========================================="
	@echo "Installation complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Review/edit .env.$(ENV) if needed"
	@echo "  2. make load-image ENV=$(ENV)"
	@echo "  3. make deploy ENV=$(ENV)"
	@echo ""
	@if [ "$(ENV)" = "local" ]; then \
		echo "Access will be available at: http://localhost:8080"; \
	fi
