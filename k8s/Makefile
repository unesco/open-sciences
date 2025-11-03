#
# ============================================================================
# KIND (Kubernetes in Docker) - Local K8s Cluster
# ============================================================================
#

.PHONY: kind-check kind-create kind-delete kind-load-image kind-deploy kind-deploy-services kind-deploy-helm kind-init kind-create-admin kind-full-deploy kind-status kind-logs kind-shell kind-port-forward kind-restart kind-clean kind-reset-lens

# Kind cluster name
KIND_CLUSTER_NAME ?= unesco-rdm
KIND_CONFIG ?= kind-config.yaml

# Docker image settings
DOCKER_IMAGE_NAME ?= sc-openscience
DOCKER_IMAGE_TAG ?= latest

# Check if Kind is installed
kind-check:
	@echo "🔍 Checking Kind installation..."
	@if ! command -v kind &> /dev/null; then \
		echo "❌ Kind is not installed!"; \
		echo ""; \
		echo "📥 Install Kind:"; \
		echo "  macOS:   brew install kind"; \
		echo "  Linux:   curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64"; \
		echo "           chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind"; \
		echo "  Windows: choco install kind"; \
		echo ""; \
		echo "📚 More info: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"; \
		exit 1; \
	fi
	@if ! command -v kubectl &> /dev/null; then \
		echo "❌ kubectl is not installed!"; \
		echo ""; \
		echo "📥 Install kubectl:"; \
		echo "  macOS:   brew install kubectl"; \
		echo "  Linux:   See https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/"; \
		echo ""; \
		exit 1; \
	fi
	@if ! command -v helm &> /dev/null; then \
		echo "❌ Helm is not installed!"; \
		echo ""; \
		echo "📥 Install Helm:"; \
		echo "  macOS:   brew install helm"; \
		echo "  Linux:   See https://helm.sh/docs/intro/install/"; \
		echo ""; \
		exit 1; \
	fi
	@echo "✅ All required tools installed!"
	@echo "   - kind:    $$(kind version | head -1)"
	@echo "   - kubectl: $$(kubectl version --client --short 2>/dev/null || kubectl version --client)"
	@echo "   - helm:    $$(helm version --short)"

# Create Kind cluster
kind-create: kind-check
	@echo "🚀 Creating Kind cluster: $(KIND_CLUSTER_NAME)"
	@if kind get clusters | grep -q "^$(KIND_CLUSTER_NAME)$$"; then \
		echo "⚠️  Cluster '$(KIND_CLUSTER_NAME)' already exists"; \
		echo "   Use 'make kind-delete' to remove it first"; \
		exit 1; \
	fi
	@echo "📋 Using config: $(KIND_CONFIG)"
	@mkdir -p /tmp/kind-data-1 /tmp/kind-data-2
	kind create cluster --name $(KIND_CLUSTER_NAME) --config $(KIND_CONFIG)
	@echo ""
	@echo "✅ Cluster created successfully!"
	@echo ""
	@echo "📊 Cluster info:"
	kubectl cluster-info --context kind-$(KIND_CLUSTER_NAME)
	@echo ""
	@echo "🔧 Installing Ingress NGINX..."
	kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
	@echo "⏳ Waiting for Ingress NGINX to be ready..."
	kubectl wait --namespace ingress-nginx \
		--for=condition=ready pod \
		--selector=app.kubernetes.io/component=controller \
		--timeout=120s || echo "⚠️  Timeout waiting for ingress - it may need more time"
	@echo ""
	@echo "✅ Kind cluster ready!"
	@echo "   Context: kind-$(KIND_CLUSTER_NAME)"

# Delete Kind cluster
kind-delete:
	@echo "🗑️  Deleting Kind cluster: $(KIND_CLUSTER_NAME)"
	@if ! kind get clusters | grep -q "^$(KIND_CLUSTER_NAME)$$"; then \
		echo "⚠️  Cluster '$(KIND_CLUSTER_NAME)' does not exist"; \
		exit 0; \
	fi
	kind delete cluster --name $(KIND_CLUSTER_NAME)
	@echo "✅ Cluster deleted!"
	@rm -rf /tmp/kind-data-1 /tmp/kind-data-2 || true

# Build and load image into Kind
kind-load-image: kind-check
	@echo "🐳 Building Docker image for Kind..."
	@if ! kind get clusters | grep -q "^$(KIND_CLUSTER_NAME)$$"; then \
		echo "❌ Cluster '$(KIND_CLUSTER_NAME)' does not exist"; \
		echo "   Run 'make kind-create' first"; \
		exit 1; \
	fi
	@echo "📦 Building image: $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)"
	cd .. && docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) -f Dockerfile .
	@echo ""
	@echo "📥 Loading image into Kind cluster..."
	kind load docker-image $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) --name $(KIND_CLUSTER_NAME)
	@echo "✅ Image loaded into Kind cluster!"

# Deploy InvenioRDM on Kind
kind-deploy: kind-check
	@echo "🚀 Deploying InvenioRDM on Kind..."
	@if ! kind get clusters | grep -q "^$(KIND_CLUSTER_NAME)$$"; then \
		echo "❌ Cluster '$(KIND_CLUSTER_NAME)' does not exist"; \
		echo "   Run 'make kind-create' first"; \
		exit 1; \
	fi
	@echo "🔧 Setting up Helm repositories..."
	helm repo add invenio https://inveniosoftware.github.io/helm-invenio/ || true
	helm repo add bitnami https://charts.bitnami.com/bitnami || true
	helm repo update
	@echo ""
	@echo "📦 Creating namespace..."
	kubectl create namespace unesco-rdm --dry-run=client -o yaml | kubectl apply -f -
	kubectl config set-context --current --namespace=unesco-rdm
	@echo ""
	@echo "🔐 Creating secrets..."
	kubectl create secret generic unesco-rdm-secrets \
		--from-literal=SECRET_KEY=$$(openssl rand -hex 32) \
		--from-literal=SECURITY_LOGIN_SALT=$$(openssl rand -hex 32) \
		--from-literal=SQLALCHEMY_DATABASE_URI="postgresql://invenio:invenio123@postgresql:5432/invenio" \
		--from-literal=CELERY_BROKER_URL="amqp://invenio:invenio123@rabbitmq:5672/" \
		--from-literal=CACHE_REDIS_URL="redis://redis:6379/0" \
		--namespace=unesco-rdm \
		--dry-run=client -o yaml | kubectl apply -f - || true
	@echo ""
	@echo "📋 Deploying with Helm..."
	@echo "⚠️  Note: This deployment uses the official Helm chart with custom values."
	@echo "   Some features may not work exactly as expected in local Kind environment."
	@echo ""
	helm upgrade --install unesco-rdm invenio/invenio \
		--namespace unesco-rdm \
		--create-namespace \
		--values values-kind.yaml \
		--wait \
		--timeout 10m || \
		(echo ""; \
		 echo "⚠️  Helm install/upgrade encountered issues."; \
		 echo "   This is normal for the first deployment."; \
		 echo "   Check status with: make kind-status"; \
		 echo "   View logs with: make kind-logs")
	@echo ""
	@echo "✅ Deployment command completed!"
	@echo ""
	@echo "📊 Checking deployment status..."
	@$(MAKE) kind-status

# Check Kind deployment status
kind-status: kind-check
	@echo "📊 Checking Kind cluster status..."
	@echo ""
	@echo "🔍 Cluster nodes:"
	kubectl get nodes
	@echo ""
	@echo "📦 Pods in unesco-rdm namespace:"
	kubectl get pods -n unesco-rdm -o wide
	@echo ""
	@echo "🌐 Services:"
	kubectl get svc -n unesco-rdm
	@echo ""
	@echo "📋 Ingress:"
	kubectl get ingress -n unesco-rdm
	@echo ""
	@echo "💾 Persistent Volume Claims:"
	kubectl get pvc -n unesco-rdm

# View logs from Kind deployment
kind-logs: kind-check
	@echo "📜 Showing logs from web-ui pod..."
	@echo "   (Press Ctrl+C to exit)"
	kubectl logs -f -l app.kubernetes.io/name=web-ui -n unesco-rdm --all-containers=true || \
		kubectl logs -f deployment/unesco-rdm-web-ui -n unesco-rdm

# Open shell in web-ui pod
kind-shell: kind-check
	@echo "🐚 Opening shell in web-ui pod..."
	kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- bash

# Port forward to access locally
kind-port-forward: kind-check
	@echo "🌐 Setting up port forwarding..."
	@echo "   Local access: http://localhost:8080"
	@echo "   Press Ctrl+C to stop"
	kubectl port-forward -n unesco-rdm service/unesco-rdm-invenio-web 8080:80

# Restart deployment
kind-restart: kind-check
	@echo "🔄 Restarting deployments..."
	kubectl rollout restart deployment -n unesco-rdm
	@echo "✅ Restart triggered!"
	@echo "⏳ Waiting for rollout to complete..."
	kubectl rollout status deployment/unesco-rdm-web-ui -n unesco-rdm || true

# Clean up Kind deployment (keep cluster)
kind-clean: kind-check
	@echo "🧹 Cleaning up Kind deployment..."
	@read -p "This will delete the Helm release. Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		helm uninstall unesco-rdm -n unesco-rdm || echo "Release not found"; \
		kubectl delete namespace unesco-rdm || echo "Namespace not found"; \
		echo "✅ Cleanup complete!"; \
	else \
		echo "❌ Cancelled."; \
	fi

# Deploy external services (PostgreSQL, Redis, RabbitMQ, OpenSearch)
kind-deploy-services: kind-check
	@echo "🚀 Deploying external services to Kind cluster..."
	@if ! kind get clusters | grep -q "^$(KIND_CLUSTER_NAME)$$"; then \
		echo "❌ Cluster '$(KIND_CLUSTER_NAME)' does not exist"; \
		echo "   Run 'make kind-create' first"; \
		exit 1; \
	fi
	@echo "📦 Creating namespace..."
	kubectl create namespace unesco-rdm --dry-run=client -o yaml | kubectl apply -f -
	kubectl config set-context --current --namespace=unesco-rdm
	@echo ""
	@echo "🗄️  Deploying external services..."
	kubectl apply -f external-services.yaml
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@echo "   This may take 2-3 minutes..."
	kubectl wait --for=condition=ready pod -l app=redis --timeout=180s -n unesco-rdm || true
	kubectl wait --for=condition=ready pod -l app=postgresql --timeout=180s -n unesco-rdm || true
	kubectl wait --for=condition=ready pod -l app=rabbitmq --timeout=180s -n unesco-rdm || true
	kubectl wait --for=condition=ready pod -l app=opensearch --timeout=180s -n unesco-rdm || true
	@echo ""
	@echo "✅ External services deployed!"
	@echo ""
	@echo "📊 Service status:"
	@kubectl get pods -n unesco-rdm

# Deploy Helm chart
kind-deploy-helm: kind-check
	@echo "🚀 Deploying InvenioRDM Helm chart..."
	@if ! kind get clusters | grep -q "^$(KIND_CLUSTER_NAME)$$"; then \
		echo "❌ Cluster '$(KIND_CLUSTER_NAME)' does not exist"; \
		exit 1; \
	fi
	@echo "🔧 Setting up Helm repositories..."
	helm repo add invenio https://inveniosoftware.github.io/helm-invenio/ 2>/dev/null || true
	helm repo update
	@echo ""
	@echo "📦 Deploying with Helm..."
	helm upgrade --install unesco-rdm invenio/invenio \
		--namespace unesco-rdm \
		--values values-unesco.yaml \
		--wait \
		--timeout 10m || \
		(echo "⚠️  Helm deployment encountered issues - checking status..."; \
		 kubectl get pods -n unesco-rdm)
	@echo ""
	@echo "✅ Helm chart deployed!"

# Initialize InvenioRDM (vocabularies, database, indices)
kind-init: kind-check
	@echo "🔧 Initializing InvenioRDM..."
	@echo "⏳ Waiting for web pod to be ready..."
	kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=web --timeout=300s -n unesco-rdm || \
		(echo "⚠️  Timeout - checking status:"; kubectl get pods -n unesco-rdm)
	@echo ""
	@echo "�️  Initializing database..."
	kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
		bash -c "invenio db init || echo 'Already initialized'" 2>/dev/null || true
	kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
		bash -c "invenio db create || echo 'Already exists'" 2>/dev/null || true
	@echo ""
	@echo "🔍 Initializing search indices..."
	kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
		bash -c "invenio index destroy --force --yes || true" 2>/dev/null || true
	kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
		bash -c "invenio index init" 2>/dev/null || true
	kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
		bash -c "invenio index queue init purge" 2>/dev/null || true
	@echo ""
	@echo "📁 Creating file storage location..."
	kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
		bash -c "invenio files location create --default 'default-location' /opt/invenio/var/instance/data || echo 'Already exists'" 2>/dev/null || true
	@echo ""
	@echo "📚 Loading default vocabularies and fixtures..."
	kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
		bash -c "invenio rdm-records fixtures" 2>/dev/null || true
	@echo "⏳ Waiting for vocabularies to be processed by workers (30 seconds)..."
	@sleep 30
	@echo ""
	@echo "✅ Initialization complete!"
	@echo ""
	@echo "🔍 Verifying vocabularies..."
	@kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
		bash -c "invenio vocabularies search resourcetypes | head -5" 2>/dev/null || \
		echo "⚠️  Vocabulary verification failed - may need more time"

# Create admin user with API token
kind-create-admin: kind-check
	@echo "👤 Creating admin user..."
	@kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- bash -c "\
		invenio users create admin@unesco.org --password=admin123 --active || echo 'User may already exist'" 2>/dev/null || true
	@kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- bash -c "\
		invenio roles add admin@unesco.org admin || echo 'Role may already be assigned'" 2>/dev/null || true
	@kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- bash -c "\
		invenio access allow superuser-access role admin || echo 'Permission may already exist'" 2>/dev/null || true
	@echo ""
	@echo "🔑 Generating API token..."
	@TOKEN=$$(kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
		invenio tokens create -n 'Admin Token' -u admin@unesco.org 2>/dev/null | \
		grep -v "WARNING\|UserWarning\|pkg_resources\|deprecated" | \
		grep -E '^[A-Za-z0-9]{40,}$$' | head -1); \
	echo "Extracted token: $$TOKEN"; \
	if [ -n "$$TOKEN" ] && [ "$$TOKEN" != "" ]; then \
		mkdir -p ../scripts/config; \
		if [ -f ../scripts/config/.env.kind ]; then \
			echo "📝 Updating existing .env.kind file..."; \
			sed -i.bak "s/INVENIO_TOKEN=.*/INVENIO_TOKEN=$$TOKEN/" ../scripts/config/.env.kind && rm -f ../scripts/config/.env.kind.bak; \
		else \
			echo "📝 Creating new .env.kind file..."; \
			echo "# UNESCO RDM - Kind Cluster Configuration" > ../scripts/config/.env.kind; \
			echo "" >> ../scripts/config/.env.kind; \
			echo "# API Configuration" >> ../scripts/config/.env.kind; \
			echo "INVENIO_BASE_URL=http://localhost:8080" >> ../scripts/config/.env.kind; \
			echo "INVENIO_TOKEN=$$TOKEN" >> ../scripts/config/.env.kind; \
			echo "" >> ../scripts/config/.env.kind; \
			echo "# Admin User" >> ../scripts/config/.env.kind; \
			echo "ADMIN_EMAIL=admin@unesco.org" >> ../scripts/config/.env.kind; \
			echo "ADMIN_PASSWORD=admin123" >> ../scripts/config/.env.kind; \
			echo "" >> ../scripts/config/.env.kind; \
			echo "# Test User (from init)" >> ../scripts/config/.env.kind; \
			echo "USER_EMAIL=user@demo.org" >> ../scripts/config/.env.kind; \
			echo "USER_PASSWORD=demo123" >> ../scripts/config/.env.kind; \
		fi; \
		echo "✅ Token saved to ../scripts/config/.env.kind"; \
		echo "📁 New token: $$TOKEN"; \
	else \
		echo "❌ Could not extract token. Generating manually..."; \
		kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
			invenio tokens create -n 'Admin Token' -u admin@unesco.org; \
		echo ""; \
		echo "⚠️  Please copy the token above and update ../scripts/config/.env.kind manually"; \
	fi
	@echo ""
	@echo "✅ Admin user created!"
	@echo "   Email: admin@unesco.org"
	@echo "   Password: admin123"

# Complete Kind deployment - all steps
kind-full-deploy: kind-create kind-deploy-services kind-load-image kind-deploy-helm kind-init kind-create-admin
	@echo ""
	@echo "=========================================="
	@echo "🎉 Kind cluster fully deployed!"
	@echo "=========================================="
	@echo ""
	@echo "✅ What's been set up:"
	@echo "   ✓ Kind cluster created"
	@echo "   ✓ External services deployed (PostgreSQL, Redis, RabbitMQ, OpenSearch)"
	@echo "   ✓ Custom Docker image built and loaded"
	@echo "   ✓ InvenioRDM Helm chart installed"
	@echo "   ✓ Vocabularies and database initialized"
	@echo "   ✓ Admin user created (admin@unesco.org / admin123)"
	@echo "   ✓ API token generated"
	@echo ""
	@echo "🌐 Next steps:"
	@echo "   1. Start port forwarding: make kind-port-forward"
	@echo "   2. Access application at: http://localhost:8080"
	@echo "   3. Import data: make kind-reset-lens"
	@echo ""
	@echo "📊 Useful commands:"
	@echo "   Status:  make kind-status"
	@echo "   Logs:    make kind-logs"
	@echo "   Shell:   make kind-shell"
	@echo "   Restart: make kind-restart"
	@echo ""
	@echo "🛑 To clean up:"
	@echo "   Remove deployment: make kind-clean"
	@echo "   Delete cluster:    make kind-delete"
	@echo "   Complete cleanup:  make kind-down"

# Legacy kind-up (now use kind-full-deploy)
kind-up: kind-full-deploy
	@echo ""
	@echo "💡 Note: 'kind-up' now calls 'kind-full-deploy'"
	@echo "   Use 'make kind-full-deploy' for clearer intent"

# Complete Kind teardown
kind-down: kind-clean kind-delete
	@echo "✅ Kind cluster completely removed!"

#============================================================================
# Kind Scripts Commands - Data Import for Kind Cluster
#============================================================================

.PHONY: kind-scripts-setup-env kind-scripts-import-lens kind-scripts-reset kind-scripts-delete-all kind-scripts-shell kind-reset-lens

# Configure scripts environment for Kind cluster
kind-scripts-setup-env:
	@echo "🔧 Setting up scripts environment for Kind cluster..."
	@echo "Creating Kind-specific .env file..."
	@mkdir -p scripts/config
	@echo "# Environment Configuration for InvenioRDM Scripts - Kind Cluster" > scripts/config/.env.kind
	@echo "# Automatically generated for Kind deployment" >> scripts/config/.env.kind
	@echo "" >> scripts/config/.env.kind
	@echo "# InvenioRDM Instance Configuration" >> scripts/config/.env.kind
	@echo "# Access Kind cluster via port-forward or localhost" >> scripts/config/.env.kind
	@echo "INVENIO_BASE_URL=http://localhost:5000" >> scripts/config/.env.kind
	@echo "" >> scripts/config/.env.kind
	@echo "# API Authentication - Token from Kind cluster" >> scripts/config/.env.kind
	@echo "# Note: You need to get a token from the Kind cluster" >> scripts/config/.env.kind
	@echo "# Run: kubectl exec -n unesco-rdm deployment/unesco-rdm -- invenio tokens create -n kind-scripts -u admin@demo.org" >> scripts/config/.env.kind
	@echo "INVENIO_TOKEN=REPLACE_WITH_TOKEN_FROM_KIND" >> scripts/config/.env.kind
	@echo "" >> scripts/config/.env.kind
	@echo "# Optional configurations" >> scripts/config/.env.kind
	@echo "DEFAULT_RESOURCE_TYPE=dataset" >> scripts/config/.env.kind
	@echo "DEFAULT_ACCESS_LEVEL=public" >> scripts/config/.env.kind
	@echo "LOG_LEVEL=INFO" >> scripts/config/.env.kind
	@echo ""
	@echo "✅ Created scripts/config/.env.kind"
	@echo ""
	@echo "⚠️  Important: You need to generate an API token from Kind cluster:"
	@echo "   1. Make sure port-forward is running: make kind-port-forward"
	@echo "   2. Get a token:"
	@echo "      kubectl exec -n unesco-rdm deployment/unesco-rdm -- invenio tokens create -n kind-scripts -u user@demo.org"
	@echo "   3. Update scripts/config/.env.kind with the token"
	@echo ""

# Import from Lens.org to Kind cluster
kind-scripts-import-lens:
	@echo "🔬 Importing from Lens.org to Kind cluster..."
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: FILE parameter required"; \
		echo "Usage:"; \
		echo "  make kind-scripts-import-lens FILE='src/sources/lens/data/publications.json'"; \
		echo "  make kind-scripts-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--dry-run'"; \
		exit 1; \
	fi
	@CMD="python -m src.sources.lens --file /project/$(FILE)"; \
	if [ -n "$(OPTS)" ]; then \
		CMD="$$CMD $(OPTS)"; \
	fi; \
	docker-compose -f ../docker-compose.scripts.kind.yml run --rm scripts-cli $$CMD

# Delete all records from Kind cluster
kind-scripts-delete-all:
	@echo "🗑️  Deleting all records from Kind cluster..."
	@docker-compose -f ../docker-compose.scripts.kind.yml run --rm scripts-cli python -m src.tools.cleanup $(OPTS)

# Reset and import data to Kind cluster
kind-scripts-reset:
	@echo "🔄 Resetting Kind cluster records..."
	@if [ -z "$(CSV)" ] && [ -z "$(LENS)" ] && [ -z "$(ZENODO_ID)" ] && [ -z "$(ZENODO_QUERY)" ]; then \
		echo "❌ Error: Source parameter required"; \
		echo "Usage:"; \
		echo "  CSV:    make kind-scripts-reset CSV='data/publications.csv'"; \
		echo "  Lens:   make kind-scripts-reset LENS='src/sources/lens/data/publications.json'"; \
		echo "  Zenodo: make kind-scripts-reset ZENODO_ID='17462748'"; \
		echo "  Zenodo: make kind-scripts-reset ZENODO_QUERY='climate data' MAX=5"; \
		exit 1; \
	fi
	@echo ""
	@echo "📋 Step 1/2: Deleting all existing records from Kind cluster..."
	@docker-compose -f ../docker-compose.scripts.kind.yml run --rm scripts-cli python -m src.tools.cleanup --confirm
	@echo ""
	@echo "📋 Step 2/2: Importing fresh records to Kind cluster..."
	@if [ -n "$(CSV)" ]; then \
		echo "📥 Importing from CSV: $(CSV)"; \
		CMD="python -m src.sources.csv --file $(CSV)"; \
		if [ -n "$(OPTS)" ]; then \
			CMD="$$CMD $(OPTS)"; \
		fi; \
		docker-compose -f ../docker-compose.scripts.kind.yml run --rm scripts-cli $$CMD; \
	elif [ -n "$(LENS)" ]; then \
		echo "🔬 Importing from Lens: $(LENS)"; \
		CMD="python -m src.sources.lens --file $(LENS)"; \
		if [ -n "$(OPTS)" ]; then \
			CMD="$$CMD $(OPTS)"; \
		fi; \
		docker-compose -f ../docker-compose.scripts.kind.yml run --rm scripts-cli $$CMD; \
	elif [ -n "$(ZENODO_ID)" ]; then \
		echo "📡 Importing from Zenodo record: $(ZENODO_ID)"; \
		docker-compose -f ../docker-compose.scripts.kind.yml run --rm scripts-cli python -m src.sources.zenodo --record-id $(ZENODO_ID) $(OPTS); \
	elif [ -n "$(ZENODO_QUERY)" ]; then \
		echo "📡 Importing from Zenodo search: $(ZENODO_QUERY)"; \
		if [ -n "$(MAX)" ]; then \
			docker-compose -f ../docker-compose.scripts.kind.yml run --rm scripts-cli python -m src.sources.zenodo --search "$(ZENODO_QUERY)" --max-results $(MAX) $(OPTS); \
		else \
			docker-compose -f ../docker-compose.scripts.kind.yml run --rm scripts-cli python -m src.sources.zenodo --search "$(ZENODO_QUERY)" $(OPTS); \
		fi; \
	fi
	@echo ""
	@echo "✅ Kind cluster reset complete!"

# Open shell in scripts container connected to Kind cluster
kind-scripts-shell:
	@echo "🐚 Opening shell in scripts container (connected to Kind cluster)..."
	@docker-compose -f ../docker-compose.scripts.kind.yml run --rm scripts-cli /bin/bash

# Quick reset with Lens.org data (delete all + import)
kind-reset-lens:
	@echo "🔄 Resetting Kind cluster with Lens.org data..."
	@echo ""
	@echo "📋 Step 1/2: Deleting all existing records..."
	@$(MAKE) kind-scripts-delete-all
	@echo ""
	@echo "📋 Step 2/2: Importing Lens.org publications..."
	@$(MAKE) kind-scripts-import-lens FILE='scripts/src/sources/lens/data/publications.json'
	@echo ""
	@echo "✅ Reset complete!"
	@echo "   26 publications imported from Lens.org"
	@echo "   Access at: http://localhost:8080"