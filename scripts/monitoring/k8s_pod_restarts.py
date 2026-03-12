#!/usr/bin/env python3
"""
k8s_pod_restarts.py
Finds Kubernetes pods with high restart counts across all namespaces.
Useful for detecting crashlooping pods early.
Usage: python k8s_pod_restarts.py --threshold 5 --namespace production
"""

import argparse
import subprocess
import json
import sys

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"


def get_pods(namespace: str = None) -> list:
    cmd = ["kubectl", "get", "pods", "-o", "json"]
    if namespace:
        cmd += ["-n", namespace]
    else:
        cmd += ["--all-namespaces"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{RED}Error running kubectl: {result.stderr}{RESET}")
        sys.exit(1)

    data = json.loads(result.stdout)
    return data.get("items", [])


def parse_pod(pod: dict, all_namespaces: bool) -> dict:
    meta = pod["metadata"]
    ns = meta.get("namespace", "default")
    name = meta["name"]
    containers = pod["status"].get("containerStatuses", [])
    total_restarts = sum(c.get("restartCount", 0) for c in containers)
    phase = pod["status"].get("phase", "Unknown")
    return {"namespace": ns, "name": name, "restarts": total_restarts, "phase": phase}


def main():
    parser = argparse.ArgumentParser(description="Find pods with high restart counts")
    parser.add_argument("--threshold", type=int, default=5, help="Restart count threshold")
    parser.add_argument("--namespace", help="Specific namespace (default: all)")
    args = parser.parse_args()

    pods = get_pods(args.namespace)
    parsed = [parse_pod(p, not args.namespace) for p in pods]
    flagged = [p for p in parsed if p["restarts"] >= args.threshold]
    flagged.sort(key=lambda x: x["restarts"], reverse=True)

    print(f"\n{'='*70}")
    print(f"  K8s Pod Restart Report (threshold: {args.threshold})")
    print(f"{'='*70}\n")
    print(f"{'NAMESPACE':20} {'POD':40} {'RESTARTS':10} {'PHASE'}")
    print("-" * 70)

    if not flagged:
        print(f"{GREEN}All pods are healthy (no pod exceeds {args.threshold} restarts){RESET}")
    else:
        for p in flagged:
            color = RED if p["restarts"] >= 20 else YELLOW
            print(f"{color}{p['namespace']:20} {p['name']:40} {p['restarts']:<10} {p['phase']}{RESET}")
        print(f"\n{RED}ALERT: {len(flagged)} pod(s) with high restart count!{RESET}")

    print(f"\nTotal pods checked: {len(parsed)}")


if __name__ == "__main__":
    main()
