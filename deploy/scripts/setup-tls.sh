#!/usr/bin/env bash
# ==============================================================================
# setup-tls.sh - Configure TLS with cert-manager and Let's Encrypt
# ==============================================================================
#
# Usage:
#   ./setup-tls.sh [--email EMAIL] [--domain DOMAIN] [--staging]
#
# Options:
#   --email    Email for Let's Encrypt notifications (required)
#   --domain   Domain name (optional, read from .env if not provided)
#   --staging  Use Let's Encrypt staging (for testing, avoids rate limits)
#
# Prerequisites:
#   - k3s installed and running
#   - kubectl configured
#   - Helm installed
# ==============================================================================

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Default values
EMAIL=""
DOMAIN=""
USE_STAGING=false
NAMESPACE="unesco-rdm"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --email)    EMAIL="$2"; shift 2 ;;
        --domain)   DOMAIN="$2"; shift 2 ;;
        --staging)  USE_STAGING=true; shift ;;
        *)          err "Unknown option: $1"; exit 1 ;;
    esac
done

# Load from .env if available
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

if [[ -f "${ENV_FILE}" ]]; then
    log "Loading configuration from .env..."
    source "${ENV_FILE}"
    EMAIL="${EMAIL:-${LETSENCRYPT_EMAIL:-}}"
    DOMAIN="${DOMAIN:-${DOMAIN:-}}"
fi

# Validate
if [[ -z "${EMAIL}" ]]; then
    err "Email is required. Use --email or set LETSENCRYPT_EMAIL in .env"
    exit 1
fi

if [[ -z "${DOMAIN}" ]]; then
    err "Domain is required. Use --domain or set DOMAIN in .env"
    exit 1
fi

echo "============================================="
echo "  TLS Setup with cert-manager"
echo "============================================="
echo ""
echo "  Domain:  ${DOMAIN}"
echo "  Email:   ${EMAIL}"
echo "  Mode:    $(if ${USE_STAGING}; then echo 'STAGING (test)'; else echo 'PRODUCTION'; fi)"
echo ""

# ------------------------------------------------------------------
# Step 1: Install cert-manager
# ------------------------------------------------------------------
log "Step 1/3: Installing cert-manager..."

if kubectl get namespace cert-manager &> /dev/null; then
    warn "  cert-manager namespace exists. Checking installation..."
    if helm list -n cert-manager | grep -q cert-manager; then
        warn "  cert-manager already installed. Skipping."
    else
        helm install cert-manager jetstack/cert-manager \
            --namespace cert-manager \
            --set installCRDs=true \
            --wait
    fi
else
    # Add Jetstack Helm repo
    helm repo add jetstack https://charts.jetstack.io 2>/dev/null || true
    helm repo update > /dev/null 2>&1

    # Install cert-manager with CRDs
    helm install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --set installCRDs=true \
        --wait

    log "  Waiting for cert-manager pods..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager \
        -n cert-manager --timeout=120s
fi

log "  cert-manager installed."

# ------------------------------------------------------------------
# Step 2: Create ClusterIssuer
# ------------------------------------------------------------------
log "Step 2/3: Creating Let's Encrypt ClusterIssuer..."

if ${USE_STAGING}; then
    ISSUER_NAME="letsencrypt-staging"
    ACME_SERVER="https://acme-staging-v02.api.letsencrypt.org/directory"
else
    ISSUER_NAME="letsencrypt-prod"
    ACME_SERVER="https://acme-v02.api.letsencrypt.org/directory"
fi

cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: ${ISSUER_NAME}
spec:
  acme:
    server: ${ACME_SERVER}
    email: ${EMAIL}
    privateKeySecretRef:
      name: ${ISSUER_NAME}-account-key
    solvers:
      - http01:
          ingress:
            class: traefik
EOF

log "  ClusterIssuer '${ISSUER_NAME}' created."

# ------------------------------------------------------------------
# Step 3: Create/Update Ingress with TLS
# ------------------------------------------------------------------
log "Step 3/3: Creating Ingress with TLS..."

cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: unesco-rdm-ingress
  namespace: ${NAMESPACE}
  annotations:
    cert-manager.io/cluster-issuer: ${ISSUER_NAME}
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.tls: "true"
spec:
  tls:
    - hosts:
        - ${DOMAIN}
      secretName: unesco-rdm-tls
  rules:
    - host: ${DOMAIN}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: unesco-rdm-invenio-web
                port:
                  number: 80
EOF

log "  Ingress created with TLS for ${DOMAIN}."

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
echo ""
echo "============================================="
echo -e "  ${GREEN}TLS setup complete!${NC}"
echo "============================================="
echo ""
echo "  Certificate will be issued automatically by Let's Encrypt."
echo "  This may take 1-2 minutes for DNS propagation."
echo ""
echo "  Check certificate status:"
echo "    kubectl get certificate -n ${NAMESPACE}"
echo "    kubectl describe certificate unesco-rdm-tls -n ${NAMESPACE}"
echo ""
echo "  Check issuer status:"
echo "    kubectl get clusterissuer"
echo ""
if ${USE_STAGING}; then
    warn "  You are using STAGING certificates (not trusted by browsers)."
    warn "  For production, run again without --staging flag."
fi
