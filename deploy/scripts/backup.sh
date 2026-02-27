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
# 3. MinIO S3 Bucket Backup (using web pod with boto3 + tar)
# --------------------------------------------------------------------------
echo "[3/4] Backing up MinIO S3 buckets..."

# Get MinIO credentials from secrets
MINIO_USER=$(kubectl get secret -n "$NAMESPACE" unesco-rdm-secrets -o jsonpath='{.data.MINIO_ROOT_USER}' | base64 -d)
MINIO_PASS=$(kubectl get secret -n "$NAMESPACE" unesco-rdm-secrets -o jsonpath='{.data.MINIO_ROOT_PASSWORD}' | base64 -d)

if [ -z "$WEB_POD" ]; then
    echo "  WARNING: Web pod not found, skipping MinIO backup"
    touch "$BACKUP_DIR/minio-backup.tar.gz"
else
    # Use boto3 (already installed in web pod) to download all S3 objects,
    # then tar them up — avoids needing mc or external downloads
    kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- python3 -c "
import boto3, os, json
from botocore.client import Config

s3 = boto3.client('s3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='$MINIO_USER',
    aws_secret_access_key='$MINIO_PASS',
    config=Config(signature_version='s3v4'),
    region_name='us-east-1')

base = '/tmp/minio-backup'
os.makedirs(base, exist_ok=True)

buckets = [b['Name'] for b in s3.list_buckets().get('Buckets', [])]
summary = {}
for bucket in buckets:
    bucket_dir = os.path.join(base, bucket)
    os.makedirs(bucket_dir, exist_ok=True)
    count = 0
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get('Contents', []):
                key = obj['Key']
                target = os.path.join(bucket_dir, key)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                s3.download_file(bucket, key, target)
                count += 1
    except Exception as e:
        print(f'  WARNING: {bucket}: {e}')
    summary[bucket] = count
    print(f'  Bucket {bucket}: {count} objects')

print(json.dumps(summary))
" 2>&1 || true

    # Create tar from web pod (which has tar) and copy it out
    kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- \
        tar -czf /tmp/minio-backup.tar.gz -C /tmp minio-backup 2>/dev/null || true

    kubectl cp -n "$NAMESPACE" "$WEB_POD:/tmp/minio-backup.tar.gz" "$BACKUP_DIR/minio-backup.tar.gz" -c web 2>/dev/null || {
        echo "  WARNING: Could not copy MinIO backup, creating empty archive"
        touch "$BACKUP_DIR/minio-backup.tar.gz"
    }

    # Cleanup web pod temp files
    kubectl exec -n "$NAMESPACE" "$WEB_POD" -c web -- rm -rf /tmp/minio-backup /tmp/minio-backup.tar.gz 2>/dev/null || true

    if [ -f "$BACKUP_DIR/minio-backup.tar.gz" ] && [ -s "$BACKUP_DIR/minio-backup.tar.gz" ]; then
        MINIO_SIZE=$(du -h "$BACKUP_DIR/minio-backup.tar.gz" | cut -f1)
        echo "  ✓ MinIO backup complete (${MINIO_SIZE})"
    else
        echo "  ⚠ MinIO backup empty or failed"
    fi
fi

# --------------------------------------------------------------------------
# 4. Metadata (config snapshot — pure kubectl, no jq/python3)
# --------------------------------------------------------------------------
echo "[4/4] Saving metadata..."

K8S_VERSION=$(kubectl version -o json 2>/dev/null | grep -o '"gitVersion": *"[^"]*"' | head -1 | cut -d'"' -f4 || echo "unknown")
NODES=$(kubectl get nodes -o jsonpath='{range .items[*]}"{.metadata.name}",{end}' 2>/dev/null | sed 's/,$//')

# Build pods JSON array using jsonpath
PODS_JSON="["
FIRST=true
for POD_INFO in $(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}|{.status.phase}|{.spec.containers[0].image}{"\n"}{end}' 2>/dev/null); do
    POD_NAME=$(echo "$POD_INFO" | cut -d'|' -f1)
    POD_STATUS=$(echo "$POD_INFO" | cut -d'|' -f2)
    POD_IMAGE=$(echo "$POD_INFO" | cut -d'|' -f3)
    if [ "$FIRST" = true ]; then FIRST=false; else PODS_JSON+=","; fi
    PODS_JSON+="{\"name\":\"$POD_NAME\",\"status\":\"$POD_STATUS\",\"image\":\"$POD_IMAGE\"}"
done
PODS_JSON+="]"

# Build PVCs JSON array using jsonpath
PVCS_JSON="["
FIRST=true
for PVC_INFO in $(kubectl get pvc -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}|{.spec.resources.requests.storage}|{.status.phase}{"\n"}{end}' 2>/dev/null); do
    PVC_NAME=$(echo "$PVC_INFO" | cut -d'|' -f1)
    PVC_SIZE=$(echo "$PVC_INFO" | cut -d'|' -f2)
    PVC_STATUS=$(echo "$PVC_INFO" | cut -d'|' -f3)
    if [ "$FIRST" = true ]; then FIRST=false; else PVCS_JSON+=","; fi
    PVCS_JSON+="{\"name\":\"$PVC_NAME\",\"size\":\"$PVC_SIZE\",\"status\":\"$PVC_STATUS\"}"
done
PVCS_JSON+="]"

cat > "$BACKUP_DIR/metadata.json" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "namespace": "$NAMESPACE",
  "kubernetes": {
    "nodes": [$NODES],
    "version": "$K8S_VERSION"
  },
  "pods": $PODS_JSON,
  "pvcs": $PVCS_JSON
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
