#!/bin/bash
# k8s_scale.sh
# Scale all deployments in a namespace up or down.
# Useful for saving resources outside business hours.
# Usage: ./k8s_scale.sh --namespace production --replicas 0
#        ./k8s_scale.sh --namespace production --replicas 2

set -euo pipefail

NAMESPACE=""
REPLICAS=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --namespace) NAMESPACE="$2"; shift 2 ;;
    --replicas)  REPLICAS="$2";  shift 2 ;;
    --dry-run)   DRY_RUN=true;   shift ;;
    *) shift ;;
  esac
done

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

[[ -z "$NAMESPACE" ]] && { echo "Missing --namespace"; exit 1; }
[[ -z "$REPLICAS" ]]  && { echo "Missing --replicas"; exit 1; }

echo ""
echo "======================================="
echo "  K8s Scale Script"
echo "  Namespace: $NAMESPACE"
echo "  Replicas:  $REPLICAS"
if $DRY_RUN; then echo "  MODE: DRY RUN"; fi
echo "======================================="
echo ""

DEPLOYMENTS=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)

if [[ -z "$DEPLOYMENTS" ]]; then
  warn "No deployments found in namespace: $NAMESPACE"
  exit 0
fi

for deploy in $DEPLOYMENTS; do
  CURRENT=$(kubectl get deployment "$deploy" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
  if $DRY_RUN; then
    warn "[DRY RUN] Would scale $deploy: $CURRENT → $REPLICAS"
  else
    kubectl scale deployment "$deploy" -n "$NAMESPACE" --replicas="$REPLICAS"
    log "Scaled $deploy: $CURRENT → $REPLICAS"
  fi
done

log "Done. Use 'kubectl get pods -n $NAMESPACE' to verify."
