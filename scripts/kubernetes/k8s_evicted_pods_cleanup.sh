#!/bin/bash
# k8s_evicted_pods_cleanup.sh
# Removes evicted and failed pods that clutter the cluster.
# Evicted pods don't clean themselves up automatically.
# Usage: ./k8s_evicted_pods_cleanup.sh [--namespace default] [--dry-run]

set -euo pipefail

NAMESPACE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --namespace) NAMESPACE="$2"; shift 2 ;;
    --dry-run)   DRY_RUN=true;   shift ;;
    *) shift ;;
  esac
done

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }

NS_FLAG=""
[[ -n "$NAMESPACE" ]] && NS_FLAG="-n $NAMESPACE" || NS_FLAG="--all-namespaces"

echo ""
echo "========================================"
echo "  K8s Evicted/Failed Pod Cleanup"
if [[ -n "$NAMESPACE" ]]; then echo "  Namespace: $NAMESPACE"; else echo "  Namespace: all"; fi
if $DRY_RUN; then echo "  MODE: DRY RUN"; fi
echo "========================================"
echo ""

# Get evicted pods
EVICTED=$(kubectl get pods $NS_FLAG --field-selector=status.phase=Failed \
  -o json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pod in data.get('items', []):
    reason = pod.get('status', {}).get('reason', '')
    ns = pod['metadata'].get('namespace', 'default')
    name = pod['metadata']['name']
    if reason in ('Evicted', 'OOMKilled') or pod['status']['phase'] == 'Failed':
        print(f'{ns} {name} {reason}')
")

COUNT=$(echo "$EVICTED" | grep -c '\S' 2>/dev/null || echo 0)
log "Found $COUNT evicted/failed pod(s)"

if [[ "$COUNT" -eq 0 ]]; then
  log "Nothing to clean up."
  exit 0
fi

while IFS=' ' read -r ns name reason; do
  [[ -z "$name" ]] && continue
  if $DRY_RUN; then
    warn "[DRY RUN] Would delete: $ns/$name ($reason)"
  else
    kubectl delete pod "$name" -n "$ns" --ignore-not-found
    log "Deleted: $ns/$name ($reason)"
  fi
done <<< "$EVICTED"

log "Cleanup complete."
