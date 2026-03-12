#!/usr/bin/env python3
"""
ec2_inventory.py
Generates a full inventory of EC2 instances: state, type, AZ, tags, private/public IPs.
Useful for auditing, documentation, and cost analysis.
Usage: python ec2_inventory.py --profile myprofile --region us-east-1 --filter running
"""

import argparse
from datetime import datetime

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

STATE_COLORS = {
    "running": GREEN, "stopped": YELLOW,
    "terminated": RED, "pending": CYAN
}


def get_tag(instance: dict, key: str, default: str = "-") -> str:
    for tag in instance.get("Tags", []):
        if tag["Key"] == key:
            return tag["Value"]
    return default


def get_instances(ec2_client, state_filter: str = None) -> list:
    filters = []
    if state_filter:
        filters.append({"Name": "instance-state-name", "Values": [state_filter]})

    instances = []
    paginator = ec2_client.get_paginator("describe_instances")
    for page in paginator.paginate(Filters=filters):
        for reservation in page["Reservations"]:
            instances.extend(reservation["Instances"])
    return instances


def print_demo():
    print(f"\n{YELLOW}[DEMO MODE] No AWS credentials - showing sample data{RESET}\n")
    demo = [
        {"name": "web-server-01", "id": "i-0abc123", "type": "t3.medium", "state": "running",
         "private_ip": "10.0.1.10", "public_ip": "54.23.11.5", "az": "us-east-1a", "env": "prod"},
        {"name": "api-server-01", "id": "i-0def456", "type": "t3.large", "state": "running",
         "private_ip": "10.0.1.11", "public_ip": "-", "az": "us-east-1b", "env": "prod"},
        {"name": "dev-instance", "id": "i-0ghi789", "type": "t2.micro", "state": "stopped",
         "private_ip": "10.0.2.5", "public_ip": "-", "az": "us-east-1a", "env": "dev"},
    ]
    return demo


def main():
    parser = argparse.ArgumentParser(description="EC2 instance inventory")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--filter", choices=["running", "stopped", "terminated"], help="Filter by state")
    parser.add_argument("--output", choices=["table", "csv"], default="table")
    args = parser.parse_args()

    print(f"\n{'='*90}")
    print(f"  EC2 Inventory | Region: {args.region} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*90}\n")

    if not HAS_BOTO3:
        demo = print_demo()
        print(f"{'NAME':20} {'ID':12} {'TYPE':12} {'STATE':10} {'PRIVATE IP':15} {'PUBLIC IP':15} {'AZ':14} ENV")
        print("-" * 90)
        for i in demo:
            color = STATE_COLORS.get(i["state"], RESET)
            print(f"{i['name']:20} {i['id']:12} {i['type']:12} {color}{i['state']:10}{RESET} "
                  f"{i['private_ip']:15} {i['public_ip']:15} {i['az']:14} {i['env']}")
        return

    try:
        session = (boto3.Session(profile_name=args.profile, region_name=args.region)
                   if args.profile else boto3.Session(region_name=args.region))
        ec2 = session.client("ec2")
        instances = get_instances(ec2, args.filter)
    except Exception:
        instances = []

    if args.output == "csv":
        print("Name,InstanceId,Type,State,PrivateIP,PublicIP,AZ,Environment")
        for i in instances:
            name = get_tag(i, "Name")
            env = get_tag(i, "Environment", get_tag(i, "Env", "-"))
            print(f"{name},{i['InstanceId']},{i['InstanceType']},{i['State']['Name']},"
                  f"{i.get('PrivateIpAddress', '-')},{i.get('PublicIpAddress', '-')},"
                  f"{i['Placement']['AvailabilityZone']},{env}")
    else:
        print(f"{'NAME':25} {'ID':20} {'TYPE':13} {'STATE':10} {'PRIVATE IP':15} {'AZ':14} ENV")
        print("-" * 100)
        counts = {}
        for i in instances:
            name = get_tag(i, "Name")
            env = get_tag(i, "Environment", get_tag(i, "Env", "-"))
            state = i["State"]["Name"]
            color = STATE_COLORS.get(state, RESET)
            counts[state] = counts.get(state, 0) + 1
            print(f"{name:25} {i['InstanceId']:20} {i['InstanceType']:13} "
                  f"{color}{state:10}{RESET} {i.get('PrivateIpAddress', '-'):15} "
                  f"{i['Placement']['AvailabilityZone']:14} {env}")

        print(f"\nTotal: {len(instances)} instance(s)")
        for state, count in counts.items():
            color = STATE_COLORS.get(state, RESET)
            print(f"  {color}{state}: {count}{RESET}")


if __name__ == "__main__":
    main()
