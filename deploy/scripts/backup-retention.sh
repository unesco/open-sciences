#!/bin/bash
# ==============================================================================
# UNESCO Open Science Portal - Backup Retention Script
# ==============================================================================
# Removes backups older than specified retention period.
#
# Usage:
#   ./scripts/backup-retention.sh <backup-path> <retention-days>
#
# Example:
#   ./scripts/backup-retention.sh /path/to/backups/local 10
# ==============================================================================

set -e

BACKUP_PATH="${1}"
RETENTION_DAYS="${2:-10}"

if [ -z "$BACKUP_PATH" ] || [ ! -d "$BACKUP_PATH" ]; then
    echo "ERROR: Backup path not found: $BACKUP_PATH"
    echo ""
    echo "Usage: $0 <backup-path> <retention-days>"
    exit 1
fi

echo "=========================================="
echo "  Backup Retention Cleanup"
echo "=========================================="
echo "Path:      $BACKUP_PATH"
echo "Retention: $RETENTION_DAYS days"
echo ""

# Find and remove old backups
REMOVED=0
KEPT=0
TOTAL_FREED=0

for BACKUP_DIR in "$BACKUP_PATH"/*/; do
    if [ ! -d "$BACKUP_DIR" ]; then
        continue
    fi
    
    BACKUP_NAME=$(basename "$BACKUP_DIR")
    
    # Check if directory name matches timestamp format YYYY-MM-DD_HH-MM-SS
    if [[ ! "$BACKUP_NAME" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo "⚠ Skipping non-backup directory: $BACKUP_NAME"
        continue
    fi
    
    # Calculate age in days
    BACKUP_TIME=$(echo "$BACKUP_NAME" | sed 's/_/ /' | sed 's/-/:/3' | sed 's/-/:/3')
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        BACKUP_EPOCH=$(date -j -f "%Y-%m-%d %H:%M:%S" "$BACKUP_TIME" +%s 2>/dev/null || echo 0)
    else
        # Linux
        BACKUP_EPOCH=$(date -d "$BACKUP_TIME" +%s 2>/dev/null || echo 0)
    fi
    
    if [ "$BACKUP_EPOCH" -eq 0 ]; then
        echo "⚠ Cannot parse timestamp: $BACKUP_NAME"
        continue
    fi
    
    NOW_EPOCH=$(date +%s)
    AGE_DAYS=$(( (NOW_EPOCH - BACKUP_EPOCH) / 86400 ))
    
    if [ $AGE_DAYS -gt $RETENTION_DAYS ]; then
        SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
        echo "  Removing: $BACKUP_NAME (${AGE_DAYS} days old, size: $SIZE)"
        
        # Calculate freed space in bytes
        SIZE_BYTES=$(du -s "$BACKUP_DIR" 2>/dev/null | cut -f1)
        TOTAL_FREED=$((TOTAL_FREED + SIZE_BYTES))
        
        rm -rf "$BACKUP_DIR"
        REMOVED=$((REMOVED + 1))
    else
        KEPT=$((KEPT + 1))
    fi
done

echo ""
echo "=========================================="
echo "  Cleanup Summary"
echo "=========================================="
echo "Backups removed: $REMOVED"
echo "Backups kept:    $KEPT"

if [ $TOTAL_FREED -gt 0 ]; then
    # Convert bytes to human readable
    if [ $TOTAL_FREED -gt 1073741824 ]; then
        FREED_HUMAN=$(awk "BEGIN {printf \"%.2f GB\", $TOTAL_FREED/1073741824}")
    elif [ $TOTAL_FREED -gt 1048576 ]; then
        FREED_HUMAN=$(awk "BEGIN {printf \"%.2f MB\", $TOTAL_FREED/1048576}")
    else
        FREED_HUMAN=$(awk "BEGIN {printf \"%.2f KB\", $TOTAL_FREED/1024}")
    fi
    echo "Space freed:     $FREED_HUMAN"
fi

echo ""

if [ $KEPT -gt 0 ]; then
    echo "Remaining backups:"
    ls -1t "$BACKUP_PATH" | head -5
    if [ $(ls -1 "$BACKUP_PATH" | wc -l) -gt 5 ]; then
        echo "  ... and $(($(ls -1 "$BACKUP_PATH" | wc -l) - 5)) more"
    fi
fi

echo ""
