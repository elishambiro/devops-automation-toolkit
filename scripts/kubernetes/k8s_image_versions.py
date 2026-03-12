#!/usr/bin/env python3
"""
k8s_image_versions.py
Lists all container images running in a Kubernetes cluster by namespace.
Useful for auditing versions and finding outdated/unknown images.
Usage: python k8s_image_versions.py [--namespace production]
"""

import subprocess
import json
import argparse
import sys
from collections import defaultdict

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def kubectl_get(resource: str, namespace: str = None) -> dict:
    cmd = ["kubectl", "get", resource, "-o", "json"]
    if namespace:
        cmd += ["-n", namespace]
    else:
        cmd += ["--all-namespaces"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"kubectl error: {result.stderr}")
        sys.exit(1)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description="List K8s container image versions")
    parser.add_argument("--namespace", help="Filter by namespace")
    args = parser.parse_args()

    data = kubectl_get("pods", args.namespace)
    pods = data["items"]

    images_by_ns = defaultdict(set)
    for pod in pods:
        ns = pod["metadata"].get("namespace", "default")
        containers = pod["spec"].get("containers", []) + pod["spec"].get("initContainers", [])
        for c in containers:
            images_by_ns[ns].add(c["image"])

    print(f"\n{'='*70}")
    print("  Container Image Versions")
    print(f"{'='*70}\n")

    total = 0
    for ns in sorted(images_by_ns.keys()):
        print(f"{CYAN}[{ns}]{RESET}")
        for image in sorted(images_by_ns[ns]):
            tag = image.split(":")[-1] if ":" in image else "latest"
            color = YELLOW if tag == "latest" else GREEN
            print(f"  {color}{image}{RESET}")
            total += 1
        print()

    print(f"Total unique images: {total}")
    latest_count = sum(1 for ns in images_by_ns for img in images_by_ns[ns] if img.endswith(":latest") or ":" not in img)
    if latest_count:
        print(f"{YELLOW}Warning: {latest_count} image(s) using :latest tag (not recommended for production){RESET}")


if __name__ == "__main__":
    main()
