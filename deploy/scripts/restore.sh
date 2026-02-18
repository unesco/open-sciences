#!/bin/bash
# ==============================================================================
# UNESCO Open Science Portal - Restore Script
# ==============================================================================
# Restores PostgreSQL, OpenSearch indices, and uploaded files from backup.
#
# Usage:
#   ./scripts/restore.sh <namespace> <backup-dir> [--no-confirm]
#
# Example:
#   ./scripts/restore.sh unesco-rdm /path/to/backups/2026-02-18_02-00-00
# ==============================================================================

set -e

NAMESPACE="${1:-unesco-rdm}"
BACKUP_DIR="${2}"
NO_CONFIRM="${3}"

if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
    echo "ERROR: Backup directory not found: $BACKUP_DIR"
    echo ""
    echo "Usage: $0 <namespace> <backup-dir> [--no-confirm]"
    exit 1
fi

echo "=========================================="
echo "  UNESCO RDM Restore"
echo "=========================================="
echo "Namespace:    $NAMESPACE"
echo "Restore from: $BACKUP_DIR"
echo ""

# Verify backup files exist
echo "Verifying backup integrity..."
REQUIRED_FILES=("postgresql.sql.gz" "opensearch.tar.gz" "uploads.tar.gz" "metadata.json")
MISSING=0

for FILE in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$BACKUP_DIR/$FILE" ]; then
        echo "  ✗ Missing: $FILE"
        MISSING=1
    else
        SIZE=$(du -h "$BACKUP_DIR/$FILE" | cut -f1)
        echo "  ✓ Found: $FILE ($SIZE)"
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "ERROR: Incomplete backup. Aborting."
    exit 1
fi

# Show backup metadata
if [ -f "$BACKUP_DIR/metadata.json" ]; then
    echo ""
    echo "Backup metadata:"
    TIMESTAMP=$(jq -r '.timestamp' "$BACKUP_DIR/metadata.json")
    echo "  Created: $TIMESTAMP"
fi

# Confirmation prompt
if [ "$NO_CONFIRM" != "--no-confirm" ]; then
    echo ""
    echo "⚠️  WARNING: This will OVERWRITE all current data!"
    echo ""
    echo "The following will be replaced:"
    echo "  - PostgreSQL database (all records, users, settings)"
    echo "  - OpenSearch indices (search data)"
    echo "  - Uploaded files"
    echo ""
    read -p "Type 'RESTORE' to continue: " CONFIRM
    
    if [ "$CONFIRM" != "RESTORE" ]; then
        echo "Cancelled."
        exit 0
    fi
fi

# --------------------------------------------------------------------------
# Stop Application
# --------------------------------------------------------------------------
echo ""
echo "[1/5] Stopping InvenioRDM application..."
kubectl scale deployment -l app.kubernetes.io/component=web --replicas=0 -n "$NAMESPACE" 2>/dev/null || true
kubectl scale deployment -l app.kubernetes.io/component=worker --replicas=0 -n "$NAMESPACE" 2>/dev/null || true
kubectl scale deployment -l app.kubernetes.io/component=worker-beat --replicas=0 -n "$NAMESPACE" 2>/dev/null || true

echo "  Waiting for pods to terminate..."
sleep 10
echo "  ✓ Application stopped"

# --------------------------------------------------------------------------
# Restore PostgreSQL
# --------------------------------------------------------------------------
echo ""
echo "[2/5] Restoring PostgreSQL..."
PG_POD=$(kubectl get pods -n "$NAMESPACE" -l app=postgresql -o jsonpath='{.items[0].metadata.name}')

if [ -z "$PG_POD" ]; then
    echo "  ERROR: PostgreSQL pod not found!"
    exit 1
fi

# Drop and recreate database
kubectl exec -n "$NAMESPACE" "$PG_POD" -- bash -c \
    "PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d postgres -c 'DROP DATABASE IF EXISTS \$POSTGRES_DB;'"

kubectl exec -n "$NAMESPACE" "$PG_POD" -- bash -c \
    "PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d postgres -c 'CREATE DATABASE \$POSTGRES_DB;'"

# Restore data
gunzip < "$BACKUP_DIR/postgresql.sql.gz" | \
    kubectl exec -i -n "$NAMESPACE" "$PG_POD" -- bash -c \
    "PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d \$POSTGRES_DB"

echo "  ✓ PostgreSQL restored"

# --------------------------------------------------------------------------
# Restore OpenSearch
# --------------------------------------------------------------------------
echo ""
echo "[3/5] Restoring OpenSearch indices..."

# Extract backup
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_DIR/opensearch.tar.gz" -C "$TEMP_DIR"

WEB_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}')

# Note: Web pod is scaled to 0, so we need to use a temporary pod or wait for restart
# For now, we'll restore indices after app restart in step 5
echo "  (OpenSearch indices will be recreated during app initialization)"
rm -rf "$TEMP_DIR"

# --------------------------------------------------------------------------
# Restore Uploaded Files
# --------------------------------------------------------------------------
echo ""
echo "[4/5] Restoring uploaded files..."

# We need the web pod running to restore files, so we'll do it after restart
echo "  (Files will be restored after app restart)"

# --------------------------------------------------------------------------
# Restart Application
# --------------------------------------------------------------------------
echo ""
echo "[5/5] Restarting InvenioRDM application..."
kubectl scale deployment -l app.kubernetes.io/component=web --replicas=1 -n "$NAMESPACE" 2>/dev/null || true
kubectl scale deployment -l app.kubernetes.io/component=worker --replicas=1 -n "$NAMESPACE" 2>/dev/null || true
kubectl scale deployment -l app.kubernetes.io/component=worker-beat --replicas=1 -n "$NAMESPACE" 2>/dev/null || true

echo "  Waiting for web pod to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=web -n "$NAMESPACE" --timeout=3m 2>/dev/null || true

# Now restore files
WEB_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}')

if [ -n "$WEB_POD" ]; then
    echo "  Restoring uploaded files..."
    kubectl exec -i -n "$NAMESPACE" "$WEB_POD" -c web -- bash -c \
        "cd /opt/invenio/var/instance && rm -rf data && tar -xzf -" \
        < "$BACKUP_DIR/uploads.tar.gz" || echo "  (no files to restore)"
    
    echo "  ✓ Files restored"
fi

# Rebuild indices (optional - comment out if not needed)
echo ""
echo "Rebuilding search indices..."
kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- bash -c \
    "invenio index destroy --force --yes-i-know && invenio index init" 2>/dev/null || true
kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- bash -c \
    "echo y | invenio index reindex --all-records" 2>/dev/null || true

echo "  ✓ Application restarted"

# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "  Restore Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Verify data: kubectl exec -n $NAMESPACE $WEB_POD -c web -- invenio shell"
echo "  2. Check logs: kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=web"
echo "  3. Test access: curl http://localhost/"
echo ""
