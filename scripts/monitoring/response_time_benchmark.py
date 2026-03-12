#!/usr/bin/env python3
"""
response_time_benchmark.py
Benchmarks API endpoints over N requests and reports p50/p95/p99 latency.
Usage: python response_time_benchmark.py --url http://api.example.com/health --requests 100
"""

import argparse
import statistics
import time
import concurrent.futures
import requests

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def make_request(url: str, method: str = "GET", payload: dict = None, timeout: int = 10) -> dict:
    start = time.time()
    try:
        if method == "POST":
            resp = requests.post(url, json=payload, timeout=timeout)
        else:
            resp = requests.get(url, timeout=timeout)
        latency = (time.time() - start) * 1000
        return {"success": True, "status_code": resp.status_code, "latency_ms": latency}
    except Exception as e:
        return {"success": False, "status_code": None, "latency_ms": None, "error": str(e)}


def percentile(data: list, pct: float) -> float:
    if not data:
        return 0
    sorted_data = sorted(data)
    index = int(len(sorted_data) * pct / 100)
    return round(sorted_data[min(index, len(sorted_data) - 1)], 2)


def main():
    parser = argparse.ArgumentParser(description="Benchmark API response times")
    parser.add_argument("--url", required=True)
    parser.add_argument("--requests", type=int, default=50, dest="num_requests")
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--method", default="GET", choices=["GET", "POST"])
    parser.add_argument("--threshold-p95", type=float, default=500.0, help="p95 alert threshold in ms")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("  API Benchmark")
    print(f"  URL:         {args.url}")
    print(f"  Requests:    {args.num_requests}")
    print(f"  Concurrency: {args.concurrency}")
    print(f"{'='*60}\n")

    results = []
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(make_request, args.url, args.method) for _ in range(args.num_requests)]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            results.append(result)
            if i % 10 == 0:
                print(f"  Progress: {i}/{args.num_requests}...", end="\r")

    total_time = time.time() - start_time
    latencies = [r["latency_ms"] for r in results if r["success"] and r["latency_ms"]]
    errors = [r for r in results if not r["success"]]
    success_rate = len(latencies) / len(results) * 100

    print(f"\n{'='*60}")
    print("  Results")
    print(f"{'='*60}\n")
    print(f"  Total requests:  {len(results)}")
    print(f"  Successful:      {len(latencies)} ({success_rate:.1f}%)")
    print(f"  Failed:          {len(errors)}")
    print(f"  Total time:      {total_time:.2f}s")
    print(f"  Throughput:      {len(results)/total_time:.1f} req/s\n")

    if latencies:
        p50 = percentile(latencies, 50)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)
        avg = round(statistics.mean(latencies), 2)
        color_p95 = RED if p95 > args.threshold_p95 else GREEN

        print(f"  {'METRIC':15} {'VALUE':>12}")
        print(f"  {'-'*30}")
        print(f"  {'Min':15} {min(latencies):>10.2f}ms")
        print(f"  {'Average':15} {avg:>10.2f}ms")
        print(f"  {'p50 (median)':15} {p50:>10.2f}ms")
        print(f"  {'p95':15} {color_p95}{p95:>10.2f}ms{RESET}")
        print(f"  {'p99':15} {p99:>10.2f}ms")
        print(f"  {'Max':15} {max(latencies):>10.2f}ms")

        if p95 > args.threshold_p95:
            print(f"\n{RED}ALERT: p95 latency ({p95}ms) exceeds threshold ({args.threshold_p95}ms){RESET}")


if __name__ == "__main__":
    main()
