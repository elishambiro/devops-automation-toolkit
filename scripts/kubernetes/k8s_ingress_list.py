#!/usr/bin/env python3
"""
k8s_ingress_list.py
Lists all Kubernetes Ingress resources across namespaces with their hosts,
paths, backend services, TLS status, and ingress class.
Usage: python k8s_ingress_list.py [--namespace NAMESPACE]
"""

import argparse
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
        print(f"{RED}kubectl error: {result.stderr.strip()}{RESET}")
        sys.exit(1)
    return json.loads(result.stdout)


def get_tls_hosts(ingress: dict) -> set:
    tls_entries = ingress.get("spec", {}).get("tls", [])
    tls_hosts = set()
    for entry in tls_entries:
        for host in entry.get("hosts", []):
            tls_hosts.add(host)
    return tls_hosts


def get_ingress_class(ingress: dict) -> str:
    # Try annotation first (older style), then spec.ingressClassName
    annotations = ingress["metadata"].get("annotations", {})
    cls = annotations.get("kubernetes.io/ingress.class", "")
    if not cls:
        cls = ingress.get("spec", {}).get("ingressClassName", "")
    return cls or "-"


def print_ingress(ingress: dict):
    meta = ingress["metadata"]
    namespace = meta.get("namespace", "-")
    name = meta["name"]
    ingress_class = get_ingress_class(ingress)
    tls_hosts = get_tls_hosts(ingress)

    rules = ingress.get("spec", {}).get("rules", [])
    if not rules:
        print(f"  {YELLOW}{namespace}/{name}{RESET}  class={ingress_class}  {RED}(no rules){RESET}")
        return

    for i, rule in enumerate(rules):
        host = rule.get("host", "*")
        tls = f"{GREEN}TLS{RESET}" if host in tls_hosts else f"{RED}no-TLS{RESET}"
        http = rule.get("http", {})
        paths = http.get("paths", [])

        prefix = f"{namespace:20} {name:35}" if i == 0 else f"{'':20} {'':35}"
        class_str = f"{ingress_class:12}" if i == 0 else f"{'':12}"

        for j, path_entry in enumerate(paths):
            path = path_entry.get("path", "/")
            path_type = path_entry.get("pathType", "")
            backend = path_entry.get("backend", {})

            # Handle networking.k8s.io/v1 (service.name) vs extensions/v1beta1 (serviceName)
            svc = backend.get("service", {})
            svc_name = svc.get("name", backend.get("serviceName", "?"))
            svc_port_obj = svc.get("port", {})
            svc_port = svc_port_obj.get("number", svc_port_obj.get("name", backend.get("servicePort", "?")))

            host_str = f"{CYAN}{host}{RESET}" if j == 0 else f"{'':25}"
            tls_str = tls if j == 0 else f"{'':10}"

            row_prefix = prefix if (i == 0 and j == 0) else f"{'':20} {'':35}"
            row_class = class_str if (i == 0 and j == 0) else f"{'':12}"

            print(f"  {row_prefix} {row_class} "
                  f"{host_str:45} {tls_str:14} "
                  f"{path:25} {path_type:12} {svc_name}:{svc_port}")


def main():
    parser = argparse.ArgumentParser(description="List all Kubernetes Ingress resources")
    parser.add_argument("--namespace", "-n", default="",
                        help="Namespace to query (default: all namespaces)")
    args = parser.parse_args()

    ns_display = args.namespace if args.namespace else "all namespaces"
    print(f"\n{'='*90}")
    print(f"  Kubernetes Ingress List | {ns_display}")
    print(f"{'='*90}\n")

    if args.namespace:
        data = kubectl(["get", "ingresses", "-n", args.namespace])
    else:
        data = kubectl(["get", "ingresses", "--all-namespaces"])

    ingresses = data.get("items", [])

    if not ingresses:
        print(f"{YELLOW}No Ingress resources found.{RESET}")
        return

    print(f"  {'NAMESPACE':20} {'NAME':35} {'CLASS':12} "
          f"{'HOST':45} {'TLS':14} {'PATH':25} {'TYPE':12} BACKEND")
    print("  " + "-" * 180)

    no_tls = []
    for ingress in ingresses:
        print_ingress(ingress)
        tls_hosts = get_tls_hosts(ingress)
        rules = ingress.get("spec", {}).get("rules", [])
        for rule in rules:
            host = rule.get("host", "")
            if host and host not in tls_hosts:
                no_tls.append(f"{ingress['metadata'].get('namespace', '-')}/{ingress['metadata']['name']} → {host}")

    print(f"\n  Total Ingress resources: {len(ingresses)}")

    if no_tls:
        print(f"\n  {YELLOW}Hosts without TLS:{RESET}")
        for item in no_tls:
            print(f"    {RED}⚠  {item}{RESET}")
        print(f"\n  {CYAN}Tip:{RESET} Consider using cert-manager for automatic TLS certificate management.")
    else:
        print(f"\n  {GREEN}All hosts have TLS configured.{RESET}")


if __name__ == "__main__":
    main()
