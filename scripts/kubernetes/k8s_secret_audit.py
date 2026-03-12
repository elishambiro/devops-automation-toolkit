#!/usr/bin/env python3
"""
k8s_secret_audit.py
Audits Kubernetes Secrets: lists all secrets, their types, sizes, and age.
Flags secrets that are very large (potential misuse) or very old (rotation candidates).
Usage: python k8s_secret_audit.py [--namespace NAMESPACE] [--max-age-days 365] [--max-size-kb 10]
"""

import argparse
import base64
import json
import subprocess
import sys
from datetime import datetime, timezone

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

SENSITIVE_TYPES = {
    "kubernetes.io/tls",
    "kubernetes.io/dockerconfigjson",
    "kubernetes.io/dockercfg",
    "kubernetes.io/ssh-auth",
    "kubernetes.io/basic-auth",
    "kubernetes.io/service-account-token",
}


def kubectl(args: list) -> dict:
    result = subprocess.run(["kubectl"] + args + ["-o", "json"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{RED}kubectl error: {result.stderr.strip()}{RESET}")
        sys.exit(1)
    return json.loads(result.stdout)


def get_secret_size_kb(secret: dict) -> float:
    """Calculate total size of all secret values in KB."""
    data = secret.get("data", {})
    total_bytes = 0
    for v in data.values():
        try:
            total_bytes += len(base64.b64decode(v))
        except Exception:
            total_bytes += len(v)
    return total_bytes / 1024


def get_age_days(secret: dict) -> int:
    created_str = secret["metadata"].get("creationTimestamp", "")
    if not created_str:
        return 0
    created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return (now - created).days


def main():
    parser = argparse.ArgumentParser(description="Audit Kubernetes Secrets")
    parser.add_argument("--namespace", "-n", default="", help="Namespace (empty = all namespaces)")
    parser.add_argument("--max-age-days", type=int, default=365,
                        help="Flag secrets older than this many days (default: 365)")
    parser.add_argument("--max-size-kb", type=float, default=10,
                        help="Flag secrets larger than this KB (default: 10)")
    args = parser.parse_args()

    ns_display = args.namespace if args.namespace else "all namespaces"
    print(f"\n{'='*80}")
    print(f"  Kubernetes Secret Audit | {ns_display}")
    print(f"  Flagging: age > {args.max_age_days}d OR size > {args.max_size_kb}KB")
    print(f"{'='*80}\n")

    if args.namespace:
        data = kubectl(["get", "secrets", "-n", args.namespace])
    else:
        data = kubectl(["get", "secrets", "--all-namespaces"])

    secrets = data.get("items", [])
    if not secrets:
        print(f"{YELLOW}No secrets found.{RESET}")
        return

    flags = []
    total = 0

    print(f"{'NAMESPACE':20} {'NAME':35} {'TYPE':35} {'KEYS':5} {'SIZE':8} {'AGE':6} WARNINGS")
    print("-" * 120)

    for secret in secrets:
        meta = secret["metadata"]
        name = meta["name"]
        namespace = meta.get("namespace", "-")
        stype = secret.get("type", "Opaque")
        keys = len(secret.get("data", {}))
        size_kb = get_secret_size_kb(secret)
        age_days = get_age_days(secret)

        warnings = []
        if age_days > args.max_age_days:
            warnings.append(f"OLD({age_days}d)")
        if size_kb > args.max_size_kb:
            warnings.append(f"LARGE({size_kb:.1f}KB)")
        if stype in SENSITIVE_TYPES:
            warnings.append("SENSITIVE")

        warn_str = ", ".join(warnings)
        color = RED if warnings else GREEN

        total += 1
        if warnings:
            flags.append({"namespace": namespace, "name": name, "type": stype,
                          "age_days": age_days, "size_kb": size_kb, "warnings": warn_str})

        print(f"{namespace:20} {color}{name:35}{RESET} {stype:35} {keys:<5} "
              f"{size_kb:>6.1f}KB {age_days:>4}d  {YELLOW}{warn_str}{RESET}")

    print(f"\nTotal secrets: {total}")
    print(f"Flagged:       {len(flags)}")

    if flags:
        print(f"\n{RED}--- Flagged Secrets ---{RESET}")
        for f in flags:
            print(f"  {f['namespace']}/{f['name']} → {YELLOW}{f['warnings']}{RESET}")
        print(f"\n{CYAN}Recommendations:{RESET}")
        print("  - Rotate secrets older than 1 year")
        print("  - Investigate unexpectedly large secrets")
        print("  - Ensure sensitive secrets are encrypted at rest (EncryptionConfiguration)")
        print("  - Consider using external secrets (Vault, AWS Secrets Manager, etc.)")
    else:
        print(f"\n{GREEN}No secrets require immediate attention.{RESET}")


if __name__ == "__main__":
    main()
