#!/usr/bin/env python3
"""
aws_cost_report.py
Pulls AWS cost and usage report for the last N days, grouped by service.
Requires: AWS CLI configured or boto3 with valid credentials.
Usage: python aws_cost_report.py --days 30 --profile myprofile
"""

import argparse
import json
from datetime import datetime, timedelta

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def get_cost_report(days: int, profile: str = None) -> list:
    if not HAS_BOTO3:
        raise ImportError("boto3 not installed. Run: pip install boto3")

    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    client = session.client("ce", region_name="us-east-1")

    end = datetime.today()
    start = end - timedelta(days=days)

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start.strftime("%Y-%m-%d"),
            "End": end.strftime("%Y-%m-%d")
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
    )

    results = []
    for period in response["ResultsByTime"]:
        for group in period["Groups"]:
            service = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if amount > 0:
                results.append({"service": service, "cost": amount})

    return sorted(results, key=lambda x: x["cost"], reverse=True)


def print_demo():
    print(f"\n{YELLOW}[DEMO MODE] boto3 not available - showing sample data{RESET}\n")
    demo_data = [
        {"service": "Amazon EC2", "cost": 142.50},
        {"service": "Amazon RDS", "cost": 89.20},
        {"service": "Amazon S3", "cost": 23.10},
        {"service": "AWS Lambda", "cost": 12.05},
        {"service": "Amazon CloudWatch", "cost": 8.40},
        {"service": "Amazon ECS", "cost": 5.90},
    ]
    return demo_data


def main():
    parser = argparse.ArgumentParser(description="AWS Cost Report")
    parser.add_argument("--days", type=int, default=30, help="Number of days to report")
    parser.add_argument("--profile", help="AWS profile name")
    parser.add_argument("--top", type=int, default=10, help="Show top N services")
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  AWS Cost Report - Last {args.days} days")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}\n")

    try:
        data = get_cost_report(args.days, args.profile)
    except Exception:
        data = print_demo()

    total = sum(d["cost"] for d in data)
    top = data[:args.top]

    print(f"{'SERVICE':45} {'COST':>10}")
    print("-" * 55)

    for item in top:
        pct = (item["cost"] / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 5)
        color = RED if pct > 30 else (YELLOW if pct > 15 else GREEN)
        print(f"{color}{item['service']:45} ${item['cost']:>8.2f}  {bar}{RESET}")

    print("-" * 55)
    print(f"{CYAN}{'TOTAL':45} ${total:>8.2f}{RESET}")
    print(f"\nShowing top {len(top)} of {len(data)} services")


if __name__ == "__main__":
    main()
