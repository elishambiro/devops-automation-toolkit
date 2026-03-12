#!/bin/bash
# rotate_logs.sh
# Compresses logs older than N days and deletes archives older than M days.
# Usage: ./rotate_logs.sh --dir /var/log/app --compress-after 7 --delete-after 30

set -euo pipefail

LOG_DIR="/var/log"
COMPRESS_AFTER=7
DELETE_AFTER=30
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --dir)             LOG_DIR="$2";         shift 2 ;;
    --compress-after)  COMPRESS_AFTER="$2";  shift 2 ;;
    --delete-after)    DELETE_AFTER="$2";    shift 2 ;;
    --dry-run)         DRY_RUN=true;         shift ;;
    *) shift ;;
  esac
done

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo ""
echo "======================================="
echo "  Log Rotation Script"
echo "  Dir: $LOG_DIR"
echo "  Compress after: ${COMPRESS_AFTER} days"
echo "  Delete after:   ${DELETE_AFTER} days"
if $DRY_RUN; then echo "  MODE: DRY RUN"; fi
echo "======================================="
echo ""

if [ ! -d "$LOG_DIR" ]; then
  echo "Directory $LOG_DIR not found."
  exit 1
fi

# Compress logs older than COMPRESS_AFTER days
log "Finding .log files older than ${COMPRESS_AFTER} days..."
COMPRESS_COUNT=0
while IFS= read -r -d '' file; do
  if $DRY_RUN; then
    warn "[DRY RUN] Would compress: $file"
  else
    gzip "$file"
    log "Compressed: $file"
  fi
  ((COMPRESS_COUNT++))
done < <(find "$LOG_DIR" -name "*.log" -mtime +"$COMPRESS_AFTER" -print0 2>/dev/null)

# Delete archives older than DELETE_AFTER days
log "Finding .gz files older than ${DELETE_AFTER} days..."
DELETE_COUNT=0
while IFS= read -r -d '' file; do
  if $DRY_RUN; then
    warn "[DRY RUN] Would delete: $file"
  else
    rm -f "$file"
    log "Deleted: $file"
  fi
  ((DELETE_COUNT++))
done < <(find "$LOG_DIR" -name "*.gz" -mtime +"$DELETE_AFTER" -print0 2>/dev/null)

echo ""
log "Done. Compressed: $COMPRESS_COUNT files, Deleted: $DELETE_COUNT archives."
