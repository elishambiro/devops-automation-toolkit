#!/usr/bin/env bash
# k8s_rolling_restart.sh
# Triggers a rolling restart of all (or selected) deployments in a namespace.
# Useful for picking up new ConfigMaps, Secrets, or forcing a pod refresh.
# Usage: ./k8s_rolling_restart.sh --namespace production [--selector app=nginx] [--dry-run]

set -euo pipefail

NAMESPACE="default"
SELECTOR=""
DRY_RUN=false

GREEN="\033[92m"
YELLOW="\033[93m"
CYAN="\033[96m"
RED="\033[91m"
RESET="\033[0m"

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --namespace, -n   Kubernetes namespace (default: default)"
    echo "  --selector, -l    Label selector (e.g. app=nginx)"
    echo "  --dry-run         Print what would be restarted without doing it"
    echo "  --help            Show this help message"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --namespace|-n) NAMESPACE="$2"; shift 2 ;;
        --selector|-l)  SELECTOR="$2"; shift 2 ;;
        --dry-run)       DRY_RUN=true; shift ;;
        --help)          usage ;;
        *) echo "Unknown argument: $1"; usage ;;
    esac
done

echo ""
echo "================================================="
echo "  K8s Rolling Restart"
echo "  Namespace : $NAMESPACE"
if [[ -n "$SELECTOR" ]]; then
    echo "  Selector  : $SELECTOR"
fi
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "  Mode      : ${YELLOW}DRY RUN${RESET}"
fi
echo "================================================="
echo ""

# Build kubectl command
KUBECTL_ARGS=("get" "deployments" "-n" "$NAMESPACE" "-o" "jsonpath={.items[*].metadata.name}")
if [[ -n "$SELECTOR" ]]; then
    KUBECTL_ARGS+=("-l" "$SELECTOR")
fi

DEPLOYMENTS=$(kubectl "${KUBECTL_ARGS[@]}" 2>/dev/null || true)

if [[ -z "$DEPLOYMENTS" ]]; then
    echo -e "${YELLOW}No deployments found in namespace '${NAMESPACE}'${RESET}"
    exit 0
fi

COUNT=0
FAILED=0

for DEPLOY in $DEPLOYMENTS; do
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "  ${CYAN}[DRY RUN]${RESET} Would restart deployment/${DEPLOY}"
    else
        echo -ne "  Restarting ${CYAN}${DEPLOY}${RESET} ... "
        if kubectl rollout restart deployment/"${DEPLOY}" -n "$NAMESPACE" > /dev/null 2>&1; then
            echo -e "${GREEN}OK${RESET}"
            COUNT=$((COUNT + 1))
        else
            echo -e "${RED}FAILED${RESET}"
            FAILED=$((FAILED + 1))
        fi
    fi
done

echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    TOTAL=$(echo "$DEPLOYMENTS" | wc -w | tr -d ' ')
    echo -e "${YELLOW}Dry run complete. Would restart ${TOTAL} deployment(s).${RESET}"
else
    echo -e "${GREEN}Restarted: ${COUNT}${RESET}"
    if [[ $FAILED -gt 0 ]]; then
        echo -e "${RED}Failed:    ${FAILED}${RESET}"
        exit 1
    fi
    echo ""
    echo "Monitor rollout status with:"
    echo "  kubectl rollout status deployment -n ${NAMESPACE}"
fi
