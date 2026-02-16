#!/usr/bin/env bash
# ==============================================================================
# install-k3s.sh - Install k3s and dependencies on a single VM
# ==============================================================================
# Supported OS: Ubuntu 22.04+, AlmaLinux 8+, RHEL 8+
#
# Usage:
#   sudo ./install-k3s.sh
#
# What it does:
#   1. Installs k3s (lightweight Kubernetes)
#   2. Installs Helm (package manager for Kubernetes)
#   3. Configures kubectl for the current user
#   4. Sets vm.max_map_count for OpenSearch
#   5. Creates required directories
# ==============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Check root
if [[ $EUID -ne 0 ]]; then
    err "This script must be run as root (or with sudo)"
    exit 1
fi

ORIGINAL_USER="${SUDO_USER:-$USER}"

echo "============================================="
echo "  UNESCO Open Science Portal"
echo "  k3s Installation Script"
echo "============================================="
echo ""

# ------------------------------------------------------------------
# Step 1: System prerequisites
# ------------------------------------------------------------------
log "Step 1/5: Checking system prerequisites..."

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID="${ID}"
    OS_VERSION="${VERSION_ID}"
    log "  OS detected: ${PRETTY_NAME}"
else
    err "Cannot detect OS. /etc/os-release not found."
    exit 1
fi

# Check minimum resources
TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_MEM_GB=$((TOTAL_MEM_KB / 1024 / 1024))
TOTAL_CPU=$(nproc)
log "  CPU cores: ${TOTAL_CPU}"
log "  RAM: ${TOTAL_MEM_GB} GB"

if [[ ${TOTAL_MEM_GB} -lt 6 ]]; then
    warn "  Less than 8GB RAM detected (${TOTAL_MEM_GB}GB)."
    warn "  Minimum recommended: 8GB. Some services may not start."
fi

if [[ ${TOTAL_CPU} -lt 2 ]]; then
    warn "  Less than 4 CPU cores detected (${TOTAL_CPU})."
    warn "  Minimum recommended: 4 cores."
fi

# Install prerequisites based on OS
case "${OS_ID}" in
    ubuntu|debian)
        log "  Installing prerequisites (apt)..."
        apt-get update -qq
        apt-get install -y -qq curl wget jq git > /dev/null 2>&1
        ;;
    almalinux|rhel|centos|rocky)
        log "  Installing prerequisites (dnf)..."
        dnf install -y -q curl wget jq git > /dev/null 2>&1
        ;;
    *)
        warn "  Unknown OS: ${OS_ID}. Trying to proceed anyway..."
        ;;
esac

log "  Prerequisites installed."

# ------------------------------------------------------------------
# Step 2: Install k3s
# ------------------------------------------------------------------
log "Step 2/5: Installing k3s..."

if command -v k3s &> /dev/null; then
    K3S_VERSION=$(k3s --version | head -1)
    warn "  k3s already installed: ${K3S_VERSION}"
    warn "  Skipping installation. To reinstall, run: /usr/local/bin/k3s-uninstall.sh"
else
    # Install k3s with Traefik enabled (default) and no local storage class
    # (we use local-path-provisioner which is included by default)
    curl -sfL https://get.k3s.io | sh -s - \
        --write-kubeconfig-mode 644 \
        --disable servicelb \
        --kube-apiserver-arg service-node-port-range=80-32767

    # Wait for k3s to be ready
    log "  Waiting for k3s to be ready..."
    sleep 10
    k3s kubectl wait --for=condition=ready node --all --timeout=120s

    log "  k3s installed successfully!"
    k3s --version | head -1
fi

# ------------------------------------------------------------------
# Step 3: Configure kubectl for the user
# ------------------------------------------------------------------
log "Step 3/5: Configuring kubectl..."

USER_HOME=$(eval echo ~${ORIGINAL_USER})

# Create .kube directory
mkdir -p "${USER_HOME}/.kube"

# Copy kubeconfig
cp /etc/rancher/k3s/k3s.yaml "${USER_HOME}/.kube/config"
chown -R "${ORIGINAL_USER}:${ORIGINAL_USER}" "${USER_HOME}/.kube"
chmod 600 "${USER_HOME}/.kube/config"

# Add kubectl alias if not present
BASHRC="${USER_HOME}/.bashrc"
if ! grep -q "alias kubectl=" "${BASHRC}" 2>/dev/null; then
    echo "" >> "${BASHRC}"
    echo "# k3s kubectl alias" >> "${BASHRC}"
    echo "alias kubectl='k3s kubectl'" >> "${BASHRC}"
    echo "export KUBECONFIG=${USER_HOME}/.kube/config" >> "${BASHRC}"
fi

log "  kubectl configured for user: ${ORIGINAL_USER}"

# ------------------------------------------------------------------
# Step 4: Install Helm
# ------------------------------------------------------------------
log "Step 4/5: Installing Helm..."

if command -v helm &> /dev/null; then
    HELM_VERSION=$(helm version --short 2>/dev/null)
    warn "  Helm already installed: ${HELM_VERSION}"
else
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    log "  Helm installed: $(helm version --short 2>/dev/null)"
fi

# Add InvenioRDM Helm repository
helm repo add invenio https://inveniosoftware.github.io/helm-invenio/ 2>/dev/null || true
helm repo update > /dev/null 2>&1
log "  InvenioRDM Helm repo added."

# ------------------------------------------------------------------
# Step 5: System tuning
# ------------------------------------------------------------------
log "Step 5/5: System tuning..."

# vm.max_map_count for OpenSearch (required, must be >= 262144)
CURRENT_MAP_COUNT=$(sysctl -n vm.max_map_count 2>/dev/null || echo "0")
if [[ ${CURRENT_MAP_COUNT} -lt 262144 ]]; then
    sysctl -w vm.max_map_count=262144
    echo "vm.max_map_count=262144" >> /etc/sysctl.d/99-opensearch.conf
    log "  vm.max_map_count set to 262144 (was: ${CURRENT_MAP_COUNT})"
else
    log "  vm.max_map_count already set: ${CURRENT_MAP_COUNT}"
fi

# Create required directories
mkdir -p /opt/backups/unesco-rdm
chown -R "${ORIGINAL_USER}:${ORIGINAL_USER}" /opt/backups/unesco-rdm
log "  Backup directory created: /opt/backups/unesco-rdm"

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
echo ""
echo "============================================="
echo -e "  ${GREEN}Installation complete!${NC}"
echo "============================================="
echo ""
echo "  k3s:    $(k3s --version 2>/dev/null | head -1)"
echo "  Helm:   $(helm version --short 2>/dev/null)"
echo "  kubectl: configured for user '${ORIGINAL_USER}'"
echo ""
echo "  Next steps:"
echo "    1. Log out and back in (or run: source ~/.bashrc)"
echo "    2. Copy .env.example to .env and fill in values"
echo "    3. Run: make deploy"
echo ""
echo "  Verify with:"
echo "    kubectl get nodes"
echo "    kubectl get pods -A"
echo ""
