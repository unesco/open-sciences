#!/bin/bash
# Setup script for Kubernetes deployment
# This script creates all necessary secrets and configmaps

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-unesco-rdm}"
REGISTRY="${DOCKER_REGISTRY:-registry.example.com}"
REGISTRY_USER="${REGISTRY_USER:-}"
REGISTRY_PASS="${REGISTRY_PASS:-}"
REGISTRY_EMAIL="${REGISTRY_EMAIL:-}"

echo -e "${GREEN}🚀 UNESCO Science Portal - Kubernetes Setup${NC}"
echo "======================================================"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed${NC}"
    exit 1
fi

# Check if helm is available
if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ helm is not installed${NC}"
    exit 1
fi

# Check cluster connection
echo -e "${YELLOW}📡 Checking cluster connection...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Connected to cluster${NC}"
echo ""

# Create namespace
echo -e "${YELLOW}📦 Creating namespace: ${NAMESPACE}${NC}"
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✅ Namespace created/updated${NC}"
echo ""

# Set context to namespace
kubectl config set-context --current --namespace=${NAMESPACE}

# Create registry credentials
if [ ! -z "$REGISTRY_USER" ] && [ ! -z "$REGISTRY_PASS" ]; then
    echo -e "${YELLOW}🔐 Creating registry credentials...${NC}"
    kubectl create secret docker-registry registry-credentials \
        --docker-server=${REGISTRY} \
        --docker-username=${REGISTRY_USER} \
        --docker-password=${REGISTRY_PASS} \
        --docker-email=${REGISTRY_EMAIL} \
        --namespace=${NAMESPACE} \
        --dry-run=client -o yaml | kubectl apply -f -
    echo -e "${GREEN}✅ Registry credentials created${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping registry credentials (REGISTRY_USER or REGISTRY_PASS not set)${NC}"
fi
echo ""

# Generate random secrets
echo -e "${YELLOW}🔑 Generating application secrets...${NC}"
SECRET_KEY=$(openssl rand -hex 32)
LOGIN_SALT=$(openssl rand -hex 32)
POSTGRES_PASS=$(openssl rand -base64 32)
REDIS_PASS=$(openssl rand -base64 32)
RABBITMQ_PASS=$(openssl rand -base64 32)

# Create application secrets
kubectl create secret generic unesco-rdm-secrets \
    --from-literal=SECRET_KEY=${SECRET_KEY} \
    --from-literal=SECURITY_LOGIN_SALT=${LOGIN_SALT} \
    --from-literal=SQLALCHEMY_DATABASE_URI="postgresql://invenio:${POSTGRES_PASS}@postgresql:5432/invenio" \
    --from-literal=CELERY_BROKER_URL="amqp://invenio:${RABBITMQ_PASS}@rabbitmq:5672/" \
    --from-literal=CACHE_REDIS_URL="redis://:${REDIS_PASS}@redis:6379/0" \
    --from-literal=ACCOUNTS_SESSION_REDIS_URL="redis://:${REDIS_PASS}@redis:6379/1" \
    --from-literal=RATELIMIT_STORAGE_URL="redis://:${REDIS_PASS}@redis:6379/2" \
    --namespace=${NAMESPACE} \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ Application secrets created${NC}"
echo ""

# Create ConfigMap
echo -e "${YELLOW}📋 Creating ConfigMap...${NC}"
kubectl create configmap unesco-rdm-config \
    --from-literal=INVENIO_SITE_NAME="UNESCO Science Portal" \
    --from-literal=INVENIO_SITE_URL="https://openscience.unesco.org" \
    --from-literal=INVENIO_THEME_LOGO="/static/images/unesco-logo.svg" \
    --from-literal=INVENIO_APP_ALLOWED_HOSTS="openscience.unesco.org,localhost" \
    --namespace=${NAMESPACE} \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ ConfigMap created${NC}"
echo ""

# Save secrets to file (for reference - DON'T COMMIT!)
echo -e "${YELLOW}💾 Saving credentials to .k8s-secrets (DO NOT COMMIT!)${NC}"
cat > .k8s-secrets <<EOF
# Kubernetes Secrets - UNESCO Science Portal
# Generated: $(date)
# ⚠️  DO NOT COMMIT THIS FILE TO GIT! ⚠️

NAMESPACE=${NAMESPACE}
SECRET_KEY=${SECRET_KEY}
SECURITY_LOGIN_SALT=${LOGIN_SALT}
POSTGRESQL_PASSWORD=${POSTGRES_PASS}
REDIS_PASSWORD=${REDIS_PASS}
RABBITMQ_PASSWORD=${RABBITMQ_PASS}

# PostgreSQL Connection String
SQLALCHEMY_DATABASE_URI=postgresql://invenio:${POSTGRES_PASS}@postgresql:5432/invenio

# Celery Broker URL
CELERY_BROKER_URL=amqp://invenio:${RABBITMQ_PASS}@rabbitmq:5672/

# Redis URLs
CACHE_REDIS_URL=redis://:${REDIS_PASS}@redis:6379/0
ACCOUNTS_SESSION_REDIS_URL=redis://:${REDIS_PASS}@redis:6379/1
RATELIMIT_STORAGE_URL=redis://:${REDIS_PASS}@redis:6379/2
EOF

chmod 600 .k8s-secrets
echo -e "${GREEN}✅ Credentials saved to .k8s-secrets${NC}"
echo ""

# Add .k8s-secrets to .gitignore
if [ -f .gitignore ]; then
    if ! grep -q ".k8s-secrets" .gitignore; then
        echo ".k8s-secrets" >> .gitignore
        echo -e "${GREEN}✅ Added .k8s-secrets to .gitignore${NC}"
    fi
fi

# Add Helm repository
echo -e "${YELLOW}📚 Adding Helm repositories...${NC}"
helm repo add invenio https://inveniosoftware.github.io/helm-invenio/ || true
helm repo update
echo -e "${GREEN}✅ Helm repositories updated${NC}"
echo ""

# Summary
echo ""
echo "======================================================"
echo -e "${GREEN}✅ Kubernetes setup completed!${NC}"
echo "======================================================"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update k8s/values-production.yaml with your configuration"
echo "2. Update passwords in values file from .k8s-secrets"
echo "3. Deploy with: helm install unesco-rdm invenio/invenio -f k8s/values-production.yaml"
echo "4. Initialize database: kubectl exec -it deployment/unesco-rdm-web-ui -- invenio db init"
echo ""
echo -e "${YELLOW}Credentials saved in: .k8s-secrets${NC}"
echo -e "${RED}⚠️  DO NOT COMMIT .k8s-secrets TO GIT!${NC}"
echo ""
