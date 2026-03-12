#!/usr/bin/env python3
"""
cloudwatch_log_retention.py
Sets retention policies on CloudWatch log groups that have no retention (never expire).
Unmanaged log groups accumulate forever and increase costs significantly.
Usage: python cloudwatch_log_retention.py --retention 30 --profile myprofile --dry-run
"""

import argparse

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"

VALID_RETENTIONS = [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]


def main():
    parser = argparse.ArgumentParser(description="Set CloudWatch log retention policies")
    parser.add_argument("--retention", type=int, default=30, help="Retention in days")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--prefix", help="Only affect log groups matching this prefix")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.retention not in VALID_RETENTIONS:
        print(f"{RED}Invalid retention. Must be one of: {VALID_RETENTIONS}{RESET}")
        return

    print(f"\n{'='*65}")
    print("  CloudWatch Log Retention Manager")
    print(f"  Retention: {args.retention} days | Region: {args.region}")
    if args.dry_run:
        print("  MODE: DRY RUN")
    print(f"{'='*65}\n")

    if not HAS_BOTO3:
        print(f"{YELLOW}[DEMO MODE]{RESET}")
        groups = [
            {"logGroupName": "/aws/lambda/my-function", "retentionInDays": None},
            {"logGroupName": "/aws/ecs/my-app", "retentionInDays": 7},
            {"logGroupName": "/app/nginx/access", "retentionInDays": None},
        ]
        no_retention = [g for g in groups if g["retentionInDays"] is None]
        print(f"Found {len(no_retention)} log groups without retention:\n")
        for g in no_retention:
            print(f"  {YELLOW}[NO RETENTION]{RESET} {g['logGroupName']}")
            if not args.dry_run:
                print(f"  → Would set to {args.retention} days")
        return

    try:
        session = (boto3.Session(profile_name=args.profile, region_name=args.region)
                   if args.profile else boto3.Session(region_name=args.region))
        logs = session.client("logs")
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        return

    paginator = logs.get_paginator("describe_log_groups")
    kwargs = {}
    if args.prefix:
        kwargs["logGroupNamePrefix"] = args.prefix

    no_retention = []
    has_retention = []
    for page in paginator.paginate(**kwargs):
        for group in page["logGroups"]:
            if group.get("retentionInDays") is None:
                no_retention.append(group)
            else:
                has_retention.append(group)

    print(f"Log groups without retention: {YELLOW}{len(no_retention)}{RESET}")
    print(f"Log groups with retention:    {GREEN}{len(has_retention)}{RESET}\n")

    updated = 0
    for group in no_retention:
        name = group["logGroupName"]
        if args.dry_run:
            print(f"{YELLOW}[DRY RUN]{RESET} Would set {name} → {args.retention}d")
        else:
            logs.put_retention_policy(logGroupName=name, retentionInDays=args.retention)
            print(f"{GREEN}Updated:{RESET} {name} → {args.retention} days")
            updated += 1

    print(f"\n{'[DRY RUN] Would update' if args.dry_run else 'Updated'}: {len(no_retention)} log groups")


if __name__ == "__main__":
    main()
