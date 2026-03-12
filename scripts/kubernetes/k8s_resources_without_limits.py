#!/usr/bin/env python3
"""
k8s_resources_without_limits.py
Finds containers running without CPU or memory resource limits.
Missing limits can cause a single pod to starve the entire node.
Usage: python k8s_resources_without_limits.py [--namespace production]
"""

import argparse
import json
import subprocess
import sys

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"


def kubectl(args: list) -> dict:
    result = subprocess.run(["kubectl"] + args + ["-o", "json"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{RED}kubectl error: {result.stderr}{RESET}")
        sys.exit(1)
    return json.loads(result.stdout)


def check_resources(container: dict) -> dict:
    resources = container.get("resources", {})
    limits = resources.get("limits", {})
    requests = resources.get("requests", {})
    return {
        "has_cpu_limit": "cpu" in limits,
        "has_mem_limit": "memory" in limits,
        "has_cpu_request": "cpu" in requests,
        "has_mem_request": "memory" in requests,
        "cpu_limit": limits.get("cpu", "-"),
        "mem_limit": limits.get("memory", "-"),
        "cpu_request": requests.get("cpu", "-"),
        "mem_request": requests.get("memory", "-"),
    }


def main():
    parser = argparse.ArgumentParser(description="Find containers without resource limits")
    parser.add_argument("--namespace", help="Specific namespace (default: all)")
    parser.add_argument("--limits-only", action="store_true", help="Only check limits, not requests")
    args = parser.parse_args()

    ns_args = ["-n", args.namespace] if args.namespace else ["--all-namespaces"]
    data = kubectl(["get", "pods"] + ns_args)
    pods = data["items"]

    print(f"\n{'='*80}")
    print(f"  K8s Resource Limits Check")
    print(f"{'='*80}\n")

    violations = []
    for pod in pods:
        ns = pod["metadata"].get("namespace", "default")
        pod_name = pod["metadata"]["name"]
        phase = pod.get("status", {}).get("phase", "Unknown")

        if phase not in ("Running", "Pending"):
            continue

        for container in pod["spec"].get("containers", []):
            c_name = container["name"]
            res = check_resources(container)

            missing = []
            if not res["has_cpu_limit"]:
                missing.append("cpu_limit")
            if not res["has_mem_limit"]:
                missing.append("mem_limit")
            if not args.limits_only:
                if not res["has_cpu_request"]:
                    missing.append("cpu_request")
                if not res["has_mem_request"]:
                    missing.append("mem_request")

            if missing:
                violations.append({
                    "namespace": ns, "pod": pod_name,
                    "container": c_name, "missing": missing, "res": res
                })

    if not violations:
        print(f"{GREEN}All containers have resource limits defined!{RESET}")
        return

    print(f"{'NAMESPACE':20} {'POD':35} {'CONTAINER':20} MISSING")
    print("-" * 80)
    for v in violations:
        missing_str = ", ".join(v["missing"])
        severity = RED if any("limit" in m for m in v["missing"]) else YELLOW
        print(f"{severity}{v['namespace']:20} {v['pod']:35} {v['container']:20} {missing_str}{RESET}")

    print(f"\n{RED}Found {len(violations)} container(s) without proper resource configuration{RESET}")
    print(f"\nRecommendation: Add resources.limits.cpu and resources.limits.memory to all containers.")


if __name__ == "__main__":
    main()
