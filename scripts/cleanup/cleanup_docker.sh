#!/bin/bash
# cleanup_docker.sh
# Removes stopped containers, dangling images, unused volumes and networks.
# Usage: ./cleanup_docker.sh [--dry-run] [--force]

set -euo pipefail

DRY_RUN=false
FORCE=false

for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=true ;;
    --force)   FORCE=true ;;
  esac
done

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }

echo ""
echo "======================================"
echo "  Docker Cleanup Script"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
if $DRY_RUN; then echo "  MODE: DRY RUN (no changes)"; fi
echo "======================================"
echo ""

STOPPED_CONTAINERS=$(docker ps -aq --filter status=exited | wc -l | tr -d ' ')
DANGLING_IMAGES=$(docker images -f "dangling=true" -q | wc -l | tr -d ' ')
UNUSED_VOLUMES=$(docker volume ls -qf dangling=true | wc -l | tr -d ' ')

log "Stopped containers: $STOPPED_CONTAINERS"
log "Dangling images:    $DANGLING_IMAGES"
log "Unused volumes:     $UNUSED_VOLUMES"
echo ""

if $DRY_RUN; then
  warn "Dry run mode - no changes made"
  exit 0
fi

if ! $FORCE; then
  read -p "Proceed with cleanup? (y/N): " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
fi

log "Removing stopped containers..."
docker container prune -f

log "Removing dangling images..."
docker image prune -f

log "Removing unused volumes..."
docker volume prune -f

log "Removing unused networks..."
docker network prune -f

echo ""
log "Cleanup complete!"
docker system df
