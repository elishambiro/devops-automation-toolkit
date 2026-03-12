#!/usr/bin/env python3
"""
s3_bucket_sizes.py
Lists all S3 buckets with their sizes and object counts.
Useful for auditing storage costs and finding large/unused buckets.
Usage: python s3_bucket_sizes.py --profile myprofile --sort size
"""

import argparse
from datetime import datetime, timezone

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def human_size(size_bytes: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def get_bucket_size(cw_client, bucket_name: str) -> tuple:
    try:
        now = datetime.now(timezone.utc)
        response = cw_client.get_metric_statistics(
            Namespace="AWS/S3",
            MetricName="BucketSizeBytes",
            Dimensions=[
                {"Name": "BucketName", "Value": bucket_name},
                {"Name": "StorageType", "Value": "StandardStorage"}
            ],
            StartTime=now.replace(hour=0, minute=0, second=0),
            EndTime=now,
            Period=86400,
            Statistics=["Average"]
        )
        points = response.get("Datapoints", [])
        size = points[-1]["Average"] if points else 0

        obj_response = cw_client.get_metric_statistics(
            Namespace="AWS/S3",
            MetricName="NumberOfObjects",
            Dimensions=[
                {"Name": "BucketName", "Value": bucket_name},
                {"Name": "StorageType", "Value": "AllStorageTypes"}
            ],
            StartTime=now.replace(hour=0, minute=0, second=0),
            EndTime=now,
            Period=86400,
            Statistics=["Average"]
        )
        obj_points = obj_response.get("Datapoints", [])
        objects = int(obj_points[-1]["Average"]) if obj_points else 0
        return size, objects
    except Exception:
        return 0, 0


def print_demo():
    print(f"\n{YELLOW}[DEMO MODE] Showing sample data{RESET}\n")
    return [
        {"name": "my-app-assets", "size": 2.5 * 1024**3, "objects": 12400, "region": "us-east-1"},
        {"name": "my-app-backups", "size": 15.2 * 1024**3, "objects": 320, "region": "us-east-1"},
        {"name": "logs-archive", "size": 0.8 * 1024**3, "objects": 8900, "region": "eu-west-1"},
        {"name": "terraform-state", "size": 0.001 * 1024**3, "objects": 12, "region": "us-east-1"},
    ]


def main():
    parser = argparse.ArgumentParser(description="List S3 bucket sizes")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--sort", choices=["size", "name", "objects"], default="size")
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"  S3 Bucket Size Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}\n")

    if not HAS_BOTO3:
        buckets = print_demo()
    else:
        try:
            session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
            s3 = session.client("s3")
            cw = session.client("cloudwatch", region_name="us-east-1")
            raw = s3.list_buckets().get("Buckets", [])
            buckets = []
            for b in raw:
                size, objects = get_bucket_size(cw, b["Name"])
                buckets.append({"name": b["Name"], "size": size, "objects": objects, "region": "us-east-1"})
        except Exception:
            buckets = print_demo()

    buckets.sort(key=lambda x: x[args.sort if args.sort != "size" else "size"], reverse=(args.sort == "size"))

    print(f"{'BUCKET':40} {'SIZE':12} {'OBJECTS':10} {'REGION'}")
    print("-" * 70)

    total_size = 0
    for b in buckets:
        color = YELLOW if b["size"] > 10 * 1024**3 else GREEN
        print(f"{color}{b['name']:40} {human_size(b['size']):12} {b['objects']:<10} {b['region']}{RESET}")
        total_size += b["size"]

    print("-" * 70)
    print(f"{CYAN}{'TOTAL':40} {human_size(total_size):12} across {len(buckets)} buckets{RESET}\n")


if __name__ == "__main__":
    main()
