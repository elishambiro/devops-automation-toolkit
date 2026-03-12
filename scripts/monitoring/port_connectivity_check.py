#!/usr/bin/env python3
"""
port_connectivity_check.py
Tests TCP connectivity to a list of host:port pairs.
Useful for validating firewall rules, service availability, and network changes.
Usage: python port_connectivity_check.py --targets 10.0.0.1:5432 redis.internal:6379
       python port_connectivity_check.py --config targets.json
"""

import argparse
import json
import socket
import time

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

COMMON_SERVICES = {
    22: "SSH", 80: "HTTP", 443: "HTTPS", 3306: "MySQL",
    5432: "PostgreSQL", 6379: "Redis", 27017: "MongoDB",
    9200: "Elasticsearch", 9090: "Prometheus", 3000: "Grafana"
}


def check_port(host: str, port: int, timeout: float = 3.0) -> dict:
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency = round((time.time() - start) * 1000, 2)
            return {"host": host, "port": port, "status": "OPEN", "latency_ms": latency}
    except socket.timeout:
        return {"host": host, "port": port, "status": "TIMEOUT", "latency_ms": None}
    except ConnectionRefusedError:
        return {"host": host, "port": port, "status": "REFUSED", "latency_ms": None}
    except OSError:
        return {"host": host, "port": port, "status": "UNREACHABLE", "latency_ms": None}


def main():
    parser = argparse.ArgumentParser(description="TCP port connectivity checker")
    parser.add_argument("--targets", nargs="+", help="host:port targets")
    parser.add_argument("--config", help="JSON file with targets list")
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()

    targets = []
    if args.config:
        with open(args.config) as f:
            targets = json.load(f).get("targets", [])
    elif args.targets:
        targets = args.targets
    else:
        targets = ["localhost:22", "localhost:80", "localhost:443"]

    print(f"\n{'='*65}")
    print(f"  Port Connectivity Check - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}\n")
    print(f"{'HOST':30} {'PORT':6} {'SERVICE':15} {'STATUS':10} {'LATENCY'}")
    print("-" * 65)

    failed = []
    for target in targets:
        host, port = target.rsplit(":", 1)
        port = int(port)
        r = check_port(host, port, args.timeout)
        service = COMMON_SERVICES.get(port, "unknown")
        color = GREEN if r["status"] == "OPEN" else RED
        latency = f"{r['latency_ms']}ms" if r["latency_ms"] else "N/A"
        print(f"{color}{host:30} {port:<6} {service:15} {r['status']:10} {latency}{RESET}")
        if r["status"] != "OPEN":
            failed.append(target)

    print(f"\nResult: {len(targets) - len(failed)}/{len(targets)} ports reachable")
    if failed:
        print(f"{RED}Unreachable: {', '.join(failed)}{RESET}")


if __name__ == "__main__":
    main()
