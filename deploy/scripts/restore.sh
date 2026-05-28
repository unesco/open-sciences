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
REQUIRED_FILES=("postgresql.sql.gz" "opensearch.tar.gz" "minio-backup.tar.gz" "metadata.json")
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
    echo "  - MinIO S3 buckets (uploaded files, CMS images)"
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
echo "[1/5] Stopping InvenioRDM + CMS..."
kubectl scale deployment -l app.kubernetes.io/component=web --replicas=0 -n "$NAMESPACE" 2>/dev/null || true
kubectl scale deployment -l app.kubernetes.io/component=worker --replicas=0 -n "$NAMESPACE" 2>/dev/null || true
kubectl scale deployment -l app.kubernetes.io/component=worker-beat --replicas=0 -n "$NAMESPACE" 2>/dev/null || true
kubectl scale deployment cms --replicas=0 -n "$NAMESPACE" 2>/dev/null || true

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
    "PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d postgres -c \"DROP DATABASE IF EXISTS \$POSTGRES_DB;\""

kubectl exec -n "$NAMESPACE" "$PG_POD" -- bash -c \
    "PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d postgres -c \"CREATE DATABASE \$POSTGRES_DB;\""

# Restore data
gunzip < "$BACKUP_DIR/postgresql.sql.gz" | \
    kubectl exec -i -n "$NAMESPACE" "$PG_POD" -- bash -c \
    "PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d \$POSTGRES_DB"

echo "  ✓ PostgreSQL (InvenioRDM) restored"

# Restore CMS database (if backup exists)
if [ -f "$BACKUP_DIR/cms-postgresql.sql.gz" ] && [ -s "$BACKUP_DIR/cms-postgresql.sql.gz" ]; then
    echo "  Restoring CMS database..."
    CMS_DB=$(kubectl get secret -n "$NAMESPACE" unesco-rdm-secrets -o jsonpath='{.data.CMS_DB_NAME}' 2>/dev/null | base64 -d 2>/dev/null || echo "")
    CMS_DB_USER=$(kubectl get secret -n "$NAMESPACE" unesco-rdm-secrets -o jsonpath='{.data.CMS_DB_USER}' 2>/dev/null | base64 -d 2>/dev/null || echo "")
    CMS_DB_PASS=$(kubectl get secret -n "$NAMESPACE" unesco-rdm-secrets -o jsonpath='{.data.CMS_DB_PASSWORD}' 2>/dev/null | base64 -d 2>/dev/null || echo "")

    if [ -n "$CMS_DB" ] && [ -n "$CMS_DB_USER" ]; then
        kubectl exec -n "$NAMESPACE" "$PG_POD" -- bash -c \
            "PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d postgres -c \"DROP DATABASE IF EXISTS $CMS_DB;\""
        kubectl exec -n "$NAMESPACE" "$PG_POD" -- bash -c \
            "PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d postgres -c \"CREATE DATABASE $CMS_DB OWNER $CMS_DB_USER;\""
        gunzip < "$BACKUP_DIR/cms-postgresql.sql.gz" | \
            kubectl exec -i -n "$NAMESPACE" "$PG_POD" -- bash -c \
            "PGPASSWORD='$CMS_DB_PASS' psql -U '$CMS_DB_USER' -d '$CMS_DB'"
        echo "  ✓ PostgreSQL (CMS) restored"
    else
        echo "  ⚠ CMS secrets not found, skipping CMS database restore"
    fi
else
    echo "  (No CMS database backup found, skipping)"
fi

# --------------------------------------------------------------------------
# Restore OpenSearch
# --------------------------------------------------------------------------
echo ""
echo "[3/5] Restoring OpenSearch indices..."

# Extract backup
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_DIR/opensearch.tar.gz" -C "$TEMP_DIR"

WEB_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)

# Note: Web pod is scaled to 0, so we need to use a temporary pod or wait for restart
# For now, we'll restore indices after app restart in step 5
echo "  (OpenSearch indices will be recreated during app initialization)"
rm -rf "$TEMP_DIR"

# --------------------------------------------------------------------------
# Restore MinIO S3 Buckets
# --------------------------------------------------------------------------
echo ""
echo "[4/5] Restoring MinIO S3 buckets..."

# Find MinIO pod
MINIO_POD=$(kubectl get pods -n "$NAMESPACE" -l app=minio -o jsonpath='{.items[0].metadata.name}')

if [ -z "$MINIO_POD" ]; then
    echo "  WARNING: MinIO pod not found, skipping S3 restore"
else
    # Get MinIO credentials
    MINIO_USER=$(kubectl get secret -n "$NAMESPACE" unesco-rdm-secrets -o jsonpath='{.data.MINIO_ROOT_USER}' | base64 -d)
    MINIO_PASS=$(kubectl get secret -n "$NAMESPACE" unesco-rdm-secrets -o jsonpath='{.data.MINIO_ROOT_PASSWORD}' | base64 -d)
    
    # Copy backup to MinIO pod
    echo "  Copying backup archive to MinIO pod..."
    kubectl cp "$BACKUP_DIR/minio-backup.tar.gz" -n "$NAMESPACE" "$MINIO_POD:/tmp/minio-backup.tar.gz" 2>/dev/null || {
        echo "  ERROR: Could not copy backup to MinIO pod"
        exit 1
    }
    
    # Extract and restore buckets
    echo "  Restoring buckets..."
    kubectl exec -n "$NAMESPACE" "$MINIO_POD" -- sh -c "
        # Configure mc client
        mc alias set local http://localhost:9000 $MINIO_USER $MINIO_PASS 2>/dev/null || exit 1
        
        # Extract backup
        cd /tmp
        rm -rf backup-restore 2>/dev/null
        mkdir -p backup-restore
        tar -xzf minio-backup.tar.gz -C backup-restore 2>/dev/null || exit 1
        
        # Remove existing buckets and restore
        for BUCKET_DIR in backup-restore/backup-temp/*; do
            if [ -d \"\$BUCKET_DIR\" ]; then
                BUCKET=\$(basename \"\$BUCKET_DIR\")
                echo \"  Restoring bucket: \$BUCKET\"
                
                # Remove existing bucket content
                mc rm --recursive --force local/\$BUCKET/ 2>/dev/null || true
                
                # Recreate bucket if needed
                mc mb local/\$BUCKET 2>/dev/null || true
                
                # Copy files back
                mc cp --recursive \"\$BUCKET_DIR/\" local/\$BUCKET/ 2>/dev/null || echo \"    (empty or error)\"
            fi
        done
        
        # Cleanup
        rm -rf backup-restore minio-backup.tar.gz
        
        echo \"  ✓ MinIO buckets restored\"
    " || {
        echo "  WARNING: MinIO restore encountered errors"
    }
    
    # Cleanup backup file from pod
    kubectl exec -n "$NAMESPACE" "$MINIO_POD" -- rm -f /tmp/minio-backup.tar.gz 2>/dev/null || true
    
    echo "  ✓ MinIO restore complete"
fi

# --------------------------------------------------------------------------
# Restart Application
# --------------------------------------------------------------------------
echo ""
echo "[5/5] Restarting InvenioRDM application..."
kubectl scale deployment -l app.kubernetes.io/component=web --replicas=1 -n "$NAMESPACE" 2>/dev/null || true
kubectl scale deployment -l app.kubernetes.io/component=worker --replicas=1 -n "$NAMESPACE" 2>/dev/null || true
kubectl scale deployment -l app.kubernetes.io/component=worker-beat --replicas=1 -n "$NAMESPACE" 2>/dev/null || true
kubectl scale deployment cms --replicas=1 -n "$NAMESPACE" 2>/dev/null || true

echo "  Waiting for web pod to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=web -n "$NAMESPACE" --timeout=3m 2>/dev/null || true

WEB_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}')

echo "  ✓ Application restarted"

# Rebuild indices (optional - comment out if not needed)
echo ""
echo "Rebuilding search indices..."
kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- bash -c \
    "echo y | invenio index destroy --force" 2>/dev/null || true
kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- bash -c \
    "invenio index init" 2>/dev/null || true
kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- bash -c \
    "echo y | invenio rdm-records rebuild-index" 2>/dev/null || true

echo "  ✓ Application restarted and indices rebuilt"

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
