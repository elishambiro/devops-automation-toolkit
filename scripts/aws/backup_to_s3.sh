#!/bin/bash
# backup_to_s3.sh
# Backs up a local directory to an S3 bucket with timestamp prefix.
# Usage: ./backup_to_s3.sh --source /data/app --bucket my-backups --prefix daily

set -euo pipefail

SOURCE_DIR=""
S3_BUCKET=""
S3_PREFIX="backup"
RETENTION_DAYS=30
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --source)    SOURCE_DIR="$2";    shift 2 ;;
    --bucket)    S3_BUCKET="$2";     shift 2 ;;
    --prefix)    S3_PREFIX="$2";     shift 2 ;;
    --retain)    RETENTION_DAYS="$2"; shift 2 ;;
    --dry-run)   DRY_RUN=true;       shift ;;
    *) shift ;;
  esac
done

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log()   { echo -e "${GREEN}[INFO]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

[[ -z "$SOURCE_DIR" ]] && error "Missing --source"
[[ -z "$S3_BUCKET" ]]  && error "Missing --bucket"
[[ -d "$SOURCE_DIR" ]]  || error "Source directory not found: $SOURCE_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="backup_${TIMESTAMP}.tar.gz"
TMP_FILE="/tmp/$ARCHIVE_NAME"
S3_KEY="${S3_PREFIX}/${ARCHIVE_NAME}"

echo ""
echo "====================================="
echo "  S3 Backup Script"
echo "  Source:  $SOURCE_DIR"
echo "  Bucket:  s3://$S3_BUCKET/$S3_KEY"
echo "  Retain:  $RETENTION_DAYS days"
if $DRY_RUN; then echo "  MODE: DRY RUN"; fi
echo "====================================="
echo ""

log "Creating archive: $ARCHIVE_NAME"
if ! $DRY_RUN; then
  tar -czf "$TMP_FILE" -C "$(dirname "$SOURCE_DIR")" "$(basename "$SOURCE_DIR")"
  SIZE=$(du -sh "$TMP_FILE" | cut -f1)
  log "Archive size: $SIZE"
fi

log "Uploading to s3://$S3_BUCKET/$S3_KEY"
if ! $DRY_RUN; then
  aws s3 cp "$TMP_FILE" "s3://$S3_BUCKET/$S3_KEY"
  rm -f "$TMP_FILE"
  log "Upload complete!"
fi

log "Cleaning up backups older than $RETENTION_DAYS days..."
CUTOFF=$(date -d "-${RETENTION_DAYS} days" +%Y-%m-%d 2>/dev/null || date -v "-${RETENTION_DAYS}d" +%Y-%m-%d)
if ! $DRY_RUN; then
  aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" \
    | awk -v cutoff="$CUTOFF" '$1 < cutoff {print $4}' \
    | while read -r key; do
        log "Deleting old backup: $key"
        aws s3 rm "s3://$S3_BUCKET/$S3_PREFIX/$key"
      done
fi

log "Backup completed successfully."
