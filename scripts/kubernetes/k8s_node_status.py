#!/usr/bin/env python3
"""
k8s_node_status.py
Shows health status, roles, and resource capacity of all Kubernetes nodes.
Usage: python k8s_node_status.py
"""

import json
import subprocess
import sys

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


def is_node_ready(node: dict) -> bool:
    for condition in node.get("status", {}).get("conditions", []):
        if condition["type"] == "Ready":
            return condition["status"] == "True"
    return False


def get_node_roles(node: dict) -> str:
    labels = node["metadata"].get("labels", {})
    roles = []
    for label in labels:
        if "node-role.kubernetes.io/" in label:
            role = label.split("/")[-1]
            roles.append(role)
    return ",".join(roles) if roles else "worker"


def parse_cpu(cpu_str: str) -> float:
    if cpu_str.endswith("m"):
        return float(cpu_str[:-1]) / 1000
    return float(cpu_str)


def parse_memory_gi(mem_str: str) -> float:
    if mem_str.endswith("Ki"):
        return float(mem_str[:-2]) / (1024 * 1024)
    if mem_str.endswith("Mi"):
        return float(mem_str[:-2]) / 1024
    if mem_str.endswith("Gi"):
        return float(mem_str[:-2])
    return float(mem_str) / (1024 ** 3)


def main():
    nodes = kubectl(["get", "nodes"])["items"]

    print(f"\n{'='*85}")
    print("  Kubernetes Node Status")
    print(f"{'='*85}\n")
    print(f"{'NAME':30} {'ROLE':12} {'STATUS':8} {'VERSION':16} {'CPU':8} {'MEMORY':10} {'PODS'}")
    print("-" * 85)

    not_ready = []
    for node in nodes:
        name = node["metadata"]["name"]
        role = get_node_roles(node)
        ready = is_node_ready(node)
        version = node["status"]["nodeInfo"]["kubeletVersion"]
        allocatable = node["status"]["allocatable"]

        cpu = parse_cpu(allocatable.get("cpu", "0"))
        mem = parse_memory_gi(allocatable.get("memory", "0Ki"))
        max_pods = allocatable.get("pods", "0")

        status_str = "Ready" if ready else "NotReady"
        color = GREEN if ready else RED

        taint_str = ""
        taints = node["spec"].get("taints", [])
        if taints:
            taint_str = f" [{','.join(t['effect'] for t in taints)}]"

        print(f"{color}{name:30}{RESET} {role:12} {color}{status_str:8}{RESET} "
              f"{version:16} {cpu:.1f}CPU   {mem:.1f}Gi   {max_pods}{taint_str}")

        if not ready:
            not_ready.append(name)

    print(f"\nTotal nodes: {len(nodes)}")
    if not_ready:
        print(f"{RED}NOT READY: {', '.join(not_ready)}{RESET}")
    else:
        print(f"{GREEN}All nodes are Ready{RESET}")


if __name__ == "__main__":
    main()
