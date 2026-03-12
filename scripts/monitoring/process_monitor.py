#!/usr/bin/env python3
"""
process_monitor.py
Monitors CPU and memory usage of specific processes by name.
Alerts when thresholds are exceeded.
Usage: python process_monitor.py --process nginx --cpu-threshold 80 --mem-threshold 500
"""

import argparse
import sys
import time

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def find_processes(name: str) -> list:
    matches = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "cpu_percent", "memory_info", "status"]):
        try:
            if name.lower() in proc.info["name"].lower():
                matches.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return matches


def get_proc_stats(proc) -> dict:
    try:
        with proc.oneshot():
            cpu = proc.cpu_percent(interval=0.1)
            mem = proc.memory_info()
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "cpu_pct": cpu,
                "mem_mb": round(mem.rss / 1024 / 1024, 1),
                "status": proc.status(),
                "cmdline": " ".join(proc.cmdline())[:60]
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def main():
    if not HAS_PSUTIL:
        print(f"{RED}psutil not installed. Run: pip install psutil{RESET}")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Monitor process resource usage")
    parser.add_argument("--process", required=True, help="Process name to monitor")
    parser.add_argument("--cpu-threshold", type=float, default=80.0)
    parser.add_argument("--mem-threshold", type=float, default=500.0, help="Memory threshold in MB")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring (refresh every 5s)")
    args = parser.parse_args()

    def run_check():
        procs = find_processes(args.process)
        print(f"\n{'='*70}")
        print(f"  Process Monitor: '{args.process}' | {time.strftime('%H:%M:%S')}")
        print(f"{'='*70}\n")

        if not procs:
            print(f"{RED}No process found matching '{args.process}'{RESET}")
            return False

        print(f"{'PID':8} {'NAME':20} {'CPU%':7} {'MEM(MB)':9} {'STATUS':12} CMDLINE")
        print("-" * 70)

        alerts = []
        for proc in procs:
            stats = get_proc_stats(proc)
            if not stats:
                continue
            cpu_color = RED if stats["cpu_pct"] >= args.cpu_threshold else GREEN
            mem_color = RED if stats["mem_mb"] >= args.mem_threshold else GREEN
            if stats["cpu_pct"] >= args.cpu_threshold or stats["mem_mb"] >= args.mem_threshold:
                alerts.append(stats)
            print(f"{stats['pid']:<8} {stats['name']:20} "
                  f"{cpu_color}{stats['cpu_pct']:>5.1f}%{RESET} "
                  f"{mem_color}{stats['mem_mb']:>7.1f}MB{RESET} "
                  f"{stats['status']:12} {stats['cmdline']}")

        total_cpu = sum(get_proc_stats(p)["cpu_pct"] for p in procs if get_proc_stats(p))
        print(f"\nTotal: {len(procs)} process(es) | Aggregate CPU: {total_cpu:.1f}%")

        if alerts:
            print(f"\n{RED}ALERT: {len(alerts)} process(es) above threshold!{RESET}")
        return bool(alerts)

    if args.watch:
        try:
            while True:
                run_check()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        if run_check():
            sys.exit(1)


if __name__ == "__main__":
    main()
