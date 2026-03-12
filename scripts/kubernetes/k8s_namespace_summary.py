#!/usr/bin/env python3
"""
k8s_namespace_summary.py
Prints a summary of all namespaces: pod count, running/failed, deployments, services.
Usage: python k8s_namespace_summary.py [--namespace specific-ns]
"""

import subprocess
import json
import sys
import argparse

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def kubectl(args: list) -> dict:
    result = subprocess.run(["kubectl"] + args + ["-o", "json"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{RED}kubectl error: {result.stderr}{RESET}")
        sys.exit(1)
    return json.loads(result.stdout)


def get_namespaces(specific: str = None) -> list:
    if specific:
        return [specific]
    data = kubectl(["get", "namespaces"])
    return [item["metadata"]["name"] for item in data["items"]]


def get_ns_summary(ns: str) -> dict:
    pods = kubectl(["get", "pods", "-n", ns])["items"]
    deployments = kubectl(["get", "deployments", "-n", ns])["items"]
    services = kubectl(["get", "services", "-n", ns])["items"]

    running = sum(1 for p in pods if p.get("status", {}).get("phase") == "Running")
    failed = sum(1 for p in pods if p.get("status", {}).get("phase") in ("Failed", "CrashLoopBackOff"))

    return {
        "namespace": ns,
        "pods": len(pods),
        "running": running,
        "failed": failed,
        "deployments": len(deployments),
        "services": len(services),
    }


def main():
    parser = argparse.ArgumentParser(description="K8s namespace summary")
    parser.add_argument("--namespace", help="Specific namespace")
    args = parser.parse_args()

    namespaces = get_namespaces(args.namespace)

    print(f"\n{'='*75}")
    print(f"  Kubernetes Namespace Summary")
    print(f"{'='*75}\n")
    print(f"{'NAMESPACE':25} {'PODS':6} {'RUNNING':8} {'FAILED':7} {'DEPLOYS':8} {'SERVICES'}")
    print("-" * 75)

    for ns in namespaces:
        s = get_ns_summary(ns)
        color = RED if s["failed"] > 0 else (YELLOW if s["pods"] == 0 else GREEN)
        print(f"{color}{s['namespace']:25} {s['pods']:<6} {s['running']:<8} {s['failed']:<7} {s['deployments']:<8} {s['services']}{RESET}")

    print(f"\n{CYAN}Total namespaces: {len(namespaces)}{RESET}\n")


if __name__ == "__main__":
    main()
