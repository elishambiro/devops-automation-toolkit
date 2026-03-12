#!/usr/bin/env python3
"""
disk_usage_alert.py
Monitors disk usage on all mount points and alerts when usage exceeds threshold.
Usage: python disk_usage_alert.py --threshold 80 --critical 90
"""

import argparse
import shutil
import os
import sys

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def get_disk_usage() -> list:
    results = []
    partitions = []

    try:
        import psutil
        partitions = psutil.disk_partitions()
        for p in partitions:
            try:
                usage = psutil.disk_usage(p.mountpoint)
                results.append({
                    "mountpoint": p.mountpoint,
                    "device": p.device,
                    "total_gb": round(usage.total / (1024**3), 1),
                    "used_gb": round(usage.used / (1024**3), 1),
                    "free_gb": round(usage.free / (1024**3), 1),
                    "percent": usage.percent
                })
            except PermissionError:
                pass
    except ImportError:
        # Fallback: check current filesystem only
        usage = shutil.disk_usage("/")
        results.append({
            "mountpoint": "/",
            "device": "unknown",
            "total_gb": round(usage.total / (1024**3), 1),
            "used_gb": round(usage.used / (1024**3), 1),
            "free_gb": round(usage.free / (1024**3), 1),
            "percent": round(usage.used / usage.total * 100, 1)
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="Monitor disk usage")
    parser.add_argument("--threshold", type=float, default=80.0, help="Warning threshold %%")
    parser.add_argument("--critical", type=float, default=90.0, help="Critical threshold %%")
    args = parser.parse_args()

    disks = get_disk_usage()

    print(f"\n{'='*70}")
    print(f"  Disk Usage Report")
    print(f"{'='*70}")
    print(f"\n{'MOUNT':20} {'TOTAL':8} {'USED':8} {'FREE':8} {'USE%':6} STATUS")
    print("-" * 70)

    alerts = []
    for d in disks:
        pct = d["percent"]
        if pct >= args.critical:
            color, status = RED, "CRITICAL"
            alerts.append(d)
        elif pct >= args.threshold:
            color, status = YELLOW, "WARNING"
            alerts.append(d)
        else:
            color, status = GREEN, "OK"

        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        print(f"{color}{d['mountpoint']:20} {d['total_gb']:>6}GB {d['used_gb']:>6}GB {d['free_gb']:>6}GB {pct:>5}% [{bar}] {status}{RESET}")

    if alerts:
        print(f"\n{RED}ALERT: {len(alerts)} partition(s) above threshold!{RESET}")
        sys.exit(1)
    else:
        print(f"\n{GREEN}All partitions within normal range.{RESET}")


if __name__ == "__main__":
    main()
