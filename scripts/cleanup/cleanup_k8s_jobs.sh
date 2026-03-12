#!/bin/bash
# cleanup_k8s_jobs.sh
# Removes completed and failed Kubernetes Jobs across namespaces.
# Completed jobs accumulate over time and clutter the cluster.
# Usage: ./cleanup_k8s_jobs.sh [--namespace default] [--dry-run]

set -euo pipefail

NAMESPACE=""
DRY_RUN=false
INCLUDE_FAILED=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --namespace)      NAMESPACE="$2";    shift 2 ;;
    --dry-run)        DRY_RUN=true;      shift ;;
    --include-failed) INCLUDE_FAILED=true; shift ;;
    *) shift ;;
  esac
done

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }

NS_FLAG=""
[[ -n "$NAMESPACE" ]] && NS_FLAG="-n $NAMESPACE" || NS_FLAG="--all-namespaces"

echo ""
echo "========================================"
echo "  K8s Job Cleanup"
if [[ -n "$NAMESPACE" ]]; then
  echo "  Namespace: $NAMESPACE"
else
  echo "  Namespace: all"
fi
if $DRY_RUN; then echo "  MODE: DRY RUN"; fi
echo "========================================"
echo ""

# Get completed jobs
COMPLETED_JOBS=$(kubectl get jobs $NS_FLAG -o json 2>/dev/null \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for job in data.get('items', []):
    conditions = job.get('status', {}).get('conditions', [])
    ns = job['metadata'].get('namespace', 'default')
    name = job['metadata']['name']
    for c in conditions:
        if c['type'] == 'Complete' and c['status'] == 'True':
            print(f'{ns} {name}')
            break
")

FAILED_JOBS=""
if $INCLUDE_FAILED; then
  FAILED_JOBS=$(kubectl get jobs $NS_FLAG -o json 2>/dev/null \
    | python3 -c "
import json, sys
data = json.load(sys.stdin)
for job in data.get('items', []):
    conditions = job.get('status', {}).get('conditions', [])
    ns = job['metadata'].get('namespace', 'default')
    name = job['metadata']['name']
    for c in conditions:
        if c['type'] == 'Failed' and c['status'] == 'True':
            print(f'{ns} {name}')
            break
")
fi

COMPLETED_COUNT=$(echo "$COMPLETED_JOBS" | grep -c '\S' || true)
FAILED_COUNT=$(echo "$FAILED_JOBS" | grep -c '\S' || true)

log "Completed jobs found: $COMPLETED_COUNT"
$INCLUDE_FAILED && log "Failed jobs found:    $FAILED_COUNT"

for line in $COMPLETED_JOBS $FAILED_JOBS; do
  NS=$(echo "$line" | awk '{print $1}')
  NAME=$(echo "$line" | awk '{print $2}')
  [[ -z "$NAME" ]] && continue
  if $DRY_RUN; then
    warn "[DRY RUN] Would delete job: $NS/$NAME"
  else
    kubectl delete job "$NAME" -n "$NS" --ignore-not-found
    log "Deleted: $NS/$NAME"
  fi
done

log "Done."
