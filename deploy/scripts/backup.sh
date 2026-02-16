#!/usr/bin/env bash
# ==============================================================================
# backup.sh - Manual backup of PostgreSQL database and files
# ==============================================================================
#
# Usage:
#   ./backup.sh [--output-dir DIR]
#
# Creates a timestamped backup of:
#   1. PostgreSQL database (pg_dump via kubectl exec)
#   2. Backup manifest with metadata
#
# Prerequisites:
#   - kubectl configured and connected to k3s
#   - unesco-rdm namespace with running PostgreSQL pod
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

NAMESPACE="unesco-rdm"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/opt/backups/unesco-rdm"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        *)            err "Unknown option: $1"; exit 1 ;;
    esac
done

# Load .env if available
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
if [[ -f "${ENV_FILE}" ]]; then
    source "${ENV_FILE}"
    OUTPUT_DIR="${BACKUP_DIR:-${OUTPUT_DIR}}"
fi

DB_DIR="${OUTPUT_DIR}/db"
mkdir -p "${DB_DIR}"

echo "============================================="
echo "  UNESCO Open Science Portal - Manual Backup"
echo "  Timestamp: ${TIMESTAMP}"
echo "============================================="
echo ""

# ------------------------------------------------------------------
# Step 1: Check PostgreSQL pod
# ------------------------------------------------------------------
log "Checking PostgreSQL pod..."

PG_POD=$(kubectl get pods -n "${NAMESPACE}" -l app=postgresql -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [[ -z "${PG_POD}" ]]; then
    err "PostgreSQL pod not found in namespace '${NAMESPACE}'"
    exit 1
fi
log "  PostgreSQL pod: ${PG_POD}"

# ------------------------------------------------------------------
# Step 2: Database backup
# ------------------------------------------------------------------
log "Backing up PostgreSQL database..."

DB_BACKUP_FILE="${DB_DIR}/db_${TIMESTAMP}.dump"

# Get credentials from secret
PGUSER=$(kubectl get secret unesco-rdm-secrets -n "${NAMESPACE}" -o jsonpath='{.data.POSTGRES_USER}' | base64 -d)
PGDB=$(kubectl get secret unesco-rdm-secrets -n "${NAMESPACE}" -o jsonpath='{.data.POSTGRES_DB}' | base64 -d)

# Run pg_dump inside the pod and stream output
kubectl exec -n "${NAMESPACE}" "${PG_POD}" -- \
    pg_dump -U "${PGUSER}" -d "${PGDB}" --format=custom --compress=9 \
    > "${DB_BACKUP_FILE}"

DB_SIZE=$(du -sh "${DB_BACKUP_FILE}" | cut -f1)
log "  Database backup: ${DB_SIZE} -> $(basename ${DB_BACKUP_FILE})"

# ------------------------------------------------------------------
# Step 3: Create manifest
# ------------------------------------------------------------------
log "Creating backup manifest..."

MANIFEST_FILE="${OUTPUT_DIR}/manifest_${TIMESTAMP}.json"
cat > "${MANIFEST_FILE}" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "type": "manual",
  "database": {
    "file": "db/db_${TIMESTAMP}.dump",
    "format": "pg_dump custom",
    "size": "${DB_SIZE}",
    "user": "${PGUSER}",
    "database": "${PGDB}"
  },
  "k3s_version": "$(k3s --version 2>/dev/null | head -1 | awk '{print $3}')",
  "namespace": "${NAMESPACE}"
}
EOF

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
echo ""
echo "============================================="
echo -e "  ${GREEN}Backup completed!${NC}"
echo "============================================="
echo ""
echo "  Database:  ${DB_BACKUP_FILE} (${DB_SIZE})"
echo "  Manifest:  ${MANIFEST_FILE}"
echo ""
echo "  To restore, run:"
echo "    ./restore.sh --backup-file ${DB_BACKUP_FILE}"
echo ""

# List recent backups
echo "Recent backups:"
ls -lht "${DB_DIR}" 2>/dev/null | head -6
