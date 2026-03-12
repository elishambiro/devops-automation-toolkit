#!/usr/bin/env bash
# k8s_pvc_status.sh
# Lists all PersistentVolumeClaims across namespaces with their status,
# capacity, storage class, access modes, and bound volume.
# Flags PVCs that are Pending or Lost.
# Usage: ./k8s_pvc_status.sh [--namespace NAMESPACE]

set -euo pipefail

NAMESPACE=""

GREEN="\033[92m"
RED="\033[91m"
YELLOW="\033[93m"
CYAN="\033[96m"
RESET="\033[0m"

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --namespace, -n   Kubernetes namespace (default: all namespaces)"
    echo "  --help            Show this help message"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --namespace|-n) NAMESPACE="$2"; shift 2 ;;
        --help) usage ;;
        *) echo "Unknown argument: $1"; usage ;;
    esac
done

NS_DISPLAY="${NAMESPACE:-all namespaces}"

echo ""
echo "====================================================="
echo "  Kubernetes PVC Status | ${NS_DISPLAY}"
echo "====================================================="
echo ""

if [[ -n "$NAMESPACE" ]]; then
    PVC_JSON=$(kubectl get pvc -n "${NAMESPACE}" -o json 2>/dev/null)
else
    PVC_JSON=$(kubectl get pvc --all-namespaces -o json 2>/dev/null)
fi

TOTAL=$(echo "${PVC_JSON}" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['items']))")

if [[ "${TOTAL}" -eq 0 ]]; then
    echo -e "${YELLOW}No PersistentVolumeClaims found in ${NS_DISPLAY}.${RESET}"
    exit 0
fi

printf "  %-20s %-35s %-10s %-10s %-20s %-15s %s\n" \
    "NAMESPACE" "NAME" "STATUS" "CAPACITY" "ACCESS MODES" "STORAGECLASS" "VOLUME"
echo "  $(printf '%.0s-' {1..130})"

PENDING_COUNT=0
LOST_COUNT=0

echo "${PVC_JSON}" | python3 - << 'PYEOF'
import sys
import json

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

data = json.load(sys.stdin)
pending = []
lost = []

for pvc in data["items"]:
    meta = pvc["metadata"]
    name = meta["name"]
    namespace = meta.get("namespace", "-")
    status = pvc["status"].get("phase", "Unknown")
    capacity = pvc["status"].get("capacity", {}).get("storage", "-")
    access_modes = ",".join(pvc["status"].get("accessModes", pvc["spec"].get("accessModes", [])))
    storage_class = pvc["spec"].get("storageClassName", "-")
    volume = pvc["spec"].get("volumeName", "-")

    if status == "Bound":
        color = GREEN
    elif status == "Pending":
        color = YELLOW
        pending.append(f"{namespace}/{name}")
    else:
        color = RED
        lost.append(f"{namespace}/{name}")

    print(f"  {namespace:20} {color}{name:35}{RESET} {color}{status:10}{RESET} "
          f"{capacity:10} {access_modes:20} {storage_class:15} {volume}")

print()
print(f"  Total PVCs : {len(data['items'])}")
print(f"  Bound      : {len(data['items']) - len(pending) - len(lost)}")
if pending:
    print(f"  {YELLOW}Pending    : {len(pending)}{RESET}")
    for p in pending:
        print(f"    {YELLOW}⚠  {p}{RESET}")
if lost:
    print(f"  {RED}Lost       : {len(lost)}{RESET}")
    for lo in lost:
        print(f"    {RED}✗  {lo}{RESET}")

if not pending and not lost:
    print(f"  {GREEN}All PVCs are Bound.{RESET}")
elif pending:
    print()
    print(f"  {YELLOW}Tip: Pending PVCs may be waiting for a matching PersistentVolume")
    print(f"  or StorageClass provisioner. Check: kubectl describe pvc <name>{RESET}")
PYEOF
