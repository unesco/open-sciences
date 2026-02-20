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

.PHONY: help install check setup-k3d env-check deploy deploy-services deploy-secrets deploy-helm \
        init-app init-minio create-admin up stop \
        backup restore list-backups deploy-backup-cronjob \
        destroy reset-lens rebuild-index render-config build-image load-image

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
BACKUP_SCHEDULE ?= 0 2 * * *
BACKUP_RETENTION_COUNT ?= 7
BACKUP_RETENTION_DAYS ?=
BACKUP_PATH ?= backups/$(ENV)
BACKUP_STORAGE_SIZE ?= 100Gi

# Export variables for envsubst in backup-cronjob.yaml
export BACKUP_SCHEDULE BACKUP_RETENTION_COUNT BACKUP_RETENTION_DAYS BACKUP_PATH BACKUP_STORAGE_SIZE

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

help: ## Show this help
	@echo ""
	@echo "UNESCO Open Science Portal - Kubernetes Deployment"
	@echo "===================================================="
	@echo "  Active environment: ENV=$(ENV)  (.env.$(ENV))"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
	@echo ""

check: ## Verify k3s, kubectl, helm are installed
	@echo "Checking required tools..."
	@command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl not found."; exit 1; }
	@command -v helm    >/dev/null 2>&1 || { echo "ERROR: helm not found."; exit 1; }
	@kubectl get nodes  >/dev/null 2>&1 || { echo "ERROR: Cannot reach k3s cluster. Is k3s running?"; exit 1; }
	@echo "  kubectl: OK"
	@echo "  helm:    OK"
	@echo "  k3s:     $$(kubectl get nodes -o jsonpath='{.items[0].status.nodeInfo.kubeletVersion}')"
	@echo "All checks passed."

setup-k3d: ## Create k3d cluster for local development
	@if [ "$(ENV)" != "local" ]; then \
		echo "Skipping k3d setup (ENV=$(ENV))"; \
		exit 0; \
	fi
	@echo "Setting up k3d cluster..."
	@if k3d cluster list | grep -q "$(K3D_CLUSTER_NAME)"; then \
		echo "  k3d cluster '$(K3D_CLUSTER_NAME)' already exists."; \
		echo "  ✓ Using existing cluster"; \
	else \
		echo "  Creating k3d cluster '$(K3D_CLUSTER_NAME)'..."; \
		mkdir -p backups/k3d; \
		k3d cluster create $(K3D_CLUSTER_NAME) \
			--port "80:80@loadbalancer" \
			--port "8443:443@loadbalancer" \
			--volume "$$(pwd)/backups/k3d:/backups@server:0" \
			--agents 0; \
		echo "  ✓ k3d cluster created with backup volume mounted"; \
	fi

env-check: ## Verify environment config files exist and have required values
	@if [ ! -f .env.$(ENV) ]; then \
		echo "ERROR: .env.$(ENV) not found!"; \
		echo "  Run: make install ENV=$(ENV)"; \
		exit 1; \
	fi
	@echo "Checking required secrets..."
	@missing=0; \
	for var in SECRET_KEY SECURITY_LOGIN_SALT POSTGRES_PASSWORD RABBITMQ_PASSWORD MINIO_ROOT_PASSWORD S3_SECRET_ACCESS_KEY; do \
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

install-helm: check env-check deploy-secrets deploy-services init-minio deploy-helm
	@echo "Helm installation complete."

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

deploy-services: check ## Deploy external services (DB, cache, search, queue)
	@echo "Deploying external services..."
	@kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@kubectl config set-context --current --namespace=$(NAMESPACE)
	@kubectl apply -f external-services.yaml -n $(NAMESPACE)
	@echo ""
	@echo "Waiting for services to be ready (up to 3 minutes)..."
	@kubectl wait --for=condition=ready pod -l app=redis        -n $(NAMESPACE) --timeout=180s 2>/dev/null || echo "  WARN: Redis not ready yet"
	@kubectl wait --for=condition=ready pod -l app=postgresql    -n $(NAMESPACE) --timeout=180s 2>/dev/null || echo "  WARN: PostgreSQL not ready yet"
	@kubectl wait --for=condition=ready pod -l app=rabbitmq      -n $(NAMESPACE) --timeout=180s 2>/dev/null || echo "  WARN: RabbitMQ not ready yet"
	@kubectl wait --for=condition=ready pod -l app=opensearch    -n $(NAMESPACE) --timeout=180s 2>/dev/null || echo "  WARN: OpenSearch not ready yet"
	@kubectl wait --for=condition=ready pod -l app=minio         -n $(NAMESPACE) --timeout=180s 2>/dev/null || echo "  WARN: MinIO not ready yet"
	@echo ""
	@echo "External services deployed."
	@kubectl get pods -n $(NAMESPACE)

init-minio: check ## Initialize MinIO bucket (create 'default' bucket)
	@echo "Initializing MinIO bucket..."
	@kubectl apply -f minio-init.yaml -n $(NAMESPACE)
	@echo "Waiting for MinIO initialization job to complete..."
	@kubectl wait --for=condition=complete --timeout=120s job/minio-create-bucket -n $(NAMESPACE) 2>/dev/null || echo "  WARN: MinIO init job not completed yet"
	@echo "MinIO bucket initialized."

deploy-secrets: check env-check render-config ## Create K8s Secrets (service env vars + invenio.cfg file)
	@echo "Creating Kubernetes Secrets..."
	@kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@echo ""
	@echo "[1/2] Creating service credentials Secret (env vars)..."
	@kubectl create secret generic $(HELM_RELEASE)-secrets \
		--from-literal=POSTGRES_USER='$(POSTGRES_USER)' \
		--from-literal=POSTGRES_PASSWORD='$(POSTGRES_PASSWORD)' \
		--from-literal=POSTGRES_DB='$(POSTGRES_DB)' \
		--from-literal=RABBITMQ_USER='$(RABBITMQ_USER)' \
		--from-literal=RABBITMQ_PASSWORD='$(RABBITMQ_PASSWORD)' \
		--from-literal=MINIO_ROOT_USER='$(MINIO_ROOT_USER)' \
		--from-literal=MINIO_ROOT_PASSWORD='$(MINIO_ROOT_PASSWORD)' \
		--from-literal=S3_ENDPOINT_URL='$(S3_ENDPOINT_URL)' \
		--from-literal=S3_ACCESS_KEY_ID='$(S3_ACCESS_KEY_ID)' \
		--from-literal=S3_SECRET_ACCESS_KEY='$(S3_SECRET_ACCESS_KEY)' \
		--from-literal=S3_REGION_NAME='$(S3_REGION_NAME)' \
		--from-literal=SECRET_KEY='$(SECRET_KEY)' \
		--from-literal=SECURITY_LOGIN_SALT='$(SECURITY_LOGIN_SALT)' \
		--from-literal=SQLALCHEMY_DATABASE_URI="postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgresql:5432/$(POSTGRES_DB)" \
		--from-literal=CELERY_BROKER_URL="amqp://$(RABBITMQ_USER):$(RABBITMQ_PASSWORD)@rabbitmq:5672/" \
		--from-literal=CACHE_REDIS_URL="redis://redis:6379/0" \
		--namespace=$(NAMESPACE) \
		--dry-run=client -o yaml | kubectl apply -f -
	@echo "  ✓ Secret created: $(HELM_RELEASE)-secrets (16 keys)"
	@echo ""
	@echo "[2/2] Creating InvenioRDM configuration Secret (invenio.cfg file)..."
	@if [ ! -f ../invenio.cfg ]; then \
		echo "ERROR: invenio.cfg not found. Run 'make render-config' first."; \
		exit 1; \
	fi
	@kubectl create secret generic $(HELM_RELEASE)-config \
		--from-file=invenio.cfg=../invenio.cfg \
		--namespace=$(NAMESPACE) \
		--dry-run=client -o yaml | kubectl apply -f -
	@echo "  ✓ Secret created: $(HELM_RELEASE)-config ($(shell wc -c < ../invenio.cfg) bytes)"
	@echo ""
	@echo "All Secrets deployed."
	@echo ""

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

init-app: check ## Reinitialize database, indices, vocabularies (manual operation)
	@echo "Reinitializing InvenioRDM application..."
	@echo "Waiting for web pod..."
	@kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=web \
		-n $(NAMESPACE) --timeout=300s 2>/dev/null || \
		{ echo "ERROR: Web pod not ready. Check with k9s or kubectl get pods -n $(NAMESPACE)"; exit 1; }
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
	echo ""; \
	echo "Step 7/7: Loading CMS fixtures (header, footer, static pages)..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "invenio cms load-fixtures" ; \
	echo ""; \
	echo "Reinitialization complete."

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

render-config: env-check ## Render invenio.cfg from template using current environment
	@echo "Rendering invenio.cfg (ENV=$(ENV))..."
	@envsubst < ../invenio.cfg.template > ../invenio.cfg
	@echo "  ✓ invenio.cfg generated ($(shell wc -c < ../invenio.cfg) bytes)"

build-image: render-config ## Build Docker image (renders config first)
	@echo "Building Docker image: $(IMAGE)"
	@echo "  Note: invenio.cfg will be mounted as Secret at runtime"
	@docker build -t $(IMAGE) -f Dockerfile ..

load-image: build-image ## Build image and load into k3d cluster
	@echo "Loading image into k3d cluster..."
	@k3d image import $(IMAGE) --cluster $(K3D_CLUSTER_NAME)
	@echo "Image loaded into k3d cluster: $(K3D_CLUSTER_NAME)"

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

backup: check env-check ## Create a backup of PostgreSQL, OpenSearch, and files
	@echo "Creating backup..."
	@if [ ! -d "$(BACKUP_PATH)" ]; then \
		mkdir -p "$(BACKUP_PATH)"; \
		echo "  Created backup directory: $(BACKUP_PATH)"; \
	fi
	@NAMESPACE=$(NAMESPACE) BACKUP_PATH=$(BACKUP_PATH) bash scripts/backup.sh
	@echo ""
	@echo "Running retention cleanup (keeping last $(BACKUP_RETENTION_COUNT) backups)..."
	@BACKUP_PATH=$(BACKUP_PATH) BACKUP_RETENTION_COUNT=$(BACKUP_RETENTION_COUNT) BACKUP_RETENTION_DAYS=$(BACKUP_RETENTION_DAYS) bash scripts/retention.sh

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
	@echo "Backups in $(BACKUP_PATH):"
	@ls -1t "$(BACKUP_PATH)" 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}$$' || echo "  (none)"

deploy-backup-cronjob: check env-check ## Deploy automated backup CronJob (staging/production)
	@echo "Deploying backup CronJob..."
	@echo ""
	@echo "[1/3] Creating ConfigMap from bash scripts..."
	@kubectl create configmap backup-scripts \
		--from-file=backup.sh=scripts/backup.sh \
		--from-file=retention.sh=scripts/retention.sh \
		--namespace=$(NAMESPACE) \
		--dry-run=client -o yaml | kubectl apply -f -
	@echo ""
	@echo "[2/3] Deploying CronJob, ServiceAccount, and storage..."
	@if [ "$(ENV)" = "local" ]; then \
		echo "  Using hostPath for backup storage (local environment)"; \
		envsubst < backup-cronjob.yaml > /tmp/backup-cronjob-rendered.yaml; \
	else \
		echo "  Using PVC for backup storage ($(ENV) environment)"; \
		envsubst < backup-cronjob.yaml | \
			sed '/hostPath:/,/type: DirectoryOrCreate/d' | \
			sed 's/# persistentVolumeClaim:/persistentVolumeClaim:/' | \
			sed 's/#   claimName: backup-pvc/  claimName: backup-pvc/' \
			> /tmp/backup-cronjob-rendered.yaml; \
	fi
	@kubectl apply -f /tmp/backup-cronjob-rendered.yaml
	@rm -f /tmp/backup-cronjob-rendered.yaml
	@echo ""
	@echo "[3/3] Backup CronJob deployed successfully!"
	@echo ""
	@echo "Schedule:  $(BACKUP_SCHEDULE)"
	@echo "Retention: $(BACKUP_RETENTION_COUNT) backups (count-based)"
	@echo ""
	@kubectl get cronjob -n $(NAMESPACE)

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
	echo "Revoking temporary token..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- \
		invenio tokens delete "$$TOKEN" 2>/dev/null || true; \
	echo ""; \
	echo "Step 3/3: Rebuilding search indices..."; \
	$(MAKE) rebuild-index ENV=$(ENV); \
	echo ""; \
	echo "Reset complete!"; \
	echo "  Access at: http://localhost"

rebuild-index: check ## Rebuild OpenSearch indices (fix DB/search sync issues)
	@echo "Rebuilding OpenSearch indices..."
	@echo ""
	@WEB_POD=$$(kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}'); \
	if [ -z "$$WEB_POD" ]; then \
		echo "ERROR: Web pod not found"; \
		exit 1; \
	fi; \
	echo "Step 1/5: Destroying existing indices..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "echo y | invenio index destroy --force" 2>/dev/null || true; \
	echo ""; \
	echo "Step 2/5: Creating fresh indices..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- invenio index init 2>/dev/null || true; \
	echo ""; \
	echo "Step 3/5: Initializing custom fields..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- invenio rdm-records custom-fields init 2>/dev/null || true; \
	echo ""; \
	echo "Step 4/5: Reindexing all records and vocabularies..."; \
	kubectl exec -n $(NAMESPACE) $$WEB_POD -c web -- bash -c "echo y | invenio rdm-records rebuild-index" 2>/dev/null || true; \
	echo ""; \
	echo "Step 5/5: Waiting for worker to process indexing queue (60s)..."; \
	sleep 60; \
	echo ""; \
	echo "Index rebuild complete!"

destroy: check ## Remove EVERYTHING from the cluster (DESTRUCTIVE!)
	@echo ""
	@echo "!!! WARNING: This will permanently delete:"
	@echo "    - All InvenioRDM data"
	@echo "    - Database and search indices"
	@echo "    - Uploaded files"
	@if [ "$(ENV)" = "local" ]; then \
		echo "    - k3d cluster '$(K3D_CLUSTER_NAME)'"; \
	fi
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
		if [ "$(ENV)" = "local" ]; then \
			echo "Destroying k3d cluster..."; \
			k3d cluster delete $(K3D_CLUSTER_NAME) 2>/dev/null || true; \
			echo "✓ k3d cluster removed"; \
		fi; \
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
	@echo "[1/5] Setting up k3d cluster (if ENV=local)..."
	@$(MAKE) setup-k3d ENV=$(ENV)
	@echo ""
	@echo "[2/5] Checking cluster and tools..."
	@$(MAKE) check ENV=$(ENV)
	@echo ""
	@echo "[3/5] Rendering invenio.cfg from template..."
	@$(MAKE) render-config ENV=$(ENV)
	@echo ""
	@echo "[4/5] Building and loading Docker image..."
	@$(MAKE) load-image ENV=$(ENV)
	@echo ""
	@echo "[5/5] Deploying services and Helm chart..."
	@$(MAKE) install-helm ENV=$(ENV)
	@echo ""
	@echo "Initializing application..."
	@$(MAKE) init-app ENV=$(ENV)
	@$(MAKE) create-admin ENV=$(ENV)
	@echo ""
	@echo "Deploying backup CronJob..."
	@$(MAKE) deploy-backup-cronjob ENV=$(ENV)
	@echo ""
	@echo "  Installation complete!  (ENV=$(ENV))"
	@echo ""
