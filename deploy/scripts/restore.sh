#!/usr/bin/env bash
# ==============================================================================
# restore.sh - Restore PostgreSQL database from backup
# ==============================================================================
#
# Usage:
#   ./restore.sh --backup-file /opt/backups/unesco-rdm/db/db_20260216_020000.dump
#
# What it does:
#   1. Stops InvenioRDM web and worker pods (scale to 0)
#   2. Drops and recreates the database
#   3. Restores from pg_dump backup
#   4. Rebuilds search indices
#   5. Restarts InvenioRDM pods
#
# ⚠️ WARNING: This will REPLACE all data in the database!
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
BACKUP_FILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --backup-file) BACKUP_FILE="$2"; shift 2 ;;
        *)             err "Unknown option: $1"; exit 1 ;;
    esac
done

# Validate
if [[ -z "${BACKUP_FILE}" ]]; then
    err "Backup file is required. Usage: ./restore.sh --backup-file <path>"
    exit 1
fi

if [[ ! -f "${BACKUP_FILE}" ]]; then
    err "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

BACKUP_SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)

echo "============================================="
echo "  UNESCO Open Science Portal - Restore"
echo "============================================="
echo ""
echo "  Backup file: ${BACKUP_FILE}"
echo "  File size:   ${BACKUP_SIZE}"
echo ""
echo -e "  ${RED}⚠️  WARNING: This will REPLACE all current data!${NC}"
echo ""
read -p "  Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "  Cancelled."
    exit 0
fi

# Get credentials
PGUSER=$(kubectl get secret unesco-rdm-secrets -n "${NAMESPACE}" -o jsonpath='{.data.POSTGRES_USER}' | base64 -d)
PGDB=$(kubectl get secret unesco-rdm-secrets -n "${NAMESPACE}" -o jsonpath='{.data.POSTGRES_DB}' | base64 -d)
PG_POD=$(kubectl get pods -n "${NAMESPACE}" -l app=postgresql -o jsonpath='{.items[0].metadata.name}')

# ------------------------------------------------------------------
# Step 1: Scale down InvenioRDM
# ------------------------------------------------------------------
log "Step 1/5: Scaling down InvenioRDM pods..."

# Save current replica counts
WEB_REPLICAS=$(kubectl get deployment -n "${NAMESPACE}" -l app.kubernetes.io/component=web -o jsonpath='{.items[0].spec.replicas}' 2>/dev/null || echo "1")
WORKER_REPLICAS=$(kubectl get deployment -n "${NAMESPACE}" -l app.kubernetes.io/component=worker -o jsonpath='{.items[0].spec.replicas}' 2>/dev/null || echo "1")

kubectl scale deployment -n "${NAMESPACE}" -l app.kubernetes.io/component=web --replicas=0 2>/dev/null || true
kubectl scale deployment -n "${NAMESPACE}" -l app.kubernetes.io/component=worker --replicas=0 2>/dev/null || true
kubectl scale deployment -n "${NAMESPACE}" -l app.kubernetes.io/component=worker-beat --replicas=0 2>/dev/null || true

log "  Waiting for pods to terminate..."
sleep 10

# ------------------------------------------------------------------
# Step 2: Drop and recreate database
# ------------------------------------------------------------------
log "Step 2/5: Recreating database..."

kubectl exec -n "${NAMESPACE}" "${PG_POD}" -- \
    psql -U "${PGUSER}" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${PGDB}' AND pid <> pg_backend_pid();" 2>/dev/null || true

kubectl exec -n "${NAMESPACE}" "${PG_POD}" -- \
    psql -U "${PGUSER}" -d postgres -c "DROP DATABASE IF EXISTS ${PGDB};"

kubectl exec -n "${NAMESPACE}" "${PG_POD}" -- \
    psql -U "${PGUSER}" -d postgres -c "CREATE DATABASE ${PGDB} OWNER ${PGUSER};"

log "  Database recreated."

# ------------------------------------------------------------------
# Step 3: Restore backup
# ------------------------------------------------------------------
log "Step 3/5: Restoring database from backup..."

# Copy backup file into the pod
kubectl cp "${BACKUP_FILE}" "${NAMESPACE}/${PG_POD}:/tmp/restore.dump"

# Restore
kubectl exec -n "${NAMESPACE}" "${PG_POD}" -- \
    pg_restore -U "${PGUSER}" -d "${PGDB}" --no-owner --no-privileges /tmp/restore.dump

# Cleanup
kubectl exec -n "${NAMESPACE}" "${PG_POD}" -- rm -f /tmp/restore.dump

log "  Database restored."

# ------------------------------------------------------------------
# Step 4: Scale up InvenioRDM
# ------------------------------------------------------------------
log "Step 4/5: Scaling up InvenioRDM pods..."

kubectl scale deployment -n "${NAMESPACE}" -l app.kubernetes.io/component=web --replicas="${WEB_REPLICAS}" 2>/dev/null || true
kubectl scale deployment -n "${NAMESPACE}" -l app.kubernetes.io/component=worker --replicas="${WORKER_REPLICAS}" 2>/dev/null || true
kubectl scale deployment -n "${NAMESPACE}" -l app.kubernetes.io/component=worker-beat --replicas=1 2>/dev/null || true

log "  Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=web \
    -n "${NAMESPACE}" --timeout=180s 2>/dev/null || warn "  Web pod not ready yet"

# ------------------------------------------------------------------
# Step 5: Rebuild search indices
# ------------------------------------------------------------------
log "Step 5/5: Rebuilding search indices..."

WEB_POD=$(kubectl get pods -n "${NAMESPACE}" -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [[ -n "${WEB_POD}" ]]; then
    kubectl exec -n "${NAMESPACE}" "${WEB_POD}" -c web -- \
        bash -c "invenio index destroy --force --yes-i-know && invenio index init" 2>/dev/null || true

    kubectl exec -n "${NAMESPACE}" "${WEB_POD}" -c web -- \
        bash -c "invenio rdm-records custom-fields init" 2>/dev/null || true

    kubectl exec -n "${NAMESPACE}" "${WEB_POD}" -c web -- \
        bash -c "invenio rdm-records rebuild-index" 2>/dev/null || true

    log "  Search indices rebuilt."
else
    warn "  Web pod not found. Rebuild indices manually after pods are ready:"
    warn "    make shell"
    warn "    invenio index destroy --force --yes-i-know && invenio index init"
    warn "    invenio rdm-records custom-fields init"
    warn "    invenio rdm-records rebuild-index"
fi

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
echo ""
echo "============================================="
echo -e "  ${GREEN}Restore completed!${NC}"
echo "============================================="
echo ""
echo "  Database restored from: $(basename ${BACKUP_FILE})"
echo "  Search indices rebuilt."
echo ""
echo "  Verify:"
echo "    kubectl get pods -n ${NAMESPACE}"
echo "    curl -s https://\${DOMAIN}/api/records?size=1 | jq '.hits.total'"
echo ""
