#!/usr/bin/env python3
"""
check_services_health.py
Checks HTTP health of multiple services and reports status.
Usage: python check_services_health.py --config services.json
       python check_services_health.py --urls http://app1/health http://app2/health
"""

import argparse
import json
import sys
import time
import requests

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_url(url: str, timeout: int = 5) -> dict:
    try:
        start = time.time()
        resp = requests.get(url, timeout=timeout)
        latency = round((time.time() - start) * 1000, 2)
        status = "UP" if resp.status_code < 400 else "DEGRADED"
        return {"url": url, "status": status, "http_code": resp.status_code, "latency_ms": latency}
    except requests.exceptions.ConnectionError:
        return {"url": url, "status": "DOWN", "http_code": None, "latency_ms": None}
    except requests.exceptions.Timeout:
        return {"url": url, "status": "TIMEOUT", "http_code": None, "latency_ms": None}


def print_result(result: dict):
    color = GREEN if result["status"] == "UP" else RED
    code = result["http_code"] or "N/A"
    latency = f"{result['latency_ms']}ms" if result["latency_ms"] else "N/A"
    print(f"{color}[{result['status']:8}]{RESET} {result['url']:50} code={code} latency={latency}")


def main():
    parser = argparse.ArgumentParser(description="Check health of multiple services")
    parser.add_argument("--urls", nargs="+", help="List of URLs to check")
    parser.add_argument("--config", help="JSON config file with URLs")
    parser.add_argument("--timeout", type=int, default=5, help="Request timeout in seconds")
    args = parser.parse_args()

    urls = []
    if args.config:
        with open(args.config) as f:
            urls = json.load(f).get("urls", [])
    elif args.urls:
        urls = args.urls
    else:
        # Demo mode
        urls = ["https://httpbin.org/status/200", "https://httpbin.org/status/500"]

    print(f"\n{'='*70}")
    print(f"  Health Check Report - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    results = [check_url(url, args.timeout) for url in urls]
    for r in results:
        print_result(r)

    down = [r for r in results if r["status"] in ("DOWN", "TIMEOUT")]
    print(f"\nSummary: {len(results) - len(down)}/{len(results)} services UP")

    if down:
        print(f"\n{RED}ALERT: {len(down)} service(s) are DOWN:{RESET}")
        for r in down:
            print(f"  - {r['url']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
