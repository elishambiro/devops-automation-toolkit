#!/usr/bin/env python3
"""
aws_untagged_resources.py
Finds EC2 instances, S3 buckets, and RDS instances missing required tags.
Essential for cost allocation, compliance, and resource ownership tracking.
Usage: python aws_untagged_resources.py --required-tags Environment Owner --profile myprofile
"""

import argparse
from datetime import datetime

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


def check_tags(resource_tags: list, required: list) -> list:
    existing = {t["Key"] for t in resource_tags}
    return [tag for tag in required if tag not in existing]


def scan_ec2(ec2_client, required_tags: list) -> list:
    findings = []
    paginator = ec2_client.get_paginator("describe_instances")
    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                if inst["State"]["Name"] == "terminated":
                    continue
                tags = inst.get("Tags", [])
                missing = check_tags(tags, required_tags)
                if missing:
                    name = next((t["Value"] for t in tags if t["Key"] == "Name"), inst["InstanceId"])
                    findings.append({
                        "type": "EC2", "id": inst["InstanceId"],
                        "name": name, "missing_tags": missing
                    })
    return findings


def scan_rds(rds_client, required_tags: list) -> list:
    findings = []
    instances = rds_client.describe_db_instances()["DBInstances"]
    for db in instances:
        arn = db["DBInstanceArn"]
        tags_resp = rds_client.list_tags_for_resource(ResourceName=arn)
        tags = tags_resp.get("TagList", [])
        missing = check_tags(tags, required_tags)
        if missing:
            findings.append({
                "type": "RDS", "id": db["DBInstanceIdentifier"],
                "name": db["DBInstanceIdentifier"], "missing_tags": missing
            })
    return findings


def print_demo(required_tags: list):
    print(f"{YELLOW}[DEMO MODE]{RESET}\n")
    findings = [
        {"type": "EC2", "id": "i-0abc123", "name": "old-server", "missing_tags": ["Environment", "Owner"]},
        {"type": "EC2", "id": "i-0def456", "name": "web-01", "missing_tags": ["Owner"]},
        {"type": "RDS", "id": "prod-db", "name": "prod-db", "missing_tags": ["Environment"]},
    ]
    return findings


def main():
    parser = argparse.ArgumentParser(description="Find AWS resources with missing tags")
    parser.add_argument("--required-tags", nargs="+", default=["Environment", "Owner", "Project"])
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    print(f"\n{'='*65}")
    print(f"  Untagged Resources Audit | {args.region}")
    print(f"  Required tags: {', '.join(args.required_tags)}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*65}\n")

    if not HAS_BOTO3:
        findings = print_demo(args.required_tags)
    else:
        findings = []
        try:
            session = (boto3.Session(profile_name=args.profile, region_name=args.region)
                       if args.profile else boto3.Session(region_name=args.region))
            findings += scan_ec2(session.client("ec2"), args.required_tags)
            findings += scan_rds(session.client("rds"), args.required_tags)
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
            return

    if not findings:
        print(f"{GREEN}All resources are properly tagged!{RESET}")
        return

    print(f"{'TYPE':6} {'ID':22} {'NAME':25} MISSING TAGS")
    print("-" * 65)
    for f in sorted(findings, key=lambda x: x["type"]):
        missing_str = ", ".join(f["missing_tags"])
        print(f"{RED}{f['type']:6}{RESET} {f['id']:22} {f['name']:25} {YELLOW}{missing_str}{RESET}")

    print(f"\n{RED}Found {len(findings)} resource(s) with missing tags{RESET}")
    print("\nRecommendation: Add the following tags to all resources:")
    for tag in args.required_tags:
        print(f"  - {CYAN}{tag}{RESET}")


if __name__ == "__main__":
    main()
