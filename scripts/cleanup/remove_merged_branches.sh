#!/bin/bash
# remove_merged_branches.sh
# Removes local and remote git branches that have been merged into main/master.
# Usage: ./remove_merged_branches.sh [--remote] [--dry-run] [--base main]

set -euo pipefail

DELETE_REMOTE=false
DRY_RUN=false
BASE_BRANCH="main"
PROTECTED=("main" "master" "develop" "staging" "production")

while [[ $# -gt 0 ]]; do
  case $1 in
    --remote)   DELETE_REMOTE=true;  shift ;;
    --dry-run)  DRY_RUN=true;        shift ;;
    --base)     BASE_BRANCH="$2";    shift 2 ;;
    *) shift ;;
  esac
done

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }

is_protected() {
  local branch="$1"
  for p in "${PROTECTED[@]}"; do
    [[ "$branch" == "$p" ]] && return 0
  done
  return 1
}

echo ""
echo "========================================"
echo "  Merged Branch Cleanup"
echo "  Base branch: $BASE_BRANCH"
echo "  Delete remote: $DELETE_REMOTE"
if $DRY_RUN; then echo "  MODE: DRY RUN"; fi
echo "========================================"
echo ""

# Ensure we're up to date
log "Fetching latest remote state..."
git fetch --prune --quiet

# Local merged branches
log "Scanning local merged branches..."
LOCAL_DELETED=0
while IFS= read -r branch; do
  branch=$(echo "$branch" | sed 's/^[[:space:]]*//')
  [[ -z "$branch" ]] && continue
  is_protected "$branch" && continue

  if $DRY_RUN; then
    warn "[DRY RUN] Would delete local: $branch"
  else
    git branch -d "$branch"
    log "Deleted local: $branch"
  fi
  ((LOCAL_DELETED++))
done < <(git branch --merged "$BASE_BRANCH" | grep -v "^\*" || true)

# Remote merged branches
if $DELETE_REMOTE; then
  log "Scanning remote merged branches..."
  REMOTE_DELETED=0
  while IFS= read -r branch; do
    branch=$(echo "$branch" | sed 's|origin/||' | sed 's/^[[:space:]]*//')
    [[ -z "$branch" ]] && continue
    is_protected "$branch" && continue

    if $DRY_RUN; then
      warn "[DRY RUN] Would delete remote: origin/$branch"
    else
      git push origin --delete "$branch"
      log "Deleted remote: origin/$branch"
    fi
    ((REMOTE_DELETED++))
  done < <(git branch -r --merged "origin/$BASE_BRANCH" | grep -v "HEAD\|$BASE_BRANCH" || true)
  log "Remote branches deleted: $REMOTE_DELETED"
fi

log "Local branches deleted: $LOCAL_DELETED"
log "Done."
