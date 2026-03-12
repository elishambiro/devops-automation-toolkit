#!/bin/bash
# cleanup_docker_cache.sh
# Clears Docker build cache and shows space reclaimed.
# Usage: ./cleanup_docker_cache.sh [--all] [--dry-run]

set -euo pipefail

ALL_CACHE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --all)     ALL_CACHE=true; shift ;;
    --dry-run) DRY_RUN=true;   shift ;;
    *) shift ;;
  esac
done

GREEN='\033[0;32m'
NC='\033[0m'
log() { echo -e "${GREEN}[INFO]${NC} $1"; }

echo ""
echo "================================"
echo "  Docker Cache Cleanup"
if $DRY_RUN; then echo "  MODE: DRY RUN"; fi
echo "================================"
echo ""

log "Current Docker disk usage:"
docker system df
echo ""

if $DRY_RUN; then
  log "Estimating reclaimable space..."
  docker system df
  exit 0
fi

if $ALL_CACHE; then
  log "Removing ALL build cache (including recent)..."
  docker builder prune --all --force
else
  log "Removing unused build cache..."
  docker builder prune --force
fi

echo ""
log "After cleanup:"
docker system df
