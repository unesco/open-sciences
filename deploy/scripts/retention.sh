#!/bin/bash
# ==============================================================================
# UNESCO Open Science Portal - Backup Retention Script
# ==============================================================================
# Removes old backups based on count or time-based retention policy.
#
# Environment variables:
#   BACKUP_PATH              - Path where backups are stored (default: /backups)
#   BACKUP_RETENTION_COUNT   - Keep last N backups (count-based retention)
#   BACKUP_RETENTION_DAYS    - Keep backups younger than N days (time-based)
#
# Note: Count-based retention takes precedence over time-based.
# ==============================================================================

set -e

BACKUP_PATH="${BACKUP_PATH:-/backups}"
RETENTION_COUNT="${BACKUP_RETENTION_COUNT:-}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-}"

echo "=========================================="
echo "  Backup Retention Cleanup"
echo "=========================================="
echo "Path: $BACKUP_PATH"

# Check if backup path exists
if [ ! -d "$BACKUP_PATH" ]; then
    echo "ERROR: Backup path does not exist"
    exit 1
fi

# Get all backup directories with valid timestamp format (YYYY-MM-DD_HH-MM-SS)
BACKUPS=()
while IFS= read -r -d '' dir; do
    basename=$(basename "$dir")
    # Validate timestamp format
    if [[ "$basename" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}$ ]]; then
        BACKUPS+=("$basename")
    fi
done < <(find "$BACKUP_PATH" -mindepth 1 -maxdepth 1 -type d -print0)

# Check if any backups found
if [ ${#BACKUPS[@]} -eq 0 ]; then
    echo "No backups found."
    exit 0
fi

# Sort backups by timestamp (newest first)
IFS=$'\n' BACKUPS=($(sort -r <<<"${BACKUPS[*]}"))
unset IFS

TOTAL_BEFORE=${#BACKUPS[@]}
REMOVED_COUNT=0
FREED_SPACE=0

# Function to get directory size in bytes
get_dir_size() {
    du -sb "$1" 2>/dev/null | cut -f1 || echo "0"
}

# Function to format bytes to human readable
format_size() {
    local bytes=$1
    if [ "$bytes" -lt 1024 ]; then
        echo "${bytes}B"
    elif [ "$bytes" -lt $((1024 * 1024)) ]; then
        echo "$(awk "BEGIN {printf \"%.1f\", $bytes/1024}")K"
    elif [ "$bytes" -lt $((1024 * 1024 * 1024)) ]; then
        echo "$(awk "BEGIN {printf \"%.1f\", $bytes/(1024*1024)}")M"
    elif [ "$bytes" -lt $((1024 * 1024 * 1024 * 1024)) ]; then
        echo "$(awk "BEGIN {printf \"%.1f\", $bytes/(1024*1024*1024)}")G"
    else
        echo "$(awk "BEGIN {printf \"%.1f\", $bytes/(1024*1024*1024*1024)}")T"
    fi
}

# Count-based retention (takes precedence)
if [ -n "$RETENTION_COUNT" ] && [ "$RETENTION_COUNT" -gt 0 ] 2>/dev/null; then
    echo "Mode: Keep last $RETENTION_COUNT backups"
    echo ""
    
    if [ "$TOTAL_BEFORE" -le "$RETENTION_COUNT" ]; then
        echo "Total backups: $TOTAL_BEFORE (keeping all)"
        echo "No cleanup needed."
    else
        TO_REMOVE=${#BACKUPS[@]}
        TO_REMOVE=$((TO_REMOVE - RETENTION_COUNT))
        
        echo "Total backups: $TOTAL_BEFORE"
        echo "To remove:     $TO_REMOVE (keeping newest $RETENTION_COUNT)"
        echo ""
        
        # Remove oldest backups (they are at the end of the sorted array)
        for ((i=RETENTION_COUNT; i<${#BACKUPS[@]}; i++)); do
            BACKUP_DIR="$BACKUP_PATH/${BACKUPS[$i]}"
            SIZE=$(get_dir_size "$BACKUP_DIR")
            
            echo "  Removing: ${BACKUPS[$i]} ($(format_size $SIZE))"
            rm -rf "$BACKUP_DIR"
            
            FREED_SPACE=$((FREED_SPACE + SIZE))
            REMOVED_COUNT=$((REMOVED_COUNT + 1))
        done
        
        echo ""
        echo "Cleanup complete. Remaining backups:"
        for ((i=0; i<5 && i<RETENTION_COUNT; i++)); do
            BACKUP_DIR="$BACKUP_PATH/${BACKUPS[$i]}"
            SIZE=$(get_dir_size "$BACKUP_DIR")
            echo "  ${BACKUPS[$i]} ($(format_size $SIZE))"
        done
    fi

# Time-based retention
elif [ -n "$RETENTION_DAYS" ] && [ "$RETENTION_DAYS" -gt 0 ] 2>/dev/null; then
    CUTOFF_TIMESTAMP=$(date -u -d "$RETENTION_DAYS days ago" +%Y-%m-%d_%H-%M-%S 2>/dev/null || \
                       date -u -v-${RETENTION_DAYS}d +%Y-%m-%d_%H-%M-%S)
    
    echo "Mode: Keep backups younger than $RETENTION_DAYS days"
    echo "Cutoff timestamp: $CUTOFF_TIMESTAMP"
    echo ""
    
    TO_REMOVE=()
    for backup in "${BACKUPS[@]}"; do
        if [[ "$backup" < "$CUTOFF_TIMESTAMP" ]]; then
            TO_REMOVE+=("$backup")
        fi
    done
    
    if [ ${#TO_REMOVE[@]} -eq 0 ]; then
        echo "Total backups: $TOTAL_BEFORE (all within retention period)"
        echo "No cleanup needed."
    else
        echo "Total backups: $TOTAL_BEFORE"
        echo "To remove:     ${#TO_REMOVE[@]} (older than $RETENTION_DAYS days)"
        echo ""
        
        for backup in "${TO_REMOVE[@]}"; do
            BACKUP_DIR="$BACKUP_PATH/$backup"
            SIZE=$(get_dir_size "$BACKUP_DIR")
            
            echo "  Removing: $backup ($(format_size $SIZE))"
            rm -rf "$BACKUP_DIR"
            
            FREED_SPACE=$((FREED_SPACE + SIZE))
            REMOVED_COUNT=$((REMOVED_COUNT + 1))
        done
        
        echo ""
        echo "Cleanup complete."
    fi
    
else
    echo "WARNING: No retention policy configured"
    echo "Set BACKUP_RETENTION_COUNT or BACKUP_RETENTION_DAYS"
    exit 0
fi

# Summary
echo ""
echo "=========================================="
echo "  Cleanup Summary"
echo "=========================================="
echo "Backups removed: $REMOVED_COUNT"
echo "Backups kept:    $((TOTAL_BEFORE - REMOVED_COUNT))"
if [ "$FREED_SPACE" -gt 0 ]; then
    echo "Space freed:     $(format_size $FREED_SPACE)"
fi
echo "=========================================="
