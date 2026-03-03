#!/bin/bash
# ==============================================================================
# UNESCO Open Science Portal - Backup Script
# ==============================================================================
# Backs up PostgreSQL, OpenSearch indices, and uploaded files.
# Can be run manually or via CronJob.
#
# Environment variables:
#   NAMESPACE     - Kubernetes namespace (default: unesco-rdm)
#   BACKUP_PATH   - Path where backups are stored (default: /tmp/backups)
#
# Manual usage:
#   NAMESPACE=unesco-rdm BACKUP_PATH=/path/to/backups ./backup.sh
# ==============================================================================

set -e

NAMESPACE="${NAMESPACE:-unesco-rdm}"
BACKUP_PATH="${BACKUP_PATH:-/tmp/backups}"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="${BACKUP_PATH}/${TIMESTAMP}"

echo "=========================================="
echo "  UNESCO RDM Backup"
echo "=========================================="
echo "Namespace:   $NAMESPACE"
echo "Backup to:   $BACKUP_DIR"
echo "Timestamp:   $TIMESTAMP"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# --------------------------------------------------------------------------
# 1. PostgreSQL Backup
# --------------------------------------------------------------------------
echo "[1/4] Backing up PostgreSQL..."
PG_POD=$(kubectl get pods -n "$NAMESPACE" -l app=postgresql -o jsonpath='{.items[0].metadata.name}')

if [ -z "$PG_POD" ]; then
    echo "  ERROR: PostgreSQL pod not found!"
    exit 1
fi

kubectl exec -n "$NAMESPACE" "$PG_POD" -- bash -c \
    "PGPASSWORD=\$POSTGRES_PASSWORD pg_dump -U \$POSTGRES_USER -d \$POSTGRES_DB --no-owner --no-acl" \
    | gzip > "$BACKUP_DIR/postgresql.sql.gz"

PG_SIZE=$(du -h "$BACKUP_DIR/postgresql.sql.gz" | cut -f1)
echo "  ✓ PostgreSQL backup complete (${PG_SIZE})"

# --------------------------------------------------------------------------
# 2. OpenSearch Dump
# --------------------------------------------------------------------------
echo "[2/4] Backing up OpenSearch indices..."
WEB_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=web -o jsonpath='{.items[0].metadata.name}')

if [ -z "$WEB_POD" ]; then
    echo "  ERROR: Web pod not found!"
    exit 1
fi

# Export all indices using elasticdump (or manual curl approach)
# For simplicity, we'll export records and vocabularies indices
kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- bash -c \
    "curl -s 'http://opensearch:9200/_cat/indices?format=json'" \
    > "$BACKUP_DIR/opensearch-indices.json"

# Backup all RDM indices (rdmrecords, vocabularies, etc.)
INDICES=$(kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- bash -c \
    "curl -s 'http://opensearch:9200/_cat/indices?format=json' | python3 -c \"import sys,json; print(' '.join([i['index'] for i in json.load(sys.stdin) if not i['index'].startswith('.')]))\"")

for INDEX in $INDICES; do
    echo "  Exporting index: $INDEX"
    kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- bash -c \
        "curl -s 'http://opensearch:9200/${INDEX}/_search?scroll=5m&size=1000' | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(json.dumps(h)) for h in d.get('hits',{}).get('hits',[])]\"" \
        > "$BACKUP_DIR/opensearch-${INDEX}.ndjson" 2>/dev/null || echo "  (empty or error)"
done

# Create tar archive with all OpenSearch export files
cd "$BACKUP_DIR"
tar -czf opensearch.tar.gz opensearch-*.ndjson opensearch-indices.json 2>/dev/null || {
    echo "  WARNING: Some OpenSearch files may be missing"
    # Create empty archive if no files found
    tar -czf opensearch.tar.gz opensearch-indices.json 2>/dev/null || touch opensearch.tar.gz
}
rm -f opensearch-*.ndjson opensearch-indices.json
cd - > /dev/null

OS_SIZE=$(du -h "$BACKUP_DIR/opensearch.tar.gz" | cut -f1)
echo "  ✓ OpenSearch backup complete (${OS_SIZE})"

# --------------------------------------------------------------------------
# 3. MinIO S3 Bucket Backup (using web pod with tar)
# --------------------------------------------------------------------------
echo "[3/4] Backing up MinIO S3 buckets..."

# Get MinIO credentials from secrets
MINIO_USER=$(kubectl get secret -n "$NAMESPACE" unesco-rdm-secrets -o jsonpath='{.data.MINIO_ROOT_USER}' | base64 -d)
MINIO_PASS=$(kubectl get secret -n "$NAMESPACE" unesco-rdm-secrets -o jsonpath='{.data.MINIO_ROOT_PASSWORD}' | base64 -d)

# Use web pod (which has tar) to backup MinIO
if [ -z "$WEB_POD" ]; then
    echo "  WARNING: Web pod not found, skipping MinIO backup"
    touch "$BACKUP_DIR/minio-backup.tar.gz"
else
    # Download mc client in web pod and backup MinIO buckets
    kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- bash -c "
        # Install mc client if not present (use amd64 for web pod)
        if [ ! -f /tmp/mc ]; then
            curl -sL https://dl.min.io/client/mc/release/linux-amd64/mc -o /tmp/mc 2>/dev/null
            chmod +x /tmp/mc 2>/dev/null
        fi
        
        # Configure mc client
        /tmp/mc alias set minio-backup http://minio:9000 '$MINIO_USER' '$MINIO_PASS' 2>/dev/null || exit 1
        
        # Mirror all buckets to temp directory
        cd /tmp
        rm -rf minio-backup 2>/dev/null
        mkdir -p minio-backup
        
        for BUCKET in \$(/tmp/mc ls minio-backup/ 2>/dev/null | awk '{print \$5}'); do
            echo \"  Backing up bucket: \$BUCKET\"
            mkdir -p minio-backup/\$BUCKET
            /tmp/mc mirror --quiet minio-backup/\$BUCKET ./minio-backup/\$BUCKET/ 2>/dev/null || echo \"    (empty or error)\"
        done
        
        # Create marker file
        touch minio-backup/.backup-complete
        
        # Create tar archive
        tar -czf /tmp/minio-backup.tar.gz minio-backup/ 2>/dev/null
        rm -rf minio-backup
    " 2>/dev/null
    
    # Copy backup from web pod
    kubectl cp -n "$NAMESPACE" "$WEB_POD:/tmp/minio-backup.tar.gz" "$BACKUP_DIR/minio-backup.tar.gz" -c web 2>/dev/null || {
        echo "  WARNING: Could not copy MinIO backup, creating empty archive"
        touch "$BACKUP_DIR/minio-backup.tar.gz"
    }
    
    # Cleanup web pod temp file
    kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- rm -f /tmp/minio-backup.tar.gz 2>/dev/null || true
    if [ -f "$BACKUP_DIR/minio-backup.tar.gz" ] && [ -s "$BACKUP_DIR/minio-backup.tar.gz" ]; then
        MINIO_SIZE=$(du -h "$BACKUP_DIR/minio-backup.tar.gz" | cut -f1)
        echo "  ✓ MinIO backup complete (${MINIO_SIZE})"
    else
        echo "  ⚠ MinIO backup empty or failed"
    fi
fi

# --------------------------------------------------------------------------
# 4. Metadata (config snapshot)
# --------------------------------------------------------------------------
echo "[4/4] Saving metadata..."

cat > "$BACKUP_DIR/metadata.json" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "namespace": "$NAMESPACE",
  "kubernetes": {
    "nodes": $(kubectl get nodes -o json | jq -c '[.items[].metadata.name]'),
    "version": "$(kubectl version --short 2>/dev/null | grep Server || echo 'unknown')"
  },
  "pods": $(kubectl get pods -n "$NAMESPACE" -o json | jq -c '[.items[] | {name: .metadata.name, status: .status.phase, image: .spec.containers[0].image}]'),
  "pvcs": $(kubectl get pvc -n "$NAMESPACE" -o json | jq -c '[.items[] | {name: .metadata.name, size: .spec.resources.requests.storage, status: .status.phase}]')
}
EOF

echo "  ✓ Metadata saved"

# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "  Backup Complete!"
echo "=========================================="
echo "Location: $BACKUP_DIR"
echo ""
ls -lh "$BACKUP_DIR"
echo ""

TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "Total size: $TOTAL_SIZE"
echo ""
