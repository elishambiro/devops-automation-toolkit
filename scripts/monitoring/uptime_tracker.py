#!/usr/bin/env python3
"""
uptime_tracker.py
Polls a health endpoint every N seconds, logs results, and calculates uptime %.
Can run as a background job and produce reports.
Usage: python uptime_tracker.py --url http://app/health --interval 30 --duration 3600
       python uptime_tracker.py --report uptime.log
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def check_health(url: str, timeout: int = 5) -> dict:
    ts = datetime.utcnow().isoformat()
    try:
        start = time.time()
        resp = requests.get(url, timeout=timeout)
        latency = round((time.time() - start) * 1000, 2)
        up = resp.status_code < 400
        return {"timestamp": ts, "up": up, "status_code": resp.status_code, "latency_ms": latency}
    except Exception as e:
        return {"timestamp": ts, "up": False, "status_code": None, "latency_ms": None, "error": str(e)}


def show_report(log_file: str):
    path = Path(log_file)
    if not path.exists():
        print(f"{RED}Log file not found: {log_file}{RESET}")
        return

    records = []
    with open(path) as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                pass

    if not records:
        print("No records found.")
        return

    total = len(records)
    up_count = sum(1 for r in records if r.get("up"))
    uptime_pct = up_count / total * 100
    latencies = [r["latency_ms"] for r in records if r.get("latency_ms")]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0

    # Find outage windows
    outages = []
    in_outage = False
    outage_start = None
    for r in records:
        if not r["up"] and not in_outage:
            in_outage = True
            outage_start = r["timestamp"]
        elif r["up"] and in_outage:
            outages.append({"start": outage_start, "end": r["timestamp"]})
            in_outage = False

    color = GREEN if uptime_pct >= 99.9 else (RED if uptime_pct < 99 else "\033[93m")

    print(f"\n{'='*55}")
    print(f"  Uptime Report")
    print(f"  Period: {records[0]['timestamp']} → {records[-1]['timestamp']}")
    print(f"{'='*55}\n")
    print(f"  Uptime:       {color}{uptime_pct:.3f}%{RESET}  ({up_count}/{total} checks passed)")
    print(f"  Avg Latency:  {avg_latency}ms")
    print(f"  Outages:      {len(outages)}")

    if outages:
        print(f"\n{RED}  Outage Windows:{RESET}")
        for o in outages:
            print(f"    {o['start']} → {o['end']}")


def main():
    parser = argparse.ArgumentParser(description="Track service uptime over time")
    parser.add_argument("--url", help="Health endpoint URL")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    parser.add_argument("--duration", type=int, help="Total duration in seconds (omit for infinite)")
    parser.add_argument("--log", default="uptime.log", help="Output log file")
    parser.add_argument("--report", help="Generate report from existing log file")
    args = parser.parse_args()

    if args.report:
        show_report(args.report)
        return

    if not args.url:
        print("--url required for tracking mode")
        sys.exit(1)

    print(f"{CYAN}Starting uptime tracker for {args.url}{RESET}")
    print(f"Interval: {args.interval}s | Log: {args.log}\n")
    print("Press Ctrl+C to stop\n")

    start_time = time.time()
    checks = 0

    try:
        with open(args.log, "a") as log_file:
            while True:
                result = check_health(args.url)
                log_file.write(json.dumps(result) + "\n")
                log_file.flush()
                checks += 1

                status_str = f"{GREEN}UP{RESET}" if result["up"] else f"{RED}DOWN{RESET}"
                latency_str = f"{result['latency_ms']}ms" if result.get("latency_ms") else result.get("error", "")
                print(f"[{result['timestamp']}] {status_str} {latency_str}")

                if args.duration and (time.time() - start_time) >= args.duration:
                    break
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\nStopped after {checks} checks.")

    show_report(args.log)


if __name__ == "__main__":
    main()
