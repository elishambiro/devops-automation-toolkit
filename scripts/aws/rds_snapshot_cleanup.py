#!/usr/bin/env python3
"""
rds_snapshot_cleanup.py
Deletes manual RDS snapshots older than N days.
Automated snapshots managed by AWS retention policy; this handles manual ones.
Usage: python rds_snapshot_cleanup.py --days 30 --profile myprofile --dry-run
"""

import argparse
from datetime import datetime, timezone

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"


def main():
    parser = argparse.ArgumentParser(description="Clean up old manual RDS snapshots")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--db-instance", help="Filter by DB instance identifier")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"\n{'='*65}")
    print(f"  RDS Snapshot Cleanup | Older than {args.days} days")
    if args.dry_run:
        print("  MODE: DRY RUN")
    print(f"{'='*65}\n")

    if not HAS_BOTO3:
        print(f"{YELLOW}[DEMO MODE]{RESET}\n")
        snapshots = [
            {"id": "mydb-snap-20240101", "db": "mydb", "age": 90, "size_gb": 20, "status": "available"},
            {"id": "mydb-snap-20240215", "db": "mydb", "age": 45, "size_gb": 21, "status": "available"},
            {"id": "mydb-snap-20240301", "db": "mydb", "age": 10, "size_gb": 22, "status": "available"},
        ]
        to_delete = [s for s in snapshots if s["age"] > args.days]
        print(f"Found {len(to_delete)} snapshot(s) older than {args.days} days:\n")
        for s in to_delete:
            print(f"  {YELLOW}[DELETE]{RESET} {s['id']} | {s['db']} | {s['age']}d old | {s['size_gb']}GB")
        return

    try:
        session = (boto3.Session(profile_name=args.profile, region_name=args.region)
                   if args.profile else boto3.Session(region_name=args.region))
        rds = session.client("rds")
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        return

    filters = [{"Name": "snapshot-type", "Values": ["manual"]}]
    if args.db_instance:
        filters.append({"Name": "db-instance-id", "Values": [args.db_instance]})

    snapshots = rds.describe_db_snapshots(Filters=filters)["DBSnapshots"]
    now = datetime.now(timezone.utc)

    to_delete = []
    for snap in snapshots:
        if snap["Status"] != "available":
            continue
        age = (now - snap["SnapshotCreateTime"]).days
        if age > args.days:
            to_delete.append({**snap, "age_days": age})

    print(f"Total manual snapshots: {len(snapshots)}")
    print(f"Snapshots to delete (>{args.days}d): {len(to_delete)}\n")

    deleted = 0
    freed_gb = 0
    for snap in to_delete:
        size = snap.get("AllocatedStorage", 0)
        print(f"  {snap['DBSnapshotIdentifier']:45} {snap['age_days']:3}d old  {size}GB")
        if not args.dry_run:
            rds.delete_db_snapshot(DBSnapshotIdentifier=snap["DBSnapshotIdentifier"])
            deleted += 1
            freed_gb += size
        else:
            print(f"    {YELLOW}[DRY RUN] Would delete{RESET}")

    if not args.dry_run:
        print(f"\n{GREEN}Deleted {deleted} snapshot(s), freed ~{freed_gb}GB{RESET}")
    else:
        total_size = sum(s.get("AllocatedStorage", 0) for s in to_delete)
        print(f"\n{YELLOW}[DRY RUN] Would delete {len(to_delete)} snapshot(s), free ~{total_size}GB{RESET}")


if __name__ == "__main__":
    main()
